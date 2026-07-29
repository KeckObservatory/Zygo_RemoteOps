# Zygo_RemoteOps

gRPC client/server for triggering exposures on the Zygo interferometer and retrieving/parsing the resulting `.datx` file.

Split out from `DMAcceptanceTest`.

## Layout

- `dmat.proto` — gRPC service definition (`Zygo`: `Expose`, `Retrieve`)
- `dmat_pb2.py`, `dmat_pb2_grpc.py` — generated from `dmat.proto` (regenerate with `python -m grpc_tools.protoc --python_out=. --pyi_out=. --grpc_python_out=. -I=. dmat.proto`)
- `server.py` — runs on the Zygo Windows PC; uses the Zygo Mx scripting API to trigger a measurement and serve the file over gRPC
- `client.py` — minimal smoke-test client for the gRPC service
- `zygo_client.py` — `Zygo` client class (`expose()`) for use in other scripts
- `convert_files.py` — parses `.datx` files (`ZygoFile`, `convert_datx_list`, etc.)

## Notes

`zygo_client.py` currently hardcodes a host (`zygo-pc.keck.hawaii.edu`) — update this for your environment.

`ZYGO_DIR` defaults to `~/zygo_data`, created on first exposure. This is scratch space, not storage: it holds a single `current_measurement.datx` that gets overwritten by every `expose()` call. Don't point it at a self-cleaning temp directory — `expose()`'s test-mode fallback (used when the RPC call fails) reads whatever `current_measurement.datx` was left over from the last successful exposure, so the file needs to persist between runs.
