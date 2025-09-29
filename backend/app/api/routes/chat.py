"""
Chat API routes for the multilingual chatbot
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.core.security import get_current_user
from app.core.database import get_supabase_client
from app.services.rag_service import rag_service

router = APIRouter()

# Request/Response models
class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    language: Optional[str] = Field("auto", description="Language code or 'auto' for detection")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")

class ChatResponse(BaseModel):
    response: str
    confidence_score: float
    language: str
    requires_human: bool
    source_documents: List[Dict[str, Any]]
    session_id: str
    timestamp: str

class ConversationHistory(BaseModel):
    conversation_id: str
    messages: List[Dict[str, Any]]
    created_at: str
    updated_at: str

class FeedbackRequest(BaseModel):
    message_id: str
    rating: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = Field(None, max_length=500)

@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_message: ChatMessage,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Send a message to the chatbot and receive a response
    """
    try:
        supabase = get_supabase_client()
        
        # Generate session ID if not provided
        session_id = chat_message.session_id or str(uuid.uuid4())
        
        # Generate response using RAG service
        rag_result = rag_service.generate_response(
            question=chat_message.message,
            language=chat_message.language
        )
        
        # Get or create conversation
        conversation = supabase.table("conversations").select("*").eq(
            "session_id", session_id
        ).eq("user_id", current_user["id"]).execute()
        
        if not conversation.data:
            # Create new conversation
            conversation_data = {
                "user_id": current_user["id"],
                "session_id": session_id,
                "language": rag_result["language"]
            }
            conversation = supabase.table("conversations").insert(conversation_data).execute()
            conversation_id = conversation.data[0]["id"]
        else:
            conversation_id = conversation.data[0]["id"]
        
        # Save message to database
        message_data = {
            "conversation_id": conversation_id,
            "user_message": chat_message.message,
            "bot_response": rag_result["response"],
            "confidence_score": rag_result["confidence_score"],
            "requires_human": rag_result["requires_human"],
            "language": rag_result["language"]
        }
        
        supabase.table("messages").insert(message_data).execute()
        
        # Return response
        return ChatResponse(
            response=rag_result["response"],
            confidence_score=rag_result["confidence_score"],
            language=rag_result["language"],
            requires_human=rag_result["requires_human"],
            source_documents=rag_result["source_documents"],
            session_id=session_id,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )

@router.get("/history", response_model=List[ConversationHistory])
async def get_conversation_history(
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = 10,
    offset: int = 0
):
    """
    Get conversation history for the current user
    """
    try:
        supabase = get_supabase_client()
        
        # Get conversations
        conversations = supabase.table("conversations").select("*").eq(
            "user_id", current_user["id"]
        ).order("updated_at", desc=True).limit(limit).offset(offset).execute()
        
        result = []
        for conv in conversations.data:
            # Get messages for each conversation
            messages = supabase.table("messages").select("*").eq(
                "conversation_id", conv["id"]
            ).order("created_at", desc=False).execute()
            
            result.append(ConversationHistory(
                conversation_id=conv["id"],
                messages=messages.data,
                created_at=conv["created_at"],
                updated_at=conv["updated_at"]
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation history: {str(e)}"
        )

@router.get("/history/{conversation_id}", response_model=ConversationHistory)
async def get_conversation_by_id(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get specific conversation by ID
    """
    try:
        supabase = get_supabase_client()
        
        # Verify conversation belongs to user
        conversation = supabase.table("conversations").select("*").eq(
            "id", conversation_id
        ).eq("user_id", current_user["id"]).execute()
        
        if not conversation.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Get messages
        messages = supabase.table("messages").select("*").eq(
            "conversation_id", conversation_id
        ).order("created_at", desc=False).execute()
        
        return ConversationHistory(
            conversation_id=conversation_id,
            messages=messages.data,
            created_at=conversation.data[0]["created_at"],
            updated_at=conversation.data[0]["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation: {str(e)}"
        )

@router.post("/feedback")
async def submit_feedback(
    feedback: FeedbackRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Submit feedback for a chatbot response
    """
    try:
        supabase = get_supabase_client()
        
        # Save feedback
        feedback_data = {
            "message_id": feedback.message_id,
            "user_id": current_user["id"],
            "rating": feedback.rating,
            "feedback_text": feedback.feedback_text,
            "created_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("feedback").insert(feedback_data).execute()
        
        return {"message": "Feedback submitted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )

@router.get("/languages")
async def get_supported_languages():
    """
    Get list of supported languages
    """
    from app.core.config import LANGUAGE_NAMES
    
    return {
        "supported_languages": LANGUAGE_NAMES,
        "default_language": "en"
    }

@router.get("/stats")
async def get_chat_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get chat statistics for the current user
    """
    try:
        supabase = get_supabase_client()
        
        # Get user statistics
        user_id = current_user["id"]
        
        # Count conversations
        conversations = supabase.table("conversations").select("*").eq(
            "user_id", user_id
        ).execute()
        
        # Count messages
        messages = supabase.table("messages").select("*").eq(
            "conversation_id", [conv["id"] for conv in conversations.data]
        ).execute()
        
        # Count languages used
        languages = {}
        for conv in conversations.data:
            lang = conv["language"]
            languages[lang] = languages.get(lang, 0) + 1
        
        return {
            "total_conversations": len(conversations.data),
            "total_messages": len(messages.data),
            "languages_used": languages,
            "account_created": current_user["created_at"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stats: {str(e)}"
        )
