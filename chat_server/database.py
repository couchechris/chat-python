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

def save_message(sender: str, recipient: str, message: str):
    """두 사용자 간의 메시지를 데이터베이스에 저장하고 ID를 반환합니다."""
    if collection is None:
        print("Database not connected. Cannot save message.")
        return None

    document = {
        "sender": sender,
        "recipient": recipient,
        "message": message,
        "timestamp": datetime.datetime.now(datetime.timezone.utc)
    }
    result = collection.insert_one(document)
    return result.inserted_id

def get_conversation_history(user1: str, user2: str, limit: int = 100):
    """두 사용자 간의 대화 기록을 가져옵니다."""
    if collection is None:
        print("Database not connected. Cannot retrieve messages.")
        return []
    
    # user1과 user2가 sender 또는 recipient인 모든 메시지를 찾습니다.
    query = {
        "$or": [
            {"sender": user1, "recipient": user2},
            {"sender": user2, "recipient": user1},
        ]
    }
    
    messages_cursor = collection.find(query).sort("timestamp", -1).limit(limit)
    return list(messages_cursor)[::-1]