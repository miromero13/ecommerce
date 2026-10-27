# Plan de Implementación – Segundo Parcial (Fase 0 + CU3 → CU17)

> **Para agentes (Claude Code / Antigravity):** este documento es el **mapa de archivos**. No recorras carpetas: cada ruta aquí fue verificada contra el código el 2026-10-27. `[EDIT]` = archivo existente a modificar, `[NEW]` = archivo a crear.
> Los contratos JSON (request/response y mensajes en español) están en `docs/SECOND_PARTIAL_USE_CASES.md` → sección del CU. Este plan **no los repite**; solo indica **dónde** y **cómo** encajan en el código real.

## 0. Alcance y orden

| Orden | CU | Estado real en código | Avance |
|---|---|---|---|
| 0 | **Fase 0 – brechas en CUs "Hecho"** (CU1, CU6, CU15 + docs) | ver sección 1.5 | Presentación 2 |
| 1 | CU3 RBAC dinámico | 0 % (roles = `RolEnum` fijo) | Presentación 2 |
| 2 | CU8 Reportes IA + ML | ~40 % (NLP Gemini + voz hechos) | Presentación 2 |
| 3 | CU9 Reabastecimiento experto | 0 % | Presentación 2 |
| 4 | CU10 Ingesta RPA | 0 % | Presentación 2/3 |
| 5 | CU16 Wishlist | 0 % | Presentación 2/3 |
| 6 | CU17 Loyalty | 0 % | Presentación 2/3 |

| 7 | CU21 Devoluciones (RMA, 30 días) | 0 % — añadido por D3 (sección 1.7) | Presentación 3 |

Fuera de alcance de este plan: CU18–CU20, CU22, CU23.

---

## 1. Mapa global del proyecto (rutas base)

### Backend (`backend/`)
| Qué | Ruta |
|---|---|
| Registro de routers | `backend/main.py` (línea 8 `from app.routes import ...`, líneas 62-82 `api_router.include_router(...)`, `lifespan` con loops asyncio) |
| Modelos SQLAlchemy | `backend/app/models/<entity>.py` (heredan `Base` de `app.models.user`; **no hay `__init__.py`**) |
| Registro de modelos para Alembic | `backend/alembic/env.py` (importar cada modelo nuevo con `# noqa: F401`) |
| Migraciones | `backend/alembic/versions/00NN_<desc>.py` — **escritas a mano**, `revision = "00NN"`, `down_revision = "00NN-1"`. Última: `0040`. Siguientes: `0041` (Fase 0) → `0046` (CU17) |
| Schemas Pydantic | `backend/app/schemas/<entity>_schema.py` |
| Enums compartidos | `backend/app/schemas/enums.py` (`RolEnum`, …) |
| Servicios | `backend/app/services/<entity>_service.py` |
| Rutas | `backend/app/routes/<entity>_routes.py` |
| Auth / dependencias | `backend/app/auth/dependencies.py` (`get_current_user`, `get_current_payload`, `require_roles`, `get_current_tenant_id`, `get_tenant_and_branch_scope`, `validate_tenant_access`) |
| JWT | `backend/app/auth/jwt.py`; claims se arman en `backend/app/routes/auth.py` (2 llamadas a `create_access_token`, líneas ~21 y ~61) |
| Respuesta estándar | `backend/app/utils/response.py` → `response(status_code, message=..., data=...)` |
| Errores | `raise HTTPException(status_code, detail="msg español")` (serializado a `message` por `backend/app/core/error_handlers.py`) |
| Feature flags de plan | `backend/app/services/subscription_service.py` → `PLAN_FEATURE_KEYS`, `tenant_has_feature(db, tenant_id, key)` |
| Gemini | paquete `google-genai` ya instalado; patrón de uso en `backend/app/services/natural_report_service.py` (`_interpret_sync`) |
| Dependencias Python | `backend/requirements.txt` |
| Tests | `backend/tests/test_<x>.py`; requieren `CU1_TEST_DATABASE_URL` (ver `backend/tests/conftest.py`) |

### Frontend web (`frontend/src/app/`)
| Qué | Ruta |
|---|---|
| Rutas | `frontend/src/app/app.routes.ts` (hijos de `path: 'app'`; admin en bloque `path: 'admin'` con `roleGuard(['administrador'])`) |
| Menú lateral | `frontend/src/app/core/layouts/app-shell.component.ts` → `sidebarSections` (líneas ~182-260, una sección por rol) |
| Cliente HTTP | `frontend/src/app/core/services/api.service.ts` |
| Errores / toasts | `frontend/src/app/core/utils/http-error.util.ts` (`getErrorMessage`), `frontend/src/app/core/utils/request-toast.util.ts` (`requestWithToast`) |
| PDF cliente (ya existe) | `frontend/src/app/core/utils/simple-pdf.util.ts` |
| Sesión / usuario | `frontend/src/app/features/shared/services/session.service.ts`, modelo `frontend/src/app/features/shared/models/auth.model.ts` |
| Guards | `frontend/src/app/features/shared/guards/auth.guards.ts` (`authenticatedGuard`, `roleGuard`) |
| Modelos TS | `frontend/src/app/features/shared/models/<x>.model.ts` |
| Servicios API | `frontend/src/app/features/shared/services/<x>-api.service.ts` |
| Páginas | `frontend/src/app/features/<rol>/pages/<x>-page.component.ts` + `.html` (template separado) |
| UI (spartan/shadcn) | `frontend/src/app/components/<button|card|table|tabs|input|select|badge|...>` |
| Charts | `ngx-area-chart`, `ngx-bar-chart`, `ngx-donut-chart` ya usados en `features/admin/pages/admin-home-page.component.html` (envueltos en `<div hlmOnBrowser>`). Reutilizarlos; no agregar librerías. |

### Móvil (`mobile/lib/`)
| Qué | Ruta |
|---|---|
| Rutas | `mobile/lib/app/routes.dart` (`AppRoutes` con `static const`) |
| Menú "Mis reservas / Mis pedidos" | `mobile/lib/features/management/management_page.dart` (**no** `profile_page.dart`) |
| Cliente HTTP | `mobile/lib/core/network/api_client.dart`, `api_response.dart`, `api_exception.dart` |
| Widgets | `mobile/lib/shared/widgets/app_*.dart` (`AppCard`, `AppButton`, `AppSnackBar`, `AppEmptyView`, …) |
| Patrón de feature | `mobile/lib/features/<x>/<x>_api.dart`, `_models.dart`, `_controller.dart`, `_page.dart` (ver `features/orders/`) |

### Archivos "calientes" (compartidos entre CUs → editar con cuidado si dos agentes trabajan a la vez)
`backend/main.py`, `backend/alembic/env.py`, `backend/app/schemas/enums.py`, `backend/app/auth/dependencies.py`, `frontend/src/app/app.routes.ts`, `frontend/src/app/core/layouts/app-shell.component.ts`, `mobile/lib/app/routes.dart`, `mobile/lib/features/management/management_page.dart`.
**Regla:** un agente por CU; los archivos calientes solo se tocan en el último paso del CU y con edición mínima (añadir líneas, no reordenar). **Las migraciones se numeran en el orden de este plan** (0041 = Fase 0, 0042 = CU3 … 0046 = CU17) para evitar choques de `down_revision`.

### Correcciones a la especificación detectadas en el código
1. `garment_points` (en `product_variants`) **NO son puntos de fidelización**: es el JSON de anclajes del vestidor virtual. CU17 usa puntos calculados por monto gastado (ver CU17).
2. No existe `admin-reports-page`: hoy la consulta en lenguaje natural vive en `frontend/src/app/features/shared/pages/sales-history-page.component.ts` (y `admin-inventory-page`). CU8 crea la página nueva.
3. El endpoint NLP real es `POST /api/reports/query` (no `/natural-query`). Se mantiene `/query` para no romper el frontend.
4. `Sale.user_id` es el **cajero**, no el cliente. CU17 agrega `sales.customer_id`.
5. Móvil: el menú del cliente está en `management_page.dart`.

