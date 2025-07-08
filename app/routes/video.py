from fastapi import APIRouter, Depends, Form, File, UploadFile, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import Optional, List
import os

from ..models.transcription import TranscriptionRequest
from ..dependencies import get_current_user
from ..services.transcription import process_transcription, save_video_file
from ..services.llm import init_google_client
from ..config import settings
from ..db.mongodb import mongodb
from google.genai import types

router = APIRouter()

@router.post("/transcribe")
async def transcribe(
    request: TranscriptionRequest,
    current_user = Depends(get_current_user)
):
    """
    Transcribe a YouTube video via Google GenAI and prepare the RAG system
    """
    try:
        client = init_google_client()
        content = types.Content(
            parts=[
                types.Part(text="Transcribe the Video. Write all the things described in the video"),
                types.Part(file_data=types.FileData(file_uri=request.youtube_url))
            ]
        )
        response = client.models.generate_content(
            model='models/gemini-2.0-flash',
            contents=content
        )
        transcription = response.candidates[0].content.parts[0].text
        title = f"YouTube Video - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
        session_id = process_transcription(
            transcription,
            current_user.username,
            title,
            source_type="youtube",
            source_url=request.youtube_url
        )
        return {"session_id": session_id, "message": "YouTube video transcribed and RAG system prepared"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transcribing video: {str(e)}")


@router.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    file: UploadFile = File(...),
    prompt: str = Form("Transcribe the Video. Write all the things described in the video"),
    current_user = Depends(get_current_user)
):
    """
    Upload a video file (max 20MB), transcribe via GenAI, and prepare the RAG system
    """
    try:
        contents = await file.read()
        file_size = len(contents)
        if file_size > 20 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 20MB limit")
        if not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")

        client = init_google_client()
        content = types.Content(
            parts=[
                types.Part(text=prompt),
                types.Part(inline_data=types.Blob(data=contents, mime_type=file.content_type))
            ]
        )
        response = client.models.generate_content(
            model='models/gemini-2.0-flash',
            contents=content
        )
        transcription = response.candidates[0].content.parts[0].text
        session_id = process_transcription(
            transcription,
            current_user.username,
            title,
            source_type="upload",
            file_size=file_size
        )
        ext = os.path.splitext(file.filename)[1]
        file_path = os.path.join(settings.VIDEOS_DIR, f"{session_id}{ext}")
        background_tasks.add_task(save_video_file, session_id, file_path, contents)
        return {"session_id": session_id, "message": "Uploaded video transcribed and RAG system prepared"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing uploaded video: {str(e)}")


@router.get("/download/{video_id}")
async def download_video(
    video_id: str,
    current_user = Depends(get_current_user)
):
    """
    Download a previously uploaded video by streaming the saved file
    """
    video_data = mongodb.videos.find_one({"video_id": video_id})
    if not video_data:
        raise HTTPException(status_code=404, detail="Video not found")
    if video_data["user_id"] != current_user.username:
        raise HTTPException(status_code=403, detail="Not authorized to access this video")

    if video_data["source_type"] == "youtube":
        return {"message": "This is a YouTube video. Access via:", "url": video_data["source_url"]}

    files = [f for f in os.listdir(settings.VIDEOS_DIR) if f.startswith(video_id)]
    if not files:
        raise HTTPException(status_code=404, detail="Video file not found")

    path = os.path.join(settings.VIDEOS_DIR, files[0])
    def iterfile():
        with open(path, 'rb') as f:
            yield from f
    mime_type = f"video/{os.path.splitext(files[0])[1][1:]}"
    return StreamingResponse(
        iterfile(),
        media_type=mime_type,
        headers={"Content-Disposition": f"attachment; filename={video_data['title']}{os.path.splitext(files[0])[1]}"}
    )