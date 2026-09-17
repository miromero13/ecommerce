from __future__ import annotations

import asyncio
import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.category import Category
from app.models.color import Color
from app.models.collection import Collection
from app.models.conversation import Conversation
from app.models.order import Order
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.season import Season
from app.models.size import Size
from app.models.user_profile import UserBodyProfile
from app.schemas.chatbot_schema import ChatIntent, ConversationTurn
from app.schemas.catalog_enums import ProductStatusEnum
from app.services.conversation_service import append_message, clear_conversation, get_or_create_conversation, load_recent_messages


DATA_DIR = Path(__file__).resolve().parent.parent / "core" / "data"
_STOP_WORDS = {
    "busco", "quiero", "necesito", "tienes", "tienen", "una", "uno", "unos", "unas",
    "para", "con", "por", "que", "del", "las", "los", "mis", "dame", "mostrar",
    "muestra", "producto", "productos", "favor", "me", "mi", "de", "el", "la", "y",
}
_FIELD_VALUES = {
    "category": ("blusa", "vestido", "falda", "pantalon", "chaqueta", "top"),
    "color": ("negro", "blanco", "azul", "rojo", "verde", "beige", "gris", "rosa", "marron"),
    "size": ("xs", "s", "m", "l", "xl", "28", "30", "32", "34", "36", "38", "40"),
    "season": ("primavera", "verano", "otono", "invierno"),
}
_TERM_ALIASES = {"roja": "rojo", "rojas": "rojo", "azules": "azul", "negras": "negro", "blancas": "blanco", "poleras": "polera"}


def classify_intent(message: str, conversation: list[ConversationTurn] | None = None) -> ChatIntent:
    intent = _classify_explicit(message)
    if intent:
        return intent
    for turn in reversed(conversation or []):
        if turn.role == "user" and (intent := _classify_explicit(turn.content)):
            return intent
    return ChatIntent.CATALOGO


def _parse_routed_intent(raw: str) -> ChatIntent | None:
    """Accept only one exact JSON intent response from the routing model."""
    text = raw.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    try:
        payload = json.loads(text, object_pairs_hook=reject_duplicate_keys)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or set(payload) != {"intent"} or not isinstance(payload["intent"], str):
        return None
    try:
        return ChatIntent(payload["intent"])
    except ValueError:
        return None


async def route_intent(message: str, history: list[ConversationTurn] | None = None) -> ChatIntent:
    """Route with Gemini without exposing catalog, order, or static source content."""
    if not settings.gemini_api_key:
        return classify_intent(message, history)

    prompt = json.dumps({
        "task": "Route the current user request to exactly one destination. Prioritize current_message over history.",
        "destinations": {
            "CATALOGO": "Product or garment recommendations and catalog search.",
            "PEDIDOS": "The authenticated user's orders, tracking, shipping, and active order status.",
            "POLITICAS": "Store policies: returns, exchanges, payments, privacy, and reservations.",
            "USO_SISTEMA": "How to use the website or account: registration, login, profile, password, and features.",
        },
        "history": [{"role": turn.role, "content": turn.content} for turn in history or []],
        "current_message": {"role": "user", "content": message},
        "output_format": '{"intent": "CATALOGO"}',
    }, ensure_ascii=False)
    try:
        raw = await asyncio.wait_for(asyncio.to_thread(_generate_sync, prompt), timeout=settings.gemini_timeout_seconds)
        return _parse_routed_intent(raw) or classify_intent(message, history)
    except Exception:
        return classify_intent(message, history)


