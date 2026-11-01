import calendar
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import case, func, literal, select, union_all
from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.category import Category
from app.models.color import Color
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.size import Size
from app.models.user import User
from app.schemas.analytics_schema import TIME_DIMENSIONS, AnalyticsQuery, AnalyticsResult, PeriodSpec
from app.schemas.order_schema import OrderStatusEnum, PaymentStatusEnum
from app.schemas.report_schema import ReportQuery
from app.schemas.sales_schema import SaleStatusEnum

LA_PAZ = timezone(timedelta(hours=-4))  # America/La_Paz: UTC-4 all year, no DST
CENT = Decimal("0.01")
# dimension: (column label, plural used in titles)
DIMENSIONS = {
    "product": ("Producto", "productos"), "variant": ("Variante", "variantes"),
    "category": ("Categoría", "categorías"), "branch": ("Sucursal", "sucursales"),
    "size": ("Talla", "tallas"), "color": ("Color", "colores"), "channel": ("Canal", "canales"),
    "payment_method": ("Método de pago", "métodos de pago"), "customer": ("Cliente", "clientes"),
    "day": ("Día", "días"), "week": ("Semana", "semanas"), "month": ("Mes", "meses"),
}
# metric: (column label, column type, wording used in titles)
METRICS = {
    "units": ("Unidades", "number", "unidades vendidas"), "revenue": ("Ingresos (Bs.)", "money", "ingresos"),
    "orders": ("Pedidos", "number", "pedidos"), "avg_ticket": ("Ticket promedio (Bs.)", "money", "ticket promedio"),
    "customers": ("Clientes", "number", "clientes distintos"),
}
CHANNEL_LABELS = {"store": "Tienda", "online": "En línea"}
PAYMENT_LABELS = {"cash": "Efectivo", "stripe": "Tarjeta (Stripe)", "qr": "QR", "wallet": "Billetera"}
PAYMENT_FILTER = {"cash": "cash", "card": "stripe", "qr": "qr", "wallet": "wallet"}  # spec value -> stored enum
PAYMENT_WORDS = {"cash": "en efectivo", "card": "con tarjeta", "qr": "con QR", "wallet": "con billetera"}
LOOKUPS = {  # dimension: (fact column, table, name column)
    "branch": ("branch_id", Branch, Branch.name), "product": ("product_id", Product, Product.name),
    "variant": ("variant_id", ProductVariant, ProductVariant.sku),
    "category": ("category_id", Category, Category.name),
    "size": ("size_id", Size, Size.name), "color": ("color_id", Color, Color.name),
    # the key comes from own-company rows only, so the (global) user table needs no tenant filter
    "customer": ("customer_id", User, User.name),
}


def _months_back(d: date, n: int) -> date:
    m = d.year * 12 + d.month - 1 - n
    y, mo = divmod(m, 12)
    return date(y, mo + 1, min(d.day, calendar.monthrange(y, mo + 1)[1]))