---

## 1.5. CUs ya implementados – mapa de archivos y brechas (Fase 0)

Rutas reales verificadas. "Brecha" = lo que falta para cerrar el CU según el examen/especificación. Las rutas que la especificación indica mal están en la columna "Doc dice (incorrecto)".

### CU1 – Multi-Tenant
| Capa | Archivos |
|---|---|
| Entidad | `backend/app/models/tenant.py` (+ `tenant_id` en todas las tablas) |
| Migración | `backend/alembic/versions/0038_add_tenants_and_multitenant_foundation.py` |
| Schema | `backend/app/schemas/tenant_schema.py` |
| Servicio | `backend/app/services/tenant_service.py` |
| Controlador | `backend/app/routes/tenant_routes.py` (`/api/saas/tenants`: `GET /`, `POST /`, `GET /public`, `GET /{id}`, `PATCH /{id}`, `PATCH /{id}/status`) |
| Aislamiento | `backend/app/auth/dependencies.py` (`get_current_tenant_id`, `get_tenant_and_branch_scope`, `validate_tenant_access`) |
| Tests | `backend/tests/test_saas_multitenant.py`, `test_*_tenant_isolation.py` |
| Front | `frontend/src/app/features/superadmin/pages/tenant-management-page.component.ts/.html`, `superadmin-dashboard-page`, `features/shared/services/tenant-api.service.ts`, `features/shared/models/tenant.model.ts` — ruta `/app/superadmin/tenants` |
| Doc dice (incorrecto) | `features/admin/pages/tenant-management-page` y `/app/admin/tenants` |

**Brechas CU1 (el checklist las marca [x] pero no existen en el código):**
| # | Brecha | Archivos |
|---|---|---|
| 0.1 | **Middleware de resolución de tenant** por `X-Tenant-ID` o subdominio (no existe; `main.py` solo tiene CORS). Regla: si hay JWT con `tenant_id` y el header difiere → 403; para cliente/catálogo público el header selecciona la empresa. Guarda el valor en `request.state.tenant_id`. | `backend/app/core/tenant_middleware.py` [NEW], `backend/main.py` [EDIT] (`app.add_middleware`), `backend/tests/test_tenant_middleware.py` [NEW] |
| 0.2 | **Front/móvil no envían `X-Tenant-ID`** | `frontend/src/app/features/shared/interceptors/auth.interceptor.ts` [EDIT] (header desde `SessionService.user().tenant_id`), `mobile/lib/core/network/api_client.dart` [EDIT] |
| 0.3 | **Branding por empresa** (spec 1.5.5: nombre, logo, moneda, colores). `tenants` solo tiene `name, slug, contact_email, currency, country, status`. | `backend/app/models/tenant.py` [EDIT] (`logo_url`, `primary_color`), `backend/alembic/versions/0041_add_tenant_branding.py` [NEW], `backend/app/schemas/tenant_schema.py` [EDIT], `tenant-management-page` [EDIT] (campos), `frontend/src/app/core/layouts/app-shell.component.ts` [EDIT] (logo + `--primary` CSS var del tenant activo) |

### CU2 – Planes y suscripciones
| Capa | Archivos |
|---|---|
| Entidad | `backend/app/models/subscription_plan.py`, `backend/app/models/tenant_subscription.py` |
| Migración | `0039_add_saas_plans_and_subscriptions.py` |
| Schema / Servicio | `backend/app/schemas/subscription_schema.py`, `backend/app/services/subscription_service.py` (`PLAN_FEATURE_KEYS`, cuotas, `tenant_has_feature`), `backend/app/services/email_service.py` (Mailtrap) |
| Controlador | `backend/app/routes/subscription_routes.py` (`/api/saas`: `/plans`, `/public/plans`, `/plans/admin`, `POST /plans`, `PATCH /plans/{id}`, `/subscriptions/purchase-simulated`, `/subscriptions/current`, `/subscriptions/change-plan`, `/tenants/with-subscription`) |
| Tests | `backend/tests/test_saas_subscriptions.py` |
| Front | `features/admin/pages/subscription-page`, `features/superadmin/pages/plan-management-page`, `features/shared/components/pricing-table.component`, `features/shared/services/subscription-api.service.ts`, `features/shared/models/subscription.model.ts` |

**Brecha CU2:** `ai_ml_smart_reports` aparece como "Próximamente" en `features/admin/pages/subscription-page.component.html` y `features/shared/components/pricing-table.component.html` → quitar la etiqueta al terminar CU8 (el vestidor 3D/AR sigue "Próximamente": el examen no lo exige).

### CU4 – Landing y catálogo de planes
| Capa | Archivos |
|---|---|
| Controlador | `subscription_routes.py` (`/api/saas/public/plans`, `/api/saas/subscriptions/purchase-simulated`), `tenant_routes.py` (`/public`) |
| Front | `features/shared/pages/landing-page.component`, `features/shared/components/pricing-table.component`, `features/shared/pages/onboarding-page.component` — rutas `/` y `/onboarding` |
| Doc dice (incorrecto) | `features/shared/services/public-api.service.ts` (no existe; se usa `subscription-api.service.ts`) |

**Brecha CU4:** ninguna funcional.

### CU5 – Vestidor virtual
| Capa | Archivos |
|---|---|
| Servicio | `backend/app/services/virtual_try_on_service.py` (HF IDM-VTON), `backend/app/services/catalog_garment_service.py` |
| Schema / Controlador | `backend/app/schemas/garment_schema.py`, `backend/app/routes/garment_routes.py` (`/api/catalog/garment`, `/api/catalog/try-on`) |
| Tests | `backend/tests/test_virtual_try_on.py`, `test_catalog_garment_service.py` |
| Front | `features/shared/components/photo-try-on.component`, `detector-mediapipe.component`, `detector-ropa.component`, `garment-overlay.renderer.ts`, `frontend/public/decart-try-on.html`, en `features/cliente/pages/product-detail-page` |
| Móvil | `mobile/lib/features/catalog/virtual_try_on_page.dart` |
| Doc dice (incorrecto) | `features/shared/components/virtual-try-on.component.ts` (no existe) |

**Brecha CU5:** ninguna funcional.

### CU6 – Recomendaciones
| Capa | Archivos |
|---|---|
| Entidad / Migración | `backend/app/models/recommendation.py`, `0031`, `0032` |
| Servicio / Controlador | `backend/app/services/recommendation_service.py`, `backend/app/routes/recommendation_routes.py` (`GET /api/recommendations/collaborative/user/{user_id}`) |
| Tests | `backend/tests/test_recommendation_service.py` |
| Front | `features/cliente/pages/catalog-page.component` + `features/shared/services/catalog-api.service.ts` |
| Móvil | `mobile/lib/features/catalog/catalog_page.dart`, `catalog_api.dart` |
| Doc dice (incorrecto) | `cliente-home-page` y `recommendation-api.service.ts` (no existe), endpoint `/me` |

**Brecha CU6:** `recommendation_routes.py:29` → `message="Recommendations retrieved"` está en inglés (viola regla 1.1) → `"Recomendaciones obtenidas exitosamente"`.

### CU7 – Chatbot
| Capa | Archivos |
|---|---|
| Entidad | `backend/app/models/conversation.py`, `conversation_message.py` (`0034`, `0035`) |
| Servicio / Controlador | `backend/app/services/chatbot_service.py`, `conversation_service.py`, `backend/app/schemas/chatbot_schema.py`, `backend/app/routes/chatbot_routes.py` (`/api/chatbot/message`, `/messages`, `/conversation`) |
| Tests | `test_chatbot_service.py`, `test_conversation_service.py` |
| Front | `features/shared/components/chatbot.component`, `chatbot-api.service.ts`, `chatbot-ui.service.ts` |
| Móvil | `mobile/lib/features/chatbot/chatbot_page.dart`, `chatbot_api.dart`, `chatbot_models.dart` |

**Brecha CU7:** ninguna.

