import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

class Settings:
    # MongoDB
    MONGO_USERNAME = os.getenv("MONGO_USERNAME")
    MONGO_PASSWORD = quote_plus(os.getenv("MONGO_PASSWORD"))  # Encode special chars
    DATABASE_NAME = os.getenv("DATABASE_NAME")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME")

    CONNECTION_STRING = f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@cluster0.ywbtfhf.mongodb.net/{DATABASE_NAME}?retryWrites=true&w=majority"

    # Security
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

    # Video storage
    VIDEOS_DIR = "temp_videos"

settings = Settings()
