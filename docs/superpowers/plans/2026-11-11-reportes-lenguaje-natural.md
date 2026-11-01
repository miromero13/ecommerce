# Reportes: cobertura de lenguaje natural y de tipos de reporte — Plan

> **For agentic workers:** usar superpowers:subagent-driven-development. Los pasos usan casillas `- [ ]`.

**Goal:** que el administrador pida reportes de muchas formas distintas (escritas o dictadas), incluidas preguntas cotidianas, y que el sistema (1) los entienda, (2) cubra más tipos de reporte (ventas, inventario, stock crítico, movimientos, clientes) y (3) **nunca responda en silencio una pregunta distinta a la que se hizo**: ante la duda devuelve "no entendí" (o pasa al respaldo con Groq).

**Antecedente medido (2026-11-11):** 52 frases sencillas → 36 entendidas, 16 sin respuesta, y varias respondidas mal sin avisar (mes por nombre, "semana pasada", "del 1 al 15 de octubre", "por internet", "tienda física", "qué sucursal vendió más").

**Architecture:** el intérprete local (`backend/app/services/report_interpreter.py`) sigue siendo el primer paso. Se amplía (sinónimos, preguntas, períodos con nombre, canales, métodos de pago, clientes, tipos de reporte) y se mide con un **corpus de frases** dividido en *dev* (el que ve quien programa) y *holdout* (oculto, se evalúa una sola vez al final). Groq (ya integrado) sigue como respaldo y hereda el nuevo esquema.

## Convenciones semánticas (fuente única de verdad para corpus e intérprete)

Fecha de referencia de los ejemplos: **hoy = 2026-11-11 (miércoles)**. Todos los textos pueden venir con o sin tildes, con o sin signos, en minúsculas, con números en cifras o en palabras, sin mayúsculas (así sale del dictado).

**Campos de la especificación (`AnalyticsQuery`, tras la tarea R2):**
`kind` (`sales` | `inventory` | `critical_stock` | `movements`; por defecto `sales`), `metric` (`units` | `revenue` | `orders` | `avg_ticket` | `customers`), `group_by` (hasta 2 de: `product`, `variant`, `category`, `branch`, `size`, `color`, `channel`, `payment_method`, `customer`, `day`, `week`, `month`; máximo una de tiempo), `top_n` (1–50), `order` (`desc`|`asc`), `period`, `branch_ids`, `product_ids`, `category_ids`, `channel` (`all`|`store`|`online`), `payment_methods` (lista de `cash`|`card`|`qr`|`wallet`), `compare_previous`, `chart`.

**Métrica (qué se mide):**
- `units`: "vendidos", "unidades", "cantidad", "prendas", "piezas", "cuántas vendimos".
- `revenue`: "ventas", "ingresos", "facturación/facturamos", "plata", "dinero", "recaudado/recaudamos", "monto", "cuánto vendimos/vendí/se vendió", "total vendido".
- `orders`: "pedidos", "órdenes", "transacciones", "tickets", "cuántas ventas hubo".
- `avg_ticket`: "ticket promedio", "promedio por venta", "compra promedio", "gasto promedio".
- `customers`: "cuántos clientes compraron", "clientes distintos", "cantidad de clientes".
- Rankings ("más vendido", "vende más", "mejor", "peor", "menos vendido", "el que más/menos"): si se agrupa por **producto/variante/talla/color/categoría** la métrica es `units`; si se agrupa por **sucursal/canal/método de pago/cliente/día** la métrica es `revenue`.
- "ganancia", "utilidad", "margen", "costo": **no existen datos** → el intérprete devuelve `None` (no inventa).

**Agrupación:** "por X", "de cada X", "en cada X", "según X", "desglosado/separado/dividido por X", "comparar/comparame X", "entre X" → X. Pregunta singular ("cuál es la sucursal/el producto que…", "la peor sucursal", "el mejor producto") → agrupar por esa dimensión con `top_n=1` y el orden que pida. Plural con número ("los 3 mejores productos", "top 5", "los cinco más vendidos") → `top_n=N`. "los más vendidos" sin número → sin `top_n` (o 10: se acepta cualquiera de los dos; el corpus no lo exige). "diario/por día/cada día" → `day`; "semanal/por semana" → `week`; "mensual/por mes/mes a mes" → `month`. Si la frase no dice cómo agrupar, el corpus **no exige** `group_by` (campo omitido = no se evalúa).

