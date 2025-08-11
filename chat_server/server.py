import asyncio
import websockets
from . import database

# 연결된 클라이언트를 저장할 집합
connected_clients = set()

async def handler(websocket):
    """
    클라이언트 연결을 처리하고, 메시지를 DB에 저장하며 브로드캐스트합니다.
    """
    # 새로운 클라이언트 연결 추가
    connected_clients.add(websocket)
    print(f"New client connected: {websocket.remote_address}")

    # --- 새로운 기능: 최근 메시지 전송 ---
    try:
        recent_messages = database.get_recent_messages()
        if recent_messages:
            # 각 메시지를 포맷하여 클라이언트에게 전송
            formatted_messages = [
                f"[{msg['timestamp'].strftime('%Y-%m-%d %H:%M')}] {msg.get('author', 'Unknown')}: {msg['message']}"
                for msg in recent_messages
            ]
            await websocket.send("\n".join(formatted_messages))
    except Exception as e:
        print(f"Error sending recent messages: {e}")
    # -------------------------------------

    try:
        # 클라이언트로부터 메시지를 계속 수신
        async for message in websocket:
            author_address = str(websocket.remote_address)
            print(f"Received message from {author_address}: {message}")
            
            # --- 새로운 기능: 메시지 저장 ---
            database.save_message(author=author_address, message=message)
            # --------------------------------

            # 연결된 모든 클라이언트에게 메시지 브로드캐스트
            formatted_message = f"{author_address} says: {message}"
            for client in connected_clients:
                # 메시지를 보낸 클라이언트를 제외하고 전송
                if client != websocket:
                    await client.send(formatted_message)

    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # 클라이언트 연결 종료 시 집합에서 제거
        connected_clients.remove(websocket)

async def main():
    """
    웹소켓 서버를 시작하고 DB에 연결합니다.
    """
    # --- 새로운 기능: DB 연결 ---
    database.connect_to_mongo()
    # ---------------------------

    async with websockets.serve(handler, "localhost", 8765):
        print("WebSocket server started at ws://localhost:8765")
        await asyncio.Future()  # 서버를 계속 실행

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shutting down.")