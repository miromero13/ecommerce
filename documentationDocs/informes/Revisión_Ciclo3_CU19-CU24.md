# Revisión de implementación — Ciclo 3 (CU19 – CU24)

Fecha: 2026-09-15
Alcance: verificación de que los casos de uso del ciclo 3 (`Casos_de_Uso_WomenStyle.md`, sección 2, tabla Ciclo 3) están implementados de forma completa (backend API + frontend web + app móvil) y de acuerdo a su definición. Revisión de solo lectura sobre el código.

---

## 1. Resumen global

| CU | Caso de uso | % implementado | Backend | Frontend | App móvil | Estado |
|---|-------------|:--------------:|:-------:|:--------:|:---------:|--------|
| CU19 | Usar vestidor virtual (RA) | **0 %** | ✘ | — (no aplica) | ✘ | No implementado |
| CU20 | Generar reportes y dashboards | **85 %** | ✔ | ✔ | — (web) | Funcional, con limitaciones |
| CU21 | Recibir recomendaciones de IA | **0 %** | ✘ | ✘ | ✘ | No implementado |
| CU22 | Consultar asistente virtual/chatbot | **0 %** | ✘ | ✘ | ✘ | No implementado |
| CU23 | Generar reporte por voz/lenguaje natural | **0 %** | ✘ | ✘ | — (web) | No implementado |
| CU24 | Recibir notificaciones push | **0 %** | ✘ | ✘ | ✘ | No implementado (plus) |

**Promedio ponderado estimado del ciclo 3: ~15 %**

Diagnóstico general: de los 6 CU del ciclo 3, **solo CU20 (reportes y dashboards) está realmente implementado** (backend y frontend web). Los 5 restantes (CU19, CU21, CU22, CU23, CU24) **no tienen código alguno** — ni modelo, ni servicio, ni endpoint, ni pantalla. CU19, CU21, CU22 y CU24 dependen además de la app móvil, que hoy solo cubre catálogo, carrito, cuenta, órdenes y reservas, sin cámara, sin RA, sin notificaciones ni servicios de IA. La Fase 8 de `docs/IMPLEMENTATION_PHASES.md` figura íntegramente con tareas `[ ]`.

---

## 2. Detalle por caso de uso

### CU19 – Usar vestidor virtual — 0 %

**Plataforma declarada:** Móvil (exclusivo). RA con cámara del dispositivo.

**Implementado:** nada.

**Evidencia de lo que falta:**
1. **No existe ningún endpoint/servicio de vestidor o RA** en el backend. `backend/main.py:61-75` registra únicamente los routers de usuarios, auth, sucursales, proveedores, catálogo, inventario, carrito, reservas, órdenes, pagos, ventas, reportes, dashboards y promociones. No hay router `/try-on`, `/ar`, `/virtual-fitting`, ni similar.
2. **La app móvil no tiene integración de cámara ni de AR.** `mobile/pubspec.yaml:30-39` solo declara `dio`, `flutter_secure_storage` y `flutter_stripe`. No hay `camera`, `ar_flutter_plugin`, `google_mlkit` ni ningún SDK de realidad aumentada.
3. **No hay pantalla de vestidor** en `mobile/lib/app/routes.dart:15-23`; las únicas rutas son catálogo, carrito, cuenta, reservas, órdenes, producto y login. La relación `<<extend>> CU19 → CU10` (documentada en el CU, sección 5.7) tampoco existe: el `product_detail_page.dart` no ofrece ninguna acción de "probar prenda".
4. Fase 8 (`IMPLEMENTATION_PHASES.md:160`): "Preparar base para vestidor virtual" sin marcar.

**Requisitos técnicos para completarlo:** selección de una prenda desde el detalle del catálogo (hook al CU10), acceso a la cámara trasera, calibración/ajuste sobre la imagen del cliente, superposición de la prenda y, si se quiere algo más que un mock, un servicio backend para gestionar las imágenes/parámetros de las prendas (el modelo actual solo guarda `image_url` por variante en `product_variant.py`).

---

### CU20 – Generar reportes y dashboards — 85 %

