 # function to read in the data file and return the height map
import h5py
import numpy as np

class ZygoFile:
    def __init__(self, file_path):
        self.file_path = file_path


    def read_intensity_map(self):
        """
        Read the intensity map from a Zygo .datx file.
        :return: intensity_m (numpy.ndarray)
        """
        # Open the file and read the data
        with h5py.File(self.file_path, 'r') as f:
            uuid = list(f['Data']['Intensity'].keys())[0]
            dset = f['Data']['Intensity'][uuid]
            intensity_raw = dset[()]
            attrs = dset.attrs

            nodata_val = attrs['No Data'][0]
            intensity_raw = np.where(intensity_raw == nodata_val, np.nan, intensity_raw)

            return intensity_raw
    

    def read_height_map(self, assume_opd=False):
        """
        Read the height map from a Zygo .datx file.
        :param assume_opd: If True, assumes the data is in OPD (Optical Path Difference) format.
        :return: height_m (numpy.ndarray), wavelength_m (float)
        """
        # Open the file and read the data
        with h5py.File(self.file_path, 'r') as f:
            uuid = list(f['Data']['Surface'].keys())[0]
            dset = f['Data']['Surface'][uuid]
            z_raw = dset[()]
            attrs = dset.attrs

            nodata_val = attrs['No Data'][0]
            z_raw = np.where(z_raw == nodata_val, np.nan, z_raw)

            zc = attrs['Z Converter'][0][2]
            wavelength_m = float(zc[1])
            scale_factor = float(zc[2])
            height_m = z_raw * wavelength_m * scale_factor

            if assume_opd:
                height_m = height_m / 2.0
        return height_m, wavelength_m
    
    def zernike_basis_j1234(self, x, y):
        """
        Minimal Zernike set up to j=4 (Noll indexing): piston (1), tip (2), tilt (3), defocus/power (4).
        Defined on unit disk; outside the unit circle the basis is 0.

        :param x: 2D array, normalized x in [-1,1]
        :param y: 2D array, normalized y in [-1,1]
        :return: list of 2D arrays [Z1, Z2, Z3, Z4]
        """
        r = np.sqrt(x**2 + y**2)
        theta = np.arctan2(y, x)

        Z1 = np.ones_like(r)
        Z2 = 2 * r * np.cos(theta)              # x-tilt
        Z3 = 2 * r * np.sin(theta)              # y-tilt
        Z4 = np.sqrt(3) * (2*r**2 - 1)          # defocus/power

        # zero outside unit circle
        outside = r > 1.0
        for Z in (Z1, Z2, Z3, Z4):
            Z[outside] = 0.0

        return [Z1, Z2, Z3, Z4]
    
    def make_unit_disk_coords(self, mask):
        """
        Build normalized coordinates (x,y) in a unit disk covering the valid mask.
        :param mask: 2D boolean array, True where data is valid/aperture.
        :return: (x_n, y_n)
            x_n, y_n: 2D arrays of normalized coordinates in [-1,1] mapped to the circumscribed circle.
        """
        h, w = mask.shape
        yy, xx = np.indices((h, w))
        cy = (np.nanmin(yy[mask]) + np.nanmax(yy[mask])) / 2.0
        cx = (np.nanmin(xx[mask]) + np.nanmax(xx[mask])) / 2.0
        r = np.nanmax(np.sqrt((xx[mask]-cx)**2 + (yy[mask]-cy)**2))
        x_n = (xx - cx) / r
        y_n = (yy - cy) / r
        return x_n, y_n

    def detrend_height_map(self, height_m):
        aperture_mask = ~np.isnan(height_m)
        x_n, y_n = self.make_unit_disk_coords(aperture_mask)
        Zs = self.zernike_basis_j1234(x_n, y_n)
        r = np.sqrt(x_n**2 + y_n**2)
        valid = aperture_mask & (r <= 1.0) & ~np.isnan(height_m)
        A = np.stack([Z[valid] for Z in Zs], axis=1)
        b = height_m[valid]
        coeffs, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
        fit = np.zeros_like(height_m)
        for c, Z in zip(coeffs, Zs):
            fit += c * Z
        out = height_m - fit
        out[~valid] = np.nan
        return out

    
# define wrappers for easy access

def convert_datx_list(file_fullpath):
    zygo = ZygoFile(file_fullpath)
    height_m, _ = zygo.read_height_map()
    height_m_detrended = zygo.detrend_height_map(height_m)
    return height_m_detrended


def convert_datx_intensity(file_fullpath):
    zygo = ZygoFile(file_fullpath)
    intensity_map = zygo.read_intensity_map()
    return intensity_map


def compute_ptv_rms(height_m_detrended):
        
        wavelength = 6.328e-07
        # Basic aperture (for RMS)
        ap_basic = ~np.isnan(height_m_detrended)
        roi_basic = height_m_detrended[ap_basic]
        rms_basic_waves = np.nanstd(roi_basic) / wavelength

        # PV-only ROI (start from provided mask or basic)
        pv_clip_frac=0.0005
        pv_erosion_iters=0
        pv_only_mask=None
        ap_pv = pv_only_mask.copy() if pv_only_mask is not None else ap_basic.copy()

        # cheap 4-neighbor erosion (no extra deps)
        def erode4(mask, iters=1):
            m = mask.copy()
            for _ in range(max(0, int(iters))):
                up    = np.roll(m, -1, axis=0)
                down  = np.roll(m,  1, axis=0)
                left  = np.roll(m,  1, axis=1)
                right = np.roll(m, -1, axis=1)
                m = m & up & down & left & right
                # zero out the rolled-in edges to avoid wrap-around artifacts
                m[0, :] = m[-1, :] = m[:, 0] = m[:, -1] = False
            return m

        if pv_erosion_iters > 0:
            ap_pv = erode4(ap_pv, pv_erosion_iters)

        # Percentile-clipped PV on PV-only ROI
        roi_pv = height_m_detrended[ap_pv & ~np.isnan(height_m_detrended)]
        if roi_pv.size:
            lo, hi = np.nanpercentile(roi_pv, [100*pv_clip_frac, 100*(1.0 - pv_clip_frac)])
            pv_match_waves = (hi - lo) / wavelength
        else:
            pv_match_waves = np.nan

        return pv_match_waves, rms_basic_waves