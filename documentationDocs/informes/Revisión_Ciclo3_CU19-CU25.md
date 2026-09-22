# Revisión de implementación — Ciclo 3 (CU19 – CU25)

Fecha: 2026-09-20
Alcance: verificación de que los casos de uso del ciclo 3 (`Casos_de_Uso_WomenStyle (1).md`, sección 2, tabla Ciclo 3) están implementados de forma completa (backend API + frontend web + app móvil) y de acuerdo a su definición. Revisión de solo lectura sobre el código. En esta versión se incorporan **CU25 – Gestionar códigos promocionales** (ampliación solicitada por la docente), **CU21 – Recibir recomendaciones de IA (ALS offline)** y **CU22 – Asistente virtual/chatbot** (último merge "recomendaciones/chat"), la página de detalle de producto con inventario por sucursal, el merge **"new update with RA" (`cae0dc3`) que agrega el backend de garment y 3 componentes de vestidor virtual (Decart VTON + dos motores locales con MediaPipe)**, y el merge más reciente **"new update, last details" (`80f37bb`)** que persiste la calibración del vestidor en el servidor por variante (backend + frontend, sin `localStorage`) para **CU19 – Usar vestidor virtual (RA)**.

---

## 1. Resumen global

| CU | Caso de uso | % implementado | Backend | Frontend | App móvil | Estado |
|---|-------------|:--------------:|:-------:|:--------:|:---------:|--------|
| CU19 | Usar vestidor virtual (RA) | **60 %** | ✔ | ✔ | ✘ | Vestidor web funcional con persistencia de calibración |
| CU20 | Generar reportes y dashboards | **95 %** | ✔ | ✔ | — (web) | Funcional, mejorado |
| CU21 | Recibir recomendaciones de IA | **80 %** | ✔ | ✔ | ✘ | Funcional (web), ALS offline |
| CU22 | Consultar asistente virtual/chatbot | **80 %** | ✔ | ✔ | ✘ | Funcional (web), con IA |
| CU23 | Generar reporte por voz/lenguaje natural | **90 %** | ✔ | ✔ | — (web) | Funcional, cubre ventas/inventario/movimientos |
| CU24 | Recibir notificaciones push | **0 %** | ✘ | ✘ | ✘ | No implementado (plus) |
| CU25 | Gestionar códigos promocionales | **90 %** | ✔ | ✔ | — (web) | Funcional |

**Promedio ponderado estimado del ciclo 3: ~71 %** (antes ~39 %, ~62 % y ~68 %).

Diagnóstico general: de los 7 CU del ciclo 3, **6 tienen implementación real en esta rama** (CU19 vestidor-RA, CU20 reportes/dashboards, CU21 recomendaciones IA, CU22 chatbot, CU23 reporte por lenguaje natural, CU25 códigos promocionales); solo **CU24 (notificaciones push) sigue sin código alguno** — sin modelo, servicio, endpoint ni pantalla. En este merge el salto lo da **CU19**: la calibración del vestidor ahora se persiste por variante en el backend (puntos 17/19 validados, endpoint `PATCH /variants/{id}/garment-points`) y el flujo web dejó de depender de `localStorage`; los dos detectores se movieron a plantillas externas con diálogos accesibles y el vestidor quedó solo en la página de detalle de producto. Aun así, el CU declara plataforma móvil exclusiva y la app móvil no tiene nada de cámara/RA; además, el backend de garment es un proxy de descarga de imagen (anti-SSRF) + persistencia de calibración, sin procesamiento RA. CU21 y CU22 siguen completos en web y pendientes solo del lado móvil. La app móvil sigue cubriendo catálogo, carrito, cuenta, órdenes y reservas, sin cámara, sin RA, sin notificaciones, y sin consumir recomendaciones ni chatbot.

---

## 2. Detalle por caso de uso

### CU19 – Usar vestidor virtual — 60 %

**Plataforma declarada:** Móvil (exclusivo). RA con cámara del dispositivo.

**Implementado (suma de los merges "new update with RA" `cae0dc3` y "new update, last details" `80f37bb`):** el vestidor web queda en estado funcional con calibración persistida en el servidor por variante, y la dependencia de `localStorage` se elimina del flujo.

