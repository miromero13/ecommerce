"""RFM segmentation uses paying customers, never cashier identities."""
from datetime import datetime, timezone
from uuid import UUID

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from app.services.ml.synthetic_data_generator import source_metadata, synthetic_customers


RECOMMENDATIONS = {
    'Clientes de alto valor': 'Fidelizar: acceso anticipado a colecciones, beneficios del programa de lealtad y atención preferente.',
    'Clientes de valor medio': 'Aumentar ticket: recomendar prendas complementarias y promociones por volumen.',
    'Clientes ocasionales': 'Reactivar: enviar un cupón de regreso o novedades de temporada.',
}


def segment_customers(customers: list[tuple[float, float, float]], names: list[str] | None = None) -> dict:
    synthetic = synthetic_customers() if len(customers) < 30 or len(set(customers)) < 3 else []
    values = np.asarray(customers + synthetic, dtype=float)
    scaled = StandardScaler().fit_transform(values)
    model = KMeans(n_clusters=3, random_state=42, n_init=10)
    labels = model.fit_predict(scaled)
    # Name by monetary centroid, without inferring unsupported price sensitivity.
    ranked = sorted(range(3), key=lambda cluster: values[labels == cluster, 2].mean(), reverse=True)
    labels_by_cluster = dict(zip(ranked, RECOMMENDATIONS))
    segments = []
    for cluster in range(3):
        mask = labels == cluster
        real_count = int(mask[:len(customers)].sum())
        size = int(mask.sum())
        top = sorted(np.flatnonzero(mask[:len(customers)]), key=lambda i: -customers[i][2])[:5]
        segments.append({'cluster_id': cluster, 'name': labels_by_cluster[cluster], 'size': size,
                         'avg_spend': round(float(values[mask, 2].mean()), 2),
                         'real_customers': real_count, 'synthetic_customers': size - real_count,
                         'avg_recency_days': round(float(values[mask, 0].mean()), 1),
                         'avg_orders': round(float(values[mask, 1].mean()), 1),
                         'recommendation': RECOMMENDATIONS[labels_by_cluster[cluster]],
                         'top_customers': [names[i] for i in top] if names else []})
    return {'model_type': 'K-Means Clustering', 'clusters_count': 3,
            'evaluation_metrics': {'silhouette_score': round(float(silhouette_score(scaled, labels, sample_size=min(2000, len(values)), random_state=42)), 6)},
            'segments': segments, 'data_source': source_metadata(len(customers), len(synthetic))}


# [CU08 - Secuencia: Paso 4.2] report_routes invoca customer_clusters(tenant_id, use_synthetic_data) sobre la entidad Pedido
# [CU08 - Secuencia: Paso 4.3] Pedido retorna customer_clusters(tenant_id, use_synthetic_data): dict a report_routes
def customer_clusters(db, tenant_id: UUID, *, use_synthetic_data: bool = False) -> dict:
    if use_synthetic_data:
        return segment_customers([])

    from sqlalchemy import func
    from app.models.order import Order

    from app.models.user import User

    rows = db.query(Order.user_id, User.name, func.max(Order.created_at), func.count(Order.id), func.sum(Order.total_amount)).outerjoin(
        User, User.id == Order.user_id).filter(
        Order.tenant_id == tenant_id, Order.status == 'paid', Order.payment_status == 'paid',
    ).group_by(Order.user_id, User.name).all()
    today = datetime.now(timezone.utc).date()
    # Compare both dates in UTC: a local timestamp would shift recency by a day late at night.
    customers = [(max(0, (today - last.astimezone(timezone.utc).date()).days), int(frequency), float(amount))
                 for _, _, last, frequency, amount in rows]
    return segment_customers(customers, [name or 'Cliente' for _, name, *_ in rows])