### CU11 – Traspaso manual de inventario
| Capa | Archivos |
|---|---|
| Entidad | `backend/app/models/inventory.py`, `inventory_movement.py` |
| Servicio / Controlador | `backend/app/services/inventory_service.py` (`register_transfer`), `backend/app/schemas/inventory_schema.py`, `backend/app/routes/inventory_routes.py` (`POST /api/inventory/movements/transfer`) |
| Tests | `test_inventory_tenant_isolation.py` |
| Front | `features/admin/pages/admin-inventory-page` (rutas `/app/admin/inventory` y `/app/encargado/inventory`), `inventory-api.service.ts`, `inventory.model.ts` |

**Brecha CU11:** ninguna (CU3 le agrega `require_permission("inventory:transfer")`).

### CU12 – Notificaciones push
| Capa | Archivos |
|---|---|
| Entidad | `backend/app/models/notification.py` (`Notification`, `DeviceToken`), `0037` |
| Servicio / Controlador | `notification_service.py`, `notification_delivery.py` (FCM), `notification_schema.py`, `notification_routes.py` (`/api/notifications`, `/unread-count`, `/read-all`, `/{id}/read`, `/tokens`) |
| Tests | `test_notifications.py` |
| Front | `features/shared/pages/notification-page`, `notification-push.service.ts`, `notification-api.service.ts`, `frontend/public/firebase-messaging-sw.js`, campana en `app-shell.component.ts` |
| Móvil | `mobile/lib/features/notifications/notification_push_service.dart`, `notifications_page.dart`, `notification_controller.dart` |
| Doc dice (incorrecto) | `push_notification_service.dart` |

**Brecha CU12:** ninguna. (Ojo CU22: el futuro `ngsw-worker.js` debe convivir con `firebase-messaging-sw.js`.)

### CU13 – Dashboard
| Capa | Archivos |
|---|---|
| Servicio / Controlador | `dashboard_service.py`, `dashboard_schema.py`, `dashboard_routes.py` (`GET /api/dashboard`) |
| Front | `features/admin/pages/admin-home-page` (`/app/admin`, usa `ngx-area-chart`, `ngx-donut-chart`, `ngx-bar-chart` → **reutilizar estos charts en CU8**), `dashboard-api.service.ts`, `dashboard.model.ts` |

**Brecha CU13:** ninguna.

### CU14 – Reportes y exportación
| Capa | Archivos |
|---|---|
| Servicio / Controlador | `report_service.py`, `report_schema.py`, `report_routes.py` (`/api/reports/sales|inventory|movements` + `/export` CSV, `POST /api/reports/query`) |
| Tests | `test_reporting_tenant_isolation.py`, `test_natural_report_contract.py` |
| Front | `features/shared/pages/sales-history-page` (`/app/admin/sales`), `admin-inventory-page`, `reports-api.service.ts`, `report.model.ts`, `core/utils/simple-pdf.util.ts` |
| Doc dice (incorrecto) | `admin-reports-page` y `/app/admin/reports` (los crea CU8) |

**Brecha CU14:** solo CSV → Excel/PDF de backend se cierra en CU8.

### CU15 – Cupones
| Capa | Archivos |
|---|---|
| Entidad | `backend/app/models/promotion_code.py`, `promotion_code_usage.py` (`0022`) |
| Servicio / Controlador | `promotion_service.py`, `pricing_service.py`, `cart_service.py` (`apply_coupon`, `remove_coupon`), `promotion_schema.py`, `promotion_routes.py` (`/api/promotions`) |
| Front | `features/shared/pages/promotions-page` (`/app/admin/promotions`, `/app/encargado/promotions`), `features/cliente/pages/cart-page`, `promotion-api.service.ts`, `promotion.model.ts` |
| Móvil | `mobile/lib/features/cart/cart_page.dart`, `cart_api.dart` |
| Doc dice (incorrecto) | `features/admin/pages/admin-promotions-page.component.ts` |

**Brecha CU15:** el **cajero no puede aplicar cupones** en caja (`caja-page` no tiene nada de cupones; el contexto del examen lo pide para Cajero). Archivos: `backend/app/schemas/sales_schema.py` [EDIT] (`promotion_code: str | None` en `SaleCreate`), `backend/app/services/sales_service.py` [EDIT] (validar con `promotion_service` y registrar `promotion_code_usages` en `_create_sale_from_items`), `frontend/src/app/features/cajero/pages/caja-page.component.ts/.html` [EDIT] (input cupón), test en `backend/tests/test_business_rules.py` [EDIT].

## 1.6. Flujos de negocio núcleo – cómo funcionan hoy y qué les falta

### Inventario por sucursal
**Cómo funciona:** una fila `inventories` por (`variant_id`, `branch_id`) (`uq_inventory_variant_branch`) con `quantity` (físico), `reserved_quantity` (apartado por reservas/pedidos) y `minimum_stock` (por sucursal). Disponible = `quantity − reserved_quantity`. Cada cambio físico deja un `inventory_movements` (`income`, `outcome`, `transfer_in`, `transfer_out`). Ventas en caja y pedidos retirados descuentan `quantity`; reservas y pedidos pendientes solo suben `reserved_quantity`. Archivos: `backend/app/models/inventory.py`, `inventory_movement.py`, `backend/app/services/inventory_service.py`, `backend/app/routes/inventory_routes.py`, `frontend/src/app/features/admin/pages/admin-inventory-page`.

| # | Brecha | Gravedad | Archivos |
|---|---|---|---|
| I1 | La BD no impide stock negativo: solo existe `CHECK minimum_stock >= 0`. Falta `quantity >= 0`, `reserved_quantity >= 0`, `reserved_quantity <= quantity`. | Alta | `backend/app/models/inventory.py` [EDIT] + migración (va con 0041) |
| I2 | No hay tipo `adjustment` con motivo (merma, daño, conteo físico); hoy se usa `outcome` genérico. Lo necesitan CU21 (merma) y CU23 (conflictos). | Media | `backend/app/schemas/inventory_schema.py` [EDIT] (`adjustment` + `reason`), `inventory_service.py` [EDIT] |

### Pasarela de pago
**Cómo funciona:** **Stripe** (PaymentIntent + webhook `POST /api/payments/stripe/webhook`, idempotencia con `payment_attempts.idempotency_key` y `stripe_events`) o **efectivo al retirar**. El pedido aparta stock 30 min (Stripe) o 24 h (efectivo). Expira solo (`expire_due_orders`, loop cada 60 s en `main.py`). Archivos: `backend/app/services/order_service.py`, `backend/app/routes/payment_routes.py`, `backend/app/models/payment_attempt.py`, `stripe_event.py`, `frontend/src/app/features/shared/services/checkout-api.service.ts`, `mobile/lib/features/orders/checkout_page.dart`.

| # | Brecha | Gravedad | Archivos |
|---|---|---|---|
| P1 | **Un pedido pagado con Stripe nunca se puede entregar.** Llega a `ready_for_pickup` y no hay endpoint para pasarlo a `collected` (`collect-cash` exige `payment_method == cash`). | **Crítica** | `order_service.py` [EDIT] (`hand_over_order(order_id, pickup_code, ...)`), `backend/app/routes/order_routes.py` [EDIT] (`POST /orders/{id}/hand-over`), `frontend/src/app/features/cajero/pages/caja-page` o `encargado/pages/orders-page` [EDIT] |
| P2 | **Moneda inconsistente:** `orders.currency` y `sales.currency` = `"usd"` (`STRIPE_CURRENCY=usd`, `sales_service.py:175` fijo), mientras `tenants.currency = "BOB"`. Se cobra en USD el número que está en Bs. | Alta | `order_service.py`, `sales_service.py` [EDIT] (usar `tenant.currency`); decidir la moneda de Stripe |
| P3 | Todas las empresas cobran en **una sola cuenta Stripe** (la de la plataforma); no hay Stripe Connect por empresa. | Media (limitación SaaS; documentarla) | `backend/app/core/config.py` |

