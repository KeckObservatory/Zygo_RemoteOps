

# Google RPC + protocol buffer generated code, build it with:
# pip install grpcio grpcio-tools
# python3 -m grpc_tools.protoc  --python_out=. --pyi_out=. --grpc_python_out=. -I=. nb.proto
import grpc
import dmat_pb2
import dmat_pb2_grpc
import os
import matplotlib.pyplot as plt
from convert_files import *
import tempfile

channel_options = [
    ('grpc.max_receive_message_length', 1024 * 1024 * 20)  # 10 MB
]

#host ='vm-aodev'
host = 'zygo-pc.keck.hawaii.edu'
#host = '10.96.10.200'
# host = '127.0.0.1'
port = '50051'


ZYGO_DIR  = "/home/mvincent/PycharmProjects/DMAcceptanceTest"
ZYGO_NAME = "current_measurement.datx"
ZYGO_PATH = os.path.join(ZYGO_DIR, ZYGO_NAME)

class Zygo():
    def __init__(self):
        self.channel = None
        self.zygo_stub = None

    def expose(self):
        if self.channel is None:
            self.channel = grpc.insecure_channel('{}:{}'.format(host, port), options=channel_options)
        if self.zygo_stub is None:
            self.zygo_stub = dmat_pb2_grpc.ZygoStub(self.channel)

        request_expose = dmat_pb2.ExposeRequest()
        reply_expose = self.zygo_stub.Expose(request_expose)
        data = None

        if reply_expose.success:
            request_retrieve = dmat_pb2.RetrieveRequest()
            reply_retrieve = self.zygo_stub.Retrieve(request_retrieve)
            data = reply_retrieve.filedata
            MODE = 'zygo'
        else:
            print('Expose failed')
            MODE = 'test'

        if MODE == 'zygo':
            # Atomically write to canonical file path
            os.makedirs(ZYGO_DIR, exist_ok=True)
            fd, tmp = tempfile.mkstemp(prefix="current_measurement_", suffix=".datx", dir=ZYGO_DIR)
            os.close(fd)
            with open(tmp, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, ZYGO_PATH)

        elif MODE == 'test':
            # For test mode, just use existing canonical file
            if not os.path.exists(ZYGO_PATH):
                raise FileNotFoundError(f"Test mode: {ZYGO_PATH} not found")
        
        # # access the data
        data = convert_datx_list(ZYGO_PATH)
        # # delete this file once done
        # if MODE == 'zygo':
            # os.remove(fname)
        return data
# Sensors


if __name__ == '__main__':
    zygo = Zygo()
    test = zygo.expose()
    plt.imshow(test, origin='lower', cmap='magma'); plt.colorbar(); plt.show()
