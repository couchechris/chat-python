import asyncio
import websockets
import json

# 내가 보낸 메시지 ID를 저장하여 읽음 확인을 추적
sent_messages = {}

async def receive_messages(websocket):
    """
    서버로부터 메시지를 수신하고, 타입에 따라 처리합니다.
    """
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type == "user_list":
                    print(f"\n[Online Users: {', '.join(data['users'])}]")
                
                elif msg_type == "chat_message":
                    sender = data['sender']
                    msg_text = data['message']
                    msg_id = data['message_id']
                    print(f"\n< From {sender}: {msg_text}")
                    
                    # 메시지를 받았으므로 '읽음 확인' 알림을 서버에 보냄
                    receipt = {
                        "type": "read_receipt",
                        "message_id": msg_id,
                        "sender": sender # 원래 메시지를 보낸 사람
                    }
                    await websocket.send(json.dumps(receipt))

                elif msg_type == "message_sent_ack":
                    # 내가 보낸 메시지에 대한 서버의 확인 응답
                    # 이 메시지의 ID를 sent_messages에 저장하여 추적 시작
                    sent_messages[data['message_id']] = {"recipient": data['recipient']}

                elif msg_type == "message_read":
                    msg_id = data['message_id']
                    original_message = sent_messages.get(msg_id)
                    if original_message:
                        print(f"\n(Message to {original_message['recipient']} was read)")

            except json.JSONDecodeError:
                print(f"< {message}")
            finally:
                # 다음 입력을 위해 프롬프트 다시 표시
                print("> ", end="", flush=True)

    except websockets.exceptions.ConnectionClosed:
        print("\nConnection to server closed.")

async def send_messages(websocket):
    """
    '수신자:메시지' 형식으로 입력을 받아 서버에 JSON 메시지를 전송합니다.
    """
    print("--- How to send a message ---")
    print("Enter message in 'recipient:your message' format.")
    print("Type 'exit' to close.")
    print("---------------------------")
    while True:
        try:
            message_text = await asyncio.to_thread(input, "> ")
            if message_text.lower() == 'exit':
                break

            parts = message_text.split(':', 1)
            if len(parts) != 2:
                print("Invalid format. Please use 'recipient:message'.")
                continue
            
            recipient, message = parts[0].strip(), parts[1].strip()
            
            if not recipient or not message:
                print("Recipient and message cannot be empty.")
                continue

            # 메시지 ID는 서버에서 생성되므로, 클라이언트는 보낼 내용만 구성
            payload = {
                "type": "chat_message",
                "recipient": recipient,
                "message": message
            }
            await websocket.send(json.dumps(payload))
            # 클라이언트에서 ID를 미리 만들어서 sent_messages에 저장할 수도 있지만,
            # 서버의 DB ID와 동기화하기 위해 지금은 서버 응답을 기다리는 편이 간단함.
            # (더 복잡한 구현에서는 UUID를 클라이언트에서 생성)

        except (KeyboardInterrupt, asyncio.CancelledError):
            break

async def main():
    """
    사용자 이름을 입력받아 서버에 연결하고 메시지 송수신을 처리합니다.
    """
    username = input("Enter your username: ")
    if not username:
        print("Username cannot be empty.")
        return

    uri = f"ws://localhost:8765/{username}"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri} as {username}")
            
            receive_task = asyncio.create_task(receive_messages(websocket))
            send_task = asyncio.create_task(send_messages(websocket))
            
            done, pending = await asyncio.wait(
                [receive_task, send_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            
            for task in pending:
                task.cancel()
    except (websockets.exceptions.InvalidURI, websockets.exceptions.WebSocketException) as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nClient finished.")