### Reservas
**Cómo funciona:** el cliente elige sucursal, fecha de visita y prendas. Se aparta stock (`reserved_quantity`) **sin pagar nada**. Estados: `pending → confirmed → attended → purchase_pending → sold / not_sold`, más `cancelled` y `expired`. Vence `visit_date + 1 día`. En la sucursal se vende en caja (`SaleCreate.reservation_id`) o pasa al carrito (`/to-cart`). Archivos: `backend/app/services/reservation_service.py`, `backend/app/routes/reservation_routes.py`, `backend/app/schemas/reservation_schema.py`, `frontend/src/app/features/cliente/pages/reservations-page`, `my-reservations-page`, `encargado/pages/reservations-page`, `mobile/lib/features/reservations/*`.

| # | Brecha | Gravedad | Archivos |
|---|---|---|---|
| R1 | **No valida `visit_date`**: acepta fechas pasadas o lejanas (ej. 2030), con lo que el stock queda apartado sin límite. Falta `hoy ≤ visit_date ≤ hoy + N días`. | **Crítica** | `backend/app/schemas/reservation_schema.py` [EDIT] (validator) |
| R2 | **Sin anticipo:** reservar es gratis, así que un cliente puede bloquear stock sin compromiso. Propuesta: pago de anticipo (ej. 50 %), ver decisiones pendientes. | Alta | `reservation.py` [EDIT] (`deposit_amount`, `deposit_status`, `stripe_payment_intent_id`), `reservation_service.py`, `payment_routes.py` [EDIT], `sales_service.py` [EDIT] (descontar anticipo al cobrar) |
| R3 | No hay límite de prendas ni de reservas activas por cliente. | Media | `reservation_service.create_reservation` [EDIT] |
| R4 | `reservation_items.unit_price = variant.price` **ignora el descuento del producto**, que el carrito sí aplica (`pricing_service.discounted_price`): el total reservado no coincide con el precio del catálogo. | Media | `reservation_service.py` [EDIT] |

### Carrito
**Cómo funciona:** un carrito por usuario (`carts.user_id` único) y de **una sola empresa** (`carts.tenant_id`; si se agrega de otra empresa aparece el modal de conflicto). Al hacer checkout se elige la sucursal de retiro, se valida y aparta stock, se crea el `order` con snapshot de ítems y el carrito se vacía. Cupones: `cart.promotion_code_id`. Archivos: `backend/app/services/cart_service.py`, `backend/app/routes/cart_routes.py`, `frontend/src/app/features/cliente/pages/cart-page`, `mobile/lib/features/cart/*`.

| # | Brecha | Gravedad | Archivos |
|---|---|---|---|
| C1 | Funciona bien. El stock solo se valida al agregar y al hacer checkout, sin apartar (correcto). Lo único: si el precio cambia, se actualiza solo al editar el ítem. | Baja | — |

## 1.7. Decisiones de negocio confirmadas (2026-10-27)

### D1 – Anticipo de reserva: 50 %, **no reembolsable**
- Al crear la reserva el cliente paga con Stripe el **50 % del total** (con el precio con descuento, ver R4). Mientras no se pague, la reserva queda `pending_payment` y aparta stock 30 min (igual que un pedido Stripe). Si no paga, expira y libera el stock.
- Al retirar en sucursal, la caja cobra **total − anticipo**.
- Si el cliente **cancela o no se presenta**: **no hay devolución**. La reserva pasa a `cancelled`/`expired`, se libera el stock y el anticipo queda como ingreso de la empresa.
- Archivos: `backend/app/models/reservation.py` [EDIT] (`deposit_amount`, `deposit_status pending/paid/forfeited/applied`, `stripe_payment_intent_id`), `backend/app/schemas/reservation_schema.py` [EDIT] (estado `pending_payment`), `backend/app/services/reservation_service.py` [EDIT], `backend/app/routes/payment_routes.py` [EDIT] (`POST /payments/stripe/reservations/{id}` + webhook), `backend/app/services/sales_service.py` [EDIT] (descontar el anticipo al vender una reserva), `frontend/src/app/features/cliente/pages/reservations-page` [EDIT] (pago con Stripe Elements como en `cart-page`), `mobile/lib/features/reservations/reservation_create_page.dart` [EDIT]. Leyenda en la UI: *"El anticipo del 50 % no es reembolsable."*

### D2 – Una cuenta Stripe por empresa (Stripe Connect)
**Problema (P3):** hoy todo el dinero de todas las empresas entra a la cuenta Stripe de la plataforma.
**Solución:** **Stripe Connect con cuentas Express + destination charges.** La plataforma conserva sus claves y un solo webhook, pero cada PaymentIntent lleva `transfer_data.destination = tenant.stripe_account_id`, así el dinero se deposita en la cuenta de la empresa. Opcionalmente se cobra una comisión de plataforma (`application_fee_amount`). Como el carrito ya es de **una sola empresa**, cada pedido tiene un único destino.
Se descartó que cada empresa cargue sus propias claves secretas: habría que guardar secretos de terceros y manejar un webhook por empresa.

| Paso | Archivos |
|---|---|
| Campos en empresa | `backend/app/models/tenant.py` [EDIT] (`stripe_account_id`, `stripe_charges_enabled`, `platform_fee_percent`), en la migración **0041** |
| Onboarding | `backend/app/services/stripe_connect_service.py` [NEW] (`stripe.Account.create(type="express")`, `stripe.AccountLink.create(...)`, `refresh_status`), `backend/app/routes/stripe_connect_routes.py` [NEW] (`/api/saas/stripe-connect`: `POST /onboarding-link`, `GET /status`; solo `administrador`) |
| Cobro | `backend/app/services/order_service.py` [EDIT] `create_stripe_payment` y `create_stripe_payment_for_order` → `transfer_data`, `application_fee_amount`. Si la empresa no habilitó Stripe → 400 `"La empresa aún no habilitó pagos en línea"` (el efectivo sigue funcionando). El anticipo D1 usa la misma función. |
| Webhook | `backend/app/routes/payment_routes.py` [EDIT]: evento `account.updated` → `stripe_charges_enabled` |
| Reembolsos (D3) | `stripe.Refund.create(payment_intent=..., reverse_transfer=True)`: el reembolso sale de la cuenta de la empresa |
| UI | `frontend/src/app/features/admin/pages/subscription-page` [EDIT] (tarjeta "Pagos en línea": estado + botón **Conectar con Stripe**), `frontend/src/app/features/cliente/pages/cart-page` [EDIT] (ocultar Stripe si la empresa no lo habilitó) |
| Tests | `backend/tests/test_stripe_connect.py` [NEW] (Stripe mockeado: destino correcto, empresa sin cuenta → 400) |

**Limitación a declarar en la defensa:** Stripe no abre cuentas en Bolivia. La demo se hace en **modo test** con cuentas Express de prueba. En producción se usaría un país soportado o un proveedor local (Libélula, QR Simple), con el mismo patrón de "cuenta por empresa".

### D3 – Devoluciones: plazo de 30 días sobre el comprobante
**Hoy:** la caja imprime un comprobante (`caja-page.component.ts` → `printReceipt`, número = UUID de la venta) y el pedido web descarga una "nota de venta" PDF (`orders-page`/`cart-page` → `core/utils/simple-pdf.util.ts`). **No existe ningún flujo de devolución.**
**Casos de uso involucrados:** **CU21 (RMA)** es el principal; **CU19 (Billetera)** según la especificación recibe el reembolso; CU15 (los cupones usados no se devuelven). Los dos están **fuera** del alcance ≤ CU17: hay que sumar CU21 al plan.
**Reglas:**
1. La devolución se hace **sobre un comprobante** (venta en caja `sale` o pedido web `order`) y **por prenda/línea** (`sale_item` u `order_item`), con cantidad ≤ comprada − ya devuelta.
2. **Plazo: 30 días** desde la fecha de compra (`sales.created_at`, o la fecha de pago del pedido). Pasado ese plazo → 400 `"La prenda supera el plazo máximo permitido de 30 días para cambios y devoluciones"`.
3. El encargado inspecciona: **aprobada** → reingresa stock (`income` con nota RMA) o merma (`adjustment`, I2); **rechazada** → sin cambios.
4. El anticipo de reserva (D1) no se devuelve nunca.
5. Comprobante legible: número correlativo por empresa (`sales.receipt_number`, `orders.receipt_number`), impreso en el comprobante y en la nota PDF, para encontrar la compra al devolver (sobre todo ventas en caja sin cliente registrado).