**Backend (proxy de imagen + persistencia de calibración, sin procesamiento RA):**
- `POST /catalog/garment` (`backend/app/routes/garment_routes.py:13-22`), registrado en `main.py:67`. Devuelve la imagen de la prenda como data-URL base64 (`{image_data_url, mime_type}`). Protegido para **cliente** (`require_roles(RolEnum.cliente)`).
- `services/catalog_garment_service.py` (126 líneas): descarga segura de `source_url` con validación anti-SSRF (conexiones pinneadas a la IP resuelta, `_validate_source_url` exige IP pública global), rechazo de redirecciones, límite de 8 MB, solo `image/jpeg|png|webp|gif`, validación de MIME real.
- **Persistencia de calibración por variante (nuevo en `80f37bb`):**
  - Migración `backend/alembic/versions/0036_add_variant_garment_points.py`: añade `product_variants.garment_points` (`JSON`, nullable), con `downgrade` limpio.
  - Modelo `backend/app/models/product_variant.py`: columna `garment_points = Column(JSON, nullable=True)`.
  - API: `PATCH /variants/{variant_id}/garment-points` (`backend/app/routes/catalog_routes.py`) con `update_variant_garment_points` en `backend/app/services/catalog_service.py`; schema de validación `ProductVariantGarmentPointsUpdate` en `backend/app/schemas/catalog_schema.py`.
  - **Validación de coherencia:** `backend/tests/test_business_rules.py` (commit `dc1842a`) valida que los puntos sean 17 (19 en vestidos), con coordenadas normalizadas `x,y` en `[0,1]` y `null` permitido.
  - No hay modelo de RA nuevo: la imagen se reutiliza de la columna existente `product_variant.image_url`.
- **No hay procesamiento de RA en el backend:** el setting `gemini_garment_model` existe en `config.py:19` pero **no se usa en ningún lado** (el recorte de fondo/preparación con IA quedó como nombre de test: `test_generate_catalog_garment_returns_source_png_without_gemini`).
- **Tests:** los 2 unitarios originales (`backend/tests/test_catalog_garment_service.py`, 28 líneas: proxy sin Gemini y rechazo de URL malformada) más el de validación de puntos de calibración. No hay tests de ruta/rol ni de integración.

**Frontend web (vestidor montado en detalle de producto, calibración servida desde el backend):**
- **`app-virtual-try-on`** → sandbox externo Decart/Lucy VTON (`public/decart-try-on.html`, 1327 líneas): iframe con `allow="camera; microphone"`, WebRTC con el modelo `lucy-vton-latest`, envía la prenda vía `postMessage` (`virtual-try-on.component.ts:41-51`). Requiere `DECART_PUBLIC_KEY`/`decartApiKey` (vacía por defecto → pantalla de error) y la sesión se corta sola a los **5 segundos** (`decart-try-on.html:1214-1233`).
- **`app-detector-ropa`** y **`app-detector-mediapipe`** → dos motores **100 % locales** (cámara real `getUserMedia`, MediaPipe WASM `pose_landmarker_full.task` + `selfie_multiclass_256x256.tflite` vía CDN, warp afín triángulo a triángulo en `garment-overlay.renderer.ts`, calibración 17/19 puntos, sliders de fit). En `80f37bb`:
  - **Reciben `variantId` y `garmentPoints` como `@Input`** (`detector-mediapipe.component.ts:20-22`, igual en `detector-ropa`), cargan los puntos guardados del servidor y solo exigen calibrar cuando la variante no tiene puntos.
  - **`saveCalibration()` ahora persiste en el backend**: `CatalogApiService.updateVariantGarmentPoints(variantId, points)` → `PATCH /catalog/variants/{variantId}/garment-points` (`catalog-api.service.ts:218`, con `firstValueFrom`), y aplica la calibración al motor tras guardar.
  - **`garment-overlay.renderer.ts` elimina `localStorage`**: se quitaron `loadGarmentProfile`/`saveGarmentProfile`/`profileKey` y el `storageKey` de la malla; `GarmentCalibrationEditor` ahora recibe `serverPoints` y expone `getPoints()`, y `save(apply)` valida sin depender del navegador.
  - **`catalog.model.ts`** añade `Point` y `garment_points: Point[] | null` a `CatalogProductVariant`.
  - Las dos plantillas se movieron a `.html` externos (`detector-*component.html`, ~114 líneas) con **modal accesible** (`role="dialog"`, `aria-modal`, `aria-labelledby`) y detalles de calibrar/ajustar/cobertura.
  - **Montaje solo en detalle de producto** (`product-detail-page.component.html:94-100`): los 3 componentes se agrupan y pasan `variantId` + `garment_points`; la página de reservas **ya no monta el vestidor** (revertido el montaje por tarjeta de `reservations-page.component.html`, con ajuste responsive `grid-cols-[1.5fr_1fr]`).
