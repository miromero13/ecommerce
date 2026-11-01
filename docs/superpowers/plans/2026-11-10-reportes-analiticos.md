# Reportes analíticos y dashboard profesional (CU08 / CU13) — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que el administrador pida por texto o por voz cualquier consulta analítica (p. ej. *"los 10 productos más vendidos de los últimos 3 meses agrupados por sucursal"*) y obtenga un reporte correcto, con gráfico y exportación PDF/Excel profesional, y un dashboard con métricas comparativas. **El área de reportes deja de usar Gemini**: texto y voz se interpretan con un intérprete local en español (sin API externa, sin tokens, sin cuotas). Gemini sigue solo en el chatbot y en la lectura de documentos (RPA).

**Architecture:** Se sigue la secuencia CU08 ya modelada: (1.1) la interfaz envía la frase → (1.2) control de plan → (1.4) catálogo de la empresa → **intérprete local en español** (reglas + catálogo de la empresa; sin IA) → (1.6) validación → (1.8) devuelve una **especificación de consulta** (`AnalyticsQuery`) ; (1.9) la interfaz ejecuta esa especificación en un **motor analítico** con consultas SQLAlchemy fijas sobre una vista unificada de ventas (tienda + online) → (1.10) filas, totales y gráfico. Exportar (2.x) re-ejecuta la misma especificación sin IA. La voz se transcribe en el navegador (Web Speech API) y el texto resultante sigue el mismo camino que lo escrito.

**Tech Stack:** FastAPI + SQLAlchemy 2 + PostgreSQL (window functions), Pydantic v2, reportlab + openpyxl (exportes), Angular 21 standalone + signals + angular-chrts (gráficos), Web Speech API.

**Spec:** Pedido del usuario en la sesión del 2026-11-10 + `docs/SECOND_PARTIAL_USE_CASES.md` (CU08 líneas ~900-1012, CU13 ~1279) + secuencia CU08/CU13 en `docs/ea/secuencia/secuencia.json`.

## Global Constraints

- Código en inglés; todo texto visible en español. Respuestas `{statusCode, message, data}`; errores con `HTTPException(detail=...)` → `{statusCode, message, error}`.
- **Reportes sin IA externa:** `natural_report_service` ya no importa `google.genai`. Ninguna consulta (texto o voz) llama a Gemini ni a otra API. Si el intérprete no entiende → 422 con ejemplos; nunca 500, 502, 503 ni 504.
- La consulta nunca se convierte en SQL libre: el intérprete solo produce una `AnalyticsQuery` con valores de listas blancas.
- La voz usa solo Web Speech API (`lang = 'es-BO'`, alternativa `'es-ES'`); si el navegador no la soporta, el botón de micrófono no se muestra.
- Aislamiento: toda consulta filtra `tenant_id` del JWT; un **encargado** siempre queda forzado a su sucursal (`branch_ids = [su sucursal]`), aunque la especificación diga otra cosa.
- Ventas que cuentan: tienda `Sale.status = completed` y `payment_status = paid`; online `Order.status = paid` (fecha `Order.created_at`). Moneda en Bs.
- Sin dependencias nuevas (pip ni npm).
- Comentarios de trazabilidad con el formato existente: `# [CU8 - Secuencia: Paso 1.9] ...` / `// [CU8 - Secuencia: Paso 1] ...`.
- Commits sin `Co-Authored-By`.
- Tests backend: `CU1_TEST_DATABASE_URL=postgresql://postgres:cu1-disposable-only@127.0.0.1:53419/cu1_test PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -B -m pytest -p no:cacheprovider <archivo>` desde `backend/`.

## Review Focus

1. **Frases en español "reales"**: sin tildes, números en palabras (*"diez"*, *"tres meses"*), mayúsculas, "más vendido/menos vendido" → el intérprete local debe resolverlas igual. Test: `test_local_interpreter_phrases` (Task 3) incluye esas variantes.
2. **Período sin ventas** → reporte vacío con mensaje *"No hay ventas en el período seleccionado"*, nunca error. Test: `test_empty_period_returns_empty_rows` (Task 2).
3. **Empates en el top-N** → orden determinista (métrica desc, luego nombre asc). Test: `test_top_n_ties_are_deterministic` (Task 2).
4. **Encargado pidiendo otra sucursal** en la especificación → se fuerza la suya. Test: `test_manager_is_forced_to_own_branch` (Task 4).
5. **Consulta que el intérprete no entiende** (texto o voz) → 422 con ejemplos y **sin** llamar a ninguna API. Test: `test_unknown_query_returns_examples_without_ai` (Task 4).