| Capa | Archivos |
|---|---|
| Entidad | `backend/app/models/rma_request.py` [NEW] (`tenant_id`, `rma_number`, `source_type sale/order`, `sale_item_id`/`order_item_id`, `quantity`, `reason`, `customer_notes`, `status pending_inspection/approved/rejected`, `inspection_notes`, `return_to_inventory`, `refund_amount`, `refund_method`, `resolved_by`, `created_at`, `resolved_at`); `receipt_number` en `backend/app/models/sale.py` y `order.py` [EDIT] |
| Migración | `backend/alembic/versions/0047_add_rma_and_receipt_numbers.py` [NEW] |
| Schema / Servicio | `backend/app/schemas/rma_schema.py` [NEW], `backend/app/services/rma_service.py` [NEW] (`create_request` valida 30 días y cantidades, `resolve` en transacción: stock + reembolso) |
| Controlador | `backend/app/routes/rma_routes.py` [NEW] (`POST /api/rma/requests`, `GET /api/rma/requests`, `PATCH /api/rma/requests/{id}/status`, `GET /api/rma/receipts/{receipt_number}` para que el encargado busque la compra) |
| Front | `frontend/src/app/features/cliente/pages/rma-request-page` [NEW] (`/app/cliente/returns`, botón "Solicitar devolución" en `orders-page`), `frontend/src/app/features/encargado/pages/rma-review-page` [NEW] (`/app/encargado/returns`, buscar por número de comprobante), `features/shared/services/rma-api.service.ts`, `models/rma.model.ts` [NEW] |
| Móvil | `mobile/lib/features/orders/rma_request_dialog.dart` [NEW] desde `orders_page.dart` |
| Tests | `backend/tests/test_rma.py` [NEW] (día 30 ok, día 31 → 400, doble devolución → 409, stock restaurado) |

### D4 – Reembolso de devoluciones
Pedido web pagado con Stripe → **reembolso a la tarjeta** (`stripe.Refund.create(..., reverse_transfer=True)`, sale de la cuenta Connect de la empresa). Venta en caja → **efectivo en caja** (se registra `refund_method = cash`). No depende de CU19.

## 1.8. Trazabilidad: cada tarea de la Fase 0 en su caso de uso

No se crean casos de uso nuevos ni relaciones include/extend: cada tarea corrige o completa un CU existente. "1P-CUxx" = caso de uso del primer parcial (`docs/FIRST_PARTIAL_USE_CASES.md`), que es la base que el segundo parcial conserva.

| Tarea | CU del 2.º parcial | CU base (1.er parcial) | Por qué |
|---|---|---|---|
| 0.1 Middleware `X-Tenant-ID` / subdominio | **CU1** Multi-Tenant | — | Resolución de tenant del Desafío VI |
| 0.2 Header `X-Tenant-ID` en web/móvil | **CU1** | — | Spec 1.5.5 |
| 0.3 Branding por empresa | **CU1** | — | Spec 1.5.5 (nombre, logo, moneda, colores) |
| P2 Moneda de la empresa (BOB) | **CU1** | 1P-CU16, 1P-CU18 | La moneda es un parámetro del tenant |
| D2 Stripe Connect (cuenta por empresa) | **CU1** (aislamiento financiero) + **CU2** (comisión de plataforma) | 1P-CU16 | Sin esto, el dinero de las empresas se mezcla |
| P1 Entregar pedido pagado con Stripe | — | **1P-CU16** Compra digital y estado del pedido | El flujo base queda incompleto |
| I1 Constraints de stock | **CU11** Traspaso de inventario (RNF04) | 1P-CU12 Movimiento de inventario | Integridad transaccional |
| I2 Ajuste con motivo (merma) | **CU11** | 1P-CU12 | Lo usan CU21 y CU23 |
| R1 Validar fecha de visita · R3 Límites · R4 Precio con descuento | — | **1P-CU14** Gestionar reservas | Reglas del flujo base |
| D1 Anticipo 50 % no reembolsable | — | **1P-CU14** (cobro) y **1P-CU17** Atender reserva (descontar anticipo) | Regla de negocio nueva sobre el flujo base |
| CU6 Mensaje en español | **CU6** | 1P-CU21 | Regla de idiomas 1.1 |
| Cupón en caja | **CU15** | 1P-CU18 Venta presencial | Actor Cajero de CU15 |
| Número de comprobante | **CU21** | 1P-CU16, 1P-CU18 | Lo necesita la devolución |
| D3/D4 Devoluciones | **CU21** RMA | — | Caso de uso propio |

### Fase 0 – Orden de trabajo
1. ✅ **P1** entrega de pedidos pagados con Stripe, **R1** validar `visit_date`, **I1** constraints de stock — *hecho 2026-10-27*: `POST /api/orders/{id}/hand-over` (cajero/encargado; `collect-cash` queda como alias), el personal ya no ve el código de retiro, ventana de visita hoy…+14 días (`MAX_VISIT_DAYS_AHEAD`), migración `0041` (constraints + campos de branding/Stripe Connect en `tenants`), página `cajero/orders`. Tests: `backend/tests/test_phase0_business_flows.py`.
2. ✅ 0.1 + 0.2 middleware `X-Tenant-ID` — *hecho 2026-10-27*: `backend/app/core/tenant_middleware.py` (header id/slug o subdominio `{slug}.TENANT_BASE_DOMAIN`), validación en `app/auth/dependencies.py` (`resolve_tenant_ref`, `get_request_tenant_id`; 403 si no coincide con el JWT, 404 si la empresa no existe), catálogo y sucursales públicas eligen la empresa por header, interceptor Angular envía `X-Tenant-ID` del personal. Móvil: sin cambio (sus usuarios son clientes globales sin `tenant_id`). Tests: `backend/tests/test_tenant_middleware.py`.
3. ✅ **P2** moneda, **R4** precio con descuento en reservas, **R3** límites — *hecho 2026-10-27*: pedidos, ventas y PaymentIntent usan `tenants.currency`; `reservation_items.unit_price` con descuento (la línea del carrito guarda el precio de lista para no descontar dos veces); máximo 5 prendas por reserva y 3 reservas activas por cliente y empresa (`MAX_RESERVATION_UNITS`, `MAX_ACTIVE_RESERVATIONS` en `reservation_service.py`).
4. ✅ **D2** Stripe Connect — *hecho 2026-10-27*: `stripe_connect_service.py`, `/api/saas/stripe-connect/onboarding-link` y `/status`, PaymentIntents con `transfer_data.destination` + `application_fee_amount` (`tenants.platform_fee_percent`), webhook `account.updated`, tarjeta "Pagos en línea" en `subscription-page`. Empresa sin cuenta habilitada → 400 antes de crear el pedido (el efectivo sigue). Tests: `backend/tests/test_stripe_connect.py`.
   ⏳ **D1** anticipo 50 % no reembolsable (usa D2).
5. 0.3 branding + I1 (misma migración **0041**).
6. CU6 mensaje en español.
7. CU15 cupón en caja.
8. Corregir en `docs/SECOND_PARTIAL_USE_CASES.md` las rutas marcadas "Doc dice (incorrecto)" y desmarcar/remarcar los checklists de CU1.

---

## 2. CU3 – RBAC dinámico

**Decisión de diseño:** `RolEnum` se **mantiene** como rol base (no se rompen guards ni tests existentes). Encima se agregan permisos dinámicos. Cada rol base tiene un **rol de sistema** sembrado con los permisos que hoy otorga `require_roles`; el administrador del tenant crea roles a medida y los asigna a usuarios. Permisos efectivos = permisos del rol de sistema ∪ roles asignados. `administrador` y `superadministrador` tienen todos.