- **Persistencia entre sesiones/navegadores:** al guardar la calibración en una variante con id, cualquier cliente web que cargue esa variante reutiliza los puntos sin recalibrar (criterio de aceptación del feature "variant garment points", documentado en `odd/tasks/variant-garment-points.md` — ODD-1 a ODD-7 ✅).
- **Limitaciones funcionales reales que persisten:** 1) exige prendas con **fondo transparente** (`garment-overlay.renderer.ts:147`) — las `image_url` reales de Cloudinary son fotos con fondo; 2) desajuste de versión MediaPipe (`package.json` `^1.0.1` vs wasm fijado a `0.10.21` en el renderer); 3) solo vista frontal y sin cálculo de talla real; 4) la variante Decart requiere clave pagada y se corta a los 5 s; 5) la calibración es **manual y por variante** (no hay generación de puntos en `seed.py`); 6) no hay guardar/compartir captura (pasos 7-8 del flujo CU19); 7) la página de reservas perdió el acceso al vestidor (lo eliminó en esta refactorización).

**App móvil (canal declarado):** **0 %**. `mobile/pubspec.yaml:30-39` solo declara `dio`, `flutter_secure_storage`, `flutter_stripe`; sin cámara, sin AR/ML Kit; `product_detail_page.dart` no tiene ninguna acción de "probar prenda". El `<<extend>> CU19 → CU10` no existe en móvil.

**Falta / a mejorar:**
1. La implementación está en **web**, pero el CU declara plataforma **móvil exclusiva** — la pieza móvil (cámara + AR) queda entera por hacer.
2. El backend es solo un proxy seguro de descarga de imagen + persistencia de calibración; el "procesamiento IA/recorte de fondo" declarado en `config.py` (`gemini_garment_model`) no está implementado.
3. Prendas con fondo transparente obligatorio (incompatibilidad con el catálogo real), desajuste de versión MediaPipe, y modo Decart dependiente de clave + límite de 5 s.
4. Sin guardado/compartición de captura ni cálculo de talla real, y el vestidor ya no aparece en la página de reservas.
5. Fase 8 (`IMPLEMENTATION_PHASES.md:160`): "Preparar base para vestidor virtual" sin marcar.

**Requisitos técnicos para completarlo:** portar el vestidor a Flutter (plugin `camera` + overlay de `image_url` sobre el frame, o ML Kit para pose), preparar/cambiar las imágenes de prendas a fondo transparente, implementar o eliminar la promesa de recorte IA en el backend, y los pasos de guardar/compartir del flujo del CU.

---

### CU20 – Generar reportes y dashboards — 95 %

**Plataforma declarada:** Web (Administrador).

**Implementado (backend + frontend), sin cambios funcionales en este merge:**
- **Reportes tabulares y exportación:** `GET /reports/sales`, `GET /reports/sales/export`, `GET /reports/inventory`, `GET /reports/inventory/export`, `GET /reports/movements`, `GET /reports/movements/export` (`backend/app/routes/report_routes.py:79-151`), con filtros por sucursal, producto, variante, rango de fechas y texto (`services/report_service.py`). Exportación CSV real (`export_rows_to_csv`).
- **Acceso por rol con alcance:** los reportes aceptan **administrador y encargado**; el encargado queda **restringido a su sucursal** (`_scoped_filters`, `report_routes.py:65-76`).
- **Dashboard:** `GET /dashboard` (`dashboard_routes.py:27`) con summary, series de ventas y movimientos por periodo (day/week/month), KPIs por sucursal, top productos y alerta de stock bajo. Protegido solo para administrador.
- **Gráficas reales:** `angular-chrts` + `@unovis/ts` (AreaChart, BarChart, DonutChart) en `admin-home-page.component.ts:13,26`.
- **Exportación PDF/HTML/CSV desde la UI:** `simple-pdf.util.ts` (jsPDF + autotable) usada por `sales-history-page.component.ts` y `admin-inventory-page.component.ts`.
- **Frontend:** `sales-history-page.component.ts` (rutas `admin/sales`, `encargado/sales`, `cajero/sales`), `admin-inventory-page.component.ts` (rutas `admin/inventory`, `encargado/inventory`) y `admin-home-page.component.ts` (ruta `admin/`).

