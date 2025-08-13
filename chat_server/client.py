import asyncio
import websockets
import json

async def receive_messages(websocket):
    """
    서버로부터 메시지를 수신하고 JSON을 파싱하여 출력합니다.
    """
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get("type") == "user_list":
                    print(f"[Online Users: {', '.join(data['users'])}]")
                elif data.get("type") == "chat_message":
                    print(f"< From {data['sender']}: {data['message']}")
                else:
                    print(f"< {message}")
            except json.JSONDecodeError:
                print(f"< {message}")
    except websockets.exceptions.ConnectionClosed:
        print("Connection to server closed.")

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

            payload = {
                "recipient": recipient,
                "message": message
            }
            await websocket.send(json.dumps(payload))

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