def _classify_explicit(message: str) -> ChatIntent | None:
    text = _normalize(message)
    scores = {
        ChatIntent.PEDIDOS: _contains_any(text, ("pedido", "orden", "envio", "entrega", "seguimiento", "tracking")),
        ChatIntent.POLITICAS: _contains_any(text, ("politica", "devolucion", "cambio", "pago", "privacidad", "reserva")),
        ChatIntent.USO_SISTEMA: _contains_any(text, (
            "como uso", "como funciona", "cuenta", "asistente", "sistema", "perfil",
            "registrar", "registro", "crear cuenta", "iniciar sesion", "iniciar sesión",
            "login", "contraseña", "contrasena", "recuperar contraseña", "recuperar contrasena",
        )),
        ChatIntent.CATALOGO: _contains_any(text, (
            "catalogo", "producto", "productos", "prenda", "prendas", "ropa", "talla", "color",
            "vestido", "blusa", "pantalon", "polera", "poleras", "camiseta", "camisetas",
            "remera", "remeras", "recomendacion", "recomendaciones",
        )),
    }
    for intent in (ChatIntent.PEDIDOS, ChatIntent.POLITICAS, ChatIntent.USO_SISTEMA, ChatIntent.CATALOGO):
        if scores[intent]:
            return intent
    return None


def extract_profile_updates(message: str) -> dict[str, str]:
    text = message.strip()
    updates: dict[str, str] = {}
    patterns = {
        "top_size": r"(?:(?:talla|tamaño|tamano)\s+(?:de\s+)?(?:arriba|superior|top)\s*(?:es|:)?\s*([a-z0-9]+)|(?:talla|tamaño|tamano)\s+([a-z0-9]+)\s+(?:de\s+)?(?:arriba|superior|top))",
        "bottom_size": r"(?:(?:talla|tamaño|tamano)\s+(?:de\s+)?(?:abajo|inferior|bottom)\s*(?:es|:)?\s*([a-z0-9]+)|(?:talla|tamaño|tamano)\s+([a-z0-9]+)\s+(?:de\s+)?(?:abajo|inferior|bottom))",
        "shoe_size": r"(?:(?:talla|numero)\s+(?:de\s+)?(?:zapato|calzado)\s*(?:es|:)?\s*([0-9]+(?:[.,][0-9]+)?)|calzo\s+([0-9]+(?:[.,][0-9]+)?))",
        "body_shape": r"(?:mi\s+)?(?:tipo|forma)\s+de\s+cuerpo\s+(?:es|:|=)\s*((?:reloj\s+de\s+arena|tri[aá]ngulo\s+invertido|tri[aá]ngulo|rect[aá]ngulo|ovalado|manzana|pera))",
        "fit_preference": r"(?:prefiero|mi\s+preferencia\s+de\s+calce\s+es)\s+(ajustado|entallado|holgado|suelto|regular)",
        "notes": r"(?:mi\s+)?nota\s+(?:es|:|=)\s*([^.!?\n]{2,160})",
    }
    for field, pattern in patterns.items():
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = next((group for group in match.groups() if group), "")
            value = " ".join(value.strip().split())
            if field in {"top_size", "bottom_size", "shoe_size"}:
                value = value.upper()
            max_length = 32 if field in {"top_size", "bottom_size", "shoe_size"} else 64 if field in {"body_shape", "fit_preference"} else 160
            updates[field] = value[:max_length]
    return updates


def upsert_profile(db: Session, user_id: UUID, updates: dict[str, str], commit: bool = True) -> UserBodyProfile | None:
    if not updates:
        return db.query(UserBodyProfile).filter(UserBodyProfile.user_id == user_id).first()
    profile = db.query(UserBodyProfile).filter(UserBodyProfile.user_id == user_id).first()
    if profile is None:
        profile = UserBodyProfile(user_id=user_id)
        db.add(profile)
    for field, value in updates.items():
        setattr(profile, field, value)
    if commit:
        db.commit()
        db.refresh(profile)
    return profile