**Falta / a mejorar:**
1. **El dashboard no tiene exportación propia** (PDF/CSV directo del dashboard); la exportación existe solo en los reportes tabulares.
2. **Alertas de indicador crítico no proactivas.** El dashboard detecta stock bajo (`low_stock`) pero solo lo muestra en pantalla; la relación `<<extend>> CU20 → CU24` no existe porque CU24 no está implementado.
3. **Agregación por periodo solo en el dashboard**.
4. Fase 8 (`IMPLEMENTATION_PHASES.md:158`): "Construir reportes y dashboards" sin marcar, pese a estar implementado.

No hay nada bloqueante funcional: el CU se considera operativo.

---

### CU21 – Recibir recomendaciones de IA — 80 %

**Plataforma declarada:** Ambas (web + móvil). Sugerencias según historial, temporada y disponibilidad. **Interfaz resuelta de facto:** sección "Recomendaciones para ti" integrada dentro del catálogo del cliente (web), lo que confirma el `<<extend>> CU21 → CU10` que estaba pospuesto en la nota 5.6 del documento de CU.

**Implementado (backend + frontend web), nuevo en esta revisión:**

- **Modelo de datos (2 tablas nuevas, migraciones `0031` y `0032`):**
  - `user_product_interactions`: registra vistas, carrito y compras por cliente con `interaction_type` (`view`=1, `add_to_cart`=2, `completed_order`=5), `weight`, y contexto `variant_id` + `branch_id` (añadidos en `0032`). Llave única por `order_id+product_id+interaction_type` (`app/models/recommendation.py:10-25`).
  - `collaborative_embeddings`: persistencia de los vectores latentes entrenados (`subject_type` user/product, `vector` JSON, único por sujeto) (`app/models/recommendation.py:28-36`).
- **Servicio ALS offline real (`services/recommendation_service.py`, 283 líneas, usa `numpy`):**
  - **Entrenamiento:** `_implicit_als` implementa factorización por **Alternating Least Squares implícito** (`alpha=40`, `factors=16`, `iterations=10`, `regularization=0.1`) con `np.linalg.solve` (`recommendation_service.py:88-119`). Se agregan las interacciones por usuario×producto (`aggregate_interactions`) y se persisten los embeddings en `collaborative_embeddings`. Se entrena offline con `python -m app.services.recommendation_service` (`train`).
  - **Consumo:** `get_recommendations` filtra productos activos con stock disponible (`_eligible_product_ids`, opcional por sucursal), excluye lo ya comprado, y hace ranking con el producto escalar euclidiano entre el vector del usuario y el de cada producto, re-ordenado con un boost de afinidad por historial (`_history_affinity`: categoría, colección, temporada, talla, color, sucursal, con tope 0.25).
  - **Fallback** para usuarios sin historia: `_popular_recommendations` (productos más ponderados) + afinidad — `logic_type: "popular_fallback"`.
  - Devuelve `logic_type` (`implicit_als` | `popular_fallback`), `user_id` y lista `{product_id, score}`.
- **Endpoint:** `GET /recommendations/collaborative/user/{user_id}` (`routes/recommendation_routes.py:16-35`), protegido para **cliente**, con validación de que el cliente solo consulte sus propias recomendaciones (403 si no coincide el id) y `branch_id` opcional.
- **Registro de interacciones en el flujo real (sin fricción):**
  - **Vistas:** `POST /catalog/products/{product_id}/view` (`catalog_routes.py:286-298`) llamado desde la UI web al ver un producto en el catálogo.
  - **Carrito:** `record_interaction(ADD_TO_CART)` al agregar un ítem (`cart_service.py`), con variante y sucursal.
  - **Pedidos completados:** `record_completed_order_interactions` al consumir un pedido (`order_service._consume_order`), idempotente por orden+producto+tipo.
