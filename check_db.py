import asyncio
from chat_server import database

def check_messages():
    """Connects to the DB and prints all messages."""
    try:
        print("Attempting to connect to the database...")
        database.connect_to_mongo()
        # Get all messages, not just recent ones, for verification
        messages = database.collection.find()
        
        print("--- Messages in MongoDB ---")
        count = 0
        for msg in messages:
            count += 1
            print(f"- {msg}")
        
        if count == 0:
            print("No messages found.")
        else:
            print(f"\nTotal messages found: {count}")
        print("---------------------------")

    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")
        print("[HINT] This might be due to the AWS EC2 Security Group blocking the connection.")
        print("[HINT] Please ensure the IP of this machine is allowed for TCP port 27017.")

if __name__ == "__main__":
    check_messages()
