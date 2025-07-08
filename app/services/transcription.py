# app/services/transcription.py
import os
import uuid
from datetime import datetime
from fastapi import BackgroundTasks, HTTPException
from langchain.text_splitter import RecursiveCharacterTextSplitter
from ..services.llm import get_embeddings
from ..config import settings
from ..db.mongodb import mongodb
from ..db.chat_manager import chat_manager
from langchain_community.vectorstores import FAISS

# ensure video dir exists
os.makedirs(settings.VIDEOS_DIR, exist_ok=True)

# Store text splits in MongoDB under "chunks" collection
chunks_collection = mongodb.db.get_collection("chunks")


def process_transcription(transcription: str, user_id: str, title: str, source_type: str,
                          source_url: str = None, file_size: int = None) -> str:
    """
    Split transcription into chunks, store in MongoDB, initialize chat history, and return session ID.
    """
    # Split text
    splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=20)
    splits = splitter.split_text(transcription)

    # Persist session metadata
    session_id = str(uuid.uuid4())
    mongodb.videos.insert_one({
        "video_id": session_id,
        "user_id": user_id,
        "title": title,
        "source_type": source_type,
        "source_url": source_url,
        "created_at": datetime.utcnow(),
        "transcription": transcription,
        "size": file_size
    })

    # Store chunks for retrieval
    chunk_docs = [{"session_id": session_id, "text": chunk} for chunk in splits]
    chunks_collection.insert_many(chunk_docs)

    # Initialize chat history in Mongo
    chat_manager.initialize_chat_history(session_id)

    return session_id


def get_retriever(session_id: str):
    """
    Build a Retriever by loading chunks from MongoDB and creating a FAISS vectorstore.
    """
    # Fetch stored text splits
    docs = [doc["text"] for doc in chunks_collection.find({"session_id": session_id})]
    if not docs:
        raise HTTPException(status_code=404, detail="Session data not found. Please transcribe first.")

    # Create embeddings and vectorstore
    embeddings = get_embeddings()
    vectorstore = FAISS.from_texts(docs, embeddings)
    return vectorstore.as_retriever(search_kwargs={"k": 3})


def save_video_file(video_id: str, file_path: str, contents: bytes) -> None:
    """
    Persist the uploaded video file to disk.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(contents)
