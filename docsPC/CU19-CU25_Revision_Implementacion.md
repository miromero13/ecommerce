# Revisión de Implementación – Casos de Uso CU19–CU25

Revisión: 2026-09-19
Alcance: evaluación del estado real de implementación (backend + frontend web + mobile) de los casos de uso **CU19 a CU25** descritos en `Casos_de_Uso_WomenStyle (1).md`.

> **Nota sobre el ciclo:** el documento de origen ubica a CU19–CU25 en el **Ciclo 3** (Realidad Aumentada, IA, Reportes avanzados, Notificaciones y Promociones). Si el equipo se refiere a este grupo como "Ciclo 4", la cobertura es idéntica: los mismos 7 CU (CU19–CU25). En esta revisión se mantiene la numeración oficial de casos de uso para evitar ambigüedades.

> **Nota previa:** a diferencia de la revisión del Ciclo 2 (`CU11-CU18_Revision_Implementacion.md`), en este repositorio **sí existe** la app móvil (`mobile/`, Flutter) que cubre flujos del Ciclo 1 y 2 (auth, catálogo, carrito, pedidos, reservas, perfil). Sin embargo, **ninguno** de los CU de este grupo dependientes de móvil (CU19, CU24) está implementado en ella, y CU21/CU22 (plataforma "Ambas") solo existen en la variante web.

---

## Resumen ejecutivo

| ID | Caso de uso | Actor | Backend | Frontend (web) | Mobile | Nivel estimado |
|---|---|---|---|---|---|---|
| CU19 | Usar vestidor virtual | Cliente | 0% (no aplica) | — (CU de móvil) | 0% | **0%** |
| CU20 | Generar reportes y dashboards | Administrador | 100% | ~95% | — (web) | **~95%** |
| CU21 | Recibir recomendaciones de IA | Cliente | ~95% | ~80% | 0% | **~75%** |
| CU22 | Consultar asistente virtual/chatbot | Cliente | ~95% | ~85% | 0% | **~80%** |
| CU23 | Generar reporte por voz/lenguaje natural | Administrador | ~95% | ~90% | — (web) | **~90%** |
| CU24 | Recibir notificaciones push | Admin, Cliente, Encargado | 0% | — (CU de móvil) | 0% | **0%** |
| CU25 | Gestionar códigos promocionales | Administrador, Encargado | 100% | ~90% | ~60% (aplicación del cupón) | **~92%** |

**Estado global: ~62%** (5 de 7 CU implementados en forma completa/mayoritaria: CU20, CU21, CU22, CU23 y CU25). Los 2 restantes (CU19 y CU24) están **sin implementar** en ninguna capa.

Leyenda: **0%** = no existe código que materialice el caso de uso; **~X%** = implementado con brechas menores.

---

## CU19 – Usar vestidor virtual *(Cliente; Móvil)*

**Implementado:** nada.

**Falta (todo):**
- **Mobile:** no existe feature de vestidor virtual ni integración de cámara. El `pubspec.yaml` de `mobile/` solo incluye `dio`, `flutter_secure_storage` y `flutter_stripe`; no hay dependencias de RA (p. ej. `camera`, `ar_flutter_plugin`, `google_mlkit_pose`) ni de modelos 3D.
- **Backend:** no hay capa de servicio para la visualización AR (la visualización es client-side) ni endpoint de soporte (p. ej. servir imágenes/modelos 3D de prendas para el overlay).
- La plataforma del CU es **exclusivamente móvil**, por lo que la ausencia en `mobile/` implica 0% completo.

**Estado: No implementado (0%).**

---

## CU20 – Generar reportes y dashboards *(Administrador; Web)*

**Implementado:**
- **Backend – Dashboard:**
  - `GET /api/dashboard` (solo admin) en `backend/app/routes/dashboard_routes.py:28`.
  - `dashboard_service.py` (`get_dashboard`) agrega: resumen (ventas, órdenes, unidades, ticket promedio, stock, reservas por estado), serie de ventas por periodo (día/semana/mes), serie de movimientos de inventario (ingreso/salida/traspaso), movimientos por sucursal, KPIs por sucursal, top productos y stock bajo (`low_stock`).
  - `dashboard_schema.py` con tipos `DashboardSummary`, `DashboardBranchKpi`, `DashboardProductKpi`, `DashboardSeriesPoint`, `DashboardMovementPoint`, `DashboardInventoryPoint`.