---

## Estructura de archivos

| Archivo | Responsabilidad |
|---|---|
| `backend/app/schemas/analytics_schema.py` (nuevo) | `AnalyticsQuery`, `PeriodSpec`, `AnalyticsResult`; listas blancas |
| `backend/app/services/analytics_service.py` (nuevo) | Vista unificada de ventas, motor de métricas × dimensiones, top-N por grupo, comparación con período anterior, `resolve_period` |
| `backend/app/services/report_interpreter.py` (nuevo) | Intérprete local en español (reglas) |
| `backend/app/services/natural_report_service.py` (modificar) | Interpretar con el intérprete local y validar contra el catálogo; se elimina el uso de Gemini |
| `backend/app/services/report_export_service.py` (modificar) | PDF/Excel profesional desde `AnalyticsResult` |
| `backend/app/routes/report_routes.py` (modificar) | `POST /reports/query`, `POST /reports/analytics`, `POST /reports/analytics/export` |
| `backend/app/services/dashboard_service.py` + `schemas/dashboard_schema.py` (modificar) | Comparación, canales, categorías, stock crítico |
| `frontend/src/app/features/shared/components/voice-input-button.component.ts` (nuevo) | Micrófono reutilizable |
| `frontend/src/app/features/admin/pages/admin-reports-page.component.*` (modificar) | Consulta + interpretación editable + gráfico + tabla + exportar |
| `frontend/src/app/features/admin/pages/admin-home-page.component.*` (modificar) | KPIs con variación, nuevos gráficos, "Pregunta rápida" |
| `frontend/src/app/features/shared/services/reports-api.service.ts`, `models/report.model.ts` (modificar) | Cliente API y tipos |

---

### Task 1: Especificación de consulta y resolución de período

**Files:**
- Create: `backend/app/schemas/analytics_schema.py`
- Create: `backend/app/services/analytics_service.py` (solo `resolve_period` en esta tarea)
- Test: `backend/tests/test_analytics_query.py`

**Interfaces:**
- Produces:
  - `Metric = Literal["units", "revenue", "orders", "avg_ticket"]`
  - `Dimension = Literal["product", "variant", "category", "branch", "size", "color", "channel", "payment_method", "day", "week", "month"]`
  - `PeriodSpec(BaseModel)`: `preset: Literal["today","yesterday","this_week","last_n_days","this_month","last_month","last_n_months","this_year","custom"] = "last_n_days"`, `n: int | None = Field(None, ge=1, le=36)`, `from_date: date | None`, `to_date: date | None`
  - `AnalyticsQuery(BaseModel)`: `metric: Metric = "units"`, `group_by: list[Dimension] = Field(default_factory=lambda: ["product"], max_length=2)`, `top_n: int | None = Field(None, ge=1, le=50)`, `order: Literal["desc","asc"] = "desc"`, `period: PeriodSpec`, `branch_ids: list[UUID] = []`, `product_ids: list[UUID] = []`, `category_ids: list[UUID] = []`, `channel: Literal["all","store","online"] = "all"`, `compare_previous: bool = False`, `chart: Literal["bar","line","donut","table"] | None = None`. Validador: dimensiones sin repetir; si hay 2 dimensiones de tiempo → error *"Solo se puede agrupar por un período de tiempo"*.
  - `resolve_period(period: PeriodSpec, today: date) -> tuple[date, date]` (inclusivo).
  - `AnalyticsResult(BaseModel)`: `title: str`, `period: dict` (`from_date`, `to_date`, `label`), `columns: list[dict]` (`key`, `label`, `type: "text"|"number"|"money"`), `rows: list[dict]`, `totals: dict`, `previous_totals: dict | None`, `delta_pct: dict | None`, `chart: str`, `message: str | None`.

- [ ] **Step 1: Write the failing tests**