**Período:**
- `today` "hoy"; `yesterday` "ayer", "anoche"; `this_week` "esta semana" (lunes a hoy); `last_week` "la semana pasada/anterior" (lunes a domingo anteriores); `this_month` "este mes", "en lo que va del mes"; `last_month` "el mes pasado/anterior"; `this_quarter` "este trimestre"; `last_quarter` "el trimestre pasado"; `this_year` "este año", "en lo que va del año"; `last_year` "el año pasado"; `last_n_days` con n ("últimos 15 días", "los últimos quince días", "de los últimos 7 días"); `last_n_months` con n ("últimos 3 meses", "último trimestre" = 3).
- **Mes con nombre** ("octubre", "en septiembre", "del mes de agosto"): `custom` del primer al último día del **mes más reciente con ese nombre cuyo primer día sea ≤ hoy**; con año explícito ("octubre de 2025") ese año. Con "del 1 al 15 de octubre" → `custom` 1–15 (mismo criterio de año). "del 3/10 al 20/10", "del 03/10/2026 al 20/10/2026" → `custom`.
- **Un día de la semana** ("el lunes", "el viernes pasado") → `custom` de un solo día: el más reciente (≤ hoy) con ese día.
- **Expresiones ambiguas o no soportadas** ("hace dos semanas", "la quincena pasada", "navidad", "antes del feriado") → **`None`** (no adivinar).
- Si no hay ninguna expresión de tiempo → período por defecto: últimos 30 días.

**Canal y método de pago (filtros):** `online` = "en línea", "por internet", "por la web", "pedidos web", "página", "app"; `store` = "en tienda", "tienda física", "en caja", "presencial", "mostrador". `payment_methods`: `cash` "efectivo/contado", `card` "tarjeta/stripe", `qr` "qr/código qr", `wallet` "billetera". "online vs tienda" / "por canal" → `group_by channel` (no filtro).

**Sucursal / producto / categoría (filtros por nombre del catálogo):** se detectan por nombre completo; el nombre más largo gana; un nombre consumido no se reutiliza. "en la sucursal sur" puede coincidir con "Ayni Zona Sur" cuando la palabra distintiva ("sur") es única entre las sucursales.

**Tipos de reporte (`kind`):**
- `inventory`: "inventario", "existencias", "stock" (sin "crítico/poco/bajo"), "cuánto stock hay de X", "cuántas X quedan".
- `critical_stock`: "stock crítico", "poco stock", "bajo stock", "por agotarse", "se está acabando", "agotados", "sin stock", "qué falta reponer".
- `movements`: "movimientos de inventario", "entradas y salidas", "transferencias", "ingresos de mercadería", "reposiciones". (Ojo: "ingresos" a secas son `revenue`.)
- `sales`: todo lo demás que mida ventas.
- Clientes: "mejores clientes", "clientes que más compran", "quién compra más" → `kind=sales`, `group_by=[customer]`, `metric=revenue`; "cuántos clientes compraron…" → `metric=customers`.

**Regla de oro:** si la frase contiene una expresión de tiempo, canal, método de pago, medida o agrupación **que el intérprete reconoce como tal pero no sabe resolver**, devuelve `None`; nunca ignora una parte reconocida de la frase.

## Global Constraints
- Código en inglés, textos de usuario en español; sin dependencias nuevas; sin commits (el árbol tiene trabajo sin commit del usuario; ledger: `.superpowers/sdd/2026-11-11-reportes-lenguaje/progress.md`).
- Aislamiento por empresa y por encargado como hasta ahora (`_validate_filters`, `_scoped_spec`); los nuevos tipos de reporte respetan esas reglas.
- Respuesta de `/reports/query` y `/reports/analytics` compatibles hacia atrás (campos nuevos opcionales).
- Pruebas backend: `CU1_TEST_DATABASE_URL=postgresql://postgres:cu1-disposable-only@127.0.0.1:53419/cu1_test PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -B -m pytest -p no:cacheprovider <archivos> -q -W ignore` desde `backend/`.

## Review Focus
1. Una frase con parte reconocida pero no resuelta no puede dar un reporte distinto al pedido (la regla de oro). 2. Los nuevos tipos de reporte no filtran datos de otra empresa ni de otra sucursal (encargado). 3. Rankings ("la peor sucursal") con empates y sin ventas. 4. Frases dictadas sin tildes ni signos y con números en palabras. 5. Groq no debe poder devolver un `kind` o ids fuera de lo permitido (validación igual que antes).

