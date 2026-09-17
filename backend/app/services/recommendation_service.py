"""Train persisted implicit ALS embeddings with `python -m app.services.recommendation_service`."""

import json
from collections import defaultdict
from uuid import UUID

import numpy as np
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.inventory import Inventory
from app.models.collection import Collection
from app.models.recommendation import CollaborativeEmbedding, UserProductInteraction
from app.schemas.catalog_enums import ProductStatusEnum


VIEW = "view"
ADD_TO_CART = "add_to_cart"
COMPLETED_ORDER = "completed_order"
WEIGHTS = {VIEW: 1, ADD_TO_CART: 2, COMPLETED_ORDER: 5}


def record_interaction(db: Session, user_id: UUID, product_id: UUID, interaction_type: str, order_id: UUID | None = None, variant_id: UUID | None = None, branch_id: UUID | None = None) -> None:
    db.add(UserProductInteraction(
        user_id=user_id,
        product_id=product_id,
        interaction_type=interaction_type,
        weight=WEIGHTS[interaction_type],
        order_id=order_id,
        variant_id=variant_id,
        branch_id=branch_id,
    ))


def record_product_view(db: Session, user_id: UUID, product_id: UUID, variant_id: UUID | None = None, branch_id: UUID | None = None) -> bool:
    active_product = db.query(Product.id).join(ProductVariant).filter(
        Product.id == product_id,
        ProductVariant.status == ProductStatusEnum.active,
    ).first()
    if not active_product:
        return False
    existing_view = db.query(UserProductInteraction).filter(
        UserProductInteraction.user_id == user_id,
        UserProductInteraction.product_id == product_id,
        UserProductInteraction.interaction_type == VIEW,
    ).first()
    if existing_view:
        if variant_id and not getattr(existing_view, "variant_id", None):
            existing_view.variant_id = variant_id
        if branch_id and not getattr(existing_view, "branch_id", None):
            existing_view.branch_id = branch_id
        return True
    record_interaction(db, user_id, product_id, VIEW, variant_id=variant_id, branch_id=branch_id)
    db.commit()
    return True


def record_completed_order_interactions(db: Session, order) -> None:
    product_ids = {item.product_id for item in order.items}
    existing = {
        row.product_id
        for row in db.query(UserProductInteraction.product_id).filter(
            UserProductInteraction.order_id == order.id,
            UserProductInteraction.interaction_type == COMPLETED_ORDER,
        )
    }
    for item in order.items:
        if item.product_id not in existing:
            record_interaction(db, order.user_id, item.product_id, COMPLETED_ORDER, order.id, item.variant_id, order.pickup_branch_id)
    db.flush()


def aggregate_interactions(rows):
    """Return deterministic sparse coordinates keyed by user and parent product IDs."""
    users = sorted({row.user_id for row in rows}, key=str)
    products = sorted({row.product_id for row in rows}, key=str)
    user_index = {user_id: index for index, user_id in enumerate(users)}
    product_index = {product_id: index for index, product_id in enumerate(products)}
    matrix: dict[tuple[int, int], float] = defaultdict(float)
    for row in rows:
        matrix[user_index[row.user_id], product_index[row.product_id]] += float(row.weight)
    return users, products, dict(matrix)


def _implicit_als(matrix, user_count: int, product_count: int, factors: int = 16, iterations: int = 10, regularization: float = 0.1, alpha: float = 40.0):
    factors = min(factors, user_count, product_count)
    rng = np.random.default_rng(0)
    users = rng.normal(0, 0.01, (user_count, factors))
    products = rng.normal(0, 0.01, (product_count, factors))
    by_user: dict[int, list[tuple[int, float]]] = defaultdict(list)
    by_product: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for (user_index, product_index), weight in matrix.items():
        by_user[user_index].append((product_index, weight))
        by_product[product_index].append((user_index, weight))
    identity = np.eye(factors)

    for _ in range(iterations):
        product_gram = products.T @ products
        for user_index, values in by_user.items():
            indices, weights = zip(*values)
            vectors = products[list(indices)]
            confidence = 1.0 + alpha * np.asarray(weights)
            users[user_index] = np.linalg.solve(
                product_gram + vectors.T @ ((confidence - 1.0)[:, None] * vectors) + regularization * identity,
                vectors.T @ confidence,
            )
        user_gram = users.T @ users
        for product_index, values in by_product.items():
            indices, weights = zip(*values)
            vectors = users[list(indices)]
            confidence = 1.0 + alpha * np.asarray(weights)
            products[product_index] = np.linalg.solve(
                user_gram + vectors.T @ ((confidence - 1.0)[:, None] * vectors) + regularization * identity,
                vectors.T @ confidence,
            )
    return users, products


