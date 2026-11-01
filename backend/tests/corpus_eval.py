"""Evaluación del intérprete contra un corpus de frases con resultado esperado PARCIAL.

Formato de cada entrada: {"id", "phrase", "expected": {...}, "must_return_none": bool, "tags": [...]}.
Solo se comparan las claves presentes en `expected`. El mismo comparador sirve para el corpus dev y el holdout.
"""
from datetime import date, timedelta
from uuid import uuid4

from app.services.report_interpreter import Catalog, interpret_locally, normalize

TODAY = date(2026, 11, 11)
BRANCHES = ["Ayni La Paz Centro", "Ayni Zona Sur", "Ayni El Alto", "Ayni Cochabamba"]
PRODUCTS = ["Blusa Floral", "Jean Clasico", "Vestido Largo", "Chaqueta de Cuero", "Polera Basica", "Falda Plisada"]
CATEGORIES = ["Blusas", "Jeans", "Vestidos", "Chaquetas", "Poleras", "Faldas"]


def build_catalog() -> tuple[Catalog, dict]:
    """Catálogo del corpus (claves normalizadas -> uuid4) y el mapa id -> nombre completo."""
    name_by_id = {}

    def ids(names):
        out = {}
        for name in names:
            out[normalize(name)] = id_ = uuid4()
            name_by_id[id_] = name
        return out

    return Catalog(branches=ids(BRANCHES), products=ids(PRODUCTS), categories=ids(CATEGORIES)), name_by_id


def _period_ok(expected: dict, period, today: date) -> bool:
    if "custom" in expected:
        start, end = (date.fromisoformat(d) for d in expected["custom"])
        return period.preset == "custom" and (period.from_date, period.to_date) == (start, end)
    if period.preset != expected["preset"]:
        # "últimos 90 días" no cabe en n (<= 36): el intérprete lo da como rango explícito equivalente
        n = expected.get("n")
        return (expected["preset"] == "last_n_days" and n and period.preset == "custom"
                and period.to_date == today and period.from_date == today - timedelta(days=n - 1))
    return "n" not in expected or period.n == expected["n"]


def compare(expected: dict, spec, name_by_id: dict, today: date = TODAY) -> str | None:
    """None si `spec` cumple todas las claves de `expected`; si no, el motivo."""
    stock_like = expected.get("kind", "sales") != "sales" or spec.kind != "sales"
    for key, value in expected.items():
        if stock_like and key in ("group_by", "metric", "top_n", "order"):
            continue  # inventario/stock/movimientos: el motor ignora esos campos
        if key == "period":
            ok = _period_ok(value, spec.period, today)
            got = spec.period.model_dump(mode="json", exclude_none=True)
        elif key in ("branches", "products", "categories"):
            ids = getattr(spec, {"branches": "branch_ids", "products": "product_ids", "categories": "category_ids"}[key])
            got = sorted(name_by_id.get(i, str(i)) for i in ids)
            ok = got == sorted(value)
        elif key == "payment_methods":
            got = sorted(spec.payment_methods)
            ok = got == sorted(value)
        else:  # kind, metric, group_by (lista ordenada), top_n, order, channel, compare_previous, chart
            got = getattr(spec, key)
            ok = got == value
        if not ok:
            return f"{key}: esperado {value!r}, obtenido {got!r}"
    # Filtros, tipo, canal, pago y comparación nunca son implícitos: si el corpus no los pide, deben estar en su valor
    # por defecto (un filtro inventado es una respuesta distinta). group_by/metric/top_n/order/period sí pueden
    # quedar sin evaluar porque las convenciones los dejan implícitos.
    for key, default, got in (
            ("branches", [], spec.branch_ids), ("products", [], spec.product_ids),
            ("categories", [], spec.category_ids), ("payment_methods", [], spec.payment_methods),
            ("channel", "all", spec.channel), ("compare_previous", False, spec.compare_previous),
            ("kind", "sales", spec.kind)):
        if key not in expected and got != default:
            shown = [name_by_id.get(i, str(i)) for i in got] if key in ("branches", "products", "categories") else got
            return f"{key}: no pedido, debía quedar {default!r}, obtenido {shown!r}"
    return None


def evaluate(entries: list[dict], today: date = TODAY) -> list[dict]:
    catalog, name_by_id = build_catalog()
    results = []
    for entry in entries:
        spec = interpret_locally(entry["phrase"], catalog, today=today)
        if entry.get("must_return_none"):
            reason = None if spec is None else "debía devolver None"
        else:
            reason = "devolvió None" if spec is None else compare(entry["expected"], spec, name_by_id, today)
        results.append({
            "id": entry["id"], "phrase": entry["phrase"], "ok": reason is None, "expected": entry["expected"],
            "got": None if spec is None else spec.model_dump(mode="json", exclude_defaults=True),
            "tags": entry.get("tags", []), "reason": reason,
            "must_return_none": bool(entry.get("must_return_none")),
        })
    return results


def accuracy_table(results: list[dict]) -> str:
    """Tabla de aciertos por etiqueta (y total)."""
    by_tag: dict[str, list[bool]] = {}
    for r in results:
        for tag in ["TOTAL", *r["tags"]]:
            by_tag.setdefault(tag, []).append(r["ok"])
    lines = [f"{'tag':<22}{'ok':>5}{'n':>5}{'%':>8}"]
    for tag, oks in sorted(by_tag.items(), key=lambda kv: (kv[0] != "TOTAL", kv[0])):
        lines.append(f"{tag:<22}{sum(oks):>5}{len(oks):>5}{100 * sum(oks) / len(oks):>7.1f}%")
    return "\n".join(lines)