**Plataforma declarada:** Web (Administrador).

**Implementado (backend + frontend):**
- **Reportes tabulares y exportación:** `GET /reports/sales`, `GET /reports/sales/export`, `GET /reports/inventory`, `GET /reports/inventory/export`, `GET /reports/movements`, `GET /reports/movements/export` (`backend/app/routes/report_routes.py:50-116`), con filtros por sucursal, producto, variante, rango de fechas y texto (`services/report_service.py`). Exportación CSV real (`export_rows_to_csv`, `report_service.py:212`).
- **Dashboard:** `GET /dashboard` (`dashboard_routes.py:27`) con summary (ventas, órdenes, ticket promedio, stock, bajo stock, reservas por estado), series de ventas y movimientos **por periodo** (day/week/month, `dashboard_service.py:37-38`), KPIs por sucursal y por producto, top 10 de productos y alerta de stock bajo. Solo administrador (`require_roles(RolEnum.administrador)`).
- **Frontend reportes:** `admin-reports-page.component.ts` (filtros, tablas, exportación CSV) en la ruta `admin/reports` (`app.routes.ts:181-186`).
- **Frontend dashboard:** `admin-home-page.component.ts` en la ruta `admin/` (`app.routes.ts:130-135`) con tarjetas de KPIs, barras de progreso de ventas por periodo, top productos y stock por sucursal.

**Falta / a mejorar:**
1. **"Indicadores visuales" limitados a barras CSS de progreso** (`admin-home-page.component.ts:63-71`, `progressWidth`). No hay gráficas reales (líneas/barras con librería de charts); es aceptable pero no equiparable a un dashboard profesional.
2. **Alertas de indicador crítico no proactivas.** El dashboard detecta stock bajo (`low_stock`, `dashboard_service.py:254-270`) pero solo lo muestra en pantalla; la relación `<<extend>> CU20 → CU24` (notificar al administrador ante un indicador crítico) no existe porque CU24 no está implementado.
3. **Solo el reporte tabular exporta; el dashboard no** tiene opción de exportación propia (aunque puede cubrirse con el CSV de los reportes).
4. En la UI de reportes no hay agregación por periodo para el tabular (solo filtro de fechas); la agregación por periodo solo está en el dashboard.
5. Fase 8 (`IMPLEMENTATION_PHASES.md:158`): "Construir reportes y dashboards" sin marcar. Sin pruebas automatizadas en `backend/tests`.

No hay nada bloqueante funcional: el CU se considera operativo.

---

### CU21 – Recibir recomendaciones de IA — 0 %

**Plataforma declarada:** Ambas (web + móvil). Sugerencias según historial, temporada y disponibilidad.

**Implementado:** nada.

**Evidencia de lo que falta:**
1. **Backend:** no existe endpoint, servicio ni modelo de recomendaciones. `requirements.txt` no incluye ninguna librería de ML/LLM (ni `openai`, `anthropic`, `langchain`, `scikit-learn`, etc.) — solo FastAPI/SQLAlchemy/Stripe/pandas.
2. **Frontend web:** no hay página ni servicio de recomendaciones; ninguna ruta en `app.routes.ts` la referencia.
3. **App móvil:** no existe pantalla ni API de recomendaciones (`mobile/lib/features/*` solo auth, catalog, cart, orders, profile, reservations).
4. **Definición de interfaz pendiente.** En `Casos_de_Uso_WomenStyle.md` (sección 5.6) CU21 está documentado como CU independiente a la espera de decidir si se integra a CU10 o va en un apartado "Para ti". Esa decisión sigue abierta, por lo que tampoco hay boceto de UI.
5. Fase 8 (`IMPLEMENTATION_PHASES.md:159`): "Preparar base para recomendaciones IA" sin marcar.

**Requisitos técnicos para completarlo:** definir estrategia (heurística simple sobre historial de compras/visitas + temporada + disponibilidad, o LLM), crear el servicio de recomendaciones, el endpoint (p. ej. `GET /recommendations`), y la UI en web y móvil según la decisión de interfaz.

---

### CU22 – Consultar asistente virtual/chatbot — 0 %

