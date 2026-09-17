from datetime import datetime, timezone
from uuid import uuid4

from app.models.conversation import Conversation
from app.models.conversation_message import ConversationMessage
from app.services.conversation_service import append_message, clear_conversation, get_or_create_conversation, list_messages, load_recent_messages


class FakeQuery:
    def __init__(self, db, model):
        self.db, self.model = db, model
        self.rows = list(db.conversations if model is Conversation else db.messages)

    def filter(self, expression):
        value = expression.right.value
        field = expression.left.name
        self.rows = [row for row in self.rows if getattr(row, field) == value]
        return self

    def order_by(self, *expressions):
        reverse = " ASC" not in str(expressions[0]).upper()
        self.rows.sort(key=lambda row: (row.created_at, str(row.id)), reverse=reverse)
        return self

    def limit(self, value):
        self.rows = self.rows[:value]
        return self

    def first(self):
        return self.rows[0] if self.rows else None

    def all(self):
        return self.rows


class FakeDB:
    def __init__(self):
        self.conversations = []
        self.messages = []

    def query(self, model):
        return FakeQuery(self, model)

    def add(self, value):
        if isinstance(value, Conversation):
            self.conversations.append(value)
        else:
            self.messages.append(value)

    def flush(self):
        for value in [*self.conversations, *self.messages]:
            value.id = value.id or uuid4()
            value.created_at = value.created_at or datetime.now(timezone.utc)

    def delete(self, conversation):
        self.conversations.remove(conversation)
        self.messages[:] = [message for message in self.messages if message.conversation_id != conversation.id]


def test_conversation_is_created_once_and_reused_per_user():
    db = FakeDB()
    user_id = uuid4()
    first = get_or_create_conversation(db, user_id)
    second = get_or_create_conversation(db, user_id)

    assert first.id == second.id
    assert len(db.conversations) == 1


def test_messages_persist_in_user_then_assistant_order_and_are_isolated():
    db = FakeDB()
    first = get_or_create_conversation(db, uuid4())
    other = get_or_create_conversation(db, uuid4())
    append_message(db, first, "user", "Busco vestidos")
    append_message(db, first, "assistant", "Encontré opciones")
    append_message(db, other, "user", "Pedido")

    assert [message.role for message in load_recent_messages(db, first)] == ["user", "assistant"]
    assert [message.content for message in load_recent_messages(db, first)] == ["Busco vestidos", "Encontré opciones"]
    assert [message.content for message in list_messages(db, first.user_id)] == ["Busco vestidos", "Encontré opciones"]


def test_message_metadata_is_persisted():
    db = FakeDB()
    conversation = get_or_create_conversation(db, uuid4())
    metadata = [{"variant_id": "variant-1", "name": "Polera", "image_url": None}]

    message = append_message(db, conversation, "assistant", "Encontré una opción", metadata)

    assert message.message_data == metadata


def test_list_messages_returns_empty_for_new_user_without_creating_conversation():
    db = FakeDB()
    user_id = uuid4()
    assert list_messages(db, user_id) == []
    assert db.conversations == []


def test_reset_deletes_old_messages_and_creates_empty_conversation():
    db = FakeDB()
    user_id = uuid4()
    old = get_or_create_conversation(db, user_id)
    append_message(db, old, "user", "historial")
    fresh = clear_conversation(db, user_id)

    assert fresh.id != old.id
    assert load_recent_messages(db, fresh) == []
    assert all(message.conversation_id != old.id for message in db.messages)
