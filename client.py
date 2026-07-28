

# Google RPC + protocol buffer generated code, build it with:
# pip install grpcio grpcio-tools
# python3 -m grpc_tools.protoc  --python_out=. --pyi_out=. --grpc_python_out=. -I=. nb.proto
import grpc
import dmat_pb2
import dmat_pb2_grpc

channel_options = [
    ('grpc.max_receive_message_length', 1024 * 1024 * 20)  # 10 MB
]

#host ='vm-aodev'
# host = 'zygo-pc.keck.hawaii.edu'
host = '127.0.0.1'
port = '50051'

channel = grpc.insecure_channel(f'{host}:{port}', options=channel_options)
zygo_stub = dmat_pb2_grpc.ZygoStub(channel)

request_expose = dmat_pb2.ExposeRequest()
reply_expose = zygo_stub.Expose(request_expose)

if reply_expose.success:
    request_retrieve = dmat_pb2.RetrieveRequest()
    reply_retrieve = zygo_stub.Retrieve(request_retrieve)
    data = reply_retrieve.filedata
    print(len(data))

# Sensors