- **Backend – Reportes:**
  - `GET /api/reports/sales`, `GET /api/reports/inventory`, `GET /api/reports/movements` (`report_routes.py`) con filtros por `branch_id`, `product_id`, `variant_id`, `from_date`, `to_date`, `q`.
  - Exportación CSV en `/api/reports/{sales|inventory|movements}/export`. Los endpoints de cuentas también hacen scoping por sucursal cuando el usuario es encargado.
  - Los reportes distinguen `type` (presencial / online), útil para CU23.
- **Frontend – Dashboard:**
  - `features/admin/pages/admin-home-page.component.ts` + `.html`: tarjetas de resumen y gráficos (ventas por periodo, top productos, desempeño por sucursal, distribución de movimientos) con filtro de sucursal y periodo (día/semana/mes) usando `angular-chrts`.
  - Modelo y servicio: `shared/models/dashboard.model.ts` y `shared/services/dashboard-api.service.ts`.
- **Frontend – Reportes con exportación:**
  - `shared/pages/sales-history-page.component.ts` (roles admin, encargado, cajero) y `admin-inventory-page.component.ts` (admin/encargado): modal "Generar reporte" con filtros, selección de columnas y formato (**PDF / HTML / CSV**).
  - Exportación PDF con jsPDF + autotable (`core/utils/simple-pdf.util.ts`), HTML descargable y CSV con BOM (Excel-friendly).

**Observaciones / brechas menores:**
- El CU22 de notificaciones (indicador crítico en dashboard) no está conectado (ver CU24).
- Sin versión móvil definida para el dashboard (plataforma Web), no aplica.

**Estado: Implementado (~95%).**

---

## CU21 – Recibir recomendaciones de IA *(Cliente; Ambas)*

**Implementado (backend):**
- Método **colaborativo** con embeddings ALS implícitos: modelos `UserProductInteraction` y `CollaborativeEmbedding` (`app/models/recommendation.py`), entrenamiento persistido vía `python -m app.services.recommendation_service`.
- `app/services/recommendation_service.py`: `record_interaction` (tipos `view` / `add_to_cart` / `completed_order` con pesos), agregación, `get_recommendations` (embedding ALS + afinidad por categoría/colección/temporada/talla/color/sucursal + fallback a productos populares) y `validate_recommendation_owner` (el cliente solo ve sus propias recomendaciones).
- Telemetría conectada: vista de producto → `POST /catalog/.../view` (`catalog_routes.py:296`), añadir al carrito → `cart_service.py:155`, completar pedido → `order_service.py:296`.
- Ruta `GET /api/recommendations/collaborative/user/{user_id}` con contexto opcional de sucursal y restricción de rol cliente (`recommendation_routes.py`).
- Seed con demo de interacciones y tests (`test_recommendation_service.py`).

**Implementado (frontend web):**
- `cliente/pages/catalog-page.component.ts` + `.html`: bloque **"Recomendaciones para ti"** (`recommendedProducts`, `loadRecommendations`) visible solo para rol cliente; llama `getCollaborativeRecommendations(user.id, { branch_id })` y enlaza cada producto a su página de detalle; `recordProductView` se dispara al agregar al carrito (telemetría) y recarga las recomendaciones.

**Falta:**
- **Mobile:** no existe versión de recomendaciones en la app Flutter (la plataforma declara "Ambas"; la implementación actual es solo web).

**Estado: Implementado (~75%).**

---

## CU22 – Consultar asistente virtual/chatbot *(Cliente; Ambas)*

**Implementado (backend):**
- Modelos `Conversation` y `ConversationMessage` (`app/models/conversation.py`, `conversation_message.py`) y `conversation_service.py` (conversación por cliente, historial, borrado).
- `app/services/chatbot_service.py`: enrutamiento de **intención con Gemini** (`route_intent`) y fallback heurístico (`classify_intent`) sobre 4 intents — `CATALOGO` (búsqueda/recomendaciones con contexto de catálogo y perfil), `PEDIDOS` (pedidos del usuario), `POLITICAS`, `USO_SISTEMA` —, conocimiento estático (`core/data/policies.json`, `system_info.json`) y aprendizaje de perfil corporal (`extract_profile_updates` / `upsert_profile` sobre `UserBodyProfile`).
- El enrutador solo expone el destino (intent); el prompt no incluye contenido de catálogo/pedidos/estáticos salvo cuando aplica, y prioriza el mensaje actual sobre el historial.
- Rutas: `POST /chatbot/message`, `GET /chatbot/messages`, `DELETE /chatbot/conversation` (restrictiva a rol cliente) en `chatbot_routes.py`.
- Tests: `test_chatbot_service.py`, `test_conversation_service.py`.

**Implementado (frontend web):**
- `features/shared/components/chatbot.component.ts` + `.html`: widget flotante **"Asistente de compras"** con historial, envío, reintentar mensajes fallidos, borrado de conversación y navegación a recomendaciones de producto; montado en `app-shell.component.html` (`<app-chatbot />`).
- `features/shared/services/chatbot-api.service.ts` (`sendMessage`, `getMessages`, `resetConversation`).

**Falta:**
- **Mobile:** no existe chatbot en la app Flutter (plataforma declara "Ambas"; la implementación actual es solo web).
- El motor de respuestas depende de `google-genai` y de `gemini_api_key` en el entorno; sin clave, cae al enrutador heurístico (fallback correcto).

**Estado: Implementado (~80%).**

---

## CU23 – Generar reporte por voz/lenguaje natural *(Administrador; Web)*

**Implementado (backend):**
- `POST /api/reports/query` (restringido a rol **administrador**) en `report_routes.py:26` → `generate_natural_report` en `services/natural_report_service.py`.
- Interpretación con **Gemini** (salida JSON estructurada `NaturalReportInterpretation`): determina `report_type` (sales/inventory/movements), formato (pdf por defecto, html, csv), columnas solicitadas (mapea nombres en español y errores de transcripción "cku"/"sku" → `variant_sku`), fechas relativas respecto al día del servidor y selección de sucursal/producto/variante solo desde catálogos reales.
- Validación de filtros interpretados (entidad inexistente → 422 `unmatched_entity`, rangos de fechas razonables). Reutiliza los reportes de **CU20** (`get_sales_report`, `get_inventory_report`, `get_movements_report`).
- Manejo de errores con códigos claros: 503 sin `gemini_api_key`, 504 timeouts, 502 fallo de Gemini, 422 solicitudes inválidas, 500 al ejecutar el reporte. Validación de longitud (≤500) y vacíos.
- Schemas `NaturalReportRequest`, `NaturalReportInterpretation`, `NaturalReportPayload` y tests (`test_natural_report_contract.py`).

**Implementado (frontend web):**
- `features/shared/pages/sales-history-page.component.ts` y `features/admin/pages/admin-inventory-page.component.ts`: campo de **consulta en lenguaje natural** con botón de micrófono usando la **Web Speech API** (`SpeechRecognition`/`webkitSpeechRecognition`, idioma `es-BO`) → transcribe y rellena la consulta; `generateNaturalReport()` llama `/reports/query`, interpreta la respuesta, rellena el modal con filtros/columnas detectados y exporta en **PDF / HTML / CSV** (`downloadSimplePdf` con jsPDF + autotable).
- Guardas por tipo: la pantalla de ventas solo acepta `report_type === 'sales'`; la de inventario solo `inventory` o `movements`.

**Observaciones / brechas menores:**
- El canal de **voz** depende de la Web Speech API del navegador; sin ella, el campo permite escribir la consulta (fallback correcto).
- Plataforma Web declarada; no hay brecha de mobile.

**Estado: Implementado (~90%).**

---

## CU24 – Recibir notificaciones push *(Admin, Cliente, Encargado; Móvil)*

**Implementado:** nada.

**Falta (todo):**
- **Mobile:** no existe integración con servicio push (FCM/APNs). El `pubspec.yaml` no incluye `firebase_messaging` ni similar; no hay feature de notificaciones ni registro de tokens de dispositivo.
- **Backend:** no existe servicio de notificaciones, ni tabla de tokens o de eventos pendientes de notificación (búsqueda de `notification`/`fcm`/`push` en `backend/app` sin resultados). Los disparadores definidos en el documento (`<<include>>` con CU14 y `<<extend>>` con CU12, CU16, CU17, CU07, CU20) no generan ninguna notificación:
  - No se avisa al encargado al crear una reserva.
  - No se avisa a admin/encargado por stock bajo (aunque existe el umbral `minimum_stock` y el dashboard `low_stock`).
  - No se notifica al cliente por cambios de estado del pedido, preparación de reserva ni nuevos productos.
- Nota: varios eventos de negocio ya existen en backend (cambio de estado de orden/reserva, movimientos de inventario, publicación de productos), por lo que la **base de disparadores** está presente pero **desconectada** de cualquier canal de notificación.

**Estado: No implementado (0%).**

---

## CU25 – Gestionar códigos promocionales *(Administrador, Encargado; Web)*