def train(db: Session) -> tuple[int, int]:
    rows = db.query(
        UserProductInteraction.user_id,
        UserProductInteraction.product_id,
        func.sum(UserProductInteraction.weight).label("weight"),
    ).group_by(UserProductInteraction.user_id, UserProductInteraction.product_id).all()
    user_ids, product_ids, matrix = aggregate_interactions(rows)
    if not matrix:
        return 0, 0
    user_vectors, product_vectors = _implicit_als(matrix, len(user_ids), len(product_ids))
    db.query(CollaborativeEmbedding).delete()
    for subject_id, vector in zip(user_ids, user_vectors):
        db.add(CollaborativeEmbedding(subject_type="user", subject_id=subject_id, vector=json.dumps(vector.tolist())))
    for subject_id, vector in zip(product_ids, product_vectors):
        db.add(CollaborativeEmbedding(subject_type="product", subject_id=subject_id, vector=json.dumps(vector.tolist())))
    db.commit()
    return len(user_ids), len(product_ids)


def _active_product_ids(db: Session) -> list[UUID]:
    return [
        row.id
        for row in db.query(Product.id).join(ProductVariant).filter(
            ProductVariant.status == ProductStatusEnum.active,
        ).distinct().all()
    ]


def _purchased_product_ids(db: Session, user_id: UUID) -> set[UUID]:
    return {
        row.product_id
        for row in db.query(UserProductInteraction.product_id).filter(
            UserProductInteraction.user_id == user_id,
            UserProductInteraction.interaction_type == COMPLETED_ORDER,
        )
    }


def rank_embedding_scores(user_vector, product_vectors, excluded_product_ids: set[UUID]):
    scores = [
        (product_id, float(np.dot(user_vector, vector)))
        for product_id, vector in product_vectors.items()
        if product_id not in excluded_product_ids
    ]
    return sorted(scores, key=lambda item: (-item[1], str(item[0])))


def _popular_recommendations(db: Session, available_ids: set[UUID], excluded_ids: set[UUID], limit: int):
    rows = db.query(
        UserProductInteraction.product_id,
        func.sum(UserProductInteraction.weight).label("score"),
    ).filter(
        UserProductInteraction.product_id.in_(available_ids - excluded_ids),
    ).group_by(UserProductInteraction.product_id).all()
    ranked = sorted(((row.product_id, float(row.score)) for row in rows), key=lambda item: (-item[1], str(item[0])))
    used = {product_id for product_id, _ in ranked}
    ranked.extend((product_id, 0.0) for product_id in sorted(available_ids - excluded_ids - used, key=str))
    return ranked[:limit]


def _eligible_product_ids(db: Session, branch_id: UUID | None = None) -> set[UUID]:
    query = db.query(Product.id).join(ProductVariant).filter(
        ProductVariant.status == ProductStatusEnum.active,
    )
    query = query.join(Inventory, Inventory.variant_id == ProductVariant.id).filter(
        Inventory.quantity > Inventory.reserved_quantity,
    )
    if branch_id:
        query = query.filter(Inventory.branch_id == branch_id)
    return {row.id for row in query.distinct().all()}


