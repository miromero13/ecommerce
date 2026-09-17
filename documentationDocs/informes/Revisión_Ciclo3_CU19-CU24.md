# Revisión de implementación — Ciclo 3 (CU19 – CU25)

Fecha: 2026-09-17
Alcance: verificación de que los casos de uso del ciclo 3 (`Casos_de_Uso_WomenStyle (1).md`, sección 2, tabla Ciclo 3) están implementados de forma completa (backend API + frontend web + app móvil) y de acuerdo a su definición. Revisión de solo lectura sobre el código. En esta versión se incorpora **CU25 – Gestionar códigos promocionales** (ampliación solicitada por la docente) y se actualiza el estado de CU20 y CU23 tras los últimos merges. **Nota: el merge "ya con el CU de IA" corresponde a mejoras de CU23 (reporte por lenguaje natural), no a CU21; no se encontró ningún código de recomendaciones.**

---

## 1. Resumen global

| CU | Caso de uso | % implementado | Backend | Frontend | App móvil | Estado |
|---|-------------|:--------------:|:-------:|:--------:|:---------:|--------|
| CU19 | Usar vestidor virtual (RA) | **0 %** | ✘ | — (no aplica) | ✘ | No implementado |
| CU20 | Generar reportes y dashboards | **95 %** | ✔ | ✔ | — (web) | Funcional, mejorado |
| CU21 | Recibir recomendaciones de IA | **0 %** | ✘ | ✘ | ✘ | No implementado |
| CU22 | Consultar asistente virtual/chatbot | **0 %** | ✘ | ✘ | ✘ | No implementado |
| CU23 | Generar reporte por voz/lenguaje natural | **90 %** | ✔ | ✔ | — (web) | Funcional, cubre ventas/inventario/movimientos |
| CU24 | Recibir notificaciones push | **0 %** | ✘ | ✘ | ✘ | No implementado (plus) |
| CU25 | Gestionar códigos promocionales | **90 %** | ✔ | ✔ | — (web) | Funcional |

**Promedio ponderado estimado del ciclo 3: ~39 %** (antes ~15 %).

Diagnóstico general: de los 7 CU del ciclo 3, **3 están implementados** (CU20 reportes/dashboards, CU23 reporte por lenguaje natural, CU25 códigos promocionales) en backend y frontend web. Los 4 restantes (CU19, CU21, CU22, CU24) **no tienen código alguno** — ni modelo, ni servicio, ni endpoint, ni pantalla. CU19, CU21, CU22 y CU24 dependen además de la app móvil, que hoy solo cubre catálogo, carrito, cuenta, órdenes y reservas, sin cámara, sin RA, sin notificaciones ni servicios de IA. La Fase 8 de `docs/IMPLEMENTATION_PHASES.md` figura íntegramente con tareas `[ ]`, pese a que CU20 y CU23 ya tienen avance real.

---

## 2. Detalle por caso de uso

### CU19 – Usar vestidor virtual — 0 %

**Plataforma declarada:** Móvil (exclusivo). RA con cámara del dispositivo.

**Implementado:** nada.

**Evidencia de lo que falta:**
1. **No existe ningún endpoint/servicio de vestidor o RA** en el backend. `backend/main.py:62-76` registra únicamente los routers de usuarios, auth, sucursales, proveedores, catálogo, inventario, carrito, reservas, órdenes, pagos, ventas, reportes, dashboards, promociones y replenishment. No hay router `/try-on`, `/ar`, `/virtual-fitting`, ni similar.
2. **La app móvil no tiene integración de cámara ni de AR.** `mobile/pubspec.yaml` solo declara `dio`, `flutter_secure_storage` y `flutter_stripe`. No hay `camera`, `ar_flutter_plugin`, `google_mlkit` ni ningún SDK de realidad aumentada.
3. **No hay pantalla de vestidor** en `mobile/lib/app/routes.dart:15-23`; las únicas rutas son catálogo, carrito, cuenta, reservas, órdenes, producto y login. La relación `<<extend>> CU19 → CU10` (documentada en el CU, sección 5.3) tampoco existe: el `product_detail_page.dart` no ofrece ninguna acción de "probar prenda".
4. Fase 8 (`IMPLEMENTATION_PHASES.md:160`): "Preparar base para vestidor virtual" sin marcar.