- **Seed con datos demo:** `RECOMMENDATION_DEMO_INTERACTIONS` en `seed.py` (10 clientes × 8 productos, con vistas/carrito/compras diseñadas para que aparenten clientes similares) y carga de interacciones.
- **Pruebas:** `backend/tests/test_recommendation_service.py` (7+ tests): agregación de pesos, ranking de embeddings excluyendo comprados y desempate por id, seed coherente, elegibilidad por stock, afinidad acotada, dueño de recomendaciones, y populares.
- **Frontend web (catálogo del cliente):**
  - `catalog-page.component.ts/html`: carrusel **"Recomendaciones para ti — Inspirado en tus gustos y compras anteriores"** (`catalog-page.component.html:131-172`) que llama a `getCollaborativeRecommendations(userId)` y `recordProductView(productId)` al ver/agregar productos (`catalog-api.service.ts`).
  - Modelo tipado `CollaborativeRecommendation(s)` con `logic_type` (`catalog.model.ts:61-69`).
- **Página de detalle de producto (apoyo al flujo CU10/CU21):** `GET /catalog/products/{product_id}` público con inventario disponible por sucursal (`catalog_service.get_public_product`), página web `product-detail-page.component.ts` en ruta `cliente/products/:productId` (`app.routes.ts:60-62`), a la que llegan las recomendaciones del catálogo y del chatbot.

**Falta / a mejorar:**
1. **App móvil sin consumir recomendaciones.** El backend y la web están listos; la app móvil no llama a `/recommendations/...` ni muestra la sección "Para ti". Con esa pieza, el CU llegaría a ~95 %+.
2. **Entrenamiento manual:** los embeddings se entrenan con un comando aparte (`python -m app.services.recommendation_service`); no hay job/scheduler que lo ejecute periódicamente ni se dispara tras cada compra (se recomienda al menos tras el seed y con frecuencia baja).
3. **`numpy` no está déclarado en `requirements.txt`** (llega como dependencia transitiva de `pandas`, que sí está). Debe añadirse explícitamente, ya que `recommendation_service.py` y sus tests lo importan.
4. **Cold start de productos nuevos:** un producto sin interacciones ni compras tiene vector inicial y aparece solo si cae en el fallback popular; el formulario de preferencias/feedback que se evaluó (nota 5.6) aún no alimenta la matriz como dato explícito.
5. Fase 8 (`IMPLEMENTATION_PHASES.md:159`): "Preparar base para recomendaciones IA" sin marcar.

**Requisitos técnicos restantes:** declarar `numpy`, automatizar el reentrenamiento (p. ej. tarea programada diaria), y exponer las recomendaciones en la app móvil.

---

### CU22 – Consultar asistente virtual/chatbot — 80 %

**Plataforma declarada:** Ambas (web + móvil). Resolución de dudas del cliente sobre productos.

**Implementado (backend + frontend web), nuevo en esta revisión:**

- **Modelo de datos (3 tablas nuevas + 1 columna, migraciones `0033`, `0034`, `0035`):**
  - `user_body_profiles`: perfil corporal del cliente (tallas arriba/abajo, número de calzado, tipo de cuerpo, preferencia de calce, notas), uno por usuario (`app/models/user_profile.py`).
  - `conversations`: una conversación persistida por usuario (`app/models/conversation.py`).
  - `conversation_messages`: mensajes `user`/`assistant` con check constraint de rol, más `message_data` (JSON) para las tarjetas de producto (migración `0035`) (`app/models/conversation_message.py`).
- **Rutas** (`routes/chatbot_routes.py`, protegidas para **cliente**):
  - `POST /chatbot/message` → procesa el mensaje y guarda la conversación.
  - `GET /chatbot/messages` → historial de la conversación.
  - `DELETE /chatbot/conversation` → reinicia la conversación.