### Backend
| # | Archivo | Acción |
|---|---|---|
| 1 | `backend/app/models/rbac.py` [NEW] | `Permission(id, name unique "module:verb", module, description)`, `Role(id, tenant_id nullable → null = sistema, code, name, base_rol RolEnum nullable, is_system)`, `role_permissions(role_id, permission_id)`, `user_roles(user_id, role_id)`. `UniqueConstraint(tenant_id, code)`. |
| 2 | `backend/alembic/env.py` [EDIT] | importar `Permission, Role` |
| 3 | `backend/alembic/versions/0042_add_rbac_permissions_and_roles.py` [NEW] | crea tablas + siembra catálogo de permisos y roles de sistema por `RolEnum` |
| 4 | `backend/app/schemas/rbac_schema.py` [NEW] | `PermissionRead`, `RoleCreate(name, code, permission_ids min 1)`, `RoleUpdate`, `RoleRead`, `UserRolesAssign(role_ids)` |
| 5 | `backend/app/services/rbac_service.py` [NEW] | `PERMISSIONS` (catálogo: `inventory:read`, `inventory:transfer`, `inventory:adjust`, `sales:create`, `sales:read`, `reports:read`, `reports:ai`, `catalog:manage`, `users:manage`, `rbac:manage`, `replenishment:manage`, `promotions:manage`, `orders:manage`, `reservations:manage`), `list_permissions`, `list_roles(tenant_id)`, `create_role` (409 código repetido, 400 sin permisos), `update_role`, `assign_user_roles` (usuario del mismo tenant), `effective_permissions(db, user) -> list[str]` |
| 6 | `backend/app/routes/rbac_routes.py` [NEW] | `APIRouter(prefix="/rbac")`: `GET /permissions`, `GET /roles`, `POST /roles`, `PUT /roles/{role_id}`, `POST /users/{user_id}/roles` — protegidos con `require_permission("rbac:manage")` |
| 7 | `backend/app/auth/dependencies.py` [EDIT] | agregar `require_permission(name)` (usa `effective_permissions`; 403 `"No tenés permisos suficientes para realizar esta acción"`) |
| 8 | `backend/app/routes/auth.py` [EDIT] | añadir claim `"permissions": effective_permissions(db, user)` en los 2 `create_access_token` y en el `user` devuelto |
| 9 | `backend/app/routes/inventory_routes.py` [EDIT] | demo: `transfer_route` pasa a `require_permission("inventory:transfer")` (manteniendo `_require_branch_access`) |
| 10 | `backend/main.py` [EDIT] | registrar `rbac_routes` |
| 11 | `backend/tests/test_rbac.py` [NEW] | crear rol, 409, 400, rol restrictivo → 403 en transfer, aislamiento tenant |

### Frontend
| # | Archivo | Acción |
|---|---|---|
| 12 | `frontend/src/app/features/shared/models/rbac.model.ts` [NEW] | `Permission`, `Role`, `RoleCreate` |
| 13 | `frontend/src/app/features/shared/models/auth.model.ts` [EDIT] | `permissions?: string[]` en el usuario |
| 14 | `frontend/src/app/features/shared/services/rbac-api.service.ts` [NEW] | métodos para los 5 endpoints |
| 15 | `frontend/src/app/features/shared/directives/has-permission.directive.ts` [NEW] | `*hasPermission="'inventory:transfer'"` leyendo `SessionService` |
| 16 | `frontend/src/app/features/admin/pages/rbac-roles-page.component.ts` + `.html` [NEW] | lista de roles, formulario con checkboxes agrupados por `module`, asignación a usuarios |
| 17 | `frontend/src/app/app.routes.ts` [EDIT] | en bloque `admin`: `path: 'roles'` |
| 18 | `frontend/src/app/core/layouts/app-shell.component.ts` [EDIT] | ítem `Roles y Permisos` → `/app/admin/roles` (sección Administración) |
| 19 | `frontend/src/app/features/admin/pages/admin-inventory-page.component.html` [EDIT] | botón de traspaso con `*hasPermission` |

**Verificación:** rol "Solo lectura inventario" asignado a un encargado → el botón de traspaso desaparece y `POST /api/inventory/movements/transfer` responde 403.

---

## 3. CU8 – Reportes IA + Machine Learning

**Ya hecho:** `backend/app/services/natural_report_service.py`, `POST /api/reports/query` en `backend/app/routes/report_routes.py`, voz (Web Speech) en `sales-history-page`.
**Falta:** datos sintéticos, regresión, K-Means, exportación Excel/PDF, página de reportes IA, 4 tipos de reportes demostrables.
**Gate de plan:** endpoints ML exigen `tenant_has_feature(db, tenant_id, "ai_ml_smart_reports")` (403 si el plan no lo incluye).

### Backend
| # | Archivo | Acción |
|---|---|---|
| 1 | `backend/requirements.txt` [EDIT] | `scikit-learn`, `openpyxl`, `reportlab` (pandas ya está) |
| 2 | `backend/app/services/ml/__init__.py` [NEW] | vacío |
| 3 | `backend/app/services/ml/synthetic_data_generator.py` [NEW] | genera semanas sintéticas (estacionalidad + ruido, semilla fija) y clientes sintéticos RFM; se **combina** con datos reales de `sales`/`orders` del tenant |
| 4 | `backend/app/services/ml/demand_forecast_service.py` [NEW] | features semana/mes/lag → `LinearRegression` o `RandomForestRegressor`, split train/test, `r2_score`, `mean_squared_error`, pronóstico N semanas con intervalo (±1.96·RMSE) |
| 5 | `backend/app/services/ml/customer_segmentation_service.py` [NEW] | RFM por cliente (frecuencia, monto, recencia) → `StandardScaler` + `KMeans(k=3)`, `silhouette_score`, nombre de segmento por centroide |
| 6 | `backend/app/services/report_export_service.py` [NEW] | `to_excel(rows, headers) -> bytes` (openpyxl), `to_pdf(title, rows, headers) -> bytes` (reportlab); reutiliza las consultas de `report_service.py` |
| 7 | `backend/app/schemas/report_schema.py` [EDIT] | `DemandForecastRequest(branch_id?, target_period_weeks 1-12)`, respuestas ML |
| 8 | `backend/app/routes/report_routes.py` [EDIT] | `POST /reports/ml/predict-demand`, `POST /reports/ml/customer-clusters`, `GET /reports/export/excel?type=sales|inventory|movements|top_products`, `GET /reports/export/pdf?...` (reusar `_scoped_filters`) |
| 9 | `backend/app/services/report_service.py` [EDIT] | si falta: `top_products` (ranking top 10) y `branch_comparison` → completan los 4 tipos obligatorios (ventas por sucursal, top 10, stock crítico, comparativa) |
| 10 | `backend/tests/test_ml_reports.py` [NEW] | métricas en rango, k=3 segmentos, export devuelve bytes xlsx/pdf válidos, aislamiento tenant |

### Frontend
| # | Archivo | Acción |
|---|---|---|
| 11 | `frontend/src/app/features/shared/models/report.model.ts` [EDIT] | `DemandForecast`, `CustomerClusters` |
| 12 | `frontend/src/app/features/shared/services/reports-api.service.ts` [EDIT] | `predictDemand`, `customerClusters`, `exportExcel`, `exportPdf` (blob) |
| 13 | `frontend/src/app/features/admin/pages/admin-reports-page.component.ts` + `.html` [NEW] | tabs: **Lenguaje natural** (mover/reusar la barra de voz de `sales-history-page`), **Predicción de demanda** (`ngx-bar-chart`/`ngx-area-chart` como en `admin-home-page` + métricas R²/MSE), **Segmentación** (tarjetas por cluster + Silhouette), botones Excel/PDF |
| 14 | `frontend/src/app/app.routes.ts` [EDIT] | bloque `admin`: `path: 'reports'` |
| 15 | `frontend/src/app/core/layouts/app-shell.component.ts` [EDIT] | ítem `Reportes IA` → `/app/admin/reports` |

