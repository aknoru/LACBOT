"""
Admin API routes for managing the chatbot system
"""

from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from app.core.security import get_current_superuser, get_current_volunteer
from app.core.database import get_supabase_client
from app.services.rag_service import rag_service

router = APIRouter()

# Request/Response models
class FAQCreate(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    answer: str = Field(..., min_length=1, max_length=2000)
    category: str = Field(..., min_length=1, max_length=100)
    language: str = Field(..., min_length=2, max_length=5)
    priority: int = Field(1, ge=1, le=5)

class FAQUpdate(BaseModel):
    question: Optional[str] = Field(None, min_length=1, max_length=500)
    answer: Optional[str] = Field(None, min_length=1, max_length=2000)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    priority: Optional[int] = Field(None, ge=1, le=5)
    is_active: Optional[bool] = None

class DocumentUpload(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    document_type: str = Field(..., min_length=1, max_length=50)
    language: str = Field(..., min_length=2, max_length=5)

class UserManagement(BaseModel):
    user_id: str
    role: Optional[str] = None
    is_active: Optional[bool] = None

class SystemStats(BaseModel):
    total_users: int
    total_conversations: int
    total_messages: int
    active_languages: Dict[str, int]
    avg_confidence_score: float
    human_intervention_rate: float

@router.get("/stats", response_model=SystemStats)
async def get_system_stats(current_user: dict = Depends(get_current_superuser)):
    """
    Get system-wide statistics
    """
    try:
        supabase = get_supabase_client()
        
        # Get user count
        users = supabase.table("users").select("*").execute()
        total_users = len(users.data)
        
        # Get conversation count
        conversations = supabase.table("conversations").select("*").execute()
        total_conversations = len(conversations.data)
        
        # Get message count
        messages = supabase.table("messages").select("*").execute()
        total_messages = len(messages.data)
        
        # Get language usage
        active_languages = {}
        for conv in conversations.data:
            lang = conv["language"]
            active_languages[lang] = active_languages.get(lang, 0) + 1
        
        # Calculate average confidence score
        confidence_scores = [msg["confidence_score"] for msg in messages.data if msg.get("confidence_score")]
        avg_confidence_score = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Calculate human intervention rate
        human_interventions = [msg for msg in messages.data if msg.get("requires_human", False)]
        human_intervention_rate = len(human_interventions) / total_messages if total_messages > 0 else 0.0
        
        return SystemStats(
            total_users=total_users,
            total_conversations=total_conversations,
            total_messages=total_messages,
            active_languages=active_languages,
            avg_confidence_score=avg_confidence_score,
            human_intervention_rate=human_intervention_rate
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system stats: {str(e)}"
        )

@router.get("/users")
async def get_all_users(
    current_user: dict = Depends(get_current_superuser),
    limit: int = 50,
    offset: int = 0
):
    """
    Get all users (superuser only)
    """
    try:
        supabase = get_supabase_client()
        
        users = supabase.table("users").select(
            "id,email,username,full_name,role,language_preference,created_at,is_active"
        ).limit(limit).offset(offset).execute()
        
        return {"users": users.data, "total": len(users.data)}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get users: {str(e)}"
        )

@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    user_data: UserManagement,
    current_user: dict = Depends(get_current_superuser)
):
    """
    Update user role or status
    """
    try:
        supabase = get_supabase_client()
        
        # Validate role
        if user_data.role and user_data.role not in ["user", "volunteer", "superuser"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role"
            )
        
        # Update user
        update_data = {}
        if user_data.role:
            update_data["role"] = user_data.role
        if user_data.is_active is not None:
            update_data["is_active"] = user_data.is_active
        
        if update_data:
            supabase.table("users").update(update_data).eq("id", user_id).execute()
        
        return {"message": "User updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )

@router.get("/conversations")
async def get_all_conversations(
    current_user: dict = Depends(get_current_volunteer),
    limit: int = 50,
    offset: int = 0,
    requires_human: Optional[bool] = None
):
    """
    Get all conversations (volunteer and superuser)
    """
    try:
        supabase = get_supabase_client()
        
        # Build query
        query = supabase.table("conversations").select("*, users(username, full_name)")
        
        if requires_human is not None:
            # Filter conversations with messages requiring human intervention
            messages = supabase.table("messages").select("conversation_id").eq(
                "requires_human", True
            ).execute()
            conversation_ids = [msg["conversation_id"] for msg in messages.data]
            query = query.in_("id", conversation_ids)
        
        conversations = query.limit(limit).offset(offset).execute()
        
        return {"conversations": conversations.data, "total": len(conversations.data)}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversations: {str(e)}"
        )

@router.get("/messages/flagged")
async def get_flagged_messages(
    current_user: dict = Depends(get_current_volunteer),
    limit: int = 50,
    offset: int = 0
):
    """
    Get messages that require human intervention
    """
    try:
        supabase = get_supabase_client()
        
        messages = supabase.table("messages").select(
            "*, conversations(session_id, users(username, full_name))"
        ).eq("requires_human", True).order(
            "created_at", desc=True
        ).limit(limit).offset(offset).execute()
        
        return {"messages": messages.data, "total": len(messages.data)}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flagged messages: {str(e)}"
        )