**Implementado (backend):**
- Modelo `PromotionCode` (`promotion_code.py`) con `code`, `discount_type` (percentage/fixed), `discount_value`, `valid_from`, `valid_until`, `branch_id` (alcance global o por sucursal), `is_active`, `created_by`. Modelo de uso único `PromotionCodeUsage`.
- `GET /api/promotions` y `POST /api/promotions` en `promotion_routes.py` con scoping por rol:
  - Admin: crea y ve **códigos globales** (rechaza `branch_id`).
  - Encargado: ve y crea **códigos de su sucursal** (403 si intenta otro).
- `promotion_service.py`: `create_code`, `list_codes`, `validate_for_user`, `calculate_discount`, `add_usage`.
- **Aplicación en el flujo de compra (CU15):** `cart_service.py` integra cupón (`apply_coupon`/`remove_coupon`), valida vigencia, alcance por sucursal y uso único por usuario, y recalcula totales (`refresh_cart_totals`). Rutas en `cart_routes.py`.

**Implementado (frontend web):**
- `shared/pages/promotions-page.component.ts` + `.html`: listado de códigos y modal de creación (código, tipo de descuento, valor, calendario de vigencia, "Sin vencimiento"), consciente del rol (admin: globales; encargado: sucursal).
- Rutas: `/app/admin/promotions` y `/app/encargado/promotions` en `app.routes.ts`.
- Aplicación del cupón en el carrito web: `cliente/pages/cart-page.component.ts` + `.html` (campo de código + apply/remove).

**Implementado (mobile – aplicación del cupón):**
- `mobile/lib/features/cart/cart_page.dart` (campo cupón, mostrar cupón aplicado y total con descuento) y `cart_controller.dart`/`cart_api.dart` (`applyCoupon`/`removeCoupon` contra `cart/coupon`).
- Corrección respecto a revisiones anteriores: la **aplicación del cupón en el carrito móvil sí existe** desde 2026-09-15 (commit `680dd2b`); lo que no existe en móvil es la **gestión** (crear/listar), que es de plataforma Web según el CU.

**Brechas menores:**
- No hay pantalla para **activar/desactivar** ni editar un código existente (`is_active` existe en el modelo pero no hay endpoint/UI de toggle). El CU pide "creación y consulta", por lo que es una mejora, no una omisión del alcance.

**Estado: Implementado (~92%).**

---

## Brechas transversales

1. **2 de 7 CU están a 0%**: CU19 (AR/vestidor virtual) y CU24 (notificaciones push). Ninguno tiene código en backend, frontend ni mobile. Los 5 restantes están implementados en backend + web con brechas menores.
2. **Backend sin servicios de AR/notificaciones:** no hay módulos de `notification` ni integración FCM/APNs. Sí hay dependencia de IA: `google-genai>=1.0.0` en `requirements.txt`, usada por CU21 (embeddings ALS, sin LLM en runtime), CU22 (enrutador de intención + generación de respuesta) y CU23 (interpretación de consultas).
3. **Mobile sin features de este grupo:** la app Flutter cubre Ciclo 1–2 (catálogo, carrito con cupones, reservas, pedidos, perfil). CU21 y CU22 (plataforma "Ambas") no tienen versión móvil, y CU19/CU24 (exclusivamente móviles) siguen a 0%.
4. **CU23 reutiliza CU20 como sustrato:** el `<<extend>>` CU23→CU20 se implementó de forma real: `/reports/query` interpreta la consulta natural/voz y delega en los mismos reportes de CU20, manteniendo el scope por rol (solo admin).
5. **CU24 tiene disparadores de negocio disponibles:** cambios de estado de pedido/reserva, movimientos de inventario y publicación de productos existen en backend; falta el canal push (FCM) y los servicios de emisión por evento.
6. **CU25 casi completo:** creación + consulta + scope por rol + aplicación en el carrito (web y móvil); solo faltan toggles de activación/desactivación y la gestión desde móvil (no requerida por plataforma).
7. **Complementos recientes:** a 2026-09-18 se agregó la página de detalle de producto y su enrutamiento (`cliente/products/:productId`) con endpoint público de detalle (`catalog_routes.py:288`), base útil para CU10 y futuro punto de inserción del vestidor virtual (CU19).
8. **Documento de origen desactualizado:** la tabla del Ciclo 3 en `Casos_de_Uso_WomenStyle (1).md` marca los 7 CU como "Pendiente"; a la fecha, CU20, CU21, CU22, CU23 y CU25 superan ampliamente ese estado (~75%–95%) y CU19/CU24 permanecen pendientes.