
import asyncio
import websockets

# 연결된 클라이언트를 저장할 집합
connected_clients = set()

async def handler(websocket):
    """
    클라이언트 연결을 처리하고 메시지를 브로드캐스트합니다.
    """
    # 새로운 클라이언트 연결 추가
    connected_clients.add(websocket)
    print(f"New client connected: {websocket.remote_address}")

    try:
        # 클라이언트로부터 메시지를 계속 수신
        async for message in websocket:
            print(f"Received message from {websocket.remote_address}: {message}")
            
            # 연결된 모든 클라이언트에게 메시지 브로드캐스트
            for client in connected_clients:
                if client != websocket:
                    await client.send(f"Client {websocket.remote_address} says: {message}")
    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")
    finally:
        # 클라이언트 연결 종료 시 집합에서 제거
        connected_clients.remove(websocket)

async def main():
    """
    웹소켓 서버를 시작합니다.
    """
    async with websockets.serve(handler, "localhost", 8765):
        print("WebSocket server started at ws://localhost:8765")
        await asyncio.Future()  # 서버를 계속 실행

if __name__ == "__main__":
    asyncio.run(main())
