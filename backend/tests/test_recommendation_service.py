from types import SimpleNamespace
import inspect
from uuid import uuid4

import numpy as np
import pytest

from app.services.recommendation_service import (
    ADD_TO_CART,
    COMPLETED_ORDER,
    _eligible_product_ids,
    _bounded_affinity_score,
    _popular_recommendations,
    aggregate_interactions,
    rank_embedding_scores,
    record_product_view,
    validate_recommendation_owner,
    VIEW,
    WEIGHTS,
)
from seed import RECOMMENDATION_DEMO_INTERACTIONS


def test_aggregate_interactions_groups_weights_by_parent_product():
    user_id, product_id, other_product_id = uuid4(), uuid4(), uuid4()
    rows = [
        SimpleNamespace(user_id=user_id, product_id=product_id, weight=1),
        SimpleNamespace(user_id=user_id, product_id=product_id, weight=2),
        SimpleNamespace(user_id=user_id, product_id=other_product_id, weight=5),
    ]

    users, products, matrix = aggregate_interactions(rows)

    assert users == [user_id]
    assert matrix[0, products.index(product_id)] == 3
    assert matrix[0, products.index(other_product_id)] == 5


def test_embedding_ranking_excludes_purchased_products_and_breaks_ties_by_id():
    user_id, first_product, second_product, bought_product = uuid4(), uuid4(), uuid4(), uuid4()
    ranked = rank_embedding_scores(
        np.asarray([1.0, 0.0]),
        {first_product: np.asarray([1.0, 0.0]), second_product: np.asarray([1.0, 0.0]), bought_product: np.asarray([10.0, 0.0])},
        {bought_product},
    )

    assert [product_id for product_id, _ in ranked] == sorted([first_product, second_product], key=str)


def test_seed_demo_interactions_recommend_products_bought_by_similar_clients():
    users = [uuid4() for _ in range(10)]
    products = [uuid4() for _ in range(8)]
    rows = [
        SimpleNamespace(user_id=users[client_index], product_id=products[product_index], weight=WEIGHTS[interaction_type])
        for client_index, interaction_type, product_indices in RECOMMENDATION_DEMO_INTERACTIONS
        for product_index in product_indices
    ]

    assert {client_index for client_index, _, _ in RECOMMENDATION_DEMO_INTERACTIONS} == set(range(10))
    assert {interaction_type for _, interaction_type, _ in RECOMMENDATION_DEMO_INTERACTIONS} == {VIEW, ADD_TO_CART, COMPLETED_ORDER}
    target_completed = {
        product_index
        for client_index, interaction_type, product_indices in RECOMMENDATION_DEMO_INTERACTIONS
        if client_index == 0 and interaction_type == COMPLETED_ORDER
        for product_index in product_indices
    }
    assert target_completed == {0, 1}
    assert len(rows) > 50

    user_ids, product_ids, matrix = aggregate_interactions(rows)
    from app.services.recommendation_service import _implicit_als

    user_vectors, product_vectors = _implicit_als(matrix, len(user_ids), len(product_ids))
    ranked = rank_embedding_scores(
        user_vectors[user_ids.index(users[0])],
        dict(zip(product_ids, product_vectors)),
        {products[product_index] for product_index in (0, 1)},
    )

    assert {product_id for product_id, _ in ranked}.issubset(set(products[2:]))
    assert ranked


def test_recommendation_owner_must_match_jwt_subject():
    user_id = uuid4()
    validate_recommendation_owner(user_id, {"sub": str(user_id)})

    with pytest.raises(PermissionError):
        validate_recommendation_owner(user_id, {"sub": str(uuid4())})


def test_recommendation_eligibility_accepts_only_optional_branch_context():
    class Query:
        def __init__(self, rows):
            self.rows = rows
            self.join_count = 0
            self.filter_count = 0

        def join(self, *args, **kwargs):
            self.join_count += 1
            return self

        def filter(self, *args, **kwargs):
            self.filter_count += 1
            return self
        def distinct(self): return self
        def all(self): return self.rows

    product_id = uuid4()
    query = Query([SimpleNamespace(id=product_id)])
    db = SimpleNamespace(query=lambda *args: query)
    assert list(inspect.signature(_eligible_product_ids).parameters) == ["db", "branch_id"]
    assert _eligible_product_ids(db, branch_id=uuid4()) == {product_id}
    assert query.join_count == 2
    assert query.filter_count == 3


def test_history_affinity_boosts_matching_weighted_attributes_and_is_bounded():
    size, other_size, category, other_category = (uuid4() for _ in range(4))
    preferences = {"size": {size: 7.0, other_size: 1.0}, "category": {category: 7.0, other_category: 1.0}}
    totals = {"size": 8.0, "category": 8.0}
    matching = _bounded_affinity_score(preferences, totals, {"size": {size}, "category": {category}})
    other = _bounded_affinity_score(preferences, totals, {"size": {other_size}, "category": {other_category}})
    assert matching > other
    assert 0 <= matching <= 1


def test_product_view_is_idempotent_for_repeated_browsing():
    product_id = uuid4()
    class FakeDB:
        def __init__(self):
            class Query:
                def __init__(self, result): self.result = result
                def join(self, *args, **kwargs): return self
                def filter(self, *args, **kwargs): return self
                def first(self): return self.result

            self.queries = [Query(SimpleNamespace(id=product_id)), Query(SimpleNamespace(id=uuid4()))]

        def query(self, _model): return self.queries.pop(0)

    db = FakeDB()
    db.add = lambda value: None
    db.commit = lambda: None
    assert record_product_view(db, uuid4(), product_id)


def test_popular_fallback_is_deterministic_and_excludes_history():
    first, second, bought = uuid4(), uuid4(), uuid4()

    class Query:
        def filter(self, *args, **kwargs): return self
        def group_by(self, *args, **kwargs): return self
        def all(self):
            return [SimpleNamespace(product_id=second, score=2)]

    ranked = _popular_recommendations(
        SimpleNamespace(query=lambda *_: Query()),
        {first, second, bought},
        {bought},
        2,
    )
    assert [product_id for product_id, _ in ranked] == [second, first]
