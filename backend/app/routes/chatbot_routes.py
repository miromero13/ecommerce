from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.schemas.chatbot_schema import ChatMessageRead, ChatRequest
from app.schemas.enums import RolEnum
from app.services.chatbot_service import handle_message
from app.services.conversation_service import clear_conversation, list_messages
from app.utils.response import response


router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


@router.post("/message")
async def chatbot_message_route(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    await handle_message(db, UUID(current_user["sub"]), request.message)
    return response(status_code=status.HTTP_200_OK, message="Mensaje enviado exitosamente")


@router.get("/messages")
async def chatbot_messages_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    messages = list_messages(db, UUID(current_user["sub"]))
    data = [ChatMessageRead.model_validate(message).model_dump() for message in messages]
    return response(status_code=status.HTTP_200_OK, message="Mensajes obtenidos exitosamente", data=data)


@router.delete("/conversation")
async def chatbot_reset_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    try:
        clear_conversation(db, UUID(current_user["sub"]))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return response(status_code=status.HTTP_200_OK, message="Conversación restablecida exitosamente")