def resolve_period(period: PeriodSpec, today: date) -> tuple[date, date]:
    """Rango inclusivo (desde, hasta) para un período; fechas futuras se recortan a hoy."""
    p = period.preset
    if p == "today":
        start = end = today
    elif p == "yesterday":
        start = end = today - timedelta(days=1)
    elif p == "this_week":
        start, end = today - timedelta(days=today.weekday()), today
    elif p == "last_week":
        end = today - timedelta(days=today.weekday() + 1)
        start = end - timedelta(days=6)
    elif p == "last_n_days":
        start, end = today - timedelta(days=(period.n or 30) - 1), today
    elif p == "this_month":
        start, end = today.replace(day=1), today
    elif p == "last_month":
        end = today.replace(day=1) - timedelta(days=1)
        start = end.replace(day=1)
    elif p == "last_n_months":
        start, end = _months_back(today, period.n or 1) + timedelta(days=1), today
    elif p in ("this_quarter", "last_quarter"):
        start, end = today.replace(month=(today.month - 1) // 3 * 3 + 1, day=1), today
        if p == "last_quarter":
            end = start - timedelta(days=1)
            start = end.replace(month=end.month - 2, day=1)
    elif p == "this_year":
        start, end = today.replace(month=1, day=1), today
    elif p == "last_year":
        start, end = date(today.year - 1, 1, 1), date(today.year - 1, 12, 31)
    else:  # custom
        if not period.from_date or not period.to_date:
            raise ValueError("Indica las fechas del período")
        if period.from_date > period.to_date:
            raise ValueError("La fecha inicial no puede ser posterior a la final")
        start, end = period.from_date, period.to_date
    return min(start, today), min(end, today)


def _sales_fact(tenant_id: UUID):
    """Completed+paid till sales UNION ALL paid online orders, one row per line, own company only."""
    def half(head, line, on, channel, branch_id, customer_id, *status_filters):
        return (
            select(head.created_at.label("occurred_at"), branch_id.label("branch_id"), line.product_id,
                   line.variant_id, Product.category_id, line.size_id, line.color_id,
                   literal(channel).label("channel"), head.payment_method, line.quantity,
                   line.line_total, head.id.label("ticket_id"), customer_id.label("customer_id"))
            .select_from(head).join(line, on)
            .join(Product, Product.id == line.product_id)
            .where(head.tenant_id == tenant_id, Product.tenant_id == tenant_id, *status_filters)
        )

    # Customer: the online buyer, or the one identified at the till (coupon/loyalty); NULL for anonymous sales.
    store = half(Sale, SaleItem, SaleItem.sale_id == Sale.id, "store", Sale.branch_id, Sale.customer_id,
                 Sale.status == SaleStatusEnum.completed, Sale.payment_status == PaymentStatusEnum.paid)
    online = half(Order, OrderItem, OrderItem.order_id == Order.id, "online", Order.pickup_branch_id, Order.user_id,
                  Order.status == OrderStatusEnum.paid)
    return union_all(store, online).subquery("sales_fact")


def _dimension(dim, fact):
    """(group key, label expression, outer join or None) for one dimension."""
    if dim in TIME_DIMENSIONS:
        bucket = func.date_trunc(dim, func.timezone("America/La_Paz", fact.c.occurred_at))
        return bucket, bucket, None
    if dim == "channel":
        return fact.c.channel, case(CHANNEL_LABELS, value=fact.c.channel), None
    if dim == "payment_method":
        return fact.c.payment_method, case(PAYMENT_LABELS, value=fact.c.payment_method, else_="Otro"), None
    column, table, name = LOOKUPS[dim]
    key = fact.c[column]
    return key, func.coalesce(name, f"Sin {DIMENSIONS[dim][0].lower()}"), (table, table.id == key)


def _label(dim, value):
    if dim == "day":
        return f"{value:%Y-%m-%d}"
    if dim == "week":
        return f"Semana del {value:%Y-%m-%d}"
    if dim == "month":
        return f"{value:%Y-%m}"
    return value


def _value(metric, value):
    return Decimal(value or 0).quantize(CENT) if METRICS[metric][1] == "money" else int(value or 0)


def _between(fact, from_date, to_date):
    # Days are La Paz calendar days, compared against the stored timestamptz.
    return [fact.c.occurred_at >= datetime.combine(from_date, time.min, LA_PAZ),
            fact.c.occurred_at < datetime.combine(to_date + timedelta(days=1), time.min, LA_PAZ)]


def _totals(db, fact, filters, with_customers=False):
    units, revenue, orders, customers = db.execute(
        select(func.sum(fact.c.quantity), func.sum(fact.c.line_total), func.count(func.distinct(fact.c.ticket_id)),
               func.count(func.distinct(fact.c.customer_id)))
        .where(*filters)
    ).one()
    revenue = Decimal(revenue or 0)
    totals = {"units": int(units or 0), "revenue": revenue.quantize(CENT), "orders": orders,
              "avg_ticket": (revenue / orders if orders else Decimal(0)).quantize(CENT)}
    # Only customer queries add it: every other sales report keeps its long-standing four keys.
    return {**totals, "customers": customers} if with_customers else totals


def _uses_customers(query):
    return query.metric == "customers" or "customer" in query.group_by


def _payment_words(methods):
    words = [PAYMENT_WORDS[m] for m in dict.fromkeys(methods)]
    return ", ".join(words[:-1]) + " y " + words[-1] if len(words) > 1 else words[0]


def _title(query):
    if query.kind != "sales":
        return KINDS[query.kind][0]
    title = _sales_title(query)
    return f"{title}, {_payment_words(query.payment_methods)}" if query.payment_methods else title


def _sales_title(query):
    dims, metric = query.group_by, METRICS[query.metric][2]
    if not dims:
        return metric.capitalize()
    ranked = dims[-1]
    if ranked == "customer" and query.metric == "customers":  # one customer per row: only the count makes sense
        title = "Clientes distintos"
    elif ranked == "customer" and query.order == "desc":
        who = f"Top {query.top_n} clientes" if query.top_n else "Clientes"
        title = f"{who} que más compran por {metric}"
    elif query.top_n:
        title = f"Top {query.top_n} {DIMENSIONS[ranked][1]} por {metric}"
    else:
        title = f"{metric.capitalize()} por {DIMENSIONS[ranked][0].lower()}"
    return title + (f", agrupado por {DIMENSIONS[dims[0]][0].lower()}" if len(dims) == 2 else "")


def _chart(query, rows):
    if query.chart:
        return query.chart
    dims = query.group_by
    if TIME_DIMENSIONS & set(dims):
        return "line"
    if len(dims) == 1 and dims[0] in ("channel", "payment_method") and len(rows) <= 6:
        return "donut"
    return "bar"  # 2 dimensions: grouped bars


# [CU08 - Secuencia: Pasos 1.6, 2.2] report_routes invoca run_query(tenant_id, query, today) sobre la entidad Venta
# [CU08 - Secuencia: Pasos 1.7, 2.3] Venta retorna run_query(tenant_id, query, today): AnalyticsResult a report_routes
def run_query(db: Session, tenant_id: UUID, query: AnalyticsQuery, today: date) -> AnalyticsResult:
    if query.kind != "sales":
        return _stock_query(db, tenant_id, query, today)
    from_date, to_date = resolve_period(query.period, today)
    fact = _sales_fact(tenant_id)
    filters = []
    if query.branch_ids:
        filters.append(fact.c.branch_id.in_(query.branch_ids))
    if query.product_ids:
        filters.append(fact.c.product_id.in_(query.product_ids))
    if query.category_ids:
        filters.append(fact.c.category_id.in_(query.category_ids))
    if query.channel != "all":
        filters.append(fact.c.channel == query.channel)
    if query.payment_methods:
        filters.append(fact.c.payment_method.in_([PAYMENT_FILTER[m] for m in query.payment_methods]))
    if _uses_customers(query):  # ruling: anonymous till sales never count as a customer (nor as 'unknown')
        filters.append(fact.c.customer_id.is_not(None))

    revenue = func.sum(fact.c.line_total)
    orders = func.count(func.distinct(fact.c.ticket_id))
    value = {"units": func.sum(fact.c.quantity), "revenue": revenue, "orders": orders,
             "avg_ticket": revenue / func.nullif(orders, 0),
             "customers": func.count(func.distinct(fact.c.customer_id))}[query.metric]
    dims = [_dimension(dim, fact) for dim in query.group_by]
    # Top-N ranks the last dimension (within each value of the first one): metric, then name.
    rank = func.row_number().over(
        partition_by=dims[0][0] if len(dims) == 2 else None,
        order_by=[value.desc() if query.order == "desc" else value.asc(), *[label.asc() for _, label, _ in dims[-1:]]],
    )
    grouped = select(*[key.label(f"k{i}") for i, (key, _, _) in enumerate(dims)],
                     *[label.label(f"l{i}") for i, (_, label, _) in enumerate(dims)],
                     value.label("value"), rank.label("rn")).select_from(fact)
    for _, _, join in dims:
        if join:
            grouped = grouped.outerjoin(*join)
    grouped = (grouped.where(*_between(fact, from_date, to_date), *filters)
               .group_by(*[key for key, _, _ in dims], *[label for _, label, _ in dims]).subquery())
    stmt = select(grouped)
    if query.top_n:
        stmt = stmt.where(grouped.c.rn <= query.top_n)
    # Rows: first dimension by name (or date), then by rank; one dimension with top-N is a ranking.
    if len(dims) == 1 and query.top_n:
        stmt = stmt.order_by(grouped.c.rn)
    elif dims:
        stmt = stmt.order_by(grouped.c.l0, grouped.c.k0, grouped.c.rn)
    rows = [
        {**{dim: _label(dim, row._mapping[f"l{i}"]) for i, dim in enumerate(query.group_by)},
         query.metric: _value(query.metric, row.value)}
        for row in db.execute(stmt)
    ]

    # Totals cover the whole filtered period (not only the top-N rows), so they compare with the previous one.
    totals = _totals(db, fact, [*_between(fact, from_date, to_date), *filters], _uses_customers(query))
    previous_totals = delta_pct = None
    if query.compare_previous:
        prev_to = from_date - timedelta(days=1)
        prev_from = prev_to - (to_date - from_date)
        previous_totals = _totals(db, fact, [*_between(fact, prev_from, prev_to), *filters], _uses_customers(query))
        delta_pct = {key: round(float((totals[key] - prev) / prev * 100), 1) if prev else None
                     for key, prev in previous_totals.items()}

    metric_label, metric_type, _ = METRICS[query.metric]
    return AnalyticsResult(
        title=_title(query),
        period={"from_date": from_date, "to_date": to_date,
                "label": f"{from_date:%d/%m/%Y} al {to_date:%d/%m/%Y}"},
        columns=[*[{"key": dim, "label": DIMENSIONS[dim][0], "type": "text"} for dim in query.group_by],
                 {"key": query.metric, "label": metric_label, "type": metric_type}],
        rows=rows,
        totals=totals,
        previous_totals=previous_totals,
        delta_pct=delta_pct,
        chart=_chart(query, rows),
        message=None if rows else "No hay ventas en el período seleccionado",
    )


_ITEM = [("branch", "branch_name", "Sucursal", "text"), ("product", "product_name", "Producto", "text"),
         ("variant", "variant_sku", "Variante", "text")]
# kind: (title, empty message, [(key, legacy field, label, type)], totals from legacy rows)
KINDS = {
    "inventory": ("Inventario por sucursal", "No hay existencias para los filtros seleccionados",
                  [*_ITEM, ("quantity", "quantity", "Stock", "number"),
                   ("reserved", "reserved_quantity", "Reservado", "number"),
                   ("available", "available_quantity", "Disponible", "number")],
                  lambda rows: {"items": len(rows), "units": sum(r["quantity"] for r in rows),
                                "available": sum(r["available_quantity"] for r in rows)}),
    "critical_stock": ("Stock crítico por sucursal", "No hay productos con stock crítico",
                       [*_ITEM, ("available", "available_quantity", "Disponible", "number"),
                        ("minimum", "minimum_stock", "Stock mínimo", "number")],
                       lambda rows: {"items": len(rows)}),
    "movements": ("Movimientos de inventario", "No hay movimientos de inventario en el período seleccionado",
                  [*_ITEM, ("movement_type", "movement_type", "Tipo de movimiento", "text"),
                   ("quantity", "quantity", "Cantidad", "number"),
                   ("movements", "movements_count", "Movimientos", "number")],
                  # units = every unit moved (entries + exits + transfers): the UI labels it "Unidades movidas"
                  lambda rows: {"items": len(rows), "units": sum(r["quantity"] for r in rows)}),
}
MOVEMENT_LABELS = {
    "income": "Entrada", "outcome": "Salida", "transfer_in": "Transferencia recibida",
    "transfer_out": "Transferencia enviada", "rma_restock": "Reingreso por devolución",
    "exchange_dispatch": "Despacho por cambio", "scrap_quarantine": "Merma / cuarentena",
}


def _stock_rows(db, tenant_id, query, report, from_date=None, to_date=None):
    """Legacy report rows honoring every id in the spec. The legacy reports take one branch/product id:
    a single id is pushed down to SQL; several ids run one company-wide query that is filtered here."""
    from app.services.report_service import get_critical_inventory_report, get_inventory_report, get_movements_report

    products = set(query.product_ids)
    if query.category_ids:
        in_categories = {id_ for (id_,) in db.query(Product.id).filter(
            Product.tenant_id == tenant_id, Product.category_id.in_(query.category_ids))}
        products = products & in_categories if products else in_categories
        if not products:
            return []
    branches = set(query.branch_ids)
    one = lambda ids: next(iter(ids)) if len(ids) == 1 else None  # noqa: E731
    function = {"inventory": get_inventory_report, "critical_stock": get_critical_inventory_report,
                "movements": get_movements_report}[report]
    filters = ReportQuery(branch_id=one(branches), product_id=one(products), from_date=from_date, to_date=to_date)
    return [row for row in function(db, filters, tenant_id)["rows"]
            if (not branches or row["branch_id"] in branches) and (not products or row["product_id"] in products)]


# [CU08 - Secuencia: Pasos 1.8, 2.4] report_routes invoca _stock_query(tenant_id, query, today) sobre la entidad Inventario
# [CU08 - Secuencia: Pasos 1.9, 2.5] Inventario retorna _stock_query(tenant_id, query, today): AnalyticsResult a report_routes
def _stock_query(db, tenant_id, query, today) -> AnalyticsResult:
    title, empty, columns, totals = KINDS[query.kind]
    if query.kind == "movements":
        from_date, to_date = resolve_period(query.period, today)
        label = f"{from_date:%d/%m/%Y} al {to_date:%d/%m/%Y}"
        rows = _stock_rows(db, tenant_id, query, query.kind, from_date, to_date)
    else:  # a stock snapshot: the period does not apply
        from_date = to_date = today
        label = f"Existencias actuales al {today:%d/%m/%Y}"
        rows = _stock_rows(db, tenant_id, query, query.kind)

    def display(field, value):
        if field == "movement_type":
            return MOVEMENT_LABELS.get(getattr(value, "value", value), str(value))
        return value

    return AnalyticsResult(
        title=title,
        period={"from_date": from_date, "to_date": to_date, "label": label},
        columns=[{"key": key, "label": text, "type": kind} for key, _, text, kind in columns],
        rows=[{key: display(field, row[field]) for key, field, _, _ in columns} for row in rows],
        totals=totals(rows),
        chart="table",
        message=None if rows else empty,
    )