**Plataforma declarada:** Ambas (web + móvil). Resolución de dudas del cliente sobre productos.

**Implementado:** nada.

**Evidencia de lo que falta:**
1. **Backend:** no hay endpoint de chat, ni websocket/SSE, ni sesiones de conversación, ni integración con LLM. No existe router `/chat`, `/assistant` ni `asistente` en `backend/main.py`.
2. **Frontend web:** no existe componente ni página de chat/ayuda; sin librería de websockets en `package.json` (sin `@nestjs/websockets` ni similar en el app code).
3. **App móvil:** no hay pantalla de asesor virtual ni service de chat en `mobile/lib/features/`.
4. Fase 8 (`IMPLEMENTATION_PHASES.md:161`): "Preparar asistente virtual si entra en alcance" sin marcar.

**Requisitos técnicos para completarlo:** decidir canal (chat por estados/reglas o IA generativa), backend con historial de conversación y contexto de productos (con consulta al catálogo), y UI web + móvil.

---

### CU23 – Generar reporte por voz/lenguaje natural — 0 %

**Plataforma declarada:** Web (Administrador). Canal alternativo de CU20 vía comando de voz (`<<extend>> CU23 → CU20`).

**Implementado:** nada.

**Evidencia de lo que falta:**
1. **Frontend:** no hay captura de audio, uso de Web Speech API/y micrófono, ni parseo de lenguaje natural en ningún componente. `admin-reports-page.component.ts` solo interactúa manualmente (filtros → botón consultar → exportar).
2. **Backend:** no hay endpoint de reporte por texto/lenguaje natural que traduzca una consulta (`"ventas de febrero en La Paz"`) a un `ReportQuery` y reutilice `report_service.py`/`dashboard_service.py`.
3. **No hay transcripción ni integración con ningún motor** (STT/LLM) en `requirements.txt`.
4. Fase 8 no contempla tarea explícita para CU23 (el propósito de "reportes por lenguaje natural" no está en la lista de tareas).

**Requisitos técnicos para completarlo:** captura de voz en el navegador (Web Speech API opcional sin backend, o un servicio STT), un intérprete de consulta → filtros, y reutilizar `get_sales_report`/`get_inventory_report`/`get_dashboard` para responder (tabla/CSV o resumen textual). La base de CU20 ya existe y facilita este caso.

---

### CU24 – Recibir notificaciones push — 0 %

**Plataforma declarada:** Móvil. Funcionalidad **plus** del equipo (sin RF numerado de origen). Actores: Administrador, Cliente, Encargado de sucursal.

**Implementado:** nada.

**Evidencia de lo que falta:**
1. **No existe infraestructura de push en el backend:** ningún router (`/notifications`, `/devices`, `/subscribe`), ningún modelo/tabla de dispositivos o tokens (en `alembic/versions/` no hay ninguna migración de notificaciones), y ninguna dependencia de Firebase/APNs/WebPush en `requirements.txt` o `config.py` (solo `stripe_webhook_secret` en `core/config.py:13`).
2. **No hay generación de eventos** en los CU que lo disparan. Las relaciones documentadas en la sección 5.5 no existen en código:
   - `CU14 <<include>> CU24` (toda reserva nueva notifica al encargado) → `reservation_service.py` no emite ninguna notificación.
   - `CU12 <<extend>> CU24` (stock bajo umbral) → `inventory_service.py` no detecta umbral ni notifica.
   - `CU16/CU17/CU07/CU20 <<extend>> CU24` → ningún cambio de estado de pedido, preparación de reserva, publicación de producto ni alerta de dashboard emite una notificación.
3. **App móvil:** no hay `firebase_messaging`, `flutter_local_notifications` ni plugin similar en `mobile/pubspec.yaml:30-39`; no hay manejo de permisos ni manejo de token de dispositivo; la app no tiene capa de recepción/redirección de notificaciones.
4. **Frontend web:** sin Service Worker ni Push API (las coincidencias de "push" en `admin-catalog-page.component.ts:185,240-242,394` y `sales-page.component.ts:88` son llamadas a `Array.push` de formularios, no notificaciones).

