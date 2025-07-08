from pymongo import MongoClient
from ..config import settings

class MongoDB:
    def __init__(self):
        self.client = MongoClient(settings.CONNECTION_STRING)
        self.db = self.client[settings.DATABASE_NAME]
        self.users = self.db["users"]
        self.videos = self.db[settings.COLLECTION_NAME]
        # Indexes
        self.users.create_index("username", unique=True)
        self.users.create_index("email", unique=True)
        self.videos.create_index("video_id", unique=True)
        self.videos.create_index("user_id")

    def close(self):
        self.client.close()

mongodb = MongoDB()