```python
def test_resolve_period_presets():
    today = date(2026, 11, 10)
    assert resolve_period(PeriodSpec(preset="last_n_months", n=3), today) == (date(2026, 8, 11), date(2026, 11, 10))
    assert resolve_period(PeriodSpec(preset="last_month"), today) == (date(2026, 10, 1), date(2026, 10, 31))
    assert resolve_period(PeriodSpec(preset="this_week"), today) == (date(2026, 11, 9), date(2026, 11, 10))  # lunes
    assert resolve_period(PeriodSpec(preset="last_n_days", n=7), today) == (date(2026, 11, 4), date(2026, 11, 10))

def test_custom_period_validates_order():
    with pytest.raises(ValueError, match="La fecha inicial no puede ser posterior a la final"):
        resolve_period(PeriodSpec(preset="custom", from_date=date(2026, 5, 2), to_date=date(2026, 5, 1)), date(2026, 11, 10))

def test_query_rejects_two_time_dimensions_and_unknown_metric():
    with pytest.raises(ValidationError):
        AnalyticsQuery(group_by=["month", "day"], period=PeriodSpec())
    with pytest.raises(ValidationError):
        AnalyticsQuery(metric="profit", period=PeriodSpec())
```

- [ ] **Step 2:** Run `pytest tests/test_analytics_query.py -v` → FAIL (módulo no existe).
- [ ] **Step 3:** Implementar el esquema y `resolve_period`. `last_n_months` = mismo día n meses atrás + 1 día (usar `calendar.monthrange` para fin de mes); `custom` sin fechas → `ValueError("Indica las fechas del período")`; fechas futuras se recortan a `today`.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(reports): analytics query spec and period resolution (CU08)`.

---

### Task 2: Motor analítico sobre ventas de tienda + online

**Files:**
- Modify: `backend/app/services/analytics_service.py`
- Test: `backend/tests/test_analytics_engine.py` (fixtures: reutilizar `catalog`/`market` de `test_marketplace_transactions.py`; crear ventas con fechas controladas)

**Interfaces:**
- Consumes: Task 1 (`AnalyticsQuery`, `resolve_period`, `AnalyticsResult`).
- Produces: `run_query(db: Session, tenant_id: UUID, query: AnalyticsQuery, today: date) -> AnalyticsResult`.

Decisiones que el implementador no puede deducir:
- **Vista unificada** `_sales_fact(db, tenant_id)` = `UNION ALL` (subquery) con columnas `occurred_at, branch_id, product_id, variant_id, category_id, size_id, color_id, channel ('store'|'online'), payment_method, quantity, line_total, ticket_id`. Tienda: `Sale ⋈ SaleItem ⋈ Product`; online: `Order ⋈ OrderItem ⋈ Product` con `Order.pickup_branch_id` como sucursal.
- **Métricas:** `units = SUM(quantity)`, `revenue = SUM(line_total)`, `orders = COUNT(DISTINCT ticket_id)`, `avg_ticket = revenue / NULLIF(orders, 0)`.
- **Etiquetas de dimensiones:** nombres (sucursal, producto, categoría, talla, color); canal `store→"Tienda"`, `online→"En línea"`; tiempo `day→YYYY-MM-DD`, `week→"Semana del YYYY-MM-DD"`, `month→"YYYY-MM"` (`date_trunc` en hora `America/La_Paz`).
- **Top-N:** con 1 dimensión → `LIMIT top_n`; con 2 dimensiones → top-N de la 2.ª dentro de cada valor de la 1.ª con `row_number() OVER (PARTITION BY dim1 ORDER BY métrica DESC, nombre ASC) <= top_n`.
- **Orden de filas:** dim1 por nombre (o fecha), luego métrica según `order`, desempate por nombre.
- **Comparación:** si `compare_previous`, mismo largo de período inmediatamente anterior → `previous_totals` y `delta_pct` (redondeo a 1 decimal; `None` si el anterior es 0).
- **Gráfico por defecto:** tiempo → `line`; 1 dimensión ≤ 6 filas y canal/método de pago → `donut`; 1 dimensión → `bar`; 2 dimensiones → `bar` agrupado.
- **Título:** se arma en español desde la especificación (p. ej. *"Top 10 productos por unidades vendidas, agrupado por sucursal"*).

- [ ] **Step 1: Write the failing tests**

```python
def test_engineer_query_top_10_per_branch_last_3_months(...):
    # 2 sucursales, 12 productos vendidos en cada una dentro del período, 1 venta fuera del período
    q = AnalyticsQuery(metric="units", group_by=["branch", "product"], top_n=10,
                       period=PeriodSpec(preset="last_n_months", n=3))
    result = run_query(db, tenant.id, q, today)
    by_branch = groupby(result.rows, key=itemgetter("branch"))
    assert all(len(list(rows)) == 10 for _, rows in by_branch)
    assert [c["key"] for c in result.columns] == ["branch", "product", "units"]
    assert result.rows[0]["units"] >= result.rows[1]["units"]           # dentro de la sucursal
    assert the_out_of_period_sale_product not in {r["product"] for r in result.rows}