**Requisitos técnicos para completarlo:** alta de proveedor de push (p. ej. FCM), modelo de `device_token`/suscripciones por usuario, endpoints de suscripción/desuscripción, un servicio emisor de notificaciones, puntos de emisión en `reservation_service`, `inventory_service`, `order_service`, `sales_service`, `catalog_service` y `dashboard_service`, y la capa de recepción en la app móvil. Al ser una funcionalidad plus de alto riesgo de integración, puede tratarse como POC/extra del equipo.

---

## 3. Brechas transversales

1. **5 de 6 CU del ciclo 3 no tienen ninguna implementación.** CU19, CU21, CU22 y CU24 requieren la app móvil y el backend; CU23 solo frontend web + backend reutilizable. El backend actual es completo para los ciclos 1-2 (usuarios, catálogo, inventario, reservas, compras, ventas, promociones) pero no tiene NINGUNA pieza de IA, RA, voz ni notificaciones.
2. **App móvil funcional pero sin las capacidades del ciclo 3.** Cubre catálogo, carrito, perfil/órdenes/reservas y checkout (Stripe), con la arquitectura adecuada (API client, session storage, controllers), pero le faltan cámara/RA, servicios de IA, chat y notificaciones push. No hay plugins de cámara, AR, firebase ni local notifications en `pubspec.yaml`.
3. **Fase 8 de `IMPLEMENTATION_PHASES.md` sin marcar**: "Construir reportes y dashboards" y las 3 "bases" (IA, RA, chatbot) figuran como `[ ]` (`IMPLEMENTATION_PHASES.md:158-161`), pese a que CU20 ya está implementado. Hay desfase entre la planificación y el código, igual que se observó en el ciclo 2.
4. **Sin pruebas automatizadas** para el ciclo 3. `backend/tests` solo contiene `test_business_rules.py` (reglas de inventario). No hay tests de reportes/dashboard ni de ninguna funcionalidad nueva; la "Regla de programación" de `docs/IMPLEMENTATION_PHASES.md:175-184` exige "prueba del flujo" en cada tarea.
5. **CU20 es el único caso "Ambas/Web" sin dependencia del móvil**, y está concentrado en el rol administrador (reportes y dashboard protegidos por `require_roles`). El resto del ciclo depende de tecnologías externas (FCM, STT, LLM/ML, RA) que hoy no están en `requirements.txt`, `package.json` ni `pubspec.yaml`.
6. **Notificaciones como canal proactivo requerirían** además refactorizar puntos de emisión en los servicios de reservas/inventario/órdenes/ventas/catálogo/dashboard; no es un añadido aislado sino transversal al negocio.

---

## 4. Prioridad de los trabajos pendientes

1. **CU20**: dejar la Fase 8 marcada como completada y añadir, si hay tiempo, gráficas reales y exportación del dashboard (único CU del ciclo con avance real; cerrarlo formalmente).
2. **CU21**: definir la interfaz de recomendaciones (decisión pendiente de la sección 5.6) y construir un primer backend heurístico (historial + temporada + disponibilidad) reutilizando `cart`/`order`/`catalog`.
3. **CU19**: como es "Alto riesgo/Alta prioridad" y es el único caso de RA, evaluar un alcance mínimo (superposición de `image_url` de la prenda sobre la cámara) como POC en la app móvil.
4. **CU22**: chatbot básico (flujo por reglas + contexto de productos) o IA generativa; es "Baja prioridad/Alto riesgo", puede quedar como extensión.
5. **CU23**: aprovechar CU20 ya implementado; un intérprete de consultas por texto más Web Speech API en `admin-reports-page` es el camino más corto.
6. **CU24**: tratar como plus/POC (FCM + registro de tokens + al menos 2 eventos: stock bajo y reserva nueva). Solo abordarlo después de los CU obligatorios, dado que no tiene RF de origen.

Prioridad sugerida por impacto y esfuerzo: **CU20 (cierre) → CU21 → CU23 → CU22 → CU19 → CU24**, alineado con el orden recomendado de `IMPLEMENTATION_PHASES.md:186-197` (primero reportes, después extras de IA y RA).