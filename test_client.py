import grpc
import firefly_pb2
import firefly_pb2_grpc

def test_send_phase(firefly_id, port):
    try:
        with grpc.insecure_channel(f'127.0.0.1:{port}') as channel:
            stub = firefly_pb2_grpc.FireflyServiceStub(channel)
            message = firefly_pb2.PhaseMessage(id='test_client', phase=0.0)
            response = stub.SendPhase(message, timeout=5)
            print(f'Successfully sent phase to Firefly {firefly_id} on port {port}')
    except grpc.RpcError as e:
        print(f'Failed to send phase to Firefly {firefly_id} on port {port}: {e}')
        print(f'gRPC Status Code: {e.code()}')
        print(f'gRPC Details: {e.details()}')

if __name__ == '__main__':
    test_send_phase(firefly_id=1, port=5001)