- **Servicio `services/chatbot_service.py` (590 líneas):**
  - **Intents** `CATALOGO | PEDIDOS | POLITICAS | USO_SISTEMA` (`schemas/chatbot_schema.py`).
  - **Enrutamiento híbrido:** clasificación determinista por palabras clave (`_classify_explicit`) y, si hay `GEMINI_API_KEY`, enrutamiento con Gemini (`route_intent`) que solo devuelve `{"intent": ...}` acotado a las 4 salidas, con fallback determinista ante error/ausencia de clave.
  - **CATALOGO:** contexto real de la BD (`_catalog_candidates` con variantes activas, stock disponible, talla, color, temporada, precio, descuento); selección de hasta 4 variantes con Gemini (o scoring local) y respuesta con **tarjetas de producto** (`_catalog_answer` + `message_data`) que el frontend renderiza con botón "Ver producto".
  - **PEDIDOS:** contexto de los pedidos del usuario autenticado (hasta 20, con etiquetas en español, sin UUIDs) para que Gemini responda con datos reales.
  - **POLITICAS / USO_SISTEMA:** conocimiento estático local (`core/data/policies.json`, `core/data/system_info.json`).
  - **Perfil corporal:** extrae y persiste tallas/tipo de cuerpo mediante regex (`extract_profile_updates`, `upsert_profile`), pregunta si no hay perfil y lo usa para personalizar las recomendaciones de catálogo.
  - **Gestión de contexto de conversación** con `conversation_service.py` (recupera antecedentes, hereda intent previo, asocia respuestas a la conversación persistida).
  - Respuesta por Gemini cuando la clave existe; `_fallback` local (texto con productos/pedidos/políticas) cuando no.
- **Pruebas:** `backend/tests/test_chatbot_service.py` (26 tests de contrato: clasificación de intents, extracción de perfil, contextos, fallback sin Gemini, prompts de router/selector, validaciones de `ChatRequest`) más los de `conversation_service`.
- **Frontend web (cliente):**
  - Componente flotante `chatbot.component.ts/html` (ícono flotante, lista de mensajes, estados enviando/error, reintento, confirmación para borrar conversación, atajo Enter) montado en `app-shell.component.html:85`.
  - Render de **tarjetas de producto** con "Ver producto" → navega a la página de detalle (`openRecommendation`, ruta `cliente/products/:productId`).
  - Servicios `chatbot-api.service.ts` y `chatbot-ui.service.ts` (este último permite cerrar el chat desde otras vistas, p. ej. al abrir un producto).

**Falta / a mejorar:**
1. **App móvil sin chatbot.** Falta la pantalla/pieza móvil equivalente (queda pendiente la mitad declarada "móvil").
2. **Dependencia opcional de Gemini:** sin `GEMINI_API_KEY` el chatbot degrada a fallback local (funcional pero menos natural); con clave depende de la disponibilidad del modelo externo.
3. Fase 8 (`IMPLEMENTATION_PHASES.md:161`): "Preparar asistente virtual si entra en alcance" sin marcar, pese a estar implementado.

**Requisitos técnicos restantes:** componente chatbot en la app móvil (Flutter) reutilizando `POST/GET/DELETE /chatbot/*`, y marcar la tarea de la Fase 8.

---

### CU23 – Generar reporte por voz/lenguaje natural — 90 %

**Plataforma declarada:** Web (Administrador). Canal alternativo de CU20 vía comando de voz (`<<extend>> CU23 → CU20`).

**Implementado (backend + frontend), sin cambios funcionales en este merge:**
- **Backend con Gemini:** `POST /reports/query` (`report_routes.py:25-35`), protegido para administrador, implementado en `services/natural_report_service.py` (169 líneas). Clasifica `sales | inventory | movements`, interpreta sucursal/producto/variante, fechas relativas, columnas (con mapeo español y corrección "cku"/"sku") y formato (`pdf`/`csv`/`html`); valida contra catálogos reales y reutiliza los reportes de CU20.
- **Soporte de columnas por tipo de reporte:** `schemas/report_schema.py` define `AllowedReportColumn` (14 claves), y los defaults de ventas/inventario/movimientos (`DEFAULT_*_REPORT_COLUMNS`); el servicio aplica las columnas por defecto de cada tipo.
- **Pruebas de contrato:** `backend/tests/test_natural_report_contract.py` (5 tests).
- **Frontend con Web Speech API en dos pantallas:** `sales-history-page.component.ts` (ventas, `report_type === 'sales'`) y `admin-inventory-page.component.ts` (inventario y movimientos, `report_type === 'inventory' || 'movements'`), ambas con dictado nativo `es-BO` y descarga PDF/HTML/CSV.