**Verificación:** consulta por voz → tabla real; predicción muestra R²/MSE; clusters muestran Silhouette; se descargan `.xlsx` y `.pdf`.

---

## 4. CU9 – Reabastecimiento automático (Sistema Experto)

**Base de hechos:** `inventories(quantity, reserved_quantity, minimum_stock)` + ventas de los últimos N días (`sales`/`sale_items`) + stock de otras sucursales del mismo tenant.
**Reglas (motor de inferencia hacia adelante, cada regla deja su "razón"):**
- R1 Punto de reorden: `disponible < minimum_stock` → candidato.
- R2 Velocidad: `velocidad = unidades vendidas / lookback_days`; `necesidad = ceil(velocidad·coverage_days + minimum_stock − disponible)`.
- R3 Origen: sucursal con `excedente = disponible − minimum_stock − velocidad_origen·coverage_days > 0`, la de mayor excedente.
- R4 Cantidad: `min(necesidad, excedente)`; si 0 → sin sugerencia (se reporta "sin origen").
Ejecutar la transferencia reutiliza `inventory_service.register_transfer` (atómico, ya existente).

### Backend
| # | Archivo | Acción |
|---|---|---|
| 1 | `backend/app/models/expert_replenishment.py` [NEW] | `ExpertReplenishmentRule(tenant_id unique, lookback_days=7, coverage_days=14, is_auto_enabled)`, `ExpertTransferSuggestion(id, tenant_id, variant_id, source_branch_id, target_branch_id, suggested_quantity, reason, status pending/applied/discarded, created_at, applied_at)` |
| 2 | `backend/alembic/env.py` [EDIT] + `backend/alembic/versions/0043_add_expert_replenishment.py` [NEW] | |
| 3 | `backend/app/schemas/expert_replenishment_schema.py` [NEW] | `RulesRead/RulesUpdate`, `SuggestionRead`, `ApplyTransfersRequest(transfer_ids)` |
| 4 | `backend/app/services/expert_replenishment_service.py` [NEW] | `evaluate(db, tenant_id)` (descarta sugerencias pendientes anteriores y crea nuevas), `apply_transfers(db, tenant_id, ids, user_id)` (404 si no pending, 400 sin stock), `get_rules/update_rules`, `run_auto_evaluation()` para todos los tenants con `is_auto_enabled` |
| 5 | `backend/app/routes/expert_replenishment_routes.py` [NEW] | `APIRouter(prefix="/inventory/expert-replenishment")`: `POST /evaluate`, `POST /apply-transfers`, `GET /rules`, `PUT /rules`, `GET /suggestions` — `require_roles(RolEnum.administrador)` (o `require_permission("replenishment:manage")` si CU3 ya está) |
| 6 | `backend/main.py` [EDIT] | registrar router + loop `_expert_replenishment_loop()` en `lifespan` (cada 6 h, mismo patrón que `_expire_orders_loop`) |
| 7 | `backend/tests/test_expert_replenishment.py` [NEW] | stock crítico → sugerencia con razón; apply mueve stock; doble apply → 404; tenant aislado |

### Frontend
| # | Archivo | Acción |
|---|---|---|
| 8 | `frontend/src/app/features/shared/models/expert-replenishment.model.ts` [NEW] | |
| 9 | `frontend/src/app/features/shared/services/expert-replenishment-api.service.ts` [NEW] | |
| 10 | `frontend/src/app/features/admin/pages/admin-expert-replenishment-page.component.ts` + `.html` [NEW] | botón "Evaluar", tabla de sugerencias con checkbox y razón, "Aplicar seleccionadas", formulario de reglas |
| 11 | `frontend/src/app/app.routes.ts` [EDIT] | bloque `admin`: `path: 'expert-replenishment'` |
| 12 | `frontend/src/app/core/layouts/app-shell.component.ts` [EDIT] | ítem `Reabastecimiento IA` |

**Verificación:** bajar stock de una variante bajo su mínimo en una sucursal → "Evaluar" sugiere traspaso desde la sucursal con excedente → aplicar → stock movido y registrado en `inventory_movements`.

---

## 5. CU10 – Ingesta de mercadería con RPA + IA

**Flujo:** el proveedor sube PDF/imagen → job `processing` → `BackgroundTasks` envía el archivo a Gemini (multimodal, salida JSON con esquema) → `completed` con `extracted_items` (o `failed`) → el proveedor/administrador revisa y corrige la grilla → **commit** por administrador o encargado eligiendo sucursal destino: cada ítem se cruza por `product_variants.sku` (único) dentro del tenant y se registra con `inventory_service.register_income`. Ítems sin SKU conocido se devuelven como "no reconocidos" (no se crean productos automáticamente — decisión propia, se puede ampliar).

### Backend
| # | Archivo | Acción |
|---|---|---|
| 1 | `backend/app/models/rpa_ingest_job.py` [NEW] | `RpaIngestJob(id, tenant_id, provider_id, uploaded_by, filename, mime_type, status processing/completed/failed/committed, extracted_items JSON, error_message, target_branch_id, created_at, committed_at)` |
| 2 | `backend/alembic/env.py` [EDIT] + `backend/alembic/versions/0044_add_rpa_ingest_jobs.py` [NEW] | |
| 3 | `backend/app/schemas/rpa_ingest_schema.py` [NEW] | `ExtractedItem(sku, name, size, color, quantity>0, unit_cost)`, `JobRead`, `JobCommit(branch_id, items)` |
| 4 | `backend/app/services/rpa_ingest_service.py` [NEW] | `create_job` (valida `application/pdf`, `image/png|jpeg|webp`, ≤10 MB → 400), `process_job(job_id, bytes)` (Gemini, patrón de `natural_report_service._interpret_sync`), `get_job`, `commit_job` (409 si ya committed, 422 si 0 ítems válidos) |
| 5 | `backend/app/routes/rpa_ingest_routes.py` [NEW] | `APIRouter(prefix="/rpa/ingest")`: `POST /upload-document` (202, `UploadFile`, `python-multipart` ya instalado), `GET /jobs`, `GET /jobs/{job_id}`, `POST /jobs/{job_id}/commit` |
| 6 | `backend/main.py` [EDIT] | registrar router |
| 7 | `backend/tests/test_rpa_ingest.py` [NEW] | Gemini mockeado: tipo inválido 400, commit suma stock, doble commit 409, tenant aislado |

### Frontend
| # | Archivo | Acción |
|---|---|---|
| 8 | `frontend/src/app/features/shared/models/rpa-ingest.model.ts` [NEW] | |
| 9 | `frontend/src/app/features/shared/services/rpa-ingest-api.service.ts` [NEW] | upload con `FormData`, polling del job cada 2 s |
| 10 | `frontend/src/app/features/proveedor/pages/provider-rpa-ingest-page.component.ts` + `.html` [NEW] | zona drag & drop, estado del job, grilla editable, botón confirmar (solo admin/encargado) |
| 11 | `frontend/src/app/app.routes.ts` [EDIT] | `proveedor/rpa-ingest` (`roleGuard(['proveedor'])`) y en bloque `admin`: `rpa-ingest` (mismo componente) |
| 12 | `frontend/src/app/core/layouts/app-shell.component.ts` [EDIT] | ítem `Ingesta RPA` en Proveedor y Administración |

**Material de demo:** `docs/tests/remito_demo.pdf` [NEW] con SKUs reales del seed.

---

## 6. CU16 – Wishlist

**Notas:** los clientes son globales (`tenant_id` null en `users`), así que `wishlist_items.tenant_id` = tenant del producto. El carrito está limitado por empresa/sucursal: `move-to-cart` recibe `variant_id` (talla/color) y reutiliza `cart_service.add_cart_item` (ya valida stock y empresa).

