"""
Webhook API routes for WhatsApp and other integrations
"""

from fastapi import APIRouter, HTTPException, Request, Depends, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
import logging
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from app.core.config import settings
from app.services.rag_service import rag_service
from app.core.database import get_supabase_client

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Twilio client
twilio_client = None
if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
    twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

class WhatsAppMessage(BaseModel):
    From: str
    Body: str
    MessageSid: str

@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Handle incoming WhatsApp messages
    """
    try:
        # Parse form data from Twilio
        form_data = await request.form()
        
        # Extract message data
        from_number = form_data.get("From", "")
        message_body = form_data.get("Body", "")
        message_sid = form_data.get("MessageSid", "")
        
        if not message_body:
            return {"error": "No message body provided"}
        
        logger.info(f"Received WhatsApp message from {from_number}: {message_body}")
        
        # Process message through RAG service
        rag_result = rag_service.generate_response(
            question=message_body,
            language="auto"  # Auto-detect language
        )
        
        # Get or create user in database
        supabase = get_supabase_client()
        
        # Check if user exists by phone number
        user = supabase.table("users").select("*").eq("phone_number", from_number).execute()
        
        if not user.data:
            # Create new user for WhatsApp
            user_data = {
                "email": f"whatsapp_{from_number}@temp.com",  # Temporary email
                "username": f"whatsapp_user_{from_number[-4:]}",
                "full_name": f"WhatsApp User {from_number[-4:]}",
                "phone_number": from_number,
                "role": "user",
                "language_preference": rag_result["language"],
                "is_active": True
            }
            user_result = supabase.table("users").insert(user_data).execute()
            user_id = user_result.data[0]["id"]
        else:
            user_id = user.data[0]["id"]
        
        # Save conversation
        session_id = f"whatsapp_{from_number}"
        
        # Get or create conversation
        conversation = supabase.table("conversations").select("*").eq(
            "session_id", session_id
        ).eq("user_id", user_id).execute()
        
        if not conversation.data:
            conversation_data = {
                "user_id": user_id,
                "session_id": session_id,
                "language": rag_result["language"]
            }
            conversation = supabase.table("conversations").insert(conversation_data).execute()
            conversation_id = conversation.data[0]["id"]
        else:
            conversation_id = conversation.data[0]["id"]
        
        # Save message
        message_data = {
            "conversation_id": conversation_id,
            "user_message": message_body,
            "bot_response": rag_result["response"],
            "confidence_score": rag_result["confidence_score"],
            "requires_human": rag_result["requires_human"],
            "language": rag_result["language"],
            "platform": "whatsapp"
        }
        
        supabase.table("messages").insert(message_data).execute()
        
        # Create TwiML response
        response = MessagingResponse()
        response.message(rag_result["response"])
        
        # If confidence is low, add a note about human support
        if rag_result["requires_human"]:
            response.message("If you need further assistance, please contact our support team.")
        
        return str(response)
        
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        
        # Return error response
        response = MessagingResponse()
        response.message("Sorry, I'm experiencing technical difficulties. Please try again later.")
        return str(response)

@router.get("/whatsapp/status")
async def whatsapp_status():
    """
    Check WhatsApp webhook status
    """
    try:
        if not twilio_client:
            return {"status": "error", "message": "Twilio not configured"}
        
        # Test Twilio connection
        account = twilio_client.api.accounts(settings.TWILIO_ACCOUNT_SID).fetch()
        
        return {
            "status": "active",
            "account_sid": account.sid,
            "friendly_name": account.friendly_name,
            "webhook_url": f"{settings.FRONTEND_URL}/api/webhook/whatsapp"
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/whatsapp/send")
async def send_whatsapp_message(
    to_number: str,
    message: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Send WhatsApp message (admin function)
    """
    try:
        if not twilio_client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="WhatsApp not configured"
            )
        
        # Send message
        message_obj = twilio_client.messages.create(
            body=message,
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            to=f"whatsapp:{to_number}"
        )
        
        return {
            "message_sid": message_obj.sid,
            "status": message_obj.status,
            "to": to_number
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send WhatsApp message: {str(e)}"
        )

@router.post("/slack")
async def slack_webhook(request: Request):
    """
    Handle incoming Slack messages (future integration)
    """
    try:
        body = await request.json()
        
        # Process Slack message
        if body.get("type") == "url_verification":
            return {"challenge": body.get("challenge")}
        
        if body.get("type") == "event_callback":
            event = body.get("event", {})
            
            if event.get("type") == "message" and not event.get("bot_id"):
                # Process user message
                text = event.get("text", "")
                channel = event.get("channel", "")
                
                # Generate response
                rag_result = rag_service.generate_response(
                    question=text,
                    language="en"  # Slack typically in English
                )
                
                # Send response back to Slack
                # This would require Slack API integration
                
                return {"status": "processed"}
        
        return {"status": "ignored"}
        
    except Exception as e:
        logger.error(f"Slack webhook error: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/telegram")
async def telegram_webhook(request: Request):
    """
    Handle incoming Telegram messages (future integration)
    """
    try:
        body = await request.json()
        
        message = body.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        
        if text:
            # Generate response
            rag_result = rag_service.generate_response(
                question=text,
                language="auto"
            )
            
            # Send response back to Telegram
            # This would require Telegram Bot API integration
            
            return {"status": "processed"}
        
        return {"status": "ignored"}
        
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/webhooks/status")
async def webhooks_status():
    """
    Get status of all webhook integrations
    """
    status_info = {
        "whatsapp": {
            "enabled": bool(twilio_client),
            "status": "active" if twilio_client else "disabled"
        },
        "slack": {
            "enabled": False,
            "status": "not_implemented"
        },
        "telegram": {
            "enabled": False,
            "status": "not_implemented"
        }
    }
    
    return status_info

@router.post("/test")
async def test_webhook(request: Request):
    """
    Test webhook endpoint
    """
    try:
        body = await request.json()
        
        # Process test message
        test_message = body.get("message", "Hello, this is a test message.")
        
        rag_result = rag_service.generate_response(
            question=test_message,
            language="en"
        )
        
        return {
            "status": "success",
            "input": test_message,
            "output": rag_result["response"],
            "confidence": rag_result["confidence_score"],
            "language": rag_result["language"]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