@router.post("/faqs")
async def create_faq(
    faq_data: FAQCreate,
    current_user: dict = Depends(get_current_superuser)
):
    """
    Create a new FAQ entry
    """
    try:
        supabase = get_supabase_client()
        
        # Create FAQ
        faq_dict = {
            "question": faq_data.question,
            "answer": faq_data.answer,
            "category": faq_data.category,
            "language": faq_data.language,
            "priority": faq_data.priority,
            "created_by": current_user["id"]
        }
        
        result = supabase.table("faqs").insert(faq_dict).execute()
        
        # Add to vector store for RAG
        rag_service.add_documents([{
            "id": result.data[0]["id"],
            "title": f"FAQ: {faq_data.question}",
            "content": faq_data.answer,
            "language": faq_data.language,
            "document_type": "faq"
        }])
        
        return {"message": "FAQ created successfully", "faq_id": result.data[0]["id"]}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create FAQ: {str(e)}"
        )

@router.get("/faqs")
async def get_faqs(
    current_user: dict = Depends(get_current_volunteer),
    language: Optional[str] = None,
    category: Optional[str] = None
):
    """
    Get FAQ entries
    """
    try:
        supabase = get_supabase_client()
        
        query = supabase.table("faqs").select("*")
        
        if language:
            query = query.eq("language", language)
        if category:
            query = query.eq("category", category)
        
        faqs = query.order("priority", desc=True).execute()
        
        return {"faqs": faqs.data}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get FAQs: {str(e)}"
        )

@router.put("/faqs/{faq_id}")
async def update_faq(
    faq_id: str,
    faq_data: FAQUpdate,
    current_user: dict = Depends(get_current_superuser)
):
    """
    Update an FAQ entry
    """
    try:
        supabase = get_supabase_client()
        
        # Update FAQ
        update_dict = {}
        if faq_data.question:
            update_dict["question"] = faq_data.question
        if faq_data.answer:
            update_dict["answer"] = faq_data.answer
        if faq_data.category:
            update_dict["category"] = faq_data.category
        if faq_data.priority:
            update_dict["priority"] = faq_data.priority
        if faq_data.is_active is not None:
            update_dict["is_active"] = faq_data.is_active
        
        if update_dict:
            supabase.table("faqs").update(update_dict).eq("id", faq_id).execute()
        
        return {"message": "FAQ updated successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update FAQ: {str(e)}"
        )

@router.delete("/faqs/{faq_id}")
async def delete_faq(
    faq_id: str,
    current_user: dict = Depends(get_current_superuser)
):
    """
    Delete an FAQ entry
    """
    try:
        supabase = get_supabase_client()
        
        supabase.table("faqs").delete().eq("id", faq_id).execute()
        
        return {"message": "FAQ deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete FAQ: {str(e)}"
        )

@router.post("/documents/upload")
async def upload_document(
    title: str = Field(...),
    document_type: str = Field(...),
    language: str = Field(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_superuser)
):
    """
    Upload a document for the knowledge base
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.pdf', '.txt', '.docx')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only PDF, TXT, and DOCX files are allowed."
            )
        
        # Read file content
        content = await file.read()
        
        # For now, we'll store the file path and process it later
        # In a production system, you'd want to use proper file storage
        file_path = f"./data/documents/{file.filename}"
        
        # Save document metadata to database
        supabase = get_supabase_client()
        document_data = {
            "title": title,
            "content": content.decode('utf-8', errors='ignore'),  # Simplified for demo
            "language": language,
            "document_type": document_type,
            "file_path": file_path,
            "created_by": current_user["id"]
        }
        
        result = supabase.table("documents").insert(document_data).execute()
        
        # Add to vector store
        rag_service.add_documents([{
            "id": result.data[0]["id"],
            "title": title,
            "content": content.decode('utf-8', errors='ignore'),
            "language": language,
            "document_type": document_type
        }])
        
        return {"message": "Document uploaded successfully", "document_id": result.data[0]["id"]}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )

@router.get("/feedback")
async def get_feedback(
    current_user: dict = Depends(get_current_volunteer),
    limit: int = 50,
    offset: int = 0
):
    """
    Get user feedback
    """
    try:
        supabase = get_supabase_client()
        
        feedback = supabase.table("feedback").select(
            "*, users(username, full_name), messages(user_message, bot_response)"
        ).order("created_at", desc=True).limit(limit).offset(offset).execute()
        
        return {"feedback": feedback.data, "total": len(feedback.data)}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback: {str(e)}"
        )

@router.post("/notifications")
async def send_notification(
    title: str = Field(...),
    message: str = Field(...),
    notification_type: str = Field("general"),
    current_user: dict = Depends(get_current_superuser)
):
    """
    Send notification to all users
    """
    try:
        supabase = get_supabase_client()
        
        # Get all active users
        users = supabase.table("users").select("id").eq("is_active", True).execute()
        
        # Create notifications for all users
        notifications = []
        for user in users.data:
            notifications.append({
                "user_id": user["id"],
                "title": title,
                "message": message,
                "type": notification_type
            })
        
        supabase.table("notifications").insert(notifications).execute()
        
        return {"message": f"Notification sent to {len(notifications)} users"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )
