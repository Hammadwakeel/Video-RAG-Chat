from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class TranscriptionRequest(BaseModel):
    youtube_url: str

class QueryRequest(BaseModel):
    query: str
    session_id: str

class QueryResponse(BaseModel):
    answer: str
    session_id: str
    source_documents: Optional[List[str]]

class VideoData(BaseModel):
    video_id: str
    user_id: str
    title: str
    source_type: str
    source_url: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    transcription: str
    size: Optional[int]