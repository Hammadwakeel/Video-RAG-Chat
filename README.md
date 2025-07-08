# Video RAG System Project

This FastAPI-based Video RAG (Retrieval-Augmented Generation) system provides endpoints to:

1. **Register & Authenticate** users
2. **Transcribe** YouTube or uploaded videos
3. **Query** the RAG system
4. **Manage** sessions (list, view, delete)

---

## Endpoint Flow

```mermaid
graph TD
  A[POST /register] --> B[POST /token]
  B --> C[POST /transcribe]
  B --> D[POST /upload]
  C --> E[Start RAG session]
  D --> E
  E --> F[POST /query]
  E --> G[GET /sessions]
  G --> H[GET /sessions/{session_id}]
  H --> F
  G --> I[DELETE /sessions/{session_id}]
```

1. **User Registration & Login**  
   - **POST /register**: Create a new user.  
   - **POST /token**: Obtain JWT access token.

2. **Video Transcription**  
   - **POST /transcribe** (YouTube URL): Transcribe via Google GenAI → split & store chunks → initialize chat history → return `session_id`.  
   - **POST /upload** (Multipart Form Video): Upload & transcribe file → split & store chunks → initialize chat history → return `session_id`.

3. **Query RAG System**  
   - **POST /query** with `{ session_id, query }`:  
     • Rebuild FAISS retriever from MongoDB chunks  
     • Invoke ConversationalRetrievalChain  
     • Append messages to chat history  
     • Return `{ answer, session_id, source_documents }`

4. **Session Management**  
   - **GET /sessions**: List all sessions for current user.  
   - **GET /sessions/{session_id}**: Get full transcription & Q&A history.  
   - **DELETE /sessions/{session_id}**: Remove metadata, chunks, chat history, and video files.

---

## README.md

```markdown
# Video RAG System

## Overview
A FastAPI application that:

- Authenticates users (JWT)
- Transcribes videos (YouTube or upload) via Google GenAI
- Stores transcription chunks in MongoDB
- Builds a FAISS retriever on demand
- Provides a conversational retrieval endpoint
- Manages sessions and associated data

## API Endpoints

| Method | Path                       | Auth Required | Description                                   |
|--------|----------------------------|---------------|-----------------------------------------------|
| POST   | /register                  | No            | Create a new user                             |
| POST   | /token                     | No            | Login and return JWT token                    |
| POST   | /transcribe                | Yes           | Transcribe YouTube video and init session     |
| POST   | /upload                    | Yes           | Upload & transcribe video file                |
| POST   | /query                     | Yes           | Run Q&A against a session                     |
| GET    | /sessions                  | Yes           | List all user sessions                        |
| GET    | /sessions/{session_id}     | Yes           | Get session transcription & chat history      |
| DELETE | /sessions/{session_id}     | Yes           | Delete session & all associated data          |

## Usage
1. Clone repo & install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create `.env` with your credentials (MongoDB, JWT secret, API keys).
3. Run the app:
   ```bash
   uvicorn app.main:app --reload
   ```
4. Interact via HTTP clients (curl, Postman) following the flow above.

## Folder Structure
```
rag_system/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   ├── models/
│   ├── db/
│   ├── services/
│   ├── routes/
│   └── utils/
├── temp_videos/
├── .env
├── requirements.txt
└── README.md
```
```
```
