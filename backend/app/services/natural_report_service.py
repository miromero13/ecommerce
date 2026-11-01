"""CU08: reportes en español: intérprete local de reglas y, opcionalmente, respaldo con Groq."""
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.branch import Branch
from app.models.category import Category
from app.models.product import Product
from app.schemas.analytics_schema import AnalyticsQuery
from app.services.analytics_service import _title, resolve_period
from app.services.report_llm_fallback import interpret_with_groq
from app.services.report_interpreter import Catalog, interpret_locally_detailed, normalize

NOT_UNDERSTOOD = (
    "No entendí la consulta. Prueba con: «top 10 productos más vendidos de los últimos 3 meses por sucursal», "
    "«ingresos por mes este año», «ventas online vs tienda de esta semana»."
)


class NaturalReportError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


# [CU08 - Secuencia: Paso 1.2] report_routes invoca _catalog(tenant_id) sobre la entidad Sucursal
# [CU08 - Secuencia: Paso 1.3] Sucursal retorna _catalog(tenant_id): Catalog a report_routes
def _catalog(db: Session, tenant_id: UUID) -> Catalog:
    def names(rows) -> dict:
        found = {}
        for id_, name in rows:
            if key := normalize(name):  # "" (solo puntuación) coincidiría en cualquier frase
                found.setdefault(key, id_)  # nombre normalizado repetido: se queda el primero
        return found

    return Catalog(
        branches=names(db.query(Branch.id, Branch.name)
                       .filter(Branch.is_active.is_(True), Branch.tenant_id == tenant_id).order_by(Branch.name)),
        products=names(db.query(Product.id, Product.name)
                       .filter(Product.tenant_id == tenant_id).order_by(Product.name)),
        categories=names(db.query(Category.id, Category.name)
                         .filter(Category.tenant_id == tenant_id).order_by(Category.name)),
    )


def _validate_filters(db: Session, tenant_id: UUID, spec: AnalyticsQuery, today: date) -> None:
    """Todo id del filtro debe pertenecer a la empresa; el período debe ser resoluble."""
    for model, ids, label in ((Branch, spec.branch_ids, "sucursal"), (Product, spec.product_ids, "producto"),
                              (Category, spec.category_ids, "categoría")):
        if not ids:
            continue
        found = {id_ for (id_,) in db.query(model.id).filter(model.id.in_(ids), model.tenant_id == tenant_id)}
        missing = next((id_ for id_ in ids if id_ not in found), None)
        if missing:
            raise NaturalReportError(422, f"No se encontró en el catálogo: {label} {missing}")
    try:
        from_date, to_date = resolve_period(spec.period, today)
    except ValueError as exc:
        raise NaturalReportError(422, str(exc)) from exc
    # Sin esto, fechas cercanas al año 1 dan OverflowError (500) al calcular el período anterior.
    # El período anterior (compare_previous) dura lo mismo y termina el día antes de from_date; se rechaza
    # (no se omite) si empieza antes de 2000, para que la comparación pedida nunca desaparezca en silencio.
    if from_date.year < 2000 or (
        spec.compare_previous and (from_date - (to_date - from_date) - timedelta(days=1)).year < 2000
    ):
        raise NaturalReportError(422, "Las fechas están fuera de un rango razonable")


def describe_query(spec: AnalyticsQuery, today: date) -> str:
    if spec.kind in ("inventory", "critical_stock"):  # foto del stock: el período no aplica
        return f"{_title(spec)}, existencias actuales"
    from_date, to_date = resolve_period(spec.period, today)
    return f"{_title(spec)}, del {from_date:%d/%m/%Y} al {to_date:%d/%m/%Y}"


def interpret_query(db: Session, tenant_id: UUID, text: str,
                    today: date) -> tuple[AnalyticsQuery, str, str, list[str]]:
    """(spec, interpretación, quién interpretó, avisos). Si el intérprete local no entendió o dejó palabras de
    contenido sin aplicar, se prueba Groq (con su cupo); si Groq no está o falla, se usa lo local y se avisa."""
    catalog = _catalog(db, tenant_id)
    spec, ignored = interpret_locally_detailed(text, catalog, today)
    interpreted_by = "local"
    if (spec is None or ignored) and settings.groq_api_key:  # respaldo: solo traduce, el catálogo no lleva datos
        groq_spec = interpret_with_groq(text, catalog, tenant_id, today)
        if groq_spec is not None:
            spec, interpreted_by, ignored = groq_spec, "groq", []
    if spec is None:
        raise NaturalReportError(422, NOT_UNDERSTOOD)
    _validate_filters(db, tenant_id, spec, today)  # también para lo que devuelve Groq (ids ajenos -> 422)
    warnings = [f"No apliqué estas palabras: {', '.join(f'«{w}»' for w in ignored)}."] if ignored else []
    return spec, describe_query(spec, today), interpreted_by, warnings