def test_online_and_store_sales_are_both_counted(...):
    # 2 u. en caja + 1 u. pedido online pagado, misma prenda y sucursal
    assert run_query(..., AnalyticsQuery(group_by=["channel"], ...)).rows == [
        {"channel": "En línea", "units": 1}, {"channel": "Tienda", "units": 2}]

def test_revenue_orders_and_avg_ticket(...):  # 2 tickets de 50 y 150 Bs.
    assert result.totals == {"revenue": Decimal("200.00"), "orders": 2, "avg_ticket": Decimal("100.00"), "units": ...}

def test_compare_previous_period_delta(...):  # 100 Bs. período anterior, 150 actual
    assert result.delta_pct["revenue"] == 50.0

def test_empty_period_returns_empty_rows(...):
    assert result.rows == [] and result.message == "No hay ventas en el período seleccionado"

def test_top_n_ties_are_deterministic(...):  # 3 productos con 5 u. cada uno, top_n=2
    assert [r["product"] for r in result.rows] == ["Blusa A", "Blusa B"]

def test_other_company_sales_never_appear(...):
    assert foreign_product_name not in {r["product"] for r in result.rows}

def test_cancelled_and_unpaid_sales_are_excluded(...): ...
```

- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implementar `_sales_fact` y `run_query` según las decisiones de arriba.
- [ ] **Step 4:** Run → PASS. Correr también `tests/test_reporting_tenant_isolation.py` (no debe romperse).
- [ ] **Step 5:** Commit `feat(reports): analytics engine over store and online sales (CU08)`.

---

### Task 3: Intérprete local en español (sin IA, para texto y voz)

**Files:**
- Create: `backend/app/services/report_interpreter.py`
- Test: `backend/tests/test_report_interpreter.py`

**Interfaces:**
- Consumes: Task 1 (`AnalyticsQuery`, `PeriodSpec`).
- Produces: `interpret_locally(text: str, catalog: Catalog) -> AnalyticsQuery | None` donde `Catalog = dataclass(branches: dict[str, UUID], products: dict[str, UUID], categories: dict[str, UUID])` con claves **normalizadas** (minúsculas, sin tildes). `None` = no entendió con confianza.

Reglas (normalizar primero: minúsculas, quitar tildes, números en palabras uno..cincuenta → dígitos):
- Métrica: `vendid|unidades|cantidad` → units; `ingres|monto|factur|cuanto se vendio|recaud` → revenue; `pedidos|tickets|transacciones|cuantas ventas` → orders; `ticket promedio|promedio por venta` → avg_ticket.
- Top: `top (\d+)` | `(\d+) (productos|prendas)? mas vendid` → `top_n`, `group_by` incluye product; `menos vendid` → `order="asc"`.
- Agrupar: `por (sucursal|tienda)`→branch, `por producto|prenda`→product, `por categoria`→category, `por talla`→size, `por color`→color, `por canal|online vs tienda`→channel, `por metodo de pago`→payment_method, `por dia|diario`→day, `por semana|semanal`→week, `por mes|mensual`→month. Con top + "por sucursal": `group_by = ["branch", "product"]`.
- Período: `hoy`, `ayer`, `esta semana`, `este mes`, `mes pasado`, `este ano`, `ultim(o|os) (\d+) (dia|dias|mes|meses)`, `ultimo trimestre` = 3 meses, `del dd/mm/aaaa al dd/mm/aaaa`. Sin período → últimos 30 días.
- Filtros: nombres del catálogo contenidos en la frase (el más largo gana); `online|en linea|web` → channel online; `en tienda|presencial|caja` → store.
- `compara|vs|comparado con` → `compare_previous=True`.
- Devuelve `None` si no encontró **ni métrica, ni top, ni agrupación**.

- [ ] **Step 1: Write the failing test (tabla de frases)**

```python
@pytest.mark.parametrize("text, expected", [
    ("Mostrar los 10 productos más vendidos durante los últimos 3 meses agrupados por sucursal",
     dict(metric="units", group_by=["branch", "product"], top_n=10, period=("last_n_months", 3))),
    ("top diez productos mas vendidos ultimos tres meses por sucursal",  # sin tildes, números en palabras
     dict(metric="units", group_by=["branch", "product"], top_n=10, period=("last_n_months", 3))),
    ("ingresos por mes este año", dict(metric="revenue", group_by=["month"], period=("this_year", None))),
    ("ticket promedio por sucursal el mes pasado comparado con el anterior",
     dict(metric="avg_ticket", group_by=["branch"], period=("last_month", None), compare_previous=True)),
    ("ventas online vs tienda de esta semana", dict(group_by=["channel"], period=("this_week", None))),
    ("los 5 productos menos vendidos en Ayni Zona Sur", dict(top_n=5, order="asc", branch_ids=[ZONA_SUR])),
    ("ventas por talla de la categoria Blusas", dict(group_by=["size"], category_ids=[BLUSAS])),
])
def test_local_interpreter_phrases(text, expected): ...

