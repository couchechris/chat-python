
import os
import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# 환경 변수에서 MongoDB URI 가져오기
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "chat_app"
COLLECTION_NAME = "messages"

# MongoDB 클라이언트와 컬렉션 객체를 전역 변수로 선언
client = None
collection = None

def connect_to_mongo():
    """MongoDB에 연결하고 컬렉션 객체를 설정합니다."""
    global client, collection
    try:
        client = MongoClient(MONGO_URI)
        # 연결 테스트
        client.admin.command('ping')
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        print("Successfully connected to MongoDB.")
    except ConnectionFailure as e:
        print(f"Could not connect to MongoDB: {e}")
        raise

def save_message(author: str, message: str):
    """메시지를 데이터베이스에 저장합니다."""
    if collection is None:
        print("Database not connected. Cannot save message.")
        return

    document = {
        "author": author,
        "message": message,
        "timestamp": datetime.datetime.now(datetime.timezone.utc)
    }
    collection.insert_one(document)

def get_recent_messages(limit: int = 50):
    """가장 최근의 메시지를 지정된 수만큼 가져옵니다."""
    if collection is None:
        print("Database not connected. Cannot retrieve messages.")
        return []
    
    # timestamp 필드를 기준으로 내림차순 정렬하여 최근 메시지부터 가져옴
    messages_cursor = collection.find().sort("timestamp", -1).limit(limit)
    # 리스트로 변환 후, 시간 순서(오래된 순)로 다시 뒤집어서 반환
    return list(messages_cursor)[::-1]