## Tareas
- [ ] **R1 Corpus** (independiente del intérprete): ~320 frases con resultado esperado parcial, partidas en `dev` (~220, en el repo) y `holdout` (~100, fuera del repo, oculto para quien programa el intérprete).
- [ ] **R2 Motor/esquema**: `kind`, métrica `customers`, dimensión `customer`, filtro `payment_methods`, presets `last_week`/`this_quarter`/`last_quarter`/`last_year`, adaptadores para `inventory`/`critical_stock`/`movements` (reutilizando los reportes existentes), exportes y Groq heredan el esquema.
- [ ] **R3 Intérprete**: cobertura según las convenciones, regla de oro, `today` inyectable; iterar contra *dev* hasta ≥ 97 %; luego medir *holdout* una sola vez y reportar.
- [ ] **R4 Frontend**: la pantalla de reportes muestra bien los tipos nuevos (sin tarjetas de ventas cuando no aplican), panel "¿Qué puedo preguntar?" con ejemplos por categoría (útil para el dictado), sugerencias clicables cuando no entiende, y "Entendí:" visible.
- [ ] **R5 Groq**: instrucciones del respaldo con los tipos nuevos y ejemplos de pocos disparos; pruebas.

## Aclaraciones de convención (decididas el 2026-11-11, tras las dudas del autor del corpus)
1. **Orden de `group_by` con dos dimensiones.** Si hay un ranking/top sobre una entidad E y además una agrupación "por X / en cada X", el orden es **[X, E]** (X agrupa por fuera; el top se calcula dentro de cada X): "top 5 productos por sucursal" → `["branch","product"]`; "los 5 colores más vendidos en cada sucursal" → `["branch","color"]`. Sin ranking, se usa el **orden de mención**: "ventas por categoría y por mes" → `["category","month"]`.
2. **Comparaciones.** "comparado con el mes/año/período anterior", "vs el anterior", "contra el mes pasado" → `compare_previous=true` y el período queda como se dijo ("este mes comparado con el mes pasado" → `this_month` + compare). "Comparar/comparame las sucursales" sin período previo → agrupar por sucursal, `compare_previous=false`.
3. **Preguntas de estado**: "cómo nos fue (ayer/hoy…)", "cómo vamos este mes", "cómo van las ventas", "qué tal las ventas" son consultas de ventas → `metric=revenue`; con "entre las sucursales" → `group_by=["branch"]`.
4. **Singular de persona**: "¿quién compra más?" → `group_by=["customer"]`, `metric=revenue`, `top_n=1`, `order=desc`. "mejores clientes" (plural, sin número) → sin `top_n`.
5. **La métrica explícita gana** a la regla de rankings: "la sucursal con más pedidos" → `metric=orders`, `group_by=["branch"]`, `top_n=1`.
6. **Mes con nombre igual al actual** ("noviembre") → `custom` del día 1 al último día del mes (el motor recorta lo futuro a hoy). "el miércoles" dicho en miércoles → hoy (un día).
7. **Se aceptan** plurales, femeninos y flexiones ("presenciales", "agotadas", "semanales", "diaria") y los sinónimos razonables ("recaudación", "forma de pago" = método de pago, "online" como filtro de canal, "más usado" en un ranking de método de pago → `group_by=["payment_method"]`, `metric=orders`).
8. **Inventario/stock crítico/movimientos**: no usan el período por defecto; el período solo aplica a `movements` si se dijo (si no se dijo, últimos 30 días).
9. **Sin palabra de métrica pero hablando de dinero** ("pagos con qr", "cuánto entró con tarjeta", "lo vendido con tarjeta" en singular) → `metric=revenue`. "vendidos/vendidas" en plural → `units`.
10. **(2026-11-11, 2.ª tanda)** "tienda" sin "física/presencial" dicho junto a un nombre de sucursal ("la tienda del alto") es sinónimo de sucursal, NO canal; "online vs tienda" sí agrupa por canal.
11. `warn_words` (palabras toleradas pero no aplicadas) son **tokens sueltos normalizados** ("santa", "cruz").
12. Partes del día ("ayer en la tarde", "esta mañana", "anoche" = ayer se mantiene) distintas de "anoche" → `None` por regla de oro (no hay datos por hora).
13. "efectivo versus/vs/contra tarjeta" (dos métodos de pago comparados) → `group_by=["payment_method"]` (no filtro), igual que "online vs tienda".
14. "la última semana" → `last_n_days` con n=7; "la semana pasada" → `last_week`.
15. "del mes" sin "este" ("mejores clientes del mes") → `this_month`; "del año" → `this_year`.
16. "qué tan bien nos fue", "cómo estamos de ventas", "los números de ayer", "balance", "cómo cerramos" → consulta de estado → `revenue`.
17. Comparación entre dos sucursales nombradas ("la sucursal sur vende más que la del alto") → `group_by=["branch"]`, `metric=revenue`, filtro con las dos sucursales.
18. "mercadería"/"cuántas X me quedan"/"qué tengo de X" → `inventory`; "entradas/ingresos de mercadería", "reposición", "llegó mercadería" → `movements`.
19. "lo que salió / se despachó / se llevaron / salieron" (prendas) → verbos de venta → `units`; "rotación" → `metric=units`, `group_by=["product"]`.
20. Pedidos de varios reportes a la vez ("ventas, stock crítico y clientes de todo") → `None` (una sola consulta por vez).
21. "cuánto ganamos/ganancia/utilidad/margen" → `None` (no hay datos de costos).
22. **Abreviaturas de teléfono**: "vtas" = ventas, "suc" = sucursal, "x" = por, "prod" = producto(s), "q tal" = qué tal, "xfa" = por favor, "pq" = por qué (None), "tmb" = también (relleno).
23. **(2026-11-11, R3 ronda 1, decisiones del intérprete)** Comparación con dos períodos: el primero es el pedido y el segundo la referencia, que debe terminar antes del pedido y a no más de 31 días de su inicio (si no, `None`: el motor compara con el período inmediatamente anterior). "cuántos clientes compraron…" sin agrupación dicha → `group_by=[]` (un total). Avisos (`warnings`): solo palabras desconocidas que siguen a "de/del/en/para/con/sobre/desde" (salteando artículos) o que continúan un nombre ya avisado ("santa cruz"); el relleno conversacional nunca aparece.
24. **(2026-11-11, R3 ronda 2)** Una entidad desconocida nombrada CON su sustantivo de tipo ("la sucursal de Santa Cruz", "la categoría zapatos", "el producto camisa hawaiana", también en inventario) → `None`: se pidió algo que no existe y no se responde para toda la empresa. Sin sustantivo de tipo ("ventas de zapatos") se tolera y se avisa (aclaración 23). Las personas mencionadas ("el contador quiere…") no cambian el reporte, pero agrupar o rankear por ellas ("ventas por vendedor", "el mejor cajero") → `None`.
25. **(2026-11-11, R3 ola final)** Palabra distintiva suelta del catálogo: **solo sucursales** ("en el centro", "del alto", "la sur", "la zona sur"); productos y categorías requieren el nombre completo (singular/plural da igual). Ni siquiera en sucursales si la palabra va tras "lo" ("a lo largo", "lo alto"), si le falta la palabra que la sigue en el nombre ("zona" sola, "zona norte"), si la palabra siguiente es desconocida ("centro comercial") o si es "centro de <otro lugar>" ("el centro de cochabamba" = Cochabamba; "el centro de santa cruz" = aviso, sin filtro).
26. Comparación: la referencia debe ser **exactamente** el período anterior pegado (termina el día antes del inicio del pedido); si no, `None` ("hoy vs el lunes", "octubre vs agosto").
27. Inventario, stock crítico y movimientos solo aceptan agrupar por sucursal o producto (si se pide otra cosa, `None`) y siempre salen con `group_by=["product"]`, sin métrica/canal/pago/comparación.
28. Pagos que no existen en el sistema (transferencia bancaria, depósito, "a cuenta", Tigo Money, Yape) → `None`; un verbo de dinero (cobrar/pagar) con un reporte de stock → `None`.
29. Personas como filtro ("ventas del vendedor Juan", "lo que vendió la cajera") → `None`; personas que piden el reporte ("el contador quiere…") no cambian nada.
30. Rankings de ventas sueltas ("la venta más alta", "el ticket más alto"), montos ("ventas mayores a 500 Bs") y mayoreo ("al por mayor/menor") → `None`. "bs/bolivianos" son moneda (relleno).
31. Días de la semana habituales ("los lunes", "todos los lunes", "cada viernes") → `None`. "el uno de noviembre" = 1 de noviembre.
32. **(2026-11-11, R3 últimos ajustes)** `compare_previous=true` solo cuando lo comparado son PERÍODOS ("este mes vs el mes pasado", "hoy vs ayer", "octubre vs septiembre") o se dice "comparado con el (período/mes/año/semana) anterior"; "online vs tienda", "efectivo vs/con tarjeta", "la sur vs el alto" agrupan (canal / método de pago / sucursal) con `compare_previous=false`. "tienda/sucursal/local/sede + de/del + <nombre>" nombra una sucursal: si no está en el catálogo → `None`. "tienda" (con o sin artículo: "ventas de la tienda", "en la tienda ayer", "lo de la tienda") es el canal tienda cuando NO le sigue "de/del <nombre>" ni lleva un nombre de sucursal ("la tienda sur" / "la tienda del alto" = esa sucursal); "online vs tienda" agrupa por canal. (Corregido el 2026-11-11.)