**Falta / a mejorar:**
1. **Dependencia de API key de Gemini:** sin `GEMINI_API_KEY` el endpoint devuelve `503`.
2. Fase 8 no contempla tarea explícita para CU23 en `IMPLEMENTATION_PHASES.md`.
3. La entrada por voz depende del navegador (Web Speech API no disponible en todos); el textarea es el respaldo.

**Requisitos técnicos restantes:** documentar el cierre en la Fase 8; opcionalmente permitir dictado en el dashboard.

---

### CU24 – Recibir notificaciones push — 0 %

**Plataforma declarada:** Móvil. Funcionalidad **plus** del equipo (sin RF numerado de origen). Actores: Administrador, Cliente, Encargado de sucursal.

**Implementado:** nada (sin cambios respecto a la revisión anterior).

**Evidencia de lo que falta:**
1. **No existe infraestructura de push en el backend:** ningún router (`/notifications`, `/devices`, `/subscribe`), ningún modelo/tabla de dispositivos o tokens, y ninguna dependencia de Firebase/APNs/WebPush en `requirements.txt` o `config.py`.
2. **No hay generación de eventos** en los CU que lo disparan: `reservation_service.py`, `inventory_service.py`, `order_service.py`, `sales_service.py`, `catalog_service.py` y `dashboard_service.py` no emiten ninguna notificación.
3. **App móvil:** no hay `firebase_messaging`, `flutter_local_notifications` ni plugin similar en `mobile/pubspec.yaml`; no hay manejo de permisos ni de token de dispositivo.
4. **Frontend web:** sin Service Worker ni Push API (las coincidencias de "push" en el código son llamadas a `Array.push` de formularios).

**Requisitos técnicos para completarlo:** alta de proveedor de push (p. ej. FCM), modelo de `device_token`/suscripciones por usuario, endpoints de suscripción/desuscripción, servicio emisor, puntos de emisión en los servicios mencionados y la capa de recepción en la app móvil. Al ser plus de alto riesgo, puede tratarse como POC/extra.

---

### CU25 – Gestionar códigos promocionales — 90 %

**Plataforma declarada:** Web. Actores: Administrador, Encargado de sucursal. Ampliación solicitada por la docente (sin RF numerado de origen).

**Implementado (backend + frontend), sin cambios funcionales en este merge:**
- **Backend:** `GET /promotions` y `POST /promotions` (`promotion_routes.py:17-43`), protegidos para administrador y encargado: el administrador solo crea códigos **globales** (`branch_id` nulo, 400 si lo acota); el encargado solo crea/listan códigos de **su propia sucursal** (403/400 en caso contrario).
- **Contratos y validaciones** (`schemas/promotion_schema.py`): código normalizado a mayúsculas (3-40), tipo `percentage | fixed`, valor > 0, porcentaje ≤ 100, vigencia opcional con validación de orden y normalización UTC.
- **Servicio** (`services/promotion_service.py`): `create_code`, `list_codes`, `validate_for_user`, `calculate_discount` y `add_usage`. La **aplicación en el carrito ya existía** desde el ciclo previo (CU15): `POST /cart/coupon` y `DELETE /cart/coupon` (+ modelos `PromotionCode` y `PromotionCodeUsage`).
- **Frontend:** `promotions-page.component.ts` (shared) con listado y modal de creación, en rutas `admin/promotions` (`app.routes.ts:183-185`) y `encargado/promotions` (`app.routes.ts:116-119`). Servicio `promotion-api.service.ts` y modelo `promotion.model.ts`.

**Falta / a mejorar:**
1. **Solo crear y consultar**, sin edición ni desactivación desde la UI (el backend sí conserva `is_active` y `valid_until`).
2. Sin cambios de estado del código ni historial de usos visible al administrador.
3. Fase 8 no lista CU25.

No hay nada bloqueante: el CU se considera operativo para el flujo crear/listar/aplicar.

---

## 3. Brechas transversales