**Requisitos técnicos para completarlo:** selección de una prenda desde el detalle del catálogo (hook al CU10), acceso a la cámara trasera, calibración/ajuste sobre la imagen del cliente, superposición de la prenda y, si se quiere algo más que un mock, un servicio backend para gestionar las imágenes/parámetros de las prendas (el modelo actual solo guarda `image_url` por variante en `product_variant.py`).

---

### CU20 – Generar reportes y dashboards — 95 %

**Plataforma declarada:** Web (Administrador).

**Implementado (backend + frontend), actualizado respecto a la revisión anterior:**
- **Reportes tabulares y exportación:** `GET /reports/sales`, `GET /reports/sales/export`, `GET /reports/inventory`, `GET /reports/inventory/export`, `GET /reports/movements`, `GET /reports/movements/export` (`backend/app/routes/report_routes.py:79-151`), con filtros por sucursal, producto, variante, rango de fechas y texto (`services/report_service.py`). Exportación CSV real (`export_rows_to_csv`).
- **Acceso por rol con alcance:** los reportes ahora aceptan **administrador y encargado**; el encargado queda **restringido a su sucursal** (`_scoped_filters`, `report_routes.py:65-76`), ya no solo administrador.
- **Dashboard:** `GET /dashboard` (`dashboard_routes.py:27`) con summary (ventas, órdenes, unidades, ticket promedio, stock, disponible, bajo stock, reservas), series de ventas y movimientos por periodo (day/week/month), KPIs por sucursal, top productos y alerta de stock bajo. Sigue protegido solo para administrador.
- **Gráficas reales (mejora):** el dashboard de administrador ahora usa **`angular-chrts` + `@unovis/ts`** (AreaChart, BarChart, DonutChart) en `admin-home-page.component.ts:13,26`, ya no solo barras CSS de progreso; incluye área de ventas por periodo, barras de top productos, barras de rendimiento por sucursal y donut de distribución de movimientos (entradas/salidas/traspasos). Paquete `angular-chrts` en `package.json`.
- **Exportación PDF/HTML/CSV desde la UI:** utilidad `simple-pdf.util.ts` (jsPDF + autotable, `jspdf` y `jspdf-autotable` en `package.json`) usada por la página de reportes de ventas (`sales-history-page.component.ts`) y por la página de inventario/movimientos (`admin-inventory-page.component.ts`): modal con selección de columnas, formato (PDF/HTML/CSV), filtros y descarga.
- **Frontend reportes de ventas:** `sales-history-page.component.ts` en las rutas `admin/sales`, `encargado/sales` y `cajero/sales` (`app.routes.ts:153,219`).
- **Frontend reportes de inventario/movimientos:** `admin-inventory-page.component.ts` (rutas `admin/inventory` y `encargado/inventory`) con generación y exportación de ambos reportes.
- **Dashboard:** `admin-home-page.component.ts` en la ruta `admin/` (`app.routes.ts:165-174`) con tarjetas de KPIs, gráficas, top productos y stock por sucursal.

**Falta / a mejorar:**
1. **El dashboard no tiene exportación propia** (PDF/CSV directo del dashboard); la exportación existe solo en los reportes tabulares (ventas, inventario, movimientos), no sobre las gráficas del dashboard.
2. **Alertas de indicador crítico no proactivas.** El dashboard detecta stock bajo (`low_stock`) pero solo lo muestra en pantalla; la relación `<<extend>> CU20 → CU24` (notificar al administrador ante un indicador crítico) no existe porque CU24 no está implementado.
3. **Agregación por periodo solo en el dashboard**; los reportes tabulares mantienen el filtro de fechas sin agrupación por periodo.
4. Fase 8 (`IMPLEMENTATION_PHASES.md:158`): "Construir reportes y dashboards" sin marcar, pese a estar implementado. Las pruebas automatizadas cubren el contrato del reporte natural (CU23) pero no los servicios de reportes/dashboard directamente.

No hay nada bloqueante funcional: el CU se considera operativo y notablemente mejorado.

---

### CU21 – Recibir recomendaciones de IA — 0 %

**Plataforma declarada:** Ambas (web + móvil). Sugerencias según historial, temporada y disponibilidad.

**Implementado:** nada.

**Evidencia de lo que falta:**
1. **Backend:** no existe endpoint, servicio ni modelo de recomendaciones. `requirements.txt` no incluye ninguna librería de recomendación (la única dependencia de IA, `google-genai`, se usa exclusivamente para el reporte por lenguaje natural de CU23, no para recomendaciones).
2. **Frontend web:** no hay página ni servicio de recomendaciones; ninguna ruta en `app.routes.ts` la referencia (los home de cliente/proveedor/encargado/cajero muestran métricas, no sugerencias personalizadas).
3. **App móvil:** no existe pantalla ni API de recomendaciones (`mobile/lib/features/*` solo auth, catalog, cart, orders, profile, reservations).
4. **Definición de interfaz pendiente.** En `Casos_de_Uso_WomenStyle (1).md` (sección 5.6) CU21 está documentado como CU independiente a la espera de decidir si se integra a CU10 o va en un apartado "Para ti". Esa decisión sigue abierta, por lo que tampoco hay boceto de UI.
5. Fase 8 (`IMPLEMENTATION_PHASES.md:159`): "Preparar base para recomendaciones IA" sin marcar.

**Requisitos técnicos para completarlo:** definir estrategia (heurística simple sobre historial de compras/visitas + temporada + disponibilidad, o LLM), crear el servicio de recomendaciones, el endpoint (p. ej. `GET /recommendations`), y la UI en web y móvil según la decisión de interfaz.

---

### CU22 – Consultar asistente virtual/chatbot — 0 %

**Plataforma declarada:** Ambas (web + móvil). Resolución de dudas del cliente sobre productos.

**Implementado:** nada.

**Evidencia de lo que falta:**
1. **Backend:** no hay endpoint de chat, ni websocket/SSE, ni sesiones de conversación, ni integración con LLM. No existe router `/chat`, `/assistant` ni `asistente` en `backend/main.py`.
2. **Frontend web:** no existe componente ni página de chat/ayuda; sin librería de websockets en `package.json`.
3. **App móvil:** no hay pantalla de asesor virtual ni service de chat en `mobile/lib/features/`.
4. Fase 8 (`IMPLEMENTATION_PHASES.md:161`): "Preparar asistente virtual si entra en alcance" sin marcar.

**Requisitos técnicos para completarlo:** decidir canal (chat por estados/reglas o IA generativa), backend con historial de conversación y contexto de productos (con consulta al catálogo), y UI web + móvil.

---

### CU23 – Generar reporte por voz/lenguaje natural — 90 %

**Plataforma declarada:** Web (Administrador). Canal alternativo de CU20 vía comando de voz (`<<extend>> CU23 → CU20`).

**Implementado (backend + frontend), actualizado tras el último merge:**
- **Backend con Gemini:** `POST /reports/query` (`report_routes.py:25-35`), protegido para administrador, implementado en `services/natural_report_service.py` (169 líneas). El servicio:
  - Clasifica la solicitud en `sales | inventory | movements` mediante Gemini (`google-genai` en `requirements.txt`), con contrato de salida tipado `NaturalReportInterpretation` (`schemas/report_schema.py`).
  - Interpreta sucursal, producto, variante, fechas **relativas al día actual**, columnas solicitadas (con mapeo de nombres en español y corrección de transcripciones "cku"/"sku") y formato (`pdf` por defecto, o `csv`/`html`).
  - Valida contra los catálogos reales de sucursales y productos, rechaza entidades inexistentes (`_validate_filters`) y reutiliza los reportes de CU20 (`get_sales_report`, `get_inventory_report`, `get_movements_report`).
  - Config con `GEMINI_API_KEY`, `GEMINI_MODEL` y `GEMINI_TIMEOUT_SECONDS` (`core/config.py`, respaldado en `.env.example`).
- **Soporte de columnas por tipo de reporte (mejora del último merge):** `schemas/report_schema.py` ahora define `AllowedReportColumn` (14 claves: ventas, inventario y movimientos), `AllowedSalesReportColumn`, `DEFAULT_SALES_REPORT_COLUMNS`, `DEFAULT_INVENTORY_REPORT_COLUMNS` y `DEFAULT_MOVEMENT_REPORT_COLUMNS`; el servicio aplica las columnas por defecto propias de cada tipo de reporte cuando el usuario no las especifica.
- **Pruebas de contrato:** `backend/tests/test_natural_report_contract.py` (5 tests): default PDF y filtros, deduplicación de columnas, rechazo de columnas/tipos inválidos y límite de longitud de la consulta (500 caracteres).
- **Frontend con Web Speech API en dos pantallas (mejora del último merge):**
  - **Reportes de ventas:** `sales-history-page.component.ts` — captura de voz nativa (`SpeechRecognition`/`webkitSpeechRecognition`, idioma `es-BO`) con botón de escuchar y textarea para escribir (`startListening`, líneas 188-209); `generateNaturalReport` valida `report_type === 'sales'` y genera PDF/HTML/CSV reutilizando la infraestructura de CU20.
  - **Reportes de inventario/movimientos:** `admin-inventory-page.component.ts` — la misma captura de voz (`naturalQuery`, `listening`, líneas 113-114, 275-298) y `generateNaturalReport` (líneas 300-339) valida `report_type === 'inventory'` o `'movements'` y descarga en PDF/HTML/CSV con las columnas mapeadas (`REPORT_COLUMNS`).
- **Solicitud a la API:** `queryNaturalLanguage` (`reports-api.service.ts:29-31`).

**Falta / a mejorar:**
1. **Dependencia de API key de Gemini** en tiempo de ejecución: sin `GEMINI_API_KEY` el endpoint devuelve `503` ("no configurado"); el servicio depende de la disponibilidad del modelo.
2. Fase 8 no contempla tarea explícita para CU23 en `IMPLEMENTATION_PHASES.md` (la lista de CU de la fase, líneas 163-169, incluye CU23 pero no hay tarea marcada para él).
3. La entrada por voz depende del navegador (Web Speech API no disponible en todos los navegadores/plataformas); el textarea es el respaldo funcional.

**Requisitos técnicos restantes:** documentar el cierre en la Fase 8. Respecto a la UI, ya no queda pendiente significativo: el backend soporta los tres tipos de reporte y cada pantalla web expone sus tipos correspondientes (ventas en reportes de ventas; inventario y movimientos en inventario). Una mejora opcional es permitir también dictado en el dashboard.

---

### CU24 – Recibir notificaciones push — 0 %

**Plataforma declarada:** Móvil. Funcionalidad **plus** del equipo (sin RF numerado de origen). Actores: Administrador, Cliente, Encargado de sucursal.

**Implementado:** nada.

**Evidencia de lo que falta:**
1. **No existe infraestructura de push en el backend:** ningún router (`/notifications`, `/devices`, `/subscribe`), ningún modelo/tabla de dispositivos o tokens (en `alembic/versions/` no hay migración de notificaciones), y ninguna dependencia de Firebase/APNs/WebPush en `requirements.txt` o `config.py`.
2. **No hay generación de eventos** en los CU que lo disparan. Las relaciones documentadas en la sección 5.5 no existen en código:
   - `CU14 <<include>> CU24` (toda reserva nueva notifica al encargado) → `reservation_service.py` no emite ninguna notificación.
   - `CU12 <<extend>> CU24` (stock bajo umbral) → `inventory_service.py` no detecta umbral ni notifica.
   - `CU16/CU17/CU07/CU20 <<extend>> CU24` → ningún cambio de estado de pedido, preparación de reserva, publicación de producto ni alerta de dashboard emite una notificación.
3. **App móvil:** no hay `firebase_messaging`, `flutter_local_notifications` ni plugin similar en `mobile/pubspec.yaml`; no hay manejo de permisos ni manejo de token de dispositivo; la app no tiene capa de recepción/redirección de notificaciones.
4. **Frontend web:** sin Service Worker ni Push API (las coincidencias de "push" en el código son llamadas a `Array.push` de formularios, no notificaciones).

**Requisitos técnicos para completarlo:** alta de proveedor de push (p. ej. FCM), modelo de `device_token`/suscripciones por usuario, endpoints de suscripción/desuscripción, un servicio emisor de notificaciones, puntos de emisión en `reservation_service`, `inventory_service`, `order_service`, `sales_service`, `catalog_service` y `dashboard_service`, y la capa de recepción en la app móvil. Al ser una funcionalidad plus de alto riesgo de integración, puede tratarse como POC/extra del equipo.

---

### CU25 – Gestionar códigos promocionales — 90 %

**Plataforma declarada:** Web. Actores: Administrador, Encargado de sucursal. Ampliación solicitada por la docente (sin RF numerado de origen).

**Implementado (backend + frontend), nuevo en esta revisión:**
- **Backend:** `GET /promotions` y `POST /promotions` (`promotion_routes.py:17-43`), protegidos para administrador y encargado:
  - El **administrador** solo crea códigos **globales** (`branch_id` nulo); si intenta acotar a una sucursal, se rechaza con 400.
  - El **encargado** solo crea/listan códigos de **su propia sucursal** (403 si intenta otra, 400 si no tiene sucursal asignada).
- **Contratos y validaciones** (`schemas/promotion_schema.py`): `PromotionCodeCreate` con código normalizado a mayúsculas (3-40), tipo de descuento `percentage | fixed`, valor > 0, porcentaje ≤ 100, vigencia opcional con validación de orden de fechas y normalización UTC; `PromotionCodeRead` con `created_by`, `branch_id`, `is_active`, `created_at`.
- **Servicio** (`services/promotion_service.py`): `create_code` (rechaza duplicados con 400), `list_codes` (filtrado por sucursal), `validate_for_user` (existencia, vigencia, alcance por sucursal, uso previo por usuario), `calculate_discount` y `add_usage`. La **aplicación en el carrito ya existía** desde el ciclo previo (CU15): `cart_routes.py` `POST /cart/coupon` y `DELETE /cart/coupon` usando `apply_coupon`/`remove_coupon`, más los modelos `PromotionCode` y `PromotionCodeUsage`.
- **Frontend:** `promotions-page.component.ts` (shared) con listado de códigos y modal de creación (código, tipo de descuento, valor, vigencia con calendario y opción "sin expiración"), usado en las rutas `admin/promotions` (`app.routes.ts:183-185`) y `encargado/promotions` (`app.routes.ts:116-119`). Servicio `promotion-api.service.ts` y modelo `promotion.model.ts`.

**Falta / a mejorar:**
1. **Solo crear y consultar** (acorde a la definición del CU), sin edición ni desactivación de códigos existentes desde la UI (el backend sí conserva `is_active` y `valid_until` como control de vigencia).
2. Sin cambios de estado del código (suspender/reactivar) ni historial de usos visible al administrador (la tabla `promotion_code_usages` existe pero no se expone en UI).
3. Fase 8 de `IMPLEMENTATION_PHASES.md` no lista CU25 (fue añadida como ampliación posterior) — las tareas de la fase 8 solo cubren la lista original.

No hay nada bloqueante: el CU se considera operativo para el flujo crear/listar/aplicar.

---

## 3. Brechas transversales

1. **4 de 7 CU del ciclo 3 no tienen ninguna implementación.** CU19, CU21, CU22 y CU24 requieren la app móvil y el backend; CU19, CU21 y CU22 tampoco tienen pieza en web. El backend es completo para los ciclos 1-2 y para CU20/CU23/CU25 (reportes, IA de lenguaje natural con Gemini, promociones) pero no tiene NINGUNA pieza de RA, recomendaciones, chatbot ni notificaciones. **Importante: el commit "ya con el CU de IA" del último merge corresponde únicamente a CU23 (reporte por voz/lenguaje natural), no a recomendaciones; no existe ningún archivo, tabla, router ni dependencia de ALS/recomendaciones en el repo.**
2. **App móvil funcional pero sin las capacidades del ciclo 3.** Cubre catálogo, carrito, perfil/órdenes/reservas y checkout (Stripe), con la arquitectura adecuada (API client, session storage, controllers), pero le faltan cámara/RA, servicios de IA, chat y notificaciones push. No hay plugins de cámara, AR, firebase ni local notifications en `pubspec.yaml`.
3. **Fase 8 de `IMPLEMENTATION_PHASES.md` desactualizada**: las 4 tareas figuran `[ ]` (`IMPLEMENTATION_PHASES.md:158-161`) aunque "Construir reportes y dashboards" (CU20) y el reporte por lenguaje natural (CU23, ya con los tres tipos de reporte en la UI) están implementados, y CU25 tampoco aparece en esa fase.
4. **Cobertura de pruebas aún baja.** `backend/tests` contiene `test_business_rules.py` (reglas de inventario) y `test_natural_report_contract.py` (contratos del reporte natural, 5 tests). No hay tests de los servicios de reportes/dashboard/promociones; la "Regla de programación" de `docs/IMPLEMENTATION_PHASES.md:175-184` exige "prueba del flujo" en cada tarea.
5. **CU23 depende de un servicio externo (Gemini)** con API key propia; la continuidad del CU depende de la configuración en producción, no solo del código.
6. **Notificaciones como canal proactivo requerirían** además refactorizar puntos de emisión en los servicios de reservas/inventario/órdenes/ventas/catálogo/dashboard; no es un añadido aislado sino transversal al negocio.

---

## 4. Prioridad de los trabajos pendientes

1. **CU20**: marcar como completada la tarea de la Fase 8 y añadir, si hay tiempo, exportación directa del dashboard. Es el CU del ciclo con mayor madurez (gráficas reales + exportación PDF/HTML/CSV + alcance por rol).
2. **CU23**: cerrar el caso documentando su estado en la Fase 8; el backend y la UI ya cubren ventas, inventario y movimientos por lenguaje natural con voz. Pendiente solo mejorar el dictado en el dashboard.
3. **CU25**: como ampliación solicitada por la docente, documentar su cierre formalmente; opcionalmente añadir desactivación de códigos y visibilidad de usos.
4. **CU21**: definir la interfaz de recomendaciones (decisión pendiente de la sección 5.6) y construir un primer backend heurístico (historial + temporada + disponibilidad) reutilizando `cart`/`order`/`catalog`.
5. **CU19**: como es "Alto riesgo/Alta prioridad" y es el único caso de RA, evaluar un alcance mínimo (superposición de `image_url` de la prenda sobre la cámara) como POC en la app móvil.
6. **CU22**: chatbot básico (flujo por reglas + contexto de productos) o IA generativa; es "Baja prioridad/Alto riesgo", puede quedar como extensión.
7. **CU24**: tratar como plus/POC (FCM + registro de tokens + al menos 2 eventos: stock bajo y reserva nueva). Solo abordarlo después de los CU obligatorios, dado que no tiene RF de origen.

Prioridad sugerida por impacto y esfuerzo: **CU20 (cierre) → CU23 (cierre) → CU25 (cierre) → CU21 → CU19 → CU22 → CU24**, alineado con el orden recomendado de `IMPLEMENTATION_PHASES.md` (primero reportes, después extras de IA y RA).