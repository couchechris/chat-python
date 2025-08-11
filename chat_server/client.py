
import asyncio
import websockets

async def receive_messages(websocket):
    """
    서버로부터 메시지를 수신하고 출력합니다.
    """
    try:
        async for message in websocket:
            print(f"< {message}")
    except websockets.exceptions.ConnectionClosed:
        print("Connection to server closed.")

async def send_messages(websocket):
    """
    사용자 입력을 받아 서버로 메시지를 전송합니다.
    """
    while True:
        message = await asyncio.to_thread(input, "> ")
        if message.lower() == 'exit':
            break
        await websocket.send(message)

async def main():
    """
    서버에 연결하고 메시지 송수신을 동시에 처리합니다.
    """
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        print(f"Connected to {uri}")
        
        # 메시지 수신 및 전송을 위한 태스크 생성
        receive_task = asyncio.create_task(receive_messages(websocket))
        send_task = asyncio.create_task(send_messages(websocket))
        
        # 두 태스크가 모두 완료될 때까지 대기
        done, pending = await asyncio.wait(
            [receive_task, send_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        
        for task in pending:
            task.cancel()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nClient finished.")
