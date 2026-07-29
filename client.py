

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
host = 'zygo-pc.keck.hawaii.edu'
port = '50051'

channel = grpc.insecure_channel(f'{host}:{port}', options=channel_options)
zygo_stub = dmat_pb2_grpc.ZygoStub(channel)

print(f'Connecting to {host}:{port}...')
request_expose = dmat_pb2.ExposeRequest()
reply_expose = zygo_stub.Expose(request_expose)

if reply_expose.success:
    print('Expose succeeded, retrieving file...')
    request_retrieve = dmat_pb2.RetrieveRequest()
    reply_retrieve = zygo_stub.Retrieve(request_retrieve)
    data = reply_retrieve.filedata
    if data:
        print(f'Retrieved {len(data)} bytes')
    else:
        print('Retrieve failed: file does not exist on server')
else:
    print('Expose failed: check server-side console for the exception')

# Sensors