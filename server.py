import grpc
from concurrent import futures
import time
import service_pb2
import service_pb2_grpc

class TestService(service_pb2_grpc.TestServiceServicer):
    def SayHello(self, request, context):
        return service_pb2.HelloReply(message=f"Hello, {request.name}!")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_TestServiceServicer_to_server(TestService(), server)
    
    # Local development: use insecure port (no SSL)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC server running on port 50051...")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve()