def _catalog_context(db: Session, message: str, profile: UserBodyProfile | None, recent_messages: list[str] | None = None) -> dict[str, Any]:
    text = _normalize(" ".join([*(recent_messages or []), message]))
    filters = {
        field: [value for value in values if re.search(rf"\b{re.escape(value)}\b", text)]
        for field, values in _FIELD_VALUES.items()
    }
    terms = [word for word in re.findall(r"[a-z0-9áéíóúñ]+", text) if word not in _STOP_WORDS and len(word) > 2]
    query = (
        db.query(Product)
        .join(ProductVariant, ProductVariant.product_id == Product.id)
        .join(Category, Category.id == Product.category_id)
        .outerjoin(Color, Color.id == ProductVariant.color_id)
        .outerjoin(Size, Size.id == ProductVariant.size_id)
        .outerjoin(Collection, Collection.id == Product.collection_id)
        .outerjoin(Season, Season.id == Collection.season_id)
        .filter(ProductVariant.status == "active")
    )
    for field, values in filters.items():
        if not values:
            continue
        column = {"category": Category.name, "color": Color.name, "size": Size.name, "season": Season.name}[field]
        query = query.filter(or_(*(column.ilike(f"%{value}%") for value in values)))
    for term in terms:
        query = query.filter(or_(Product.name.ilike(f"%{term}%"), Product.description.ilike(f"%{term}%"), Category.name.ilike(f"%{term}%"), Color.name.ilike(f"%{term}%"), Size.name.ilike(f"%{term}%"), Season.name.ilike(f"%{term}%")))
    products = query.distinct().order_by(Product.name.asc()).limit(4).all()
    result = []
    for product in products:
        variants = [variant for variant in product.variants if str(variant.status) == "ProductStatusEnum.active" or getattr(variant.status, "value", variant.status) == "active"]
        result.append({
            "id": str(product.id),
            "name": product.name,
            "description": product.description,
            "category_id": str(product.category_id),
            "variants": [{"sku": item.sku, "price": _safe_value(item.price), "size_id": str(item.size_id) if item.size_id else None, "color_id": str(item.color_id) if item.color_id else None} for item in variants],
        })
    return {"filters": filters, "search_terms": terms, "products": result, "profile": _profile_dict(profile)}


def _has_meaningful_profile(profile: UserBodyProfile | None) -> bool:
    return bool(profile and any((getattr(profile, field, None) or "").strip() for field in _profile_fields()))


def _profile_fields() -> tuple[str, ...]:
    return ("top_size", "bottom_size", "shoe_size", "body_shape", "fit_preference", "notes")


def _profile_question_pending(history: list[ConversationTurn]) -> bool:
    return bool(
        history
        and history[-1].role == "assistant"
        and any(term in _normalize(history[-1].content) for term in ("datos de tu cuerpo", "datos de perfil", "talla de arriba"))
    )


def _is_affirmative(message: str) -> bool:
    return bool(re.fullmatch(r"(?:si|sí|claro|dale|de acuerdo|ok|okay|bueno|acepto)[.!? ]*", message.strip(), re.IGNORECASE))


def _is_negative(message: str) -> bool:
    return bool(re.fullmatch(r"(?:no|no gracias|prefiero no|ahora no)[.!? ]*", message.strip(), re.IGNORECASE))


def _profile_request_answer(message: str, updates: dict[str, str]) -> str | None:
    if updates:
        return None
    if _is_affirmative(message):
        return "Perfecto. Decime tus tallas de arriba y abajo, número de calzado, tipo de cuerpo y preferencia de calce para recomendarte mejor."
    if _is_negative(message):
        return None
    return None


def _active_products(db: Session) -> list[Product]:
    return (
        db.query(Product)
        .join(ProductVariant, ProductVariant.product_id == Product.id)
        .filter(ProductVariant.status == ProductStatusEnum.active)
        .distinct()
        .order_by(Product.name.asc())
        .all()
    )


def _available_quantity(variant: ProductVariant) -> int:
    return sum(max((item.quantity or 0) - (item.reserved_quantity or 0), 0) for item in getattr(variant, "inventory", []) or [])


def _catalog_candidates(db: Session) -> list[dict[str, Any]]:
    rows = (
        db.query(ProductVariant, Product, Category, Collection, Season, Size, Color)
        .join(Product, Product.id == ProductVariant.product_id)
        .join(Category, Category.id == Product.category_id)
        .outerjoin(Collection, Collection.id == Product.collection_id)
        .outerjoin(Season, Season.id == Collection.season_id)
        .outerjoin(Size, Size.id == ProductVariant.size_id)
        .outerjoin(Color, Color.id == ProductVariant.color_id)
        .options(selectinload(ProductVariant.inventory))
        .filter(ProductVariant.status == ProductStatusEnum.active)
        .order_by(Product.name.asc(), ProductVariant.sku.asc())
        .all()
    )
    return [
        {
            "variant_id": str(variant.id),
            "product_id": str(product.id),
            "product_name": product.name,
            "product_description": product.description,
            "category_id": str(category.id),
            "category_name": category.name,
            "collection_id": str(collection.id) if collection else None,
            "collection_name": collection.name if collection else None,
            "season_id": str(season.id) if season else None,
            "season_name": season.name if season else None,
            "sku": variant.sku,
            "price": _safe_value(variant.price),
            "discount_type": product.discount_type,
            "discount_value": _safe_value(product.discount_value),
            "size_id": str(size.id) if size else None,
            "size_name": size.name if size else None,
            "color_id": str(color.id) if color else None,
            "color_name": color.name if color else None,
            "image_url": variant.image_url,
            "status": _safe_value(variant.status),
            "available_quantity": _available_quantity(variant),
        }
        for variant, product, category, collection, season, size, color in rows
    ]


def _catalog_candidates_text(candidates: list[dict[str, Any]]) -> str:
    return json.dumps(candidates, ensure_ascii=False, default=str)


def _profile_terms(profile: UserBodyProfile | None) -> list[str]:
    return [_normalize(value) for field in _profile_fields() if (value := getattr(profile, field, None)) and value.strip()]


def _fallback_selected_ids(message: str, candidates: list[dict[str, Any]], profile: UserBodyProfile | None) -> list[str]:
    request_terms = re.findall(r"[a-z0-9áéíóúñ]+", _normalize(message))
    terms = [_TERM_ALIASES.get(term, term) for term in request_terms if len(term) > 2 and term not in _STOP_WORDS]
    terms += _profile_terms(profile)
    requested_colors = {_TERM_ALIASES.get(term, term) for term in request_terms if term in _FIELD_VALUES["color"] or term in _TERM_ALIASES}
    searchable = [item for item in candidates if any(color in _normalize(item.get("color_name") or "") for color in requested_colors)] or candidates
    scored = sorted(
        searchable,
        key=lambda item: sum(term in _normalize(" ".join(str(value or "") for value in item.values())) for term in terms),
        reverse=True,
    )
    matches = [item["variant_id"] for item in scored if any(term in _normalize(" ".join(str(value or "") for value in item.values())) for term in terms)]
    return matches[:4] or [item["variant_id"] for item in candidates[:4]]


def _parse_selected_ids(raw: str, candidate_ids: set[str]) -> list[str]:
    try:
        payload = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.IGNORECASE))
        selected = payload.get("selected_variant_ids", []) if isinstance(payload, dict) else []
        if not isinstance(selected, list):
            return []
        return list(dict.fromkeys(item for item in selected if isinstance(item, str) and item in candidate_ids))[:4]
    except (TypeError, ValueError, json.JSONDecodeError):
        return []


async def _select_catalog_ids(message: str, candidates: list[dict[str, Any]], profile: UserBodyProfile | None) -> tuple[list[str], bool]:
    fallback = _fallback_selected_ids(message, candidates, profile)
    if not settings.gemini_api_key or not candidates:
        return fallback, True
    prompt = json.dumps({
        "task": "Selecciona como máximo 4 variantes activas que coincidan con la solicitud y el perfil.",
        "request": message,
        "profile": _profile_dict(profile),
        "candidates": json.loads(_catalog_candidates_text(candidates)),
        "instructions": "Usa solo variant_id exactos de candidates; prefiere available_quantity > 0; no inventes IDs.",
        "output_format": '{"selected_variant_ids": ["uuid"]}',
    }, ensure_ascii=False)
    try:
        raw = await asyncio.wait_for(asyncio.to_thread(_generate_sync, prompt), timeout=settings.gemini_timeout_seconds)
        selected = _parse_selected_ids(raw, {item["id"] for item in candidates})
        return selected or fallback, not bool(selected)
    except Exception:
        return fallback, True


def _catalog_final_context(db: Session, selected_ids: list[str], profile: UserBodyProfile | None) -> dict[str, Any]:
    if not selected_ids:
        return {"products": [], "profile": _profile_dict(profile), "selected_variant_ids": []}
    rows = (
        db.query(ProductVariant, Product, Category, Collection, Season, Size, Color)
        .join(Product, Product.id == ProductVariant.product_id)
        .join(Category, Category.id == Product.category_id)
        .outerjoin(Collection, Collection.id == Product.collection_id)
        .outerjoin(Season, Season.id == Collection.season_id)
        .outerjoin(Size, Size.id == ProductVariant.size_id)
        .outerjoin(Color, Color.id == ProductVariant.color_id)
        .options(selectinload(ProductVariant.inventory))
        .filter(ProductVariant.id.in_(selected_ids), ProductVariant.status == ProductStatusEnum.active)
        .all()
    )
    by_variant_id = {str(row[0].id): row for row in rows}
    products_by_id: dict[str, dict[str, Any]] = {}
    result: list[dict[str, Any]] = []
    selected_variant_ids: list[str] = []
    for variant_id in dict.fromkeys(selected_ids):
        row = by_variant_id.get(variant_id)
        if row is None:
            continue
        variant, product, category, collection, season, size, color = row
        product_id = str(product.id)
        item = products_by_id.get(product_id)
        if item is None:
            item = {
                "id": product_id, "name": product.name, "description": product.description,
                "category_id": str(category.id), "category_name": category.name,
                "collection_id": str(collection.id) if collection else None,
                "collection_name": collection.name if collection else None,
                "season_id": str(season.id) if season else None,
                "season_name": season.name if season else None, "variants": [],
            }
            products_by_id[product_id] = item
            result.append(item)
        item["variants"].append({
            "variant_id": variant_id, "sku": variant.sku, "price": _safe_value(variant.price),
            "discount_type": product.discount_type, "discount_value": _safe_value(product.discount_value),
            "size_id": str(size.id) if size else None, "size_name": size.name if size else None,
            "color_id": str(color.id) if color else None, "color_name": color.name if color else None,
            "image_url": variant.image_url, "status": _safe_value(variant.status),
            "available_quantity": _available_quantity(variant),
        })
        selected_variant_ids.append(variant_id)
    return {"products": result, "profile": _profile_dict(profile), "selected_variant_ids": selected_variant_ids}


def _orders_context(db: Session, user_id: UUID) -> dict[str, Any]:
    orders = db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).limit(20).all()
    return {"orders": [{
        "display_reference": f"#{str(order.id).replace('-', '')[:8]}",
        "payment_status": _payment_status_label(getattr(order, "payment_status", getattr(order, "status", None))),
        "fulfillment_status": _fulfillment_status_label(getattr(order, "fulfillment_status", None)),
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
        "total": _safe_value(order.total_amount),
        "currency": order.currency,
        "shipping_reference": getattr(order, "shipping_reference", None),
    } for order in orders]}


def _static_context(intent: ChatIntent, message: str) -> dict[str, Any]:
    filename = "policies.json" if intent == ChatIntent.POLITICAS else "system_info.json"
    with (DATA_DIR / filename).open(encoding="utf-8") as file:
        content = json.load(file)
    return {"knowledge": content}


async def generate_answer(message: str, intent: ChatIntent, context: dict[str, Any], conversation: list[ConversationTurn] | None = None) -> tuple[str, bool]:
    if not settings.gemini_api_key:
        return _fallback(intent, context), True
    prompt = json.dumps({
        "intent": intent.value,
        "conversation": [{"role": turn.role, "content": turn.content} for turn in conversation or []],
        "current_message": {"role": "user", "content": message},
        "context": context,
    }, ensure_ascii=False, default=str)
    try:
        answer = await asyncio.wait_for(asyncio.to_thread(_generate_sync, prompt), timeout=settings.gemini_timeout_seconds)
        return answer, False
    except Exception:
        return _fallback(intent, context), True


def _generate_sync(prompt: str) -> str:
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)
    result = client.models.generate_content(
        model=settings.gemini_model,
        contents=("Responde en español de forma clara y breve. Responde únicamente lo que pregunta el usuario; "
                  "no agregues información relacionada que no haya solicitado. Usa únicamente el contexto estructurado; "
                  "no inventes disponibilidad, estados ni políticas y no reveles secretos. "
                  "En pedidos, nunca muestres UUIDs ni valores técnicos de enums: usa display_reference "
                  "y las etiquetas en español del contexto (Pagado, Pendiente, Fallido o Cancelado).\n" + prompt),
    )
    answer = (result.text or "").strip()
    if not answer:
        raise ValueError("Gemini returned an empty response")
    return answer


async def handle_message(db: Session, user_id: UUID, message: str, conversation: list[ConversationTurn] | None = None) -> dict[str, Any]:
    try:
        if _is_reset_request(message):
            persisted = clear_conversation(db, user_id)
            db.commit()
            return {
                "intent": ChatIntent.USO_SISTEMA.value,
                "answer": "Listo, inicié una conversación nueva.",
                "profile_updated": False,
                "context": {},
                "conversation_id": str(persisted.id),
                "conversation_context_used": False,
                "conversation_reset": True,
                "fallback": False,
            }

        persisted = get_or_create_conversation(db, user_id)
        persisted_messages = load_recent_messages(db, persisted)
        history = [ConversationTurn(role=item.role, content=item.content[:400]) for item in persisted_messages]
        intent = await route_intent(message, history)
        updates = extract_profile_updates(message)
        pending_profile = _profile_question_pending(history)
        if pending_profile and (updates or _is_affirmative(message) or _is_negative(message)):
            intent = ChatIntent.CATALOGO
        profile = upsert_profile(db, user_id, updates, commit=False)
        if intent == ChatIntent.CATALOGO:
            if not _has_meaningful_profile(profile) and not pending_profile and not updates:
                answer = "No tengo tus datos de perfil. Compartime tus tallas, número de calzado, tipo de cuerpo y preferencia de calce para analizar mejor qué prendas recomendarte. Si preferís no indicarlos, igual puedo buscar sin usar tus características."
                append_message(db, persisted, "user", message)
                append_message(db, persisted, "assistant", answer)
                db.commit()
                return {"intent": intent.value, "answer": answer, "profile_updated": False, "context": {},
                        "conversation_id": str(persisted.id), "conversation_context_used": bool(persisted_messages),
                        "conversation_reset": False, "fallback": False, "profile_requested": True}
            if pending_profile and _is_affirmative(message) and not updates:
                answer = _profile_request_answer(message, updates)
                append_message(db, persisted, "user", message)
                append_message(db, persisted, "assistant", answer)
                db.commit()
                return {"intent": intent.value, "answer": answer, "profile_updated": False, "context": {},
                        "conversation_id": str(persisted.id), "conversation_context_used": True,
                        "conversation_reset": False, "fallback": False, "profile_requested": True}
            candidates = _catalog_candidates(db)
            current_profile = None if (pending_profile and _is_negative(message)) else (profile if _has_meaningful_profile(profile) else None)
            selected_ids, selection_fallback = await _select_catalog_ids(message, candidates, current_profile)
            context = _catalog_final_context(db, selected_ids, current_profile)
            fallback = selection_fallback
        elif intent == ChatIntent.PEDIDOS:
            context = _orders_context(db, user_id)
            fallback = False
        else:
            context = _static_context(intent, message)
            fallback = False
        if intent == ChatIntent.CATALOGO:
            answer = _catalog_answer(context)
        else:
            answer, fallback = await generate_answer(message, intent, context, history)
        append_message(db, persisted, "user", message)
        message_data = _catalog_message_data(context) if intent == ChatIntent.CATALOGO else None
        append_message(db, persisted, "assistant", answer, message_data)
        db.commit()
        return {"intent": intent.value, "answer": answer, "profile_updated": bool(updates), "context": context,
                "conversation_id": str(persisted.id), "conversation_context_used": bool(persisted_messages),
                "conversation_reset": False, "fallback": fallback}
    except Exception:
        db.rollback()
        raise


