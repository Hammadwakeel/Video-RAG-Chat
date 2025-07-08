# app/routes/sessions.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import os

from ..dependencies import get_current_user
from ..db.mongodb import mongodb
from ..db.chat_manager import chat_manager
from ..config import settings

router = APIRouter()

@router.get("/sessions", response_model=List[Dict[str, Any]])
async def list_sessions(current_user = Depends(get_current_user)):
    """
    List all video sessions for the current user.
    """
    videos = list(mongodb.videos.find({"user_id": current_user.username}))
    sessions_list = []
    for v in videos:
        sessions_list.append({
            "session_id": v["video_id"],
            "title": v["title"],
            "source_type": v["source_type"],
            "created_at": v["created_at"],
            "transcription_preview": (v["transcription"][:200] + "...") if len(v["transcription"]) > 200 else v["transcription"]
        })
    return sessions_list

@router.get("/sessions/{session_id}", response_model=Dict[str, Any])
async def get_session(session_id: str, current_user = Depends(get_current_user)):
    """
    Retrieve details and chat history for a specific session.
    """
    video = mongodb.videos.find_one({"video_id": session_id})
    if not video:
        raise HTTPException(status_code=404, detail="Session not found")
    if video.get("user_id") != current_user.username:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")

    # Fetch chat history
    history = chat_manager.get_chat_history(session_id)
    chat_messages = []
    if history:
        msgs = history.messages
        for i in range(0, len(msgs) - 1, 2):
            chat_messages.append({
                "question": msgs[i].content,
                "answer": msgs[i+1].content
            })

    return {
        "session_id": session_id,
        "title": video["title"],
        "source_type": video["source_type"],
        "source_url": video.get("source_url"),
        "created_at": video["created_at"],
        "transcription_preview": (video["transcription"][:200] + "...") if len(video["transcription"]) > 200 else video["transcription"],
        "full_transcription": video["transcription"],
        "chat_history": chat_messages
    }

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, current_user = Depends(get_current_user)):
    """
    Delete a session, its chunks, chat history, and associated video file.
    """
    video = mongodb.videos.find_one({"video_id": session_id})
    if not video:
        raise HTTPException(status_code=404, detail="Session not found")
    if video.get("user_id") != current_user.username:
        raise HTTPException(status_code=403, detail="Not authorized to delete this session")

    # Delete video metadata
    mongodb.videos.delete_one({"video_id": session_id})
    # Delete chunks
    mongodb.db.get_collection("chunks").delete_many({"session_id": session_id})
    # Delete chat history
    history = chat_manager.get_chat_history(session_id)
    if history:
        mongodb.db.get_collection(settings.COLLECTION_NAME).delete_many({"session_id": session_id})
    # Delete video file(s)
    video_files = [f for f in os.listdir(settings.VIDEOS_DIR) if f.startswith(session_id)]
    for file in video_files:
        try:
            os.remove(os.path.join(settings.VIDEOS_DIR, file))
        except OSError:
            pass

    return {"message": f"Session {session_id} deleted successfully"}