def test_unknown_phrase_returns_none():
    assert interpret_locally("haz un poema sobre ropa", catalog) is None
```

- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implementar con `re` y `unicodedata` (stdlib). Sin IA.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(reports): local Spanish interpreter, no AI tokens (CU08)`.

---

### Task 4: Interpretación local y rutas según la secuencia CU08 (sin Gemini)

**Files:**
- Modify: `backend/app/services/natural_report_service.py`, `backend/app/routes/report_routes.py`
- Test: `backend/tests/test_analytics_routes.py`

**Interfaces:**
- Consumes: Tasks 1–3.
- Produces:
  - `interpret_query(db, tenant_id, text, today) -> tuple[AnalyticsQuery, str]` → `(spec, interpretation_es)`; la interpretación es una frase en español generada desde la especificación (p. ej. *"Top 10 productos por unidades vendidas en cada sucursal, del 11/08/2026 al 10/11/2026"*).
  - **Paso 1.1** `POST /api/reports/query` body `{query: str(1..500)}` → 200 *"Reporte interpretado exitosamente"* `data = {spec, interpretation}` (ya **no** ejecuta el reporte).
  - **Paso 1.9** `POST /api/reports/analytics` body `AnalyticsQuery` → 200 *"Reporte generado exitosamente"* `data = AnalyticsResult`.
  - Ambos: `require_permission("reports:read")`; `/query` además exige el plan `ai_text_reports` (como hoy). Encargado: `branch_ids` forzado a su sucursal en ambos.

No entendida → `NaturalReportError(422, "No entendí la consulta. Prueba con: «top 10 productos más vendidos de los últimos 3 meses por sucursal», «ingresos por mes este año», «ventas online vs tienda de esta semana».")`. Quitar `_prompt`, `_interpret_sync` y la dependencia de `settings.gemini_*` en este servicio; los tests que hoy hacen monkeypatch de `_interpret_sync` (`test_reporting_tenant_isolation.py`) se reescriben contra el intérprete local.

- [ ] **Step 1: Write the failing tests**

```python
def test_engineer_phrase_is_resolved_without_ai(api):
    data = call(api, admin, "POST", "/reports/query", json={"query": ENGINEER_PHRASE})
    assert data["spec"]["group_by"] == ["branch", "product"] and data["spec"]["top_n"] == 10
    assert data["spec"]["period"] == {"preset": "last_n_months", "n": 3, "from_date": None, "to_date": None}

def test_unknown_query_returns_examples_without_ai(api):
    body = call(api, admin, "POST", "/reports/query", 422, json={"query": "haz un poema"})
    # el mensaje incluye los ejemplos

def test_reports_never_import_gemini():
    import app.services.natural_report_service as service
    assert "genai" not in open(service.__file__, encoding="utf-8").read()

def test_analytics_route_runs_the_spec(api): ...  # filas reales, 200 "Reporte generado exitosamente"

def test_manager_is_forced_to_own_branch(api):
    data = call(api, manager, "POST", "/reports/analytics", json={..., "branch_ids": [str(other_branch.id)]})
    assert {r["branch"] for r in data["rows"]} <= {manager_branch_name}

```

- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implementar `interpret_query` + rutas, con comentarios `# [CU8 - Secuencia: Paso 1.x]` alineados a la secuencia (1.2 `tenant_features`, 1.4 `_catalog` ahora con categorías, 1.6 `_validate_filters`, 1.8 retorno, 1.9/1.10 nueva ruta analytics).
- [ ] **Step 4:** Run → PASS; correr `tests/test_natural_report_contract.py` y `tests/test_reporting_tenant_isolation.py` y ajustar los que esperaban que `/query` devolviera el reporte (ahora devuelve la especificación).
- [ ] **Step 5:** Commit `feat(reports): local Spanish interpreter replaces Gemini in reports (CU08)`.

---

### Task 5: Exportación profesional PDF / Excel

**Files:**
- Modify: `backend/app/services/report_export_service.py`, `backend/app/routes/report_routes.py`
- Test: `backend/tests/test_analytics_export.py`

**Interfaces:**
- Consumes: Task 2 (`AnalyticsResult`), Task 4 (rutas).
- Produces: `analytics_to_pdf(result: AnalyticsResult, company: str, generated_by: str) -> bytes`, `analytics_to_excel(result, company, generated_by) -> bytes`; **Paso 2.1/2.3** `POST /api/reports/analytics/export?format=pdf|excel` body `AnalyticsQuery` → archivo `reporte-<slug-título>-<fecha>.pdf|xlsx`.

Formato fijo:
- **PDF (reportlab, A4 horizontal):** encabezado con nombre de la empresa y título; línea de período y filtros en español; fecha/hora de generación y usuario; tarjetas de totales (y variación % si hay comparación); gráfico de barras/líneas con `reportlab.graphics` cuando hay ≤ 20 filas y 1 dimensión; tabla con encabezado repetido por página, montos `#,##0.00 Bs.`, filas alternas sombreadas; con 2 dimensiones, una sección por valor de la 1.ª con subtotal; pie *"Página X de Y"*.
- **Excel (openpyxl):** filas 1-4 título/empresa/período/filtros; tabla desde la fila 6 con encabezado congelado y autofiltro; formatos numéricos `#,##0.00` y `#,##0`; subtotales por grupo en negrita; anchos de columna ajustados; texto siempre `data_type='s'` (anti-fórmulas, como hoy).

- [ ] **Step 1: Write the failing tests**

```python
def test_pdf_has_title_period_and_pages(): assert pdf.startswith(b"%PDF-") and b"Top 10" in text_of(pdf) and "Página 1 de" in text_of(pdf)
def test_excel_has_header_block_subtotals_and_number_formats(): ...  # ws["A1"] == título, fila de subtotal en negrita, number_format "#,##0.00"
def test_excel_never_executes_formulas(): ...  # producto llamado "=HYPERLINK(...)" queda como texto
def test_export_route_returns_file_with_name(api): ...  # Content-Disposition con reporte-...xlsx
```

