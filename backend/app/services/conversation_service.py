from uuid import UUID

from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.conversation_message import ConversationMessage


MAX_CONTEXT_MESSAGES = 2
MAX_CONTEXT_CHARS = 800


# [CU07 - Secuencia: Pasos 2.4, 3.4] chatbot_routes invoca get_or_create_conversation(user_id) sobre la entidad Conversacion
def get_or_create_conversation(db: Session, user_id: UUID) -> Conversation:
    conversation = db.query(Conversation).filter(Conversation.user_id == user_id).first()
    if conversation is None:
        conversation = Conversation(user_id=user_id)
        db.add(conversation)
        db.flush()
    return conversation


# [CU07 - Secuencia: Paso 2.6] chatbot_routes invoca load_recent_messages(conversation) sobre la entidad MensajeConversacion
def load_recent_messages(db: Session, conversation: Conversation) -> list[ConversationMessage]:
    messages = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conversation.id)
        .order_by(ConversationMessage.created_at.desc(), ConversationMessage.id.desc())
        .limit(MAX_CONTEXT_MESSAGES)
        .all()
    )
    messages.reverse()
    selected: list[ConversationMessage] = []
    chars = 0
    for message in reversed(messages):
        if chars + len(message.content) > MAX_CONTEXT_CHARS:
            break
        selected.append(message)
        chars += len(message.content)
    selected.reverse()
    return selected


# [CU07 - Secuencia: Pasos 1.2, 2.30] chatbot_routes invoca list_messages(user_id) sobre la entidad MensajeConversacion
def list_messages(db: Session, user_id: UUID) -> list[ConversationMessage]:
    conversation = db.query(Conversation).filter(Conversation.user_id == user_id).first()
    if conversation is None:
        return []
    return (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conversation.id)
        .order_by(ConversationMessage.created_at.asc(), ConversationMessage.id.asc())
        .all()
    )


# [CU07 - Secuencia: Pasos 2.12, 2.14, 2.26] chatbot_routes invoca append_message(conversation, role, content, message_data) sobre la entidad MensajeConversacion
def append_message(db: Session, conversation: Conversation, role: str, content: str, message_data: object | None = None) -> ConversationMessage:
    message = ConversationMessage(conversation_id=conversation.id, role=role, content=content.strip(), message_data=message_data)
    db.add(message)
    db.flush()
    return message


# [CU07 - Secuencia: Pasos 2.2, 3.2] chatbot_routes invoca clear_conversation(user_id) sobre la entidad Conversacion
def clear_conversation(db: Session, user_id: UUID) -> Conversation:
    existing = db.query(Conversation).filter(Conversation.user_id == user_id).first()
    if existing is not None:
        db.delete(existing)
        db.flush()
    return get_or_create_conversation(db, user_id)


def reset_conversation(db: Session, user_id: UUID) -> Conversation:
    return clear_conversation(db, user_id)
