from concurrent import futures
from threading import Thread, Event

# Google RPC + protocol buffer generated code, build it with:
# pip install grpcio grpcio-tools
# python3 -m grpc_tools.protoc  --python_out=. --pyi_out=. --grpc_python_out=. -I=. dmat.proto
import grpc
import dmat_pb2
import dmat_pb2_grpc

import os

import sys
p = r"C:\ProgramData\Zygo\Mx\Scripting"
if p not in sys.path:
    sys.path.insert(0, p)

# Zygo imports
from zygo.core import *
from zygo import mx, ui
from zygo import instrument, motion

RPC_SERVICE_PORT = 50051

class RPCZygoServicer(dmat_pb2_grpc.ZygoServicer):
    """Implements the status responses for the GRPC server."""

    def __init__(self):
        super(RPCZygoServicer, self).__init__()
        self.data_dir = r'C:\Users\zygo\Documents\Mx\Scripts'
        self.filename = 'current_measurement.datx'


    def Expose(self, request, context):

        reply = dmat_pb2.ExposeReply()

        try:
            os.remove(os.path.join(self.data_dir, self.filename))
        except FileNotFoundError:
            pass
        try:
            instrument.measure(wait=True)
            reply.success = True
        except Exception as e:
            print(f'Instrument measurement failed :( {e}')
            reply.success = False
        else:
            mx.save_data(os.path.join(self.data_dir, self.filename))
        print(f'Received request to expose and temporarily save data.')

        return reply

    def Retrieve(self, request, context):

        reply = dmat_pb2.RetrieveReply()
        file = os.path.join(self.data_dir, self.filename)
        if os.path.exists(file):
            with open(file, 'rb') as f:
                reply.filedata = f.read()
        else:
            print(f'File {file} does not exist, try again.')
            reply.exists = False

        return reply

class RPCService:
    """Wrapper around the GRPC server for threaded control."""

    _stop = False

    def __init__(self, stop_event=None, debug=False, log=None):

        # Common to all tasks are a stop event, logger, and a debug flag
        self.stop_event  = Event()
        self.log         = log
        self.debug       = debug

        # Normal thread cycle @ 10 Hz
        self.tickrate    = 0.1

    def run(self):
        """Thread run method"""

        # # Start the RPC service
        # server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

        # # Create the RPC status servicer and give it our logger
        # zygo_servicer = RPCZygoServicer()
        # dmat_pb2_grpc.add_ZygoServicer_to_server(zygo_servicer, server)

        # server.add_insecure_port(f'0.0.0.0:{RPC_SERVICE_PORT}')
        # server.start()

        # print(f'Started RPC service on port {RPC_SERVICE_PORT}')
        # # Run this loop at using the stop event timeout as our tick
        # while not self.stop_event.wait(self.tickrate):
        #     # There's actually nothing to do in this loop except let the thread
        #     # run until stop is asserted
        #     pass

        # # Stop the server on the way out
        # server.stop()

        # return('Service task complete.')

        # Start the RPC service
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

        # Register servicer
        zygo_servicer = RPCZygoServicer()
        dmat_pb2_grpc.add_ZygoServicer_to_server(zygo_servicer, server)

        # ***** IMPORTANT: bind IPv4 explicitly *****
        # Option A (listen on all IPv4 interfaces):
        server.add_insecure_port(f'0.0.0.0:{RPC_SERVICE_PORT}')
        # Option B (safer on multi-NIC machines): bind to the exact server IP
        # server.add_insecure_port('192.168.176.158:50051')

        server.start()
        print(f'Started RPC service on 0.0.0.0:{RPC_SERVICE_PORT}')

        # Prefer this over the custom loop:
        server.wait_for_termination()

        # If you prefer your loop, at least keep stop() graceful:
        # try:
        #     while not self.stop_event.wait(self.tickrate):
        #         pass
        # finally:
        #     server.stop(grace=None)

if __name__ == '__main__':
    rpc = RPCService()
    rpc.run()
