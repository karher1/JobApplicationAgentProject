from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from src.services.chatbot_service import ChatbotService
from src.models.schemas import ServiceHealth
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# Request/Response Models
class StartConversationRequest(BaseModel):
    user_id: int
    conversation_type: str = "general"  # general, job_search, resume_review, interview_prep, career_guidance
    initial_message: Optional[str] = None

class StartConversationResponse(BaseModel):
    conversation_id: str
    status: str
    conversation: Dict[str, Any]

class SendMessageRequest(BaseModel):
    user_id: int
    message: str

class SendMessageResponse(BaseModel):
    message_id: str
    content: str
    timestamp: str
    conversation_id: str

class ChatbotStatsResponse(BaseModel):
    total_conversations: int
    active_conversations: int
    total_messages: int
    rate_limit_remaining: int

class UserConversationsResponse(BaseModel):
    conversations: List[Dict[str, Any]]
    total: int

# Dependency injection
def get_chatbot_service() -> ChatbotService:
    from src.api.main import chatbot_service
    return chatbot_service

@router.post("/start", response_model=StartConversationResponse)
async def start_conversation(
    request: StartConversationRequest,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """Start a new conversation with the AI assistant"""
    try:
        conversation_id = await chatbot_service.start_conversation(
            user_id=request.user_id,
            conversation_type=request.conversation_type,
            initial_message=request.initial_message
        )
        
        # Get the conversation details
        conversation_details = await chatbot_service.get_conversation_history(
            conversation_id=conversation_id,
            user_id=request.user_id,
            limit=50
        )
        
        return StartConversationResponse(
            conversation_id=conversation_id,
            status="active",
            conversation=conversation_details
        )
        
    except Exception as e:
        logger.error(f"Error starting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{conversation_id}/message", response_model=SendMessageResponse)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """Send a message to an existing conversation"""
    try:
        response = await chatbot_service.send_message(
            conversation_id=conversation_id,
            user_id=request.user_id,
            message=request.message
        )
        
        return SendMessageResponse(**response)
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{conversation_id}/history")
async def get_conversation_history(
    conversation_id: str,
    user_id: int,
    limit: int = 50,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """Get conversation history"""
    try:
        history = await chatbot_service.get_conversation_history(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=limit
        )
        
        return history
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{conversation_id}/end")
async def end_conversation(
    conversation_id: str,
    user_id: int,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """End a conversation"""
    try:
        success = await chatbot_service.end_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        return {
            "conversation_id": conversation_id,
            "status": "ended",
            "success": success
        }
        
    except Exception as e:
        logger.error(f"Error ending conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}/conversations", response_model=UserConversationsResponse)
async def get_user_conversations(
    user_id: int,
    limit: int = 20,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """Get user's conversations"""
    try:
        conversations = await chatbot_service.list_conversations(
            user_id=user_id,
            limit=limit
        )
        
        return UserConversationsResponse(
            conversations=conversations,
            total=len(conversations)
        )
        
    except Exception as e:
        logger.error(f"Error getting user conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}/stats", response_model=ChatbotStatsResponse)
async def get_user_stats(
    user_id: int,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """Get user's chatbot statistics"""
    try:
        stats = await chatbot_service.get_conversation_stats(user_id=user_id)
        
        return ChatbotStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check(
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """Check chatbot service health"""
    try:
        health = await chatbot_service.health_check()
        return health.dict()
        
    except Exception as e:
        logger.error(f"Error checking chatbot health: {e}")
        return {"status": "unhealthy", "message": str(e)}