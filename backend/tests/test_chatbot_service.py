import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.chatbot_service import (
    _catalog_context,
    _catalog_candidates,
    _catalog_final_context,
    _fallback_selected_ids,
    _select_catalog_ids,
    _parse_selected_ids,
    _orders_context,
    _catalog_answer,
    _static_context,
    classify_intent,
    extract_profile_updates,
    generate_answer,
    upsert_profile,
)
from app.schemas.chatbot_schema import ChatIntent
from pydantic import ValidationError
from app.schemas.chatbot_schema import ChatRequest, ConversationTurn


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.limit_value = None
        self.filters = []

    def filter(self, *args):
        self.filters.extend(args)
        return self

    def join(self, *args, **kwargs):
        return self

    def outerjoin(self, *args, **kwargs):
        return self

    def options(self, *args, **kwargs):
        return self

    def distinct(self, *args):
        return self

    def order_by(self, *args):
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def all(self):
        return self.rows[: self.limit_value] if self.limit_value else self.rows

    def first(self):
        return self.rows[0] if self.rows else None


class FakeProfileDB:
    def __init__(self):
        self.profile = None

    def query(self, model):
        return FakeQuery([self.profile] if self.profile else [])

    def add(self, profile):
        self.profile = profile

    def commit(self):
        pass

    def refresh(self, profile):
        pass


def test_classifies_all_chatbot_intents_deterministically():
    assert classify_intent("¿Qué vestido rojo tienes?") == ChatIntent.CATALOGO
    assert classify_intent("Quiero recomendaciones de poleras rojas") == ChatIntent.CATALOGO
    assert classify_intent("¿Dónde está mi pedido?") == ChatIntent.PEDIDOS
    assert classify_intent("¿Cuál es la política de devolución?") == ChatIntent.POLITICAS
    assert classify_intent("¿Cómo funciona mi cuenta?") == ChatIntent.USO_SISTEMA


def test_profile_extraction_requires_explicit_unambiguous_phrases():
    assert extract_profile_updates("Uso talla M arriba y calzo 38") == {"top_size": "M", "shoe_size": "38"}
    assert extract_profile_updates("Mi tipo de cuerpo es reloj de arena") == {"body_shape": "reloj de arena"}
    assert extract_profile_updates("Me veo de forma triangular") == {}


def test_profile_upsert_creates_then_updates_only_explicit_fields():
    db = FakeProfileDB()
    user_id = uuid4()
    profile = upsert_profile(db, user_id, {"top_size": "M"})
    assert profile.user_id == user_id
    assert profile.top_size == "M"
    profile = upsert_profile(db, user_id, {"fit_preference": "holgado"})
    assert profile.top_size == "M"
    assert profile.fit_preference == "holgado"


def test_static_context_loads_local_topics():
    context = _static_context(ChatIntent.POLITICAS, "Quiero conocer devoluciones")
    assert context["topics"]
    assert any("devol" in key for key in context["topics"])


def test_catalog_context_caps_products_at_four_and_keeps_descriptions():
    products = [SimpleNamespace(id=uuid4(), name=f"Producto {i}", description="Descripción", category_id=uuid4(), variants=[]) for i in range(5)]
    for product in products:
        product.variants = [SimpleNamespace(status="active", sku="SKU", price=10, size_id=None, color_id=None)]
    query = FakeQuery(products)
    db = SimpleNamespace(query=lambda *args: query)
    context = _catalog_context(db, "busco ropa", None)
    assert query.limit_value == 4
    assert len(context["products"]) == 4
    assert all(item["description"] == "Descripción" for item in context["products"])


def test_orders_context_filters_by_authenticated_user_and_returns_safe_fields():
    user_id = uuid4()
    order = SimpleNamespace(id=uuid4(), user_id=user_id, status="paid", created_at=datetime.now(timezone.utc), updated_at=None, total_amount=25, currency="usd")
    query = FakeQuery([order])
    db = SimpleNamespace(query=lambda *args: query)
    context = _orders_context(db, user_id)
    assert query.filters
    assert set(context["orders"][0]) == {"display_reference", "payment_status", "fulfillment_status", "created_at", "updated_at", "total", "currency", "shipping_reference"}
    assert context["orders"][0]["display_reference"] == f"#{str(order.id).replace('-', '')[:8]}"
    assert context["orders"][0]["payment_status"] == "Pagado"
    assert "stripe_payment_intent_id" not in context["orders"][0]


def test_fallback_is_useful_without_gemini(monkeypatch):
    from app.core import config

    monkeypatch.setattr(config.settings, "gemini_api_key", None)
    answer, used_fallback = asyncio.run(generate_answer("¿Qué hay?", ChatIntent.CATALOGO, {"products": [{"name": "Vestido"}]}))
    assert used_fallback is True
    assert "Vestido" in answer


def test_catalog_answer_keeps_product_details_in_cards():
    assert _catalog_answer({"products": [{"name": "Polera roja"}]}) == "Tengo algunas recomendaciones para vos."
    assert _catalog_answer({"products": []}) == "No encontré prendas que coincidan con tu búsqueda."


def test_chat_request_rejects_blank_messages():
    with pytest.raises(ValidationError):
        ChatRequest(message="   ")


def test_chat_request_rejects_client_conversation():
    with pytest.raises(ValidationError):
        ChatRequest(message="ok", conversation=[])


def test_persisted_history_context_truncates_legacy_long_messages():
    message = SimpleNamespace(role="assistant", content="x" * 600)
    turn = ConversationTurn(role=message.role, content=message.content[:400])
    assert len(turn.content) == 400


def test_continuation_inherits_previous_user_intent():
    conversation = [ConversationTurn(role="user", content="Busco vestidos rojos"), ConversationTurn(role="assistant", content="Encontré opciones")]
    assert classify_intent("No entiendo, ¿cuál me recomiendas?", conversation) == ChatIntent.CATALOGO


def test_explicit_catalog_request_overrides_previous_order_context():
    conversation = [ConversationTurn(role="user", content="¿Tengo algún pedido activo?"), ConversationTurn(role="assistant", content="Pedido #89190024 — Pagado")]
    assert classify_intent("Quiero recomendaciones de poleras rojas para comprar", conversation) == ChatIntent.CATALOGO


def test_gemini_prompt_includes_history(monkeypatch):
    from app.services import chatbot_service
    prompts = []
    monkeypatch.setattr(chatbot_service.settings, "gemini_api_key", "test")
    monkeypatch.setattr(chatbot_service.settings, "gemini_timeout_seconds", 1)
    monkeypatch.setattr(chatbot_service, "_generate_sync", lambda prompt: prompts.append(prompt) or "respuesta")
    conversation = [ConversationTurn(role="user", content="Busco vestidos rojos"), ConversationTurn(role="assistant", content="Tengo dos opciones")]
    answer, fallback = asyncio.run(generate_answer("No entiendo", ChatIntent.CATALOGO, {}, conversation))
    assert answer == "respuesta" and not fallback
    assert '"role": "user"' in prompts[0]
    assert '"current_message": {"role": "user", "content": "No entiendo"}' in prompts[0]


def _catalog_row(name="Polera", color_name="Rojo"):
    category = SimpleNamespace(id=uuid4(), name="Poleras")
    color = SimpleNamespace(id=uuid4(), name=color_name)
    size = SimpleNamespace(id=uuid4(), name="M")
    variant = SimpleNamespace(
        id=uuid4(), product_id=uuid4(), sku="SKU-1", price=25, status="active",
        size_id=size.id, color_id=color.id, image_url="https://image",
        inventory=[SimpleNamespace(quantity=5, reserved_quantity=2)],
    )
    product = SimpleNamespace(
        id=variant.product_id, name=name, description="Algodón", category_id=category.id,
        collection_id=None, discount_type="percentage", discount_value=10,
    )
    return variant, product, category, None, None, size, color


def test_catalog_candidates_include_all_variant_context_without_internal_fields():
    rows = [_catalog_row(), _catalog_row(name="Polera azul", color_name="Azul")]
    query = FakeQuery(rows)
    candidates = _catalog_candidates(SimpleNamespace(query=lambda *args: query))
    assert len(candidates) == 2
    assert {item["color_name"] for item in candidates} == {"Rojo", "Azul"}
    assert all(item["size_name"] == "M" and item["available_quantity"] == 3 for item in candidates)
    assert all("provider_id" not in item and "reserved_quantity" not in item for item in candidates)


def test_selector_accepts_only_variant_ids_deduplicated_and_capped():
    ids = [str(uuid4()) for _ in range(5)]
    raw = '{"selected_variant_ids": ["%s", "unknown", "%s", "%s", "%s", "%s"]}' % tuple(ids)
    assert _parse_selected_ids(raw, set(ids)) == ids[:4]


def test_red_shirt_fallback_uses_variant_color_data():
    red = _catalog_row(color_name="Rojo")
    blue = _catalog_row(color_name="Azul")
    candidates = _catalog_candidates(SimpleNamespace(query=lambda *args: FakeQuery([red, blue])))
    assert _fallback_selected_ids("Busco poleras rojas", candidates, None) == [candidates[0]["variant_id"]]


def test_final_context_fetches_variants_from_db_and_drops_fabricated_ids():
    row = _catalog_row()
    actual_id = str(row[0].id)
    query = FakeQuery([row])
    context = _catalog_final_context(SimpleNamespace(query=lambda *args: query), [actual_id, str(uuid4())], None)
    assert context["selected_variant_ids"] == [actual_id]
    assert context["products"][0]["variants"][0]["variant_id"] == actual_id


def test_selection_prompt_includes_profile_and_all_candidates(monkeypatch):
    from app.services import chatbot_service
    rows = [_catalog_row(), _catalog_row(name="Polera azul", color_name="Azul")]
    profile = SimpleNamespace(top_size="M", bottom_size=None, shoe_size=None, body_shape="pera", fit_preference=None, notes=None)
    prompts = []
    monkeypatch.setattr(chatbot_service.settings, "gemini_api_key", "test")
    monkeypatch.setattr(chatbot_service, "_generate_sync", lambda prompt: prompts.append(prompt) or '{"selected_variant_ids": []}')
    candidates = _catalog_candidates(SimpleNamespace(query=lambda *args: FakeQuery(rows)))
    selected, used_fallback = asyncio.run(_select_catalog_ids("poleras", candidates, profile))
    payload = __import__("json").loads(prompts[0])
    assert payload["profile"]["top_size"] == "M"
    assert len(payload["candidates"]) == 2
    assert selected and used_fallback