1. **1 de 7 CU del ciclo 3 sigue sin ninguna implementación: CU24 (notificaciones push)**, dependiente de la app móvil. El backend es completo para los ciclos 1-2 y para CU19 (proxy + calibración), CU20/CU21/CU22/CU23/CU25.
2. **CU19 implementado en web, aunque declara plataforma móvil exclusiva.** Los 3 componentes de vestidor (Decart + 2 motores MediaPipe locales) están montados solo en el detalle de producto; la calibración se persiste por variante en el backend (migración `0036`, `PATCH /variants/{id}/garment-points`, validación 17/19 puntos en `[0,1]`) y `localStorage` quedó fuera del flujo; la app móvil no tiene cámara ni AR, y el backend de garment es solo un proxy de imagen + persistencia, sin procesamiento RA.
3. **App móvil funcional pero sin las capacidades del ciclo 3.** Cubre catálogo, carrito, perfil/órdenes/reservas y checkout (Stripe), pero no tiene cámara/RA (CU19), no consume recomendaciones (CU21), no tiene chatbot (CU22), ni notificaciones push (CU24). No hay plugins de cámara, AR, firebase ni local notifications en `pubspec.yaml`.
4. **Fase 8 de `IMPLEMENTATION_PHASES.md` desactualizada**: las 4 tareas figuran `[ ]` (`IMPLEMENTATION_PHASES.md:158-161`) aunque reportes/dashboards (CU20), reporte por lenguaje natural (CU23), recomendaciones (CU21), asistente virtual (CU22) y vestidor virtual (CU19) ya están implementados (al menos parcialmente); CU25 tampoco aparece en esa fase. El commit `e8eb6fd` agrega Dockerfiles (backend/frontend) y el merge `80f37bb` la persistencia de calibración, pero ninguno toca esta fase.
5. **Cobertura de pruebas moderada:** `test_business_rules.py`, `test_natural_report_contract.py` (5), `test_recommendation_service.py` (8), `test_chatbot_service.py` (26) + `test_conversation_service.py` (5), y `test_catalog_garment_service.py` (solo 2). Faltan tests de los servicios de reportes/dashboard/promociones e integración de rutas (roles) y de los motores de RA.
6. **CU21/CU22/CU23 dependen (parcial u opcionalmente) de un servicio externo (Gemini).** CU21 es el único 100 % local/offline (ALS con `numpy`); CU22 funciona en modo degradado sin la clave; CU23 requiere la clave sí o sí. **`numpy` no está declarado en `requirements.txt`** (llega como transición de `pandas`) y es obligatorio para CU21.
7. **CU21 declara "ambas" plataformas pero solo está en web.** La web ya expone la sección "Recomendaciones para ti"; el móvil no la consume.
8. **Entrenamiento de embeddings sin automatizar** (CU21): depende de ejecutar manualmente `python -m app.services.recommendation_service`.
9. **CU19 requiere prendas con fondo transparente** (`garment-overlay.renderer.ts:147`) — incompatibilidad con las `image_url` reales del catálogo, desajuste de versión de MediaPipe, sandbox Decart con clave y límite de 5 s, y calibración manual sin seed de puntos.

---

## 4. Prioridad de los trabajos pendientes

1. **CU19**: portar el vestidor a la app móvil (cámara + overlay), preparar prendas con fondo transparente, e implementar o eliminar el recorte IA prometido en el backend. Es el CU con el mayor delta recién agregado (vestidor web funcional con calibración persistida) pero que sigue sin cumplir su canal declarado; opcionalmente, devolver el acceso al vestidor en la página de reservas.
2. **CU21**: declarar `numpy` en `requirements.txt`, programar el reentrenamiento de embeddings, y exponer "Para ti" en la app móvil. El CU web ya es funcional y es además 100 % local/offline, lo que lo hace la pieza de IA más robusta del ciclo.
3. **CU22**: añadir el componente chatbot a la app móvil reutilizando `POST/GET/DELETE /chatbot/*`; documentar el cierre de la Fase 8.
4. **CU20 / CU23 / CU25**: marcar tareas en la Fase 8; opcionalmente exportación directa del dashboard (CU20) y dictado en dashboard (CU23).
5. **CU24**: tratar como plus/POC (FCM + registro de tokens + al menos 2 eventos: stock bajo y reserva nueva).

Prioridad sugerida por impacto y esfuerzo: **CU19 (móvil) → CU21 (móvil + entrenamiento) → CU22 (móvil) → CU24**, con los cierres de Fase 8 de CU20/CU23/CU25 en paralelo (trabajo de documentación de bajo esfuerzo).