"""RFM segmentation uses paying customers, never cashier identities."""
from datetime import datetime, timezone
from uuid import UUID

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from app.services.ml.synthetic_data_generator import source_metadata, synthetic_customers


def segment_customers(customers: list[tuple[float, float, float]]) -> dict:
    synthetic = synthetic_customers() if len(customers) < 30 or len(set(customers)) < 3 else []
    values = np.asarray(customers + synthetic, dtype=float)
    scaled = StandardScaler().fit_transform(values)
    model = KMeans(n_clusters=3, random_state=42, n_init=10)
    labels = model.fit_predict(scaled)
    # Name by monetary centroid, without inferring unsupported price sensitivity.
    ranked = sorted(range(3), key=lambda cluster: values[labels == cluster, 2].mean(), reverse=True)
    names = dict(zip(ranked, ['Clientes de alto valor', 'Clientes de valor medio', 'Clientes ocasionales']))
    segments = []
    for cluster in range(3):
        mask = labels == cluster
        real_count = int(mask[:len(customers)].sum())
        size = int(mask.sum())
        segments.append({'cluster_id': cluster, 'name': names[cluster], 'size': size,
                         'avg_spend': round(float(values[mask, 2].mean()), 2),
                         'real_customers': real_count, 'synthetic_customers': size - real_count})
    return {'model_type': 'K-Means Clustering', 'clusters_count': 3,
            'evaluation_metrics': {'silhouette_score': round(float(silhouette_score(scaled, labels, sample_size=min(2000, len(values)), random_state=42)), 6)},
            'segments': segments, 'data_source': source_metadata(len(customers), len(synthetic))}


def customer_clusters(db, tenant_id: UUID, *, use_synthetic_data: bool = False) -> dict:
    if use_synthetic_data:
        return segment_customers([])

    from sqlalchemy import func
    from app.models.order import Order

    rows = db.query(Order.user_id, func.max(Order.created_at), func.count(Order.id), func.sum(Order.total_amount)).filter(
        Order.tenant_id == tenant_id, Order.status == 'paid', Order.payment_status == 'paid',
    ).group_by(Order.user_id).all()
    today = datetime.now(timezone.utc).date()
    # Compare both dates in UTC: a local timestamp would shift recency by a day late at night.
    customers = [(max(0, (today - last.astimezone(timezone.utc).date()).days), int(frequency), float(amount))
                 for _, last, frequency, amount in rows]
    return segment_customers(customers)
