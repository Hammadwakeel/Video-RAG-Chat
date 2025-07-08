# app/routes/query.py
from fastapi import APIRouter, Depends, HTTPException
from ..models.transcription import QueryRequest, QueryResponse
from ..dependencies import get_current_user
from ..services.transcription import get_retriever
from ..db.mongodb import mongodb
from ..db.chat_manager import chat_manager
from ..services.llm import create_chain

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def query_system(request: QueryRequest, current_user = Depends(get_current_user)):
    """
    Query the RAG system for a given session and question
    """
    # Verify metadata exists
    video = mongodb.videos.find_one({"video_id": request.session_id})
    if not video:
        raise HTTPException(status_code=404, detail="Session not found. Please transcribe a video first.")
    if video.get("user_id") != current_user.username:
        raise HTTPException(status_code=403, detail="Not authorized to access this session.")

    # Build retriever from MongoDB chunks
    retriever = get_retriever(request.session_id)
    chat_history = chat_manager.initialize_chat_history(request.session_id)
    chain = create_chain(retriever)

    # Format previous messages for chain
    history = chat_history.messages or []
    formatted_history = []
    for i in range(0, len(history) - 1, 2):
        formatted_history.append((history[i].content, history[i+1].content))

    # Invoke chain
    result = chain.invoke({
        "question": request.query,
        "chat_history": formatted_history
    })

    # Extract answer
    answer = result.get("answer", "I couldn't find an answer to your question.")
    # Save new messages
    chat_history.add_user_message(request.query)
    chat_history.add_ai_message(answer)

    # Process source docs
    source_docs = []
    for doc in result.get("source_documents", []):
        try:
            text = getattr(doc, 'page_content', None) or str(doc)
            snippet = text[:100] + "..." if len(text) > 100 else text
            source_docs.append(snippet)
        except:
            continue

    return QueryResponse(
        answer=answer,
        session_id=request.session_id,
        source_documents=source_docs
    )
