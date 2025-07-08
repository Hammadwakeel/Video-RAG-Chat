import os
import shutil
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .config import settings
from .db.mongodb import mongodb
from .routes import auth, video, query, sessions

load_dotenv()

app = FastAPI(
    title="RAG System API",
    description="An API for question answering based on video content with user authentication"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(video.router)
app.include_router(query.router)
app.include_router(sessions.router)

@app.get("/")
async def root():
    return {"message": "Video Transcription and QA API"}

@app.on_event("shutdown")
def on_shutdown():
    # Close DB
    mongodb.close()
    # Clean up temp videos
    shutil.rmtree(settings.VIDEOS_DIR, ignore_errors=True)

if __name__ == "__main__":
    import uvicorn
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    uvicorn.run(app, host="0.0.0.0", port=8000)