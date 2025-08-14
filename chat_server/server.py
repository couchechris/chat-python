import asyncio
import websockets
import json
from . import database
from bson import ObjectId

# 사용자 이름과 웹소켓 객체를 매핑하여 저장하는 딕셔너리
connected_users = {}

async def broadcast_user_list():
    """현재 접속 중인 사용자 목록을 모든 클라이언트에게 브로드캐스트합니다."""
    if not connected_users:
        return
    
    user_list = list(connected_users.keys())
    message = json.dumps({"type": "user_list", "users": user_list})
    
    await asyncio.gather(*[user.send(message) for user in connected_users.values()])

async def handler(websocket):
    """클라이언트 연결을 처리하고 1:1 메시지 및 읽음 확인을 중계합니다."""
    username = websocket.request.path.strip('/')
    
    if not username or username in connected_users:
        print(f"Connection rejected: Invalid or duplicate username '{username}'.")
        await websocket.close(code=1008, reason="Invalid or duplicate username")
        return

    connected_users[username] = websocket
    print(f"User '{username}' connected.")
    await broadcast_user_list()

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type == "chat_message":
                    recipient = data.get("recipient")
                    msg_text = data.get("message")

                    if not recipient or not msg_text:
                        continue

                    # 메시지를 저장하고 고유 ID를 받음
                    message_id = database.save_message(sender=username, recipient=recipient, message=msg_text)

                    if message_id:
                        # [FIX] 발신자에게 메시지 ID를 알려주어 추적할 수 있게 함
                        ack_response = {
                            "type": "message_sent_ack",
                            "message_id": str(message_id),
                            "recipient": recipient
                        }
                        await websocket.send(json.dumps(ack_response))

                        # 수신자에게 메시지 ID와 함께 메시지 전송
                        recipient_socket = connected_users.get(recipient)
                        if recipient_socket:
                            response = {
                                "type": "chat_message",
                                "message_id": str(message_id), # ObjectId를 문자열로 변환
                                "sender": username,
                                "message": msg_text
                            }
                            await recipient_socket.send(json.dumps(response))
                        else:
                            print(f"Message from '{username}' to offline user '{recipient}' saved.")
                
                elif msg_type == "read_receipt":
                    message_id = data.get("message_id")
                    sender = data.get("sender") # 이 메시지를 보낸 원래 발신자
                    
                    # 원래 발신자에게 읽음 알림 전송
                    sender_socket = connected_users.get(sender)
                    if sender_socket:
                        response = {
                            "type": "message_read",
                            "message_id": message_id
                        }
                        await sender_socket.send(json.dumps(response))

            except json.JSONDecodeError:
                print(f"Received invalid JSON from {username}")

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if username in connected_users:
            del connected_users[username]
            print(f"User '{username}' disconnected.")
            await broadcast_user_list()

async def main():
    """웹소켓 서버를 시작하고 DB에 연결합니다."""
    database.connect_to_mongo()
    
    async with websockets.serve(handler, "localhost", 8765):
        print("WebSocket server with read receipts started at ws://localhost:8765")
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shutting down.")
