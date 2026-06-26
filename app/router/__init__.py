from fastapi import APIRouter

from app.router.department import router as department_router
from app.router.user import router as user_router
from app.router.conversation import router as conversation_router
from app.router.message import router as message_router
from app.router.chat import router as chat_router

api_router = APIRouter()
api_router.include_router(department_router)
api_router.include_router(user_router)
api_router.include_router(conversation_router)
api_router.include_router(message_router)
api_router.include_router(chat_router)