- [ ] **Step 2:** Run → FAIL. **Step 3:** Implementar. **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(reports): professional PDF and Excel exports (CU08)`.

---

### Task 6: Dashboard con métricas comparativas (CU13, backend)

**Files:**
- Modify: `backend/app/schemas/dashboard_schema.py`, `backend/app/services/dashboard_service.py`
- Test: `backend/tests/test_dashboard_metrics.py`

**Interfaces:**
- Consumes: Task 2 (`run_query` para canales y categorías).
- Produces (nuevos campos de `DashboardResponse`, sin quitar los existentes):
  - `comparison: {sales_delta_pct, orders_delta_pct, units_delta_pct, avg_ticket_delta_pct: float | None}` (vs. período anterior de igual largo)
  - `channel_split: list[{channel_label, sales, orders}]`
  - `top_categories: list[{category_name, units, sales}]` (máx. 5)
  - `low_stock: list[{product_name, sku, branch_name, available, minimum}]` (máx. 10, `available <= minimum_stock`, ordenado por `available` asc)

- [ ] **Step 1:** Tests: `test_dashboard_comparison_deltas`, `test_dashboard_channel_split_includes_online`, `test_dashboard_low_stock_list_is_tenant_scoped`.
- [ ] **Step 2:** FAIL → **Step 3:** implementar (paso `1.2/2.2 get_dashboard` de la secuencia CU13) → **Step 4:** PASS.
- [ ] **Step 5:** Commit `feat(dashboard): comparison, channels, categories and low stock (CU13)`.

---

### Task 7: Frontend — micrófono reutilizable y página de reportes

**Files:**
- Create: `frontend/src/app/features/shared/components/voice-input-button.component.ts`
- Modify: `frontend/src/app/features/admin/pages/admin-reports-page.component.ts|html`, `frontend/src/app/features/shared/services/reports-api.service.ts`, `frontend/src/app/features/shared/models/report.model.ts`

**Interfaces:**
- Consumes: Task 4/5 rutas.
- Produces: `<app-voice-input-button (transcript)="..." />` (emite `string`; muestra estado "Escuchando…"; oculto si no hay `SpeechRecognition`); `ReportsApiService.interpret(query)`, `.runAnalytics(spec)`, `.exportAnalytics(spec, format)`; tipos `AnalyticsQuery`, `AnalyticsResult`.

Pantalla (en este orden, secuencia CU08 pasos 1 → 1.10 → 2):
1. Caja de consulta + micrófono + botón "Consultar"; debajo, 6 ejemplos clicables (incluida la consulta de la ingeniera).
2. Al interpretar: **chips editables** (Métrica, Agrupar por, Top, Período, Sucursal/Categoría/Canal, Comparar) y la frase de interpretación. Cambiar un chip re-ejecuta `runAnalytics` **sin** volver a interpretar (cero tokens).
3. Resultado: título, período, tarjetas de totales con variación ▲/▼, gráfico (`ngx-bar-chart` / `ngx-line-chart` / `ngx-donut-chart` según `result.chart`), tabla (con 2 dimensiones: secciones por grupo con subtotal).
4. Botones "Exportar PDF" / "Exportar Excel".
5. Estados: cargando, vacío (`result.message`), error 422 con los ejemplos sugeridos.
- Admite `?q=...` en la URL: si viene, se interpreta y ejecuta al entrar (lo usa el dashboard).

- [ ] **Step 1:** Implementar el componente de voz extrayendo la lógica actual de `admin-reports-page.component.ts` (líneas ~20-35 y ~228-241) con `lang = 'es-BO'`.
- [ ] **Step 2:** Implementar API, tipos y la página.
- [ ] **Step 3:** `npx ng build` en `frontend/` → *"Application bundle generation complete"* sin errores.
- [ ] **Step 4:** Prueba manual: decir la consulta de la ingeniera por voz → chips correctos → tabla con 10 filas por sucursal → PDF y Excel descargan.
- [ ] **Step 5:** Commit `feat(reports-ui): voice query, editable interpretation, charts and exports (CU08)`.

---

### Task 8: Frontend — dashboard profesional con "Pregunta rápida"

**Files:**
- Modify: `frontend/src/app/features/admin/pages/admin-home-page.component.ts|html`, modelo del dashboard

**Interfaces:**
- Consumes: Task 6 (campos nuevos), Task 7 (`voice-input-button`, ruta de reportes con `?q=`).

Contenido: tarjetas KPI (Ventas, Pedidos, Unidades, Ticket promedio) con ▲/▼ y % vs. período anterior en verde/rojo; gráfico de tendencia (existente); dona Tienda vs En línea; barras Top 5 categorías; tabla "Stock crítico" con enlace a inventario; campo **"Pregunta rápida"** con micrófono que navega a `/app/admin/reports?q=<frase>`.

- [ ] **Step 1:** Implementar. **Step 2:** `npx ng build` sin errores. **Step 3:** prueba manual con filtros de sucursal y período (pasos 2–2.4 de la secuencia CU13).
- [ ] **Step 4:** Commit `feat(dashboard-ui): KPI deltas, channel and category charts, quick voice question (CU13)`.

---

### Task 9: Documentación y trazabilidad

**Files:**
- Modify: `docs/SECOND_PARTIAL_USE_CASES.md` (CU08 y CU13), comentarios de secuencia en el código nuevo

- [ ] **Step 1:** CU08: describir la secuencia nueva (1.1 interpretar con el intérprete local → 1.8 especificación → 1.9 analytics → 1.10 resultado → 2.x exportar), las métricas y dimensiones permitidas, la tabla de frases de ejemplo y que los reportes ya no dependen de Gemini (sin tokens ni cuotas). CU13: nuevas métricas.
- [ ] **Step 2:** Verificar que cada ruta/servicio nuevo tenga sus comentarios `[CU8 - Secuencia: Paso ...]` / `[CU13 - ...]` y regenerar `docs/ea/secuencia` con `python docs/ea/secuencia/generar_secuencia.py`.
- [ ] **Step 3:** Commit `docs(cu08,cu13): analytic reports and dashboard`.
