import asyncio
import websockets
import json
from . import database

# 사용자 이름과 웹소켓 객체를 매핑하여 저장하는 딕셔너리
connected_users = {}

async def broadcast_user_list():
    """현재 접속 중인 사용자 목록을 모든 클라이언트에게 브로드캐스트합니다."""
    if not connected_users:
        return
    
    user_list = list(connected_users.keys())
    message = json.dumps({"type": "user_list", "users": user_list})
    
    # asyncio.gather를 사용하여 모든 전송 작업을 동시에 실행
    await asyncio.gather(*[user.send(message) for user in connected_users.values()])

async def handler(websocket):
    """클라이언트 연결을 처리하고 1:1 메시지를 중계합니다."""
    # 디버깅을 통해 알아낸 올바른 방법: websocket.request.path
    username = websocket.request.path.strip('/')
    
    if not username or username in connected_users:
        print(f"Connection rejected: Invalid or duplicate username '{username}'.")
        await websocket.close(code=1008, reason="Invalid or duplicate username")
        return

    # 새로운 사용자 등록
    connected_users[username] = websocket
    print(f"User '{username}' connected.")
    await broadcast_user_list()

    try:
        # 클라이언트로부터 메시지를 계속 수신
        async for message in websocket:
            try:
                data = json.loads(message)
                recipient = data.get("recipient")
                msg_text = data.get("message")

                if not recipient or not msg_text:
                    continue

                # 메시지 저장
                database.save_message(sender=username, recipient=recipient, message=msg_text)

                # 수신자에게 메시지 전송
                recipient_socket = connected_users.get(recipient)
                if recipient_socket:
                    response = {
                        "type": "chat_message",
                        "sender": username,
                        "message": msg_text
                    }
                    await recipient_socket.send(json.dumps(response))
                else:
                    print(f"Message from '{username}' to offline user '{recipient}' saved.")

            except json.JSONDecodeError:
                print(f"Received invalid JSON from {username}")

    except websockets.exceptions.ConnectionClosed:
        pass  # 정상 종료는 조용히 처리
    finally:
        # 사용자 연결 종료 시 등록 해제 및 목록 브로드캐스트
        if username in connected_users:
            del connected_users[username]
            print(f"User '{username}' disconnected.")
            await broadcast_user_list()

async def main():
    """
    웹소켓 서버를 시작하고 DB에 연결합니다.
    """
    database.connect_to_mongo()
    
    async with websockets.serve(handler, "localhost", 8765):
        print("WebSocket server for 1:1 chat started at ws://localhost:8765")
        await asyncio.Future()  # 서버를 계속 실행

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shutting down.")