### Backend
| # | Archivo | Acción |
|---|---|---|
| 1 | `backend/app/models/wishlist_item.py` [NEW] | `WishlistItem(id, tenant_id, user_id, product_id, created_at)`, `UniqueConstraint(user_id, product_id)` |
| 2 | `backend/alembic/env.py` [EDIT] + `backend/alembic/versions/0045_add_wishlist_items.py` [NEW] | |
| 3 | `backend/app/schemas/wishlist_schema.py` [NEW] | `WishlistItemCreate(product_id)`, `WishlistItemRead(product_name, price, image_url, in_stock)`, `MoveToCartRequest(variant_id, quantity=1)` |
| 4 | `backend/app/services/wishlist_service.py` [NEW] | `list_items`, `add_item` (404/409), `remove_item`, `move_to_cart` (llama `cart_service.add_cart_item` y borra de la lista; 400 sin stock) |
| 5 | `backend/app/routes/wishlist_routes.py` [NEW] | `APIRouter(prefix="/wishlist")`: `GET ""`, `POST /items` (201), `DELETE /items/{product_id}`, `POST /items/{product_id}/move-to-cart` — `require_roles(RolEnum.cliente)` |
| 6 | `backend/main.py` [EDIT] | registrar router |
| 7 | `backend/tests/test_wishlist.py` [NEW] | duplicado 409, inexistente 404, move-to-cart sin stock 400 |

### Frontend
| # | Archivo | Acción |
|---|---|---|
| 8 | `frontend/src/app/features/shared/models/wishlist.model.ts` [NEW] | |
| 9 | `frontend/src/app/features/shared/services/wishlist-api.service.ts` [NEW] | + `signal<Set<string>>` con ids favoritos para pintar corazones |
| 10 | `frontend/src/app/features/cliente/components/wishlist-toggle-button.component.ts` [NEW] | corazón (lucide `lucideHeart`) |
| 11 | `frontend/src/app/features/cliente/pages/catalog-page.component.html` [EDIT] y `product-detail-page.component.html` [EDIT] | insertar el botón |
| 12 | `frontend/src/app/features/cliente/pages/wishlist-page.component.ts` + `.html` [NEW] | grilla + selector de variante + "Mover al carrito" |
| 13 | `frontend/src/app/app.routes.ts` [EDIT] | `cliente/wishlist` (`roleGuard(['cliente'])`) |
| 14 | `frontend/src/app/core/layouts/app-shell.component.ts` [EDIT] | `Lista de deseos` en sección Navegación del cliente |

### Móvil
| # | Archivo | Acción |
|---|---|---|
| 15 | `mobile/lib/features/wishlist/wishlist_models.dart`, `wishlist_api.dart`, `wishlist_controller.dart`, `wishlist_page.dart` [NEW] | |
| 16 | `mobile/lib/features/catalog/product_detail_page.dart` [EDIT] | botón corazón |
| 17 | `mobile/lib/app/routes.dart` [EDIT] | `static const wishlist = '/wishlist'` |
| 18 | `mobile/lib/features/management/management_page.dart` [EDIT] | ítem "Lista de deseos" junto a reservas/pedidos |

---

## 7. CU17 – Fidelización y billetera de puntos

**Reglas (decisión propia, constantes en el servicio):** acumula **1 punto por cada 10 Bs** del `total_amount` pagado; **10 puntos = 1 Bs** de descuento; niveles por puntos históricos ganados: Bronce < 500 ≤ Plata < 1500 ≤ Oro. Cuenta por **cliente + empresa** (`tenant_id`), porque el marketplace tiene varias empresas. El canje no puede superar el total.
**Acreditación (hooks):** `order_service._consume_order` (pedido pagado/retirado) y `sales_service._create_sale_from_items` cuando la venta tiene `customer_id`. Idempotente con `UniqueConstraint(source_type, source_id, type)` en el ledger.
**Canje:** `POST /api/loyalty/redeem` sobre un **pedido pendiente de pago** (web, recalcula `discount_amount`/`total_amount`) o en caja como campo `points_to_redeem` + `customer_email` del `SaleCreate` (descuento aplicado antes de cerrar la venta, misma transacción).

### Backend
| # | Archivo | Acción |
|---|---|---|
| 1 | `backend/app/models/loyalty.py` [NEW] | `LoyaltyAccount(id, tenant_id, user_id, points_balance, lifetime_points, UniqueConstraint(tenant_id, user_id))`, `LoyaltyLedgerTransaction(id, tenant_id, account_id, type earn/redeem, points, source_type order/sale, source_id, created_at)` |
| 2 | `backend/app/models/sale.py` [EDIT] | `customer_id` nullable FK `users.id` |
| 3 | `backend/alembic/env.py` [EDIT] + `backend/alembic/versions/0046_add_loyalty_and_sale_customer.py` [NEW] | |
| 4 | `backend/app/schemas/loyalty_schema.py` [NEW] | `LoyaltyBalanceRead(total_points, cash_equivalent, tier)`, `RedeemRequest(order_or_sale_id, points_to_redeem>0)`, `LedgerRead` |
| 5 | `backend/app/schemas/sales_schema.py` [EDIT] | `SaleCreate`: `customer_email: EmailStr | None`, `points_to_redeem: int = 0` |
| 6 | `backend/app/services/loyalty_service.py` [NEW] | `get_or_create_account`, `get_balance(user_id, tenant_id)`, `earn_for(db, source_type, source_id, user_id, tenant_id, amount)`, `redeem_on_order`, `redeem_points(account, points, max_amount) -> Decimal`, `list_ledger` |
| 7 | `backend/app/services/order_service.py` [EDIT] | en `_consume_order`: `loyalty_service.earn_for(...)` |
| 8 | `backend/app/services/sales_service.py` [EDIT] | en `_create_sale_from_items`: resolver `customer_email` → `customer_id`, aplicar canje y acreditar |
| 9 | `backend/app/routes/loyalty_routes.py` [NEW] | `APIRouter(prefix="/loyalty")`: `GET /balance?tenant_id=`, `GET /transactions`, `POST /redeem` (cliente); `GET /customers/{email}/balance` (cajero) |
| 10 | `backend/main.py` [EDIT] | registrar router |
| 11 | `backend/tests/test_loyalty.py` [NEW] | acreditación al vender, idempotencia, puntos insuficientes 400, canje > total 400 |

### Frontend
| # | Archivo | Acción |
|---|---|---|
| 12 | `frontend/src/app/features/shared/models/loyalty.model.ts` [NEW] + `services/loyalty-api.service.ts` [NEW] | |
| 13 | `frontend/src/app/features/cliente/pages/loyalty-page.component.ts` + `.html` [NEW] | saldo, nivel, equivalente en Bs, historial |
| 14 | `frontend/src/app/features/cliente/pages/orders-page.component.html` [EDIT] | "Usar puntos" en pedidos pendientes de pago |
| 15 | `frontend/src/app/features/cajero/pages/caja-page.component.ts` + `.html` [EDIT] | email del cliente → consulta saldo → `points_to_redeem` en la venta |
| 16 | `frontend/src/app/app.routes.ts` [EDIT] + `app-shell.component.ts` [EDIT] | `cliente/loyalty`, ítem `Mis puntos` |

### Móvil
| # | Archivo | Acción |
|---|---|---|
| 17 | `mobile/lib/features/loyalty/loyalty_models.dart`, `loyalty_api.dart`, `loyalty_page.dart` [NEW] | |
| 18 | `mobile/lib/app/routes.dart` [EDIT] + `mobile/lib/features/management/management_page.dart` [EDIT] | ítem "Mis puntos" |

---

## 8. Definición de "hecho" por CU
1. Migración aplica (`alembic upgrade head`) y revierte (`downgrade -1`).
2. `pytest backend/tests/test_<cu>.py` en verde (con `CU1_TEST_DATABASE_URL`).
3. `npm run build` del frontend sin errores.
4. Toasts muestran `res.message` del backend (sin textos hardcodeados).
5. Marcar `[x]` en el checklist del CU en `docs/SECOND_PARTIAL_USE_CASES.md` y cambiar su estado a **Hecho** en la matriz (sección 3) y en `docs/SECOND_PARTIAL_PROJECT_CONTEXT.md` (sección 7).
6. Commit por CU: `feat(<modulo>): <descripción en inglés>`.