def _fallback(intent: ChatIntent, context: dict[str, Any]) -> str:
    if intent == ChatIntent.CATALOGO:
        products = context.get("products", [])
        return "Encontré estos productos: " + ", ".join(item["name"] for item in products) if products else "No encontré productos activos que coincidan con tu consulta."
    if intent == ChatIntent.PEDIDOS:
        orders = context.get("orders", [])
        return "Tus pedidos recientes: " + "; ".join(
            f"{item['display_reference']} — {item['payment_status']}" + (f", {item['fulfillment_status']}" if item.get('fulfillment_status') else "")
            for item in orders
        ) if orders else "No encontré pedidos asociados a tu cuenta."
    knowledge = context.get("knowledge", context.get("topics", {}))
    return "Información disponible: " + " ".join(str(value) for value in knowledge.values())


def _catalog_answer(context: dict[str, Any]) -> str:
    return "Tengo algunas recomendaciones para vos." if context.get("products") else "No encontré prendas que coincidan con tu búsqueda."


def _profile_dict(profile: UserBodyProfile | None) -> dict[str, Any] | None:
    if profile is None:
        return None
    return {field: getattr(profile, field) for field in ("top_size", "bottom_size", "shoe_size", "body_shape", "fit_preference", "notes")}


def _safe_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    return getattr(value, "value", value)


def _payment_status_label(value: Any) -> str:
    return {"paid": "Pagado", "pending": "Pendiente", "failed": "Fallido", "cancelled": "Cancelado"}.get(_safe_value(value), "Pendiente")


def _fulfillment_status_label(value: Any) -> str | None:
    return {"pending_pickup": "En preparación", "ready_for_pickup": "Listo para retirar", "collected": "Retirado", "expired": "Expirado", "cancelled": "Cancelado"}.get(_safe_value(value)) if value else None


def _catalog_message_data(context: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "variant_id": variant["variant_id"], "product_id": product["id"], "name": product["name"],
            "description": product.get("description"), "image_url": variant.get("image_url"),
            "sku": variant.get("sku"), "price": variant.get("price"), "size_id": variant.get("size_id"),
            "size_name": variant.get("size_name"), "color_id": variant.get("color_id"),
            "color_name": variant.get("color_name"), "available_quantity": variant.get("available_quantity"),
        }
        for product in context.get("products", [])
        for variant in product.get("variants", [])
    ]


def _normalize(value: str) -> str:
    return value.lower().translate(str.maketrans("áéíóúñ", "aeioun"))


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _is_reset_request(message: str) -> bool:
    text = _normalize(message)
    return any(phrase in text for phrase in (
        "borra la conversacion", "borrar la conversacion", "borra el chat", "borrar el chat",
        "elimina la conversacion", "elimina el chat", "reinicia la conversacion",
        "reiniciar la conversacion", "reinicia el chat", "empezar de nuevo",
        "comenzar de nuevo", "empezar desde cero", "nueva conversacion", "nuevo chat",
        "clear chat", "reset chat",
    ))