def _history_affinity(db: Session, user_id: UUID, candidate_ids: set[UUID]) -> dict[UUID, float]:
    """Learn weighted parent, variant, season, and branch metadata; cap boost at 0.25."""
    events = db.query(UserProductInteraction).filter(UserProductInteraction.user_id == user_id).all()
    products = {row.id: row for row in db.query(Product).filter(Product.id.in_(candidate_ids)).all()}
    all_products = {row.id: row for row in db.query(Product).all()}
    variants = {row.id: row for row in db.query(ProductVariant).all()}
    collections = {row.id: row for row in db.query(Collection).all()}
    preferences = defaultdict(lambda: defaultdict(float))
    totals = defaultdict(float)
    for event in events:
        product = all_products.get(event.product_id)
        if not product:
            continue
        variant = variants.get(event.variant_id)
        collection = collections.get(product.collection_id)
        features = {"category": product.category_id, "collection": product.collection_id,
                    "season": collection.season_id if collection else None,
                    "size": getattr(variant, "size_id", None), "color": getattr(variant, "color_id", None),
                    "branch": event.branch_id}
        for dimension, value in features.items():
            if value is not None:
                preferences[dimension][value] += event.weight
                totals[dimension] += event.weight
    result = {}
    for product_id, product in products.items():
        variants_for_product = [row for row in variants.values() if row.product_id == product_id]
        collection = collections.get(product.collection_id)
        values = {"category": {product.category_id}, "collection": {product.collection_id} if product.collection_id else set(),
                  "season": {collection.season_id} if collection else set(),
                  "size": {row.size_id for row in variants_for_product if row.size_id},
                  "color": {row.color_id for row in variants_for_product if row.color_id},
                  "branch": {row.branch_id for row in db.query(Inventory.branch_id).filter(Inventory.variant_id.in_([variant.id for variant in variants_for_product])).all()}}
        result[product_id] = _bounded_affinity_score(preferences, totals, values)
    return result


def _bounded_affinity_score(preferences, totals, candidate_values) -> float:
    matches = [max((preferences[dimension][value] for value in values), default=0) / totals[dimension]
               for dimension, values in candidate_values.items() if values and totals[dimension]]
    return sum(matches) / len(matches) if matches else 0.0


def get_recommendations(
    db: Session,
    user_id: UUID,
    limit: int = 12,
    branch_id: UUID | None = None,
) -> dict:
    available_ids = _eligible_product_ids(db, branch_id)
    excluded_ids = _purchased_product_ids(db, user_id)
    user_embedding = db.query(CollaborativeEmbedding).filter(
        CollaborativeEmbedding.subject_type == "user",
        CollaborativeEmbedding.subject_id == user_id,
    ).first()
    if user_embedding:
        product_embeddings = {
            row.subject_id: np.asarray(json.loads(row.vector))
            for row in db.query(CollaborativeEmbedding).filter(
                CollaborativeEmbedding.subject_type == "product",
                CollaborativeEmbedding.subject_id.in_(available_ids),
            )
        }
        ranked = rank_embedding_scores(np.asarray(json.loads(user_embedding.vector)), product_embeddings, excluded_ids)
        if ranked:
            affinity = _history_affinity(db, user_id, {product_id for product_id, _ in ranked})
            ranked = sorted(((product_id, score + min(0.25, 0.25 * affinity.get(product_id, 0.0))) for product_id, score in ranked), key=lambda item: (-item[1], str(item[0])))
            return {
                "logic_type": "implicit_als",
                "user_id": str(user_id),
                "recommendations": [{"product_id": str(product_id), "score": score} for product_id, score in ranked[:limit]],
            }
    ranked = _popular_recommendations(db, available_ids, excluded_ids, limit)
    affinity = _history_affinity(db, user_id, {product_id for product_id, _ in ranked})
    ranked = sorted(((product_id, score + min(0.25, 0.25 * affinity.get(product_id, 0.0))) for product_id, score in ranked), key=lambda item: (-item[1], str(item[0])))[:limit]
    return {
        "logic_type": "popular_fallback",
        "user_id": str(user_id),
        "recommendations": [{"product_id": str(product_id), "score": score} for product_id, score in ranked],
    }


def validate_recommendation_owner(path_user_id: UUID, payload: dict) -> None:
    if path_user_id != UUID(payload["sub"]):
        raise PermissionError("A client can only request their own recommendations")


if __name__ == "__main__":
    with SessionLocal() as session:
        users, products = train(session)
    print(f"Trained implicit ALS embeddings for {users} users and {products} products.")
