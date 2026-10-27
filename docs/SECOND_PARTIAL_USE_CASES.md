# Casos de Uso – Segundo Parcial

Documento exhaustivo de especificación de requisitos, arquitectura de software, flujo de desarrollo y contratos de integración para el **Segundo Parcial**. Consolida el software desarrollado en el primer ciclo (MVP base implementado) y especifica en profundidad el nuevo alcance: **Plataforma SaaS Multi-Tenant**, cobertura de las **6 ramas de Inteligencia Artificial**, **fidelización omnicanal con billetera digital**, **logística de delivery y devoluciones**, y **arquitectura PWA / Offline-First**.

> **Mapa de archivos para implementar CU3–CU17:** ver `docs/SECOND_PARTIAL_IMPLEMENTATION_PLAN.md` (rutas exactas verificadas en el código, `[NEW]`/`[EDIT]`, orden y decisiones de diseño).

---

## 1. Convenciones Estrictas de Desarrollo y Arquitectura

### 1.1. Regla de Idiomas: Código en Inglés vs. Interfaz en Español
* **Todo el código es estrictamente en inglés:** nombres de archivos, funciones, clases, componentes, servicios, modelos de base de datos, nombres de tablas, columnas SQL, interfaces TypeScript, esquemas Pydantic, nombres de endpoints HTTP, verbos, parámetros de query/body, variables locales, comentarios técnicos y mensajes de commit de Git (ej. `tenant_id`, `StripeSubscriptionService`, `StoreWalletComponent`, `POST /api/saas/tenants`).
* **Únicamente lo que ve el usuario final es en español:** los textos de los mensajes de respuesta (`message`), los títulos, etiquetas de formularios (*labels*), textos de botones, alertas visuales (*toasts* / *snackbars*), modales y textos explicativos de la interfaz.

### 1.2. Prefijo Canónico de Endpoints (Sin versión /v1)
* El backend monta todos los routers bajo el prefijo raíz `/api` definido en `backend/main.py`.
* **No se utiliza `/v1` ni subversiones.** Las rutas siguen directamente el módulo:
  - `/api/saas/tenants`, `/api/saas/plans`, `/api/saas/subscriptions`
  - `/api/rbac/roles`, `/api/rbac/permissions`
  - `/api/inventory/movements/transfer`, `/api/promotions`, `/api/cart`
  - `/api/wishlist`, `/api/loyalty/...`, `/api/gift-cards/...`, `/api/wallet/...`
  - `/api/delivery/...`, `/api/rma/...`, `/api/offline/...`

### 1.3. Contrato Estándar de Respuestas y Errores del Backend
El sistema utiliza la función utilitaria `response(...)` de `backend/app/utils/response.py` y los manejadores globales de `backend/app/core/error_handlers.py`.

#### Mecanismo de Excepciones y Serialización HTTP
* En el código Python de backend se lanza la excepción nativa:
  ```python
  raise HTTPException(status_code=400, detail="Mensaje de error en español")
  ```
* El manejador global `StarletteHTTPException` en `backend/app/core/error_handlers.py` captura esta excepción y la serializa **siempre** bajo el contrato unificado:
  ```json
  {
    "statusCode": 400,
    "message": "Mensaje de error en español",
    "error": "HTTPException"
  }
  ```
* **Aclaración crítica para desarrollo y agentes IA:** En la respuesta HTTP JSON que viaja por la red hacia el frontend o móvil, **el campo siempre se llama `"message"`, NUNCA `"detail"`**. No se debe esperar un campo `"detail"` en el JSON de respuesta.

#### Modelos de Respuesta HTTP
* **Estructura de Respuesta Exitosa (`status_code: 200 / 201`):**
```json
{
  "statusCode": 200,
  "message": "Operación completada exitosamente",
  "data": { ... },
  "countData": null
}
```

* **Estructura de Error de Negocio (`status_code: 400 / 403 / 404 / 409`):**
```json
{
  "statusCode": 400,
  "message": "Stock insuficiente en la sucursal de origen",
  "error": "HTTPException"
}
```

* **Estructura de Error de Validación (`status_code: 422`):**
```json
{
  "statusCode": 422,
  "message": "Error de validación en los datos enviados",
  "error": [
    {
      "loc": ["body", "email"],
      "msg": "Formato de correo inválido",
      "type": "value_error"
    }
  ]
}
```

### 1.4. Regla Mandatoria para el Frontend y Móvil: Mostrar el Mensaje del Backend
* **La interfaz de usuario DEBE mostrar el mensaje exacto retornado por el backend en `response.message`.** Queda terminantemente prohibido hardcodear textos genéricos de éxito o error en los componentes.
* En **Angular**:
  - En peticiones exitosas: consumir y mostrar `response.message` usando `toast.success(res.message)`.
  - En errores HTTP: utilizar la utilidad del sistema `getErrorMessage(error, fallback)` (`frontend/src/app/core/utils/http-error.util.ts`) que extrae automáticamente `error.error?.message` o emplear `requestWithToast(...)` (`request-toast.util.ts`).
* En **Flutter (Móvil)**:
  - Deserializar la respuesta con `ApiResponse.fromJson(...)` y mostrar `response.message` en el `AppSnackBar.showSuccess(context, message)` o `AppSnackBar.showError(context, message)`.

### 1.5. Alcance Mandatorio de la Transformación Multi-Tenant (Migración Integral de Todo el Software)
* **La arquitectura multi-tenant NO se limita a crear la tabla `tenants` y nuevos endpoints.** Requiere una **migración integral y transversal de todo el software preexistente** en sus tres capas (Base de Datos, Backend y Frontend/Móvil):
  1. **Migración de Base de Datos y Modelos:** Toda tabla existente y futura (`users`, `branches`, `products`, `inventories`, `orders`, `sales`, `promotions`, `reservations`, `carts`, `notifications`, etc.) debe ser migrada para contener la columna `tenant_id` (`UUID`, FK hacia `tenants.id`, indexada, `nullable=False`). Se debe aplicar una migración con Alembic que siembre un *Tenant Inicial por Defecto* y asigne todos los datos preexistentes a este tenant antes de bloquear la nulabilidad.
  2. **Refactorización de Servicios y Consultas (Backend):** Todos los servicios existentes (`catalog_service.py`, `inventory_service.py`, `order_service.py`, `sales_service.py`, `cart_service.py`, `branch_service.py`, `user_service.py`, `promotion_service.py`, `dashboard_service.py`, `report_service.py`, `recommendation_service.py`, `chatbot_service.py`, etc.) deben ser refactorizados para inyectar y filtrar estrictamente por `tenant_id` en cada consulta `SELECT`, `UPDATE`, `INSERT` y `DELETE`. Ninguna operación transaccional puede quedar sin aislamiento de tenant, previniendo fuga de datos (*Data Leakage*) entre marcas.
  3. **Middleware de Aislamiento y Contexto:** Middleware en FastAPI que captura cada petición entrante, resuelve el `tenant_id` a partir del subdominio (`{tenant}.plataforma.com`) o encabezado `X-Tenant-ID`, y lo inyecta en el contexto de base de datos.
  4. **Autenticación y Tokens JWT:** El token JWT debe incluir el claim `tenant_id` para asociar inequívocamente a cada usuario con su empresa correspondiente (exceptuando al Superadministrador que posee visión global de la plataforma).
  5. **Frontend y Aplicación Móvil:** Los clientes HTTP (`ApiService`) e interceptores deben transmitir automáticamente el identificador de tenant y soportar la parametrización de marca (nombre comercial, logotipo, moneda y colores corporativos) según la organización activa.

---

## 2. Orden General de Implementación de un Nuevo Caso de Uso

Para mantener la cohesión y respetar **estrictamente la estructura existente del sistema**, la construcción de cualquier caso de uso nuevo o modificación de uno existente debe seguir de forma rigurosa el siguiente pipeline de desarrollo:

```
[1. MODEL DB] ➔ [2. MIGRACIÓN ALEMBIC] ➔ [3. SCHEMA PYDANTIC] ➔ [4. SERVICIO BACKEND] ➔ [5. ROUTE FASTAPI] ➔ [6. REGISTRO EN MAIN.PY] ➔ [7. TESTS]
                                                                                                                           │
                                                                                                                           ▼
[8. MODEL TYPESCRIPT] ➔ [9. SERVICIO API ANGULAR] ➔ [10. COMPONENTE & VISTA] ➔ [11. RUTA APP.ROUTES] ➔ [12. INTEGRACIÓN EN MENÚ / APPSHELL]
                                                                                                                           │
                                                                                                                           ▼
[13. MODEL DART (MÓVIL)] ➔ [14. SERVICIO API DART] ➔ [15. CONTROLLER / ESTADO] ➔ [16. PANTALLA UI] ➔ [17. RUTAS APP / MENÚ PERFIL]
```

### Fase A: Backend (Python / FastAPI)
1. **Modelo de Base de Datos (`backend/app/models/<entity>.py`):** Crear o actualizar la clase SQLAlchemy heredando de `Base`. Incluir siempre `tenant_id` para aislamiento multi-tenant, claves foráneas, índices y constraints de unicidad.
2. **Migración Alembic (`backend/alembic/versions/xxxx_<description>.py`):** Generar y aplicar la migración incremental para alterar la base de datos sin romper tablas previas.
3. **Esquema Pydantic (`backend/app/schemas/<entity>_schema.py`):** Definir modelos de validación de entrada (`Create`, `Update`) y de serialización de salida (`Read`), con nombres de propiedades en inglés.
4. **Servicio de Dominio (`backend/app/services/<entity>_service.py`):** Escribir la lógica pura de negocio, reglas de cálculo y persistencia transaccional en base de datos.
5. **Ruta y Endpoints (`backend/app/routes/<entity>_routes.py`):** Crear el `APIRouter(prefix="/<entity>", tags=["<Tag>"])`. Inyectar sesión de base de datos con `Depends(get_db)`, aplicar control de acceso con `require_roles(...)` o validación de permisos RBAC, y retornar siempre mediante la función `response(status_code, message="...", data=...)`. Lanzar errores con `raise HTTPException(status_code, detail="Mensaje en español")`.
6. **Registro en Router Principal (`backend/main.py`):** Incluir la nueva ruta en `api_router.include_router(<entity>_routes.router)`.
7. **Pruebas de Backend (`backend/tests/test_<entity>_service.py`):** Crear tests automatizados cubriendo casos de éxito y caminos alternativos.

### Fase B: Frontend Web (Angular)
8. **Modelo TypeScript (`frontend/src/app/features/<modulo>/models/<entity>.model.ts` o `shared/models/`):** Declarar las interfaces de datos reflejando exactamente el contrato JSON del backend en inglés.
9. **Servicio API Angular (`frontend/src/app/features/<modulo>/services/<entity>-api.service.ts`):** Inyectar `ApiService` (`frontend/src/app/core/services/api.service.ts`) y definir métodos que retornen `Observable<ApiResponse<T>>` hacia la ruta `/api/<entity>`.
10. **Componente y Plantilla HTML (`frontend/src/app/features/<modulo>/pages/<component-name>.component.ts` y `.html`):** Implementar la vista del usuario, formularios reactivos y feedback visual consumiendo el `message` que devuelve el backend a través de `toast` o `requestWithToast`.
11. **Enrutamiento Web (`frontend/src/app/app.routes.ts`):** Registrar la ruta con `loadComponent()` y protegerla mediante `authenticatedGuard` y `roleGuard(['<rol>'])`.
12. **Integración en Menú y Shell (`frontend/src/app/core/layouts/app-shell.component.ts`):** Incorporar la opción en `sidebarSections` para el rol correspondiente o en la sección de perfil si es una funcionalidad transversal de cuenta.

### Fase C: Aplicación Móvil (Flutter – para casos con soporte móvil)
13. **Modelo Dart (`mobile/lib/features/<modulo>/<entity>_models.dart`):** Crear clases con serializadores `fromJson` y `toJson`.
14. **Servicio API Móvil (`mobile/lib/features/<modulo>/<entity>_api.dart`):** Implementar llamadas HTTP usando el cliente base autenticado.
15. **Controlador de Estado (`mobile/lib/features/<modulo>/<entity>_controller.dart`):** Gestionar el ciclo de vida, estados de carga y errores.
16. **Pantalla UI (`mobile/lib/features/<modulo>/<entity>_page.dart`):** Diseñar widgets siguiendo los componentes compartidos (`AppCard`, `AppButton`, `AppSnackBar`).
17. **Rutas y Menú (`mobile/lib/app/routes.dart`):** Registrar la ruta de navegación y añadir el botón de acceso en el Menú de Perfil (`ProfilePage`) o tarjeta activa en la pantalla principal.

---

## 3. Matriz General de Casos de Uso (CU1 al CU23)

| **ID** | **Caso de uso** | **Módulo** | **Estado en Código** | **Actor(es) principal** | **Plataforma** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CU1** | **Plataforma Multi-Tenant (Multi-empresa)** | M1: Plataforma SaaS y Seguridad | **Hecho** | Superadministrador | Web |
| **CU2** | **Gestión de planes y suscripciones B2B** | M1: Plataforma SaaS y Seguridad | **Hecho** | Superadministrador, Administrador | Web |
| **CU3** | **Gestión granular de roles y permisos (RBAC)** | M1: Plataforma SaaS y Seguridad | **Pendiente** | Superadministrador, Administrador | Web |
| **CU4** | **Landing page y catálogo de planes** | M1: Plataforma SaaS y Seguridad | **Hecho** | Prospecto / Marca B2B | Web |
| **CU5** | **Usar vestidor virtual en tiempo real** | M2: Inteligencia Artificial | **Hecho** | Cliente | Móvil / Web |
| **CU6** | **Recibir recomendaciones de catálogo** | M2: Inteligencia Artificial | **Hecho** | Cliente | Ambas |
| **CU7** | **Consultar asistente virtual / Chatbot** | M2: Inteligencia Artificial | **Hecho** | Cliente | Ambas |
| **CU8** | **Generar reportes inteligentes con IA y Machine Learning** | M2: Inteligencia Artificial | **Pendiente** | Administrador | Web |
| **CU9** | **Reabastecimiento automático de stock (Sistema Experto)** | M2: Inteligencia Artificial | **Pendiente** | Administrador, Sistema | Web |
| **CU10** | **Ingesta de mercadería con RPA e IA** | M2: Inteligencia Artificial | **Pendiente** | Proveedor, Sistema | Web |
| **CU11** | **Traspaso manual de inventario** | M3: Inventario y Operaciones | **Hecho** | Administrador, Encargado | Web |
| **CU12** | **Notificaciones push móviles** | M3: Inventario y Operaciones | **Hecho** | Cliente, Sistema | Móvil |
| **CU13** | **Dashboard de control y métricas** | M4: Business Intelligence | **Hecho** | Administrador | Web |
| **CU14** | **Generación y exportación de reportes** | M4: Business Intelligence | **Hecho** | Administrador | Web |
| **CU15** | **Gestionar y aplicar cupones promocionales** | M5: Promociones y Fidelización | **Hecho** | Cliente, Admin, Encargado | Ambas |
| **CU16** | **Gestionar lista de deseos (*Wishlist*)** | M5: Promociones y Fidelización | **Pendiente** | Cliente | Ambas |
| **CU17** | **Fidelización y billetera de puntos (*Loyalty*)** | M5: Promociones y Fidelización | **Pendiente** | Cliente, Cajero | Ambas |
| **CU18** | **Emitir y comprar tarjetas de regalo (*Gift Cards*)** | M5: Promociones y Fidelización | **Pendiente** | Cliente | Ambas |
| **CU19** | **Gestionar billetera digital (*Store Wallet*)** | M5: Promociones y Fidelización | **Pendiente** | Cliente, Cajero | Ambas |
| **CU20** | **Delivery y despacho a domicilio** | M6: Logística y Posventa | **Pendiente** | Cliente, Delivery | Ambas |
| **CU21** | **Solicitar y procesar cambios y devoluciones (RMA)** | M6: Logística y Posventa | **Pendiente** | Cliente, Encargado, Admin | Ambas |
| **CU22** | **Progressive Web App (PWA) e Instalabilidad** | M6: Logística y Posventa | **Pendiente** | Cliente, Todos | Web |
| **CU23** | **Modo Offline y Sincronización Diferida (Offline-First)** | M6: Logística y Posventa | **Pendiente** | Cajero, Cliente, Delivery | Ambas |

---

## 4. Especificación Técnica Detallada por Caso de Uso

---

### Módulo 1: Plataforma SaaS, Seguridad y Comercial

#### CU1 – Plataforma Multi-Tenant (Multi-empresa)
* **Módulo:** M1: Plataforma SaaS y Seguridad
* **Actor Principal:** Superadministrador
* **Estado:** Hecho | **Plataforma:** Web
* **Descripción Funcional y Alcance de Migración:**
  Transición y migración estructural de **todo el software existente** a un modelo SaaS Multi-Inquilino (*Row-Level Multi-Tenancy* mediante `tenant_id`). **No consiste únicamente en crear tablas nuevas**, sino en migrar de forma integral la base de datos preexistente, refactorizar la totalidad de los servicios del backend para aislar consultas, e instrumentar el frontend y app móvil:
  1. **Migración de Datos y Base de Datos:** Se crea la tabla `tenants` y se siembra un *Tenant Inicial por Defecto* (ej. "Tenant Principal / WomenStyle"). Mediante migraciones incrementales de Alembic, **se altera cada tabla del sistema** agregando `tenant_id` (`UUID`, FK a `tenants.id`, indexada). Se asignan todos los registros preexistentes a este tenant inicial y posteriormente se impone la restricción `nullable=False`.
  2. **Refactorización Completa de Servicios Backend:** Cada uno de los servicios existentes (`catalog_service.py`, `inventory_service.py`, `cart_service.py`, `order_service.py`, `sales_service.py`, `branch_service.py`, `user_service.py`, `promotion_service.py`, `dashboard_service.py`, `report_service.py`, `recommendation_service.py`, `chatbot_service.py`) debe ser refactorizado para exigir e inyectar el filtro `tenant_id == current_tenant_id` en cada consulta `SELECT`, `UPDATE`, `INSERT` y `DELETE`, imposibilitando filtraciones cruzadas de información entre marcas.
  3. **Resolución de Contexto y Middleware:** Implementación de un middleware en FastAPI que determina el `tenant_id` en cada petición entrante a partir del subdominio (`marca.plataforma.com`) o encabezado `X-Tenant-ID`.
  4. **Autenticación Multi-Tenant:** El login valida la existencia del usuario en el tenant específico y el token JWT incluye el claim `tenant_id` (el Superadministrador es la única entidad global con capacidad de operar sobre múltiples organizaciones).
  5. **Frontend y Móvil:** El cliente HTTP (`ApiService`) inyecta automáticamente el contexto de tenant en todas las solicitudes y la interfaz adopta el branding personalizado (logotipo, nombre de empresa, moneda y colores).

##### Endpoints Backend
```http
POST /api/saas/tenants
Headers: Authorization: Bearer <superadmin_jwt>
Request Body:
{
  "name": "Boutique Elegance",
  "slug": "boutique-elegance",
  "subdomain": "elegance",
  "contact_email": "admin@elegance.com",
  "currency": "BOB",
  "country": "BO"
}
Response 201 Created:
{
  "statusCode": 201,
  "message": "Organización creada exitosamente",
  "data": {
    "id": "e3b0c442-98fc-1c14-9afb-4c72e0500001",
    "name": "Boutique Elegance",
    "slug": "boutique-elegance",
    "subdomain": "elegance",
    "status": "pending_subscription",
    "created_at": "2026-04-10T12:00:00Z"
  }
}

Response 409 Conflict:
{
  "statusCode": 409,
  "message": "El subdominio ya se encuentra registrado por otra empresa",
  "error": "HTTPException"
}

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "El correo de contacto no tiene un formato válido",
  "error": "HTTPException"
}
```
```http
GET /api/saas/tenants
Headers: Authorization: Bearer <superadmin_jwt>
Response 200 OK:
{
  "statusCode": 200,
  "message": "Listado de organizaciones obtenido",
  "data": [ ... ]
}
```
```http
GET /api/saas/tenants/{tenant_id}
PATCH /api/saas/tenants/{tenant_id}
```

##### Ubicación en Frontend (Angular)
* **Página y Vista:** `frontend/src/app/features/admin/pages/tenant-management-page.component.ts` (`tenant-management-page.component.html`)
* **Servicio API:** `frontend/src/app/features/shared/services/tenant-api.service.ts`
* **Modelo TypeScript:** `frontend/src/app/features/shared/models/tenant.model.ts`
* **Ruta Angular:** `/app/admin/tenants` (`canActivate: [roleGuard(['superadministrador'])]`)
* **Integración en Menú:** Ítem `"Empresas / Tenants"` en `sidebarSections` de Superadministrador en `app-shell.component.ts`.
* **Mensajes en UI:** La vista consume y muestra directamente el `message` del backend vía `toast.success(res.message)` o `toast.error(getErrorMessage(err, 'No se pudo crear la empresa'))`.

##### Checklist de Implementación y Migración Integral
- [x] Backend (Modelo SaaS): Crear modelo SQLAlchemy `Tenant` con campos de organización, subdominio, contacto y estado.
- [x] Backend (Migración de BD Existente): Crear migración Alembic que agregue la columna `tenant_id` (FK a `tenants.id`, indexada) en TODAS las tablas existentes del sistema (`users`, `user_profiles`, `branches`, `categories`, `collections`, `seasons`, `products`, `product_variants`, `sizes`, `colors`, `inventories`, `inventory_movements`, `carts`, `cart_items`, `reservations`, `reservation_items`, `orders`, `order_items`, `payment_attempts`, `sales`, `sale_items`, `promotion_codes`, `promotion_code_usages`, `replenishment_requests`, `recommendations`, `chat_conversations`, `chat_messages`, `notifications`, `user_device_tokens`).
- [x] Backend (Migración de Datos): Ejecutar script de datos para sembrar el Tenant Inicial por defecto ("Tenant Principal / WomenStyle") y vincular todos los registros preexistentes a dicho tenant antes de aplicar la restricción `nullable=False`.
- [x] Backend (Middleware de Aislamiento): Implementar middleware de contexto multi-tenant que extraiga el `tenant_id` del subdominio de la petición o encabezado HTTP `X-Tenant-ID`.
- [x] Backend (Refactorización de Servicios): Refactorizar la totalidad de los servicios existentes del backend (`catalog_service.py`, `inventory_service.py`, `cart_service.py`, `order_service.py`, `sales_service.py`, `branch_service.py`, `user_service.py`, `promotion_service.py`, `dashboard_service.py`, `report_service.py`, `recommendation_service.py`, `chatbot_service.py`) para filtrar y aislar obligatoriamente todas las consultas SQL por `tenant_id`.
- [x] Backend (Autenticación y JWT): Modificar el servicio de autenticación y generación de tokens JWT para inyectar el claim `tenant_id` y restringir el acceso del usuario a su organización.
- [x] Backend (Endpoints de Administración): Implementar endpoints CRUD `/api/saas/tenants` para provisionamiento y configuración de organizaciones por el Superadministrador.
- [x] Frontend: Configurar `ApiService` e interceptores HTTP para resolver subdominios o adjuntar el encabezado `X-Tenant-ID` en todas las peticiones salientes.
- [x] Frontend: Desarrollar pantalla `tenant-management-page` con listado de organizaciones, formulario de alta y estados de suscripción.
- [x] Verificación: Comprobar que los datos preexistentes permanecen operativos bajo el tenant inicial y que un nuevo tenant registrado inicia con su base de datos completamente limpia e inaccesible desde otros tenants.

---

#### CU2 – Gestión de planes y suscripciones B2B
* **Módulo:** M1: Plataforma SaaS y Seguridad
* **Actor Principal:** Superadministrador (crea planes), Administrador de Tenant (contrata y paga)
* **Estado:** **Hecho** | **Plataforma:** Web
* **Descripción Funcional:** Gestión de tiers de suscripción mensual/anual con límites operativos (número de sucursales y prendas) y módulos habilitados por plan (chatbot, vestidor virtual, reportes con IA). El pago es **simulado (sandbox)** con tarjeta de prueba; no se integra Stripe Checkout para suscripciones B2B.
* **Reglas de negocio:**
  1. Una suscripción vigente es la que está `active` y cuya `end_date` no pasó. Al vencer deja de contar, aunque su estado no cambie.
  2. Sin suscripción vigente, la empresa no puede crear sucursales ni prendas, y sus módulos de IA quedan desactivados.
  3. Los módulos se aplican según el plan de la **empresa que vende**: el vestidor virtual solo aparece en sus productos si su plan incluye `virtual_try_on_2d`, y el chatbot solo recomienda productos de empresas cuyo plan incluye `chatbot`.
  4. Una empresa `suspended` no tiene acceso para su personal y sus productos se ocultan del catálogo público.
  5. Cambiar de plan inicia un período nuevo y cancela el anterior. No se permite bajar a un plan cuyos límites ya se superan.
  6. Desactivar un plan lo quita de la venta; las empresas que ya lo tienen lo conservan hasta su vencimiento.

##### Endpoints Backend
```http
GET /api/saas/plans
Response 200 OK:
{
  "statusCode": 200,
  "message": "Planes de suscripción recuperados",
  "data": [
    {
      "id": "plan_basic_01",
      "name": "Básico",
      "price_monthly": 49.00,
      "max_branches": 2,
      "max_garments": 500,
      "features": ["catalog", "pos", "inventory"]
    },
    {
      "id": "plan_pro_02",
      "name": "Profesional",
      "price_monthly": 129.00,
      "max_branches": 5,
      "max_garments": 3000,
      "features": ["catalog", "pos", "inventory", "ai_try_on", "chatbot"]
    }
  ]
}
```
```http
POST /api/saas/subscriptions/purchase-simulated        (público: alta de una marca nueva)
Request Body:
{
  "company_name": "Boutique Elegance",
  "admin_name": "Ana Pérez",
  "admin_email": "admin@elegance.com",
  "plan_id": "plan_pro",
  "billing_cycle": "monthly",
  "card_number": "4242424242424242", "card_holder": "Ana Pérez", "card_exp": "12/28", "card_cvv": "123"
}
Response 201 Created:
{
  "statusCode": 201,
  "message": "Suscripción activada con éxito. Te enviamos un correo con los datos de acceso.",
  "data": { "tenant_id": "...", "tenant_slug": "boutique-elegance", "admin_email": "admin@elegance.com", "plan_name": "Profesional", "subscription_status": "active" }
}
```
```http
POST /api/saas/subscriptions/change-plan               (Administrador de la empresa)
Headers: Authorization: Bearer <admin_jwt>
Request Body:
{ "plan_id": "plan_enterprise", "billing_cycle": "yearly", "card_number": "4242424242424242" }
Response 200 OK:
{
  "statusCode": 200,
  "message": "Plan actualizado con éxito. Tu empresa ahora tiene el plan Enterprise.",
  "data": { "has_active_subscription": true, "plan": { ... }, "subscription": { ... }, "usage": { ... }, "features": [ ... ] }
}

Response 400 Bad Request:
{ "statusCode": 400, "message": "El plan seleccionado no se encuentra disponible.", "error": "HTTPException" }
{ "statusCode": 400, "message": "No podés cambiar al plan Básico: tenés 3 sucursales y permite 2.", "error": "HTTPException" }
```
```http
GET  /api/saas/subscriptions/current                   (personal de la empresa; superadmin con ?tenant_id=)
POST /api/saas/tenants/with-subscription               (Superadministrador: alta directa con pago en efectivo)
GET  /api/saas/plans/admin                             (Superadministrador: todos los planes, incluso desactivados)
POST /api/saas/plans                                   (Superadministrador: crear plan → 201 "Plan creado exitosamente")
PATCH /api/saas/plans/{plan_id}                        (Superadministrador: editar o desactivar → 200 "Plan actualizado exitosamente")
```
```http
Límites aplicados al crear sucursales (POST /api/branches/) y prendas (POST /api/catalog/products):
Response 403 Forbidden:
{ "statusCode": 403, "message": "Límite de sucursales alcanzado para el plan actual. Actualizá tu suscripción.", "error": "HTTPException" }
{ "statusCode": 403, "message": "Límite de prendas alcanzado para el plan actual. Actualizá tu suscripción.", "error": "HTTPException" }
{ "statusCode": 403, "message": "Tu empresa no tiene una suscripción activa. Renová o elegí un plan para continuar.", "error": "HTTPException" }
```

##### Ubicación en Frontend (Angular)
* **Página y Vista:** `frontend/src/app/features/admin/pages/subscription-page.component.ts` (`subscription-page.component.html`)
* **Servicio API:** `frontend/src/app/features/shared/services/subscription-api.service.ts`
* **Modelo TypeScript:** `frontend/src/app/features/shared/models/subscription.model.ts`
* **Ruta Angular:** `/app/admin/subscription` (`canActivate: [roleGuard(['administrador', 'superadministrador'])]`)
* **Integración en Menú:** Ítem `"Suscripción y Plan"` en `sidebarSections` de Administrador en `app-shell.component.ts`.
* **Cambio de plan:** El botón "Cambiar plan" de `subscription-page` despliega `pricing-table.component` (marca el plan actual) y un formulario de pago simulado que llama a `change-plan`.
* **Gestión de planes (Superadministrador):** `frontend/src/app/features/superadmin/pages/plan-management-page.component.ts`, ruta `/app/superadmin/plans`, ítem `"Planes de Suscripción"`.
* **Landing:** `pricing-table.component` muestra en cada tarjeta lo que agrega cada plan sobre el anterior y una tabla comparativa completa (precios, límites y módulos con su descripción), construida con los datos de `GET /api/saas/plans`.
* **Mensajes en UI:** Notificación de éxito y alertas de límite obtenidas directamente del `response.message`.

##### Checklist de Implementación
- [x] Backend: Crear tablas `saas_plans` y `tenant_subscriptions` con foreign key `tenant_id`.
- [x] Backend: Implementar cliente de Mailtrap API, servicio de onboarding y pasarela de pago simulada (Sandbox) con creación atómica de tenant y admin aleatorio.
- [x] Backend: Validador de límites del plan vigente antes de permitir crear sucursales (`max_branches`) o prendas (`max_garments`); sin plan vigente se bloquea la creación.
- [x] Backend: Vencimiento por `end_date`, cambio de plan con pago simulado y validación de bajada de plan.
- [x] Backend: Módulos por plan aplicados en vestidor virtual (`/api/catalog/garment` y `try_on_enabled` del producto), chatbot y reportes con IA.
- [x] Backend: Bloqueo de empresas suspendidas (personal y catálogo público).
- [x] Backend: CRUD de planes para el Superadministrador (crear, editar, desactivar).
- [x] Frontend: Crear `SubscriptionApiService` y componente de tarjetas comparativas de precios con los planes de la base de datos, más una tabla comparativa detallada en la landing.
- [x] Frontend: Desarrollar pantalla `subscription-page` con estado actual de la suscripción, barras de cuotas, aviso de suscripción vencida y cambio de plan.
- [x] Frontend: Pantalla `plan-management-page` del Superadministrador.
- [x] Móvil: el botón "Probar prenda" solo aparece si el plan de la tienda incluye el vestidor.
- [x] Verificación: `backend/tests/test_saas_subscriptions.py` sobre el PostgreSQL desechable (sin tocar la base de desarrollo).
- [ ] Pendiente: vestidor 3D con realidad aumentada y analítica con Machine Learning (se muestran como "Próximamente").

---

#### CU3 – Gestión granular de roles y permisos (RBAC dinámico)
* **Módulo:** M1: Plataforma SaaS y Seguridad
* **Actor Principal:** Superadministrador, Administrador
* **Estado:** Pendiente | **Plataforma:** Web
* **Descripción Funcional:** Sustitución del enum rígido de roles por un sistema de permisos dinámicos (`permissions`, `roles`, `role_permissions`). Permite crear perfiles a medida asignando permisos granulares por módulo y verbo (ej. `inventory:read`, `inventory:transfer`, `sales:create`).

##### Endpoints Backend
```http
GET /api/rbac/permissions
Headers: Authorization: Bearer <jwt>
Response 200 OK:
{
  "statusCode": 200,
  "message": "Catálogo de permisos obtenido",
  "data": [
    { "id": "perm_01", "name": "inventory:read", "module": "inventory", "description": "Consultar stock" },
    { "id": "perm_02", "name": "inventory:transfer", "module": "inventory", "description": "Efectuar traspasos entre sucursales" }
  ]
}
```
```http
POST /api/rbac/roles
Headers: Authorization: Bearer <jwt>
Request Body:
{
  "name": "Encargado de Almacén",
  "code": "warehouse_manager",
  "permission_ids": ["perm_01", "perm_02"]
}
Response 201 Created:
{
  "statusCode": 201,
  "message": "Rol creado exitosamente",
  "data": { "id": "role_123", "code": "warehouse_manager", "name": "Encargado de Almacén" }
}

Response 409 Conflict:
{
  "statusCode": 409,
  "message": "El código del rol ya existe en la organización",
  "error": "HTTPException"
}

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "Debe asignar al menos un permiso al rol",
  "error": "HTTPException"
}

Response 403 Forbidden:
{
  "statusCode": 403,
  "message": "No tenés permisos suficientes para realizar esta acción",
  "error": "HTTPException"
}
```
```http
GET /api/rbac/roles
PUT /api/rbac/roles/{role_id}
POST /api/rbac/users/{user_id}/roles
```

##### Ubicación en Frontend (Angular)
* **Página y Vista:** `frontend/src/app/features/admin/pages/rbac-roles-page.component.ts` (`rbac-roles-page.component.html`)
* **Servicio API:** `frontend/src/app/features/shared/services/rbac-api.service.ts`
* **Modelo TypeScript:** `frontend/src/app/features/shared/models/rbac.model.ts`
* **Directiva Estructural:** `frontend/src/app/features/shared/directives/has-permission.directive.ts`
* **Ruta Angular:** `/app/admin/roles` (`canActivate: [roleGuard(['administrador', 'superadministrador'])]`)
* **Integración en Menú:** Ítem `"Roles y Permisos"` dentro de la sección Administración en `app-shell.component.ts`.
* **Mensajes en UI:** El toast proyecta `res.message` al guardar roles y `getErrorMessage(...)` ante rechazos de permisos.

##### Checklist de Implementación
- [ ] Backend: Modelar tablas `permissions`, `roles`, `role_permissions` y `user_roles`.
- [ ] Backend: Inyectar matriz de permisos en el payload del token JWT (`permissions: [...]`).
- [ ] Backend: Crear dependencia FastAPI `require_permission("permission_name")`.
- [ ] Frontend: Crear directiva `*hasPermission="'inventory:transfer'"` para ocultar elementos en el DOM.
- [ ] Frontend: Desarrollar pantalla `rbac-roles-page` con checkboxes de permisos agrupados por módulo.
- [ ] Verificación: Asignar rol restrictivo a un usuario de prueba y validar bloqueo en endpoints y UI.

---

#### CU4 – Landing page y catálogo de planes
* **Módulo:** M1: Plataforma SaaS y Seguridad
* **Actor Principal:** Prospecto / Marca B2B (Visitante público)
* **Estado:** **Hecho** | **Plataforma:** Web
* **Descripción Funcional:** Portal web público institucional para captación comercial de marcas B2B. Presenta los diferenciales del software (IA, Vestidor Virtual, Omnicanalidad), tabla comparativa de planes y formulario para iniciar prueba gratuita de 14 días (*Free Trial*).

##### Endpoints Backend
```http
GET /api/public/plans
Response 200 OK:
{
  "statusCode": 200,
  "message": "Planes públicos obtenidos",
  "data": [ ... ]
}
```
```http
POST /api/public/register-tenant-trial
Request Body:
{
  "company_name": "Moda Urbana",
  "subdomain": "modaurbana",
  "admin_name": "Valeria Gómez",
  "admin_email": "valeria@modaurbana.com",
  "password": "PasswordSeguro2026!"
}
Response 201 Created:
{
  "statusCode": 201,
  "message": "Prueba gratuita iniciada. Te enviamos un correo con los datos de acceso.",
  "data": {
    "subdomain_url": "https://modaurbana.plataforma.com",
    "trial_ends_at": "2026-04-24T23:59:59Z"
  }
}

Response 409 Conflict:
{
  "statusCode": 409,
  "message": "El subdominio solicitado ya está en uso. Elegí otro nombre.",
  "error": "HTTPException"
}

Response 422 Unprocessable Entity:
{
  "statusCode": 422,
  "message": "Error de validación en los datos enviados",
  "error": [
    {
      "loc": ["body", "admin_email"],
      "msg": "Formato de correo electrónico inválido",
      "type": "value_error"
    }
  ]
}
```

##### Ubicación en Frontend (Angular)
* **Página y Vista:** `frontend/src/app/features/shared/pages/landing-page.component.ts` (`landing-page.component.html`)
* **Componentes de Sección:** `frontend/src/app/features/shared/components/pricing-table.component.ts`
* **Servicio API:** `frontend/src/app/features/shared/services/public-api.service.ts`
* **Ruta Angular:** `/landing` o `/` (acceso público sin autenticación)
* **Mensajes en UI:** La alerta de éxito muestra el mensaje del backend: `"Prueba gratuita iniciada. Te enviamos un correo con los datos de acceso."`

##### Checklist de Implementación
- [x] Backend: Endpoints públicos `/api/saas/plans` y `/api/saas/subscriptions/purchase-simulated` con aprovisionamiento atómico y credenciales por correo.
- [x] Frontend: Desarrollar página pública `landing-page` responsiva con sección hero, features, spotlight del vestidor virtual 2D/3D y tabla de precios.
- [x] Frontend: Flujo de onboarding reactivo con selección de plan, ciclo, datos de empresa/admin y pasarela simulada.
- [x] Verificación: Registrar una nueva organización desde la landing/onboarding y verificar inicio de sesión con las credenciales generadas.

---

### Módulo 2: Inteligencia Artificial y Automatización

#### CU5 – Usar vestidor virtual en tiempo real
* **Rama de IA:** **Visión por Computadora** (*Pose Estimation*) + **IA Generativa de Video** (Decart AI)
* **Actor Principal:** Cliente
* **Estado:** **Hecho** (Implementado en `mobile/lib/features/catalog/virtual_try_on_page.dart` y `frontend/public/decart-try-on.html`) | **Plataforma:** Móvil / Web
* **Descripción Funcional:** Proyección en vivo de prendas del catálogo sobre la silueta del cliente mediante la cámara del móvil o webcam, con detección de puntos anatómicos y adaptación de caída y movimiento de la prenda.

##### Endpoints Backend
```http
POST /api/ai/virtual-try-on/session
Headers: Authorization: Bearer <jwt>
Request Body:
{
  "garment_id": "550e8400-e29b-41d4-a716-446655440000",
  "stream_provider": "decart"
}
Response 200 OK:
{
  "statusCode": 200,
  "message": "Sesión de vestidor virtual inicializada",
  "data": {
    "session_id": "vto_sess_9921",
    "webrtc_url": "wss://ai.plataforma.com/webrtc/stream",
    "garment_texture_url": "https://storage.plataforma.com/textures/dress_01.png"
  }
}

Response 404 Not Found:
{
  "statusCode": 404,
  "message": "Prenda no encontrada para la sesión de vestidor virtual",
  "error": "HTTPException"
}

Response 422 Unprocessable Entity:
{
  "statusCode": 422,
  "message": "La prenda seleccionada no posee mapeo de textura 3D disponible",
  "error": "HTTPException"
}
```

##### Ubicación en Frontend (Angular & Móvil)
* **Vista Web / Iframe:** `frontend/public/decart-try-on.html`
* **Componente Modal Angular:** `frontend/src/app/features/shared/components/virtual-try-on.component.ts`
* **Página de Detalle de Prenda:** `frontend/src/app/features/cliente/pages/product-detail-page.component.ts`
* **App Móvil Flutter:** `mobile/lib/features/catalog/virtual_try_on_page.dart`
* **Mensajes en UI:** Muestra en pantalla el estado devuelto por el motor: `"Sesión de vestidor virtual inicializada"` o advertencias de encuadre.

##### Checklist de Implementación
- [x] Backend: Microservicio y router WebRTC/Decart AI para procesamiento de video en tiempo real.
- [x] Frontend: Integración de visor interactivo en `decart-try-on.html` y modal en `product-detail-page`.
- [x] Móvil: Integración de cámara y visualizador de stream en Flutter (`virtual_try_on_page.dart`).
- [x] Verificación: Renderizado de prendas en vivo con tracking anatómico en cámara web y móvil.

---

#### CU6 – Recibir recomendaciones personalizadas de catálogo
* **Rama de IA:** **Machine Learning** (Filtrado Colaborativo con Implicit ALS)
* **Actor Principal:** Cliente
* **Estado:** **Hecho** (Implementado en `backend/app/services/recommendation_service.py` y `recommendation_routes.py`) | **Plataforma:** Ambas
* **Descripción Funcional:** Generación de sugerencias personalizadas de prendas en portada y detalle a partir de la matriz de interacciones del cliente (vistas, carritos y compras), con fallback automático por popularidad para usuarios nuevos (*Cold Start*).

##### Endpoints Backend
```http
GET /api/recommendations/me?limit=6
Headers: Authorization: Bearer <jwt>
Response 200 OK:
{
  "statusCode": 200,
  "message": "Recomendaciones generadas exitosamente",
  "data": [
    {
      "product_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "name": "Vestido Midi Seda Floral",
      "score": 0.892,
      "recommendation_reason": "Basado en tus compras recientes y favoritos"
    }
  ]
}

Response 404 Not Found:
{
  "statusCode": 404,
  "message": "No se encontraron interacciones suficientes para generar recomendaciones personalizadas",
  "error": "HTTPException"
}
```
```http
POST /api/recommendations/interactions
Request Body: { "product_id": "...", "interaction_type": "view" }
Response 200 OK:
{
  "statusCode": 200,
  "message": "Interacción registrada para el modelo de recomendaciones"
}
```

##### Ubicación en Frontend (Angular & Móvil)
* **Página y Vista:** `frontend/src/app/features/cliente/pages/cliente-home-page.component.ts` (`cliente-home-page.component.html`)
* **Servicio API:** `frontend/src/app/features/shared/services/recommendation-api.service.ts`
* **Móvil Flutter:** Carrusel de recomendaciones en `mobile/lib/features/catalog/catalog_page.dart`
* **Mensajes en UI:** Encabezado dinámico: `"Recomendado para vos"` / `"Prendas que combinan con tu estilo"`.

##### Checklist de Implementación
- [x] Backend: Algoritmo Implicit ALS con NumPy en `recommendation_service.py`.
- [x] Backend: Endpoint `/api/recommendations/me` con cálculo vectorial y fallback cold-start.
- [x] Frontend: Carrusel de productos recomendados en `cliente-home-page`.
- [x] Móvil: Integración de carrusel de recomendaciones en la portada del catálogo Flutter.
- [x] Verificación: Comprobar actualización de recomendaciones tras registrar nuevas compras.

---

#### CU7 – Consultar asistente virtual / Chatbot
* **Rama de IA:** **Procesamiento de Lenguaje Natural (PLN)** + **IA Generativa** (Google Gemini)
* **Actor Principal:** Cliente
* **Estado:** **Hecho** (Implementado en `backend/app/services/chatbot_service.py` y `chatbot_routes.py`) | **Plataforma:** Ambas
* **Descripción Funcional:** Asistente conversacional con clasificación de intenciones (`CATALOGO`, `PEDIDOS`, `TALLES`, `POLITICAS`, `OFERTAS`), respuestas directas de stock real y generación de sugerencias de moda con Google Gemini.

##### Endpoints Backend
```http
POST /api/chatbot/message
Headers: Authorization: Bearer <jwt> (opcional si es visitante)
Request Body:
{
  "message": "¿Tenés disponible la chaqueta de cuero negra en talle M en la sucursal Centro?"
}
Response 200 OK:
{
  "statusCode": 200,
  "message": "Respuesta generada por el asistente virtual",
  "data": {
    "reply_text": "¡Sí! Tenemos 3 unidades de la Chaqueta de Cuero Negra en talle M en la Sucursal Centro.",
    "suggested_products": [ ... ]
  }
}

Response 422 Unprocessable Entity:
{
  "statusCode": 422,
  "message": "El mensaje no puede estar vacío",
  "error": "HTTPException"
}

Response 503 Service Unavailable:
{
  "statusCode": 503,
  "message": "El servicio de inteligencia artificial no está disponible temporalmente",
  "error": "HTTPException"
}
```
```http
GET /api/chatbot/messages
```

##### Ubicación en Frontend (Angular & Móvil)
* **Widget Flotante Web:** `frontend/src/app/features/shared/components/chatbot.component.ts` (`chatbot.component.html`)
* **Servicio API:** `frontend/src/app/features/shared/services/chatbot-api.service.ts`
* **Integración Global:** Incluido en `frontend/src/app/core/layouts/app-shell.component.html` para el rol cliente.
* **Móvil Flutter:** Pantalla de chat en `mobile/lib/features/chatbot/chatbot_page.dart`.
* **Mensajes en UI:** Muestra directamente las respuestas generadas por el bot en las burbujas de diálogo.

##### Checklist de Implementación
- [x] Backend: Servicio `chatbot_service.py` con integración a Google Gemini y clasificador de intenciones.
- [x] Backend: Persistencia de conversaciones en tablas `chat_conversations` y `chat_messages`.
- [x] Frontend: Componente widget flotante `chatbot.component` con mensajes optimistas y reintentos.
- [x] Móvil: Integración de pantalla de chat interactivo en Flutter.
- [x] Verificación: Consultas sobre disponibilidad real por talle, color y sucursal.

---

#### CU8 – Generar reportes inteligentes con IA y Machine Learning
* **Rama de IA:** **Procesamiento de Lenguaje Natural (PLN)** + **IA Generativa** (*Text-to-Filters* con Gemini) + **Machine Learning** (Supervisado y No Supervisado con Scikit-Learn)
* **Actor Principal:** Administrador
* **Estado:** **Pendiente** (Base de lenguaje natural implementada; pendiente evolución de modelos de Machine Learning, exportación a Excel/PDF y demostración de 4 tipos de reportes) | **Plataforma:** Web
* **Descripción Funcional:** Motor analítico avanzado para la generación de reportes empresariales inteligentes acorde al Desafío V del examen. Permite a usuarios autorizados formular solicitudes en lenguaje natural escrito o por voz (Web Speech API), interpretando intenciones para generar tanto reportes convencionales como reportes predictivos y de patrones:
  1. **Reportes Descriptivos e Históricos (NLP con Gemini):** Traducción de consultas en lenguaje natural a filtros SQL parametrizados y seguros contra datos reales de PostgreSQL, garantizando la demostración de al menos cuatro tipos de reportes (ventas por sucursal, ranking de productos más vendidos, existencias críticas/inventario bajo, y comparativas de ventas entre sucursales).
  2. **Reportes Predictivos con Machine Learning Supervisado:** Invocación de un modelo de regresión (entrenado con datos sintéticos y reales) para predecir variables objetivo como la demanda de prendas o la proyección de ventas de la próxima temporada, reportando métricas de evaluación ($R^2$, MSE).
  3. **Reportes de Patrones con Machine Learning No Supervisado:** Invocación de un modelo de clustering (K-Means) para descubrir patrones de compra o segmentar clientes según frecuencia y volumen de compra, reportando métricas de calidad (Silhouette Score).
  4. **Exportación Dinámica:** Capacidad de visualizar resultados en tablas o gráficos dinámicos y exportar los reportes generados a archivos formateados de **Excel (.xlsx)** y **PDF**.

##### Endpoints Backend
```http
POST /api/reports/natural-query
Headers: Authorization: Bearer <admin_jwt>
Request Body:
{
  "query_text": "Cuánto vendimos de blusas en la sucursal Centro la semana pasada"
}
Response 200 OK:
{
  "statusCode": 200,
  "message": "Consulta en lenguaje natural interpretada exitosamente",
  "data": {
    "report_kind": "descriptive_sql",
    "interpreted_filters": {
      "branch_name": "Sucursal Centro",
      "category": "Blusas",
      "date_from": "2026-04-01",
      "date_to": "2026-04-07"
    },
    "metrics": { "total_sales_amount": 3450.00, "total_units_sold": 23 },
    "rows": [ ... ]
  }
}

Response 422 Unprocessable Entity:
{
  "statusCode": 422,
  "message": "No se pudo interpretar el comando. Por favor especificá el período o la sucursal.",
  "error": "HTTPException"
}
```
```http
POST /api/reports/ml/predict-demand
Headers: Authorization: Bearer <admin_jwt>
Request Body:
{
  "branch_id": "branch_central",
  "target_period_weeks": 4
}
Response 200 OK:
{
  "statusCode": 200,
  "message": "Predicción de demanda con modelo supervisado generada exitosamente",
  "data": {
    "model_type": "Supervised Regression",
    "evaluation_metrics": { "r2_score": 0.884, "mse": 12.4 },
    "forecast": [
      { "week": "2026-W18", "predicted_units": 140, "confidence_lower": 125, "confidence_upper": 155 }
    ]
  }
}
```
```http
POST /api/reports/ml/customer-clusters
Headers: Authorization: Bearer <admin_jwt>
Response 200 OK:
{
  "statusCode": 200,
  "message": "Segmentación de clientes con modelo no supervisado generada",
  "data": {
    "model_type": "K-Means Clustering",
    "clusters_count": 3,
    "evaluation_metrics": { "silhouette_score": 0.72 },
    "segments": [
      { "cluster_id": 0, "name": "Compradores Frecuentes Alto Ticket", "size": 120, "avg_spend": 450.00 },
      { "cluster_id": 1, "name": "Cazadores de Ofertas", "size": 340, "avg_spend": 95.00 },
      { "cluster_id": 2, "name": "Clientes Ocasionales", "size": 510, "avg_spend": 130.00 }
    ]
  }
}
```
```http
GET /api/reports/export/excel?type=sales&start_date=2026-04-01&end_date=2026-04-10
GET /api/reports/export/pdf?type=sales&start_date=2026-04-01&end_date=2026-04-10
```

##### Ubicación en Frontend (Angular)
* **Página y Vista:** `frontend/src/app/features/admin/pages/admin-reports-page.component.ts` (`admin-reports-page.component.html`)
* **Servicio API:** `frontend/src/app/features/shared/services/reports-api.service.ts`
* **Ruta Angular:** `/app/admin/reports`
* **Mensajes en UI:** El toast proyecta `res.message`: `"Consulta en lenguaje natural interpretada exitosamente"` y los mensajes de estado del modelo.

##### Checklist de Implementación
- [x] Backend: Servicio `natural_report_service.py` con prompt estructurado JSON hacia Gemini para interpretar intenciones.
- [x] Backend: Endpoint `/api/reports/natural-query` con ejecución de consultas dinámicas de ventas, inventario y movimientos.
- [x] Frontend: Barra de consulta por voz/texto en `admin-reports-page` con Web Speech API.
- [ ] Backend (Datos Sintéticos): Implementar generador de datos sintéticos (`synthetic_data_generator.py`) para entrenamiento y validación de los modelos de Machine Learning.
- [ ] Backend (ML Supervisado): Desarrollar y entrenar modelo supervisado de regresión para proyección de demanda y ventas con cálculo de métricas ($R^2$ / MSE).
- [ ] Backend (ML No Supervisado): Desarrollar y entrenar modelo no supervisado de clustering (K-Means) para segmentación de clientes y detección de patrones de compra con Silhouette Score.
- [ ] Backend (Exportación Excel/PDF): Implementar generación y exportación de reportes dinámicos a Excel (.xlsx con `openpyxl`) y PDF formateado.
- [ ] Backend (4 Tipos de Reportes): Probar y asegurar la demostración de los 4 tipos de reportes obligatorios con datos reales (ventas por sucursal, top 10 productos, inventario con menor stock, y comparativa temporal/proyección).
- [ ] Frontend: Visualización de gráficos para clusters y proyecciones en `admin-reports-page` y botones de exportación a Excel y PDF.
- [ ] Verificación: Ejecutar en vivo consultas por voz y texto demostrando reportes históricos de PostgreSQL, reportes predictivos de ML supervisado y segmentaciones de ML no supervisado.

---

#### CU9 – Reabastecimiento automático de stock (Sistema Experto)
* **Rama de IA:** **Sistemas Expertos** (Motor de Inferencia de Reglas Determinísticas)
* **Actor Principal:** Administrador, Sistema
* **Estado:** Pendiente | **Plataforma:** Web
* **Descripción Funcional:** Motor de inferencia autónomo que evalúa reglas de inventario (umbrales mínimos, velocidad de ventas de los últimos 7 días y stock disponible en depósitos) para emitir órdenes automáticas de traspaso (`transfer`) entre sucursales, previniendo quiebres de stock.

##### Endpoints Backend
```http
POST /api/inventory/expert-replenishment/evaluate
Headers: Authorization: Bearer <admin_jwt>, X-Tenant-ID: <tenant_id>
Response 200 OK:
{
  "statusCode": 200,
  "message": "Evaluación del sistema experto finalizada",
  "data": {
    "rules_evaluated_count": 4,
    "suggested_transfers": [
      {
        "id": "sug_trans_01",
        "product_variant_id": "770e8400-e29b-41d4-a716-446655440001",
        "product_name": "Jeans Slim Denim Talle 38",
        "source_branch_name": "Depósito Central",
        "target_branch_name": "Sucursal Mall Ventura",
        "suggested_quantity": 15,
        "reason": "Stock actual (2) inferior al punto de reorden (5) con tasa de venta de 1.8 uds/día"
      }
    ]
  }
}
```
```http
POST /api/inventory/expert-replenishment/apply-transfers
Headers: Authorization: Bearer <admin_jwt>
Request Body: { "transfer_ids": ["sug_trans_01"] }
Response 200 OK:
{
  "statusCode": 200,
  "message": "Órdenes de traspaso automático aplicadas al inventario"
}

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "No hay stock disponible en el depósito de origen para realizar el traspaso sugerido",
  "error": "HTTPException"
}

Response 404 Not Found:
{
  "statusCode": 404,
  "message": "Una o más sugerencias de traspaso ya no son válidas o fueron procesadas",
  "error": "HTTPException"
}
```
```http
GET /api/inventory/expert-replenishment/rules
PUT /api/inventory/expert-replenishment/rules
```

##### Ubicación en Frontend (Angular)
* **Página y Vista:** `frontend/src/app/features/admin/pages/admin-expert-replenishment-page.component.ts` (`admin-expert-replenishment-page.component.html`)
* **Servicio API:** `frontend/src/app/features/shared/services/expert-replenishment-api.service.ts`
* **Modelo TypeScript:** `frontend/src/app/features/shared/models/expert-replenishment.model.ts`
* **Ruta Angular:** `/app/admin/expert-replenishment` (`canActivate: [roleGuard(['administrador'])]`)
* **Integración en Menú:** Ítem `"Reabastecimiento IA"` en la sección Administración en `app-shell.component.ts`.
* **Mensajes en UI:** Toast con `res.message`: `"Evaluación del sistema experto finalizada"` y `"Órdenes de traspaso automático aplicadas al inventario"`.

##### Checklist de Implementación
- [ ] Backend: Servicio `expert_replenishment_service.py` con motor de reglas lógicas basadas en hechos.
- [ ] Backend: Endpoints `/api/inventory/expert-replenishment/...` para evaluar y confirmar transferencias.
- [ ] Backend: Tarea programada en segundo plano para evaluación automática periódica.
- [ ] Frontend: Crear `ExpertReplenishmentApiService` y página `admin-expert-replenishment-page`.
- [ ] Frontend: Tabla de sugerencias del sistema experto con botón para aprobar traspasos en lote.
- [ ] Verificación: Provocar nivel de stock crítico en una sucursal y validar la recomendación generada por el motor.

---

#### CU10 – Ingesta de mercadería con RPA e IA
* **Rama de IA:** **RPA con IA** (*Intelligent Document Processing* - IDP)
* **Actor Principal:** Proveedor, Sistema
* **Estado:** Pendiente | **Plataforma:** Web
* **Descripción Funcional:** Bot desatendido que procesa notas de remisión, facturas y catálogos en PDF o imágenes enviados por proveedores. Utiliza OCR y extracción semántica para reconocer atributos de prendas (talle, color, costo, cantidades) y crear borradores de ingreso de mercadería sin tipeo manual.

##### Endpoints Backend
```http
POST /api/rpa/ingest/upload-document
Headers: Authorization: Bearer <provider_jwt>
Content-Type: multipart/form-data
Body: file: remito_lote42.pdf
Response 202 Accepted:
{
  "statusCode": 202,
  "message": "Documento recibido. Extracción RPA en proceso.",
  "data": {
    "job_id": "rpa_job_7710",
    "filename": "remito_lote42.pdf",
    "status": "processing"
  }
}

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "El archivo proporcionado no es un documento PDF o imagen válido",
  "error": "HTTPException"
}
```
```http
GET /api/rpa/ingest/jobs/{job_id}
Response 200 OK:
{
  "statusCode": 200,
  "message": "Resultado de extracción obtenido",
  "data": {
    "status": "completed",
    "extracted_items": [
      {
        "sku": "BLU-SED-NEG-M",
        "name": "Blusa de Seda Negra",
        "size": "M",
        "color": "Negro",
        "quantity": 50,
        "unit_cost": 85.00
      }
    ]
  }
}

Response 422 Unprocessable Entity:
{
  "statusCode": 422,
  "message": "No se pudieron reconocer ítems válidos en el documento suministrado",
  "error": "HTTPException"
}
```
```http
POST /api/rpa/ingest/jobs/{job_id}/commit
Response 201 Created:
{
  "statusCode": 201,
  "message": "Mercadería ingresada al inventario y catálogo sincronizado exitosamente"
}
```

##### Ubicación en Frontend (Angular)
* **Página y Vista:** `frontend/src/app/features/proveedor/pages/provider-rpa-ingest-page.component.ts` (`provider-rpa-ingest-page.component.html`)
* **Servicio API:** `frontend/src/app/features/shared/services/rpa-ingest-api.service.ts`
* **Modelo TypeScript:** `frontend/src/app/features/shared/models/rpa-ingest.model.ts`
* **Ruta Angular:** `/app/proveedor/rpa-ingest` (`canActivate: [roleGuard(['proveedor', 'administrador'])]`)
* **Integración en Menú:** Ítem `"Ingesta RPA"` en la barra lateral del Proveedor en `app-shell.component.ts`.
* **Mensajes en UI:** Toast con el mensaje devuelto por el backend: `"Mercadería ingresada al inventario y catálogo sincronizado exitosamente"`.

##### Checklist de Implementación
- [ ] Backend: Servicio `rpa_ingest_service.py` con OCR y extracción estructurada con Gemini Flash / Vision.
- [ ] Backend: Endpoints `/api/rpa/ingest/...` para subida de documentos, consulta de job y confirmación.
- [ ] Frontend: Desarrollar vista `provider-rpa-ingest-page` con zona de arrastre de archivos y grilla de ítems detectados.
- [ ] Verificación: Subir un PDF de prueba de remito y corroborar la carga automática en existencias.

---

### Módulo 3: Inventario y Operaciones de Sucursal

#### CU11 – Traspaso manual de inventario
* **Módulo:** M3: Inventario y Operaciones
* **Actor Principal:** Administrador, Encargado de sucursal
* **Estado:** **Hecho** (Implementado en `backend/app/routes/inventory_routes.py` endpoint `/inventory/movements/transfer`) | **Plataforma:** Web
* **Descripción Funcional:** Registro atómico de movimientos de transferencia de prendas entre dos sucursales físicas (`transfer_out` en origen y `transfer_in` en destino).

##### Endpoints Backend
```http
POST /api/inventory/movements/transfer
Headers: Authorization: Bearer <jwt>
Request Body:
{
  "origin_branch_id": "d1e7c520-2c70-4f3a-969d-7db0a0210001",
  "destination_branch_id": "d1e7c520-2c70-4f3a-969d-7db0a0210002",
  "product_variant_id": "8b0c8b00-1111-4444-aaaa-123456789012",
  "quantity": 5,
  "notes": "Refuerzo por campaña de fin de semana"
}
Response 201 Created:
{
  "statusCode": 201,
  "message": "Traspaso de inventario registrado exitosamente",
  "data": { ... }
}

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "Stock insuficiente en la sucursal de origen para la variante seleccionada",
  "error": "HTTPException"
}

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "La sucursal de origen y destino no pueden ser iguales",
  "error": "HTTPException"
}
```

##### Ubicación en Frontend (Angular)
* **Página y Vista:** `frontend/src/app/features/admin/pages/admin-inventory-page.component.ts` (`admin-inventory-page.component.html`)
* **Servicio API:** `frontend/src/app/features/shared/services/inventory-api.service.ts`
* **Ruta Angular:** `/app/admin/inventory`
* **Mensajes en UI:** El diálogo modal proyecta `res.message`: `"Traspaso de inventario registrado exitosamente"`.

##### Checklist de Implementación
- [x] Backend: Endpoint transaccional `/api/inventory/movements/transfer` con bloqueo concurrente.
- [x] Backend: Modelos `inventory_movements` con tipos `transfer_out` y `transfer_in`.
- [x] Frontend: Formulario modal de traspaso en `admin-inventory-page`.
- [x] Verificación: Transferencia exitosa entre dos sucursales con actualización inmediata de existencias.

---

#### CU12 – Notificaciones push móviles
* **Módulo:** M3: Inventario y Operaciones
* **Actor Principal:** Cliente, Sistema
* **Estado:** **Hecho** (Implementado con FCM en backend y Flutter móvil) | **Plataforma:** Móvil
* **Descripción Funcional:** Despacho automatizado de notificaciones push ante eventos del negocio (pedido listo, reserva confirmada, alerta de retiro) con bandeja in-app.

##### Endpoints Backend
```http
POST /api/notifications/push/register-token
Headers: Authorization: Bearer <jwt>
Request Body:
{
  "fcm_token": "eXamPL3_fCm_ToK3n_12345...",
  "device_platform": "android"
}
Response 200 OK:
{
  "statusCode": 200,
  "message": "Token de dispositivo registrado exitosamente"
}

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "El token FCM no es válido o ha expirado",
  "error": "HTTPException"
}
```
```http
GET /api/notifications
PATCH /api/notifications/{notification_id}/read
```

##### Ubicación en Frontend (Angular & Móvil)
* **Bandeja Web:** `frontend/src/app/features/shared/pages/notification-page.component.ts`
* **Servicio Web:** `frontend/src/app/features/shared/services/notification-push.service.ts`
* **Móvil Flutter:** `mobile/lib/features/notifications/notifications_page.dart` y `push_notification_service.dart`
* **Mensajes en UI:** Notificación emergente: `"¡Tu pedido está listo para retirar en la Sucursal Centro!"`

##### Checklist de Implementación
- [x] Backend: Integración con Firebase Admin SDK y tabla `user_device_tokens`.
- [x] Frontend: Campana de notificaciones con contador de no leídas en `app-shell.component.html`.
- [x] Móvil: Manejador de notificaciones push en primer plano y segundo plano en Flutter.
- [x] Verificación: Despacho de push tras cambio de estado de pedido a `ready_for_pickup`.

---

### Módulo 4: Business Intelligence y Reportes

#### CU13 – Dashboard de control y métricas
* **Módulo:** M4: Business Intelligence
* **Actor Principal:** Administrador
* **Estado:** **Hecho** (Implementado en `backend/app/routes/dashboard_routes.py` y `admin-home-page`) | **Plataforma:** Web
* **Descripción Funcional:** Tablero visual interactivo con KPIs comerciales: facturación total, prendas vendidas, ranking de productos y nivel de inventario por sucursal y fechas.

##### Endpoints Backend
```http
GET /api/dashboard/kpis?branch_id=all&period=month
Headers: Authorization: Bearer <admin_jwt>
Response 200 OK:
{
  "statusCode": 200,
  "message": "Métricas del dashboard obtenidas",
  "data": {
    "total_revenue": 128450.00,
    "units_sold": 842,
    "average_ticket": 152.55,
    "top_products": [ ... ]
  }
}

Response 403 Forbidden:
{
  "statusCode": 403,
  "message": "No tenés permisos para visualizar métricas globales de otras sucursales",
  "error": "HTTPException"
}
```

##### Ubicación en Frontend (Angular)
* **Página y Vista:** `frontend/src/app/features/admin/pages/admin-home-page.component.ts` (`admin-home-page.component.html`)
* **Servicio API:** `frontend/src/app/features/shared/services/dashboard-api.service.ts`
* **Ruta Angular:** `/app/admin`
* **Mensajes en UI:** Muestra datos analíticos y el mensaje de estado de carga proveniente del backend.

##### Checklist de Implementación
- [x] Backend: Endpoints de agregación SQL optimizados en `dashboard_routes.py`.
- [x] Frontend: Tarjetas de KPIs y gráficos analíticos en `admin-home-page`.
- [x] Verificación: Filtrar métricas por sucursal específica y verificar coincidencia con ventas reales.

---

#### CU14 – Generación y exportación de reportes
* **Módulo:** M4: Business Intelligence
* **Actor Principal:** Administrador
* **Estado:** **Hecho** (Implementado en `backend/app/routes/report_routes.py`) | **Plataforma:** Web
* **Descripción Funcional:** Consultas tabulares detalladas de transacciones, existencias y movimientos con filtros combinados y exportación a archivos CSV.

##### Endpoints Backend
```http
GET /api/reports/sales?start_date=2026-04-01&end_date=2026-04-10
GET /api/reports/export/csv?type=sales&start_date=2026-04-01&end_date=2026-04-10
Headers: Authorization: Bearer <admin_jwt>
Response 200 OK:
Content-Type: text/csv

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "El rango de fechas especificado es inválido (fecha inicio mayor a fecha fin)",
  "error": "HTTPException"
}
```

##### Ubicación en Frontend (Angular)
* **Página y Vista:** `frontend/src/app/features/admin/pages/admin-reports-page.component.ts`
* **Servicio API:** `frontend/src/app/features/shared/services/reports-api.service.ts`
* **Ruta Angular:** `/app/admin/reports`
* **Mensajes en UI:** Toast: `"Archivo CSV generado exitosamente. La descarga comenzará automáticamente."`

##### Checklist de Implementación
- [x] Backend: Streaming de archivos CSV en `report_routes.py`.
- [x] Frontend: Filtros avanzados y botón de descarga en `admin-reports-page`.
- [x] Verificación: Descargar reporte masivo de ventas y validar estructura de columnas.

---

### Módulo 5: Promociones, Fidelización y Experiencia de Cliente

#### CU15 – Gestionar y aplicar cupones promocionales
* **Módulo:** M5: Promociones y Fidelización
* **Actor Principal:** Cliente (aplica), Administrador / Encargado (crean)
* **Estado:** **Hecho** (Implementado en `promotion_routes.py`, `cart_service.py` y `promotions-page`) | **Plataforma:** Ambas
* **Descripción Funcional:** Emisión de códigos promocionales alfanuméricos con porcentaje o importe fijo, vigencia temporal, tope de usos y aplicación directa en el checkout.

##### Endpoints Backend
```http
POST /api/cart/apply-coupon
Headers: Authorization: Bearer <jwt>
Request Body: { "coupon_code": "PROMOVERANO20" }
Response 200 OK:
{
  "statusCode": 200,
  "message": "Cupón de descuento aplicado exitosamente",
  "data": {
    "discount_amount": 25.00,
    "new_subtotal": 100.00
  }
}

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "El cupón ingresado no existe o se encuentra vencido",
  "error": "HTTPException"
}

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "El cupón ha alcanzado el límite máximo de usos permitidos",
  "error": "HTTPException"
}
```

##### Ubicación en Frontend (Angular & Móvil)
* **Páginas y Vistas:** `frontend/src/app/features/cliente/pages/cart-page.component.ts`, `frontend/src/app/features/admin/pages/admin-promotions-page.component.ts`
* **Servicio API:** `frontend/src/app/features/shared/services/promotion-api.service.ts`
* **Móvil Flutter:** Input de cupón en `mobile/lib/features/cart/cart_page.dart`
* **Mensajes en UI:** El carrito muestra exactamente el mensaje del backend: `"Cupón de descuento aplicado exitosamente"` o el error si está vencido.

##### Checklist de Implementación
- [x] Backend: Modelo `promotion_codes` y validación en `cart_service.py`.
- [x] Frontend: Sección de cupón promocional en la vista del carrito de compras.
- [x] Móvil: Campo de cupón promocional en la pantalla de checkout de Flutter.
- [x] Verificación: Validar restricción de tope de usos y fechas de vigencia.

---

#### CU16 – Gestionar lista de deseos (*Wishlist*)
* **Módulo:** M5: Promociones y Fidelización
* **Actor Principal:** Cliente
* **Estado:** Pendiente | **Plataforma:** Ambas
* **Descripción Funcional:** Permite al cliente autenticado guardar prendas en su lista de favoritos mediante el botón de corazón en catálogo y detalle, con vista consolidada para transferir directamente al carrito.

##### Endpoints Backend
```http
GET /api/wishlist
Headers: Authorization: Bearer <client_jwt>
Response 200 OK:
{
  "statusCode": 200,
  "message": "Lista de deseos obtenida exitosamente",
  "data": [
    {
      "id": "wish_01",
      "product_id": "770e8400-e29b-41d4-a716-446655440001",
      "product_name": "Tapado Lana Premium",
      "price": 280.00,
      "image_url": "https://storage.plataforma.com/img/tapado.jpg",
      "in_stock": true
    }
  ]
}
```
```http
POST /api/wishlist/items
Headers: Authorization: Bearer <client_jwt>
Request Body: { "product_id": "770e8400-e29b-41d4-a716-446655440001" }
Response 201 Created:
{
  "statusCode": 201,
  "message": "Prenda añadida a tu lista de deseos",
  "data": { "wishlist_item_id": "wish_01" }
}

Response 404 Not Found:
{
  "statusCode": 404,
  "message": "La prenda seleccionada no existe en el catálogo",
  "error": "HTTPException"
}

Response 409 Conflict:
{
  "statusCode": 409,
  "message": "La prenda ya se encuentra en tu lista de deseos",
  "error": "HTTPException"
}
```
```http
DELETE /api/wishlist/items/{product_id}
POST /api/wishlist/items/{product_id}/move-to-cart
Response 200 OK:
{
  "statusCode": 200,
  "message": "Prenda movida al carrito de compras con éxito"
}

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "No hay stock disponible para mover la prenda al carrito",
  "error": "HTTPException"
}
```

##### Ubicación en Frontend (Angular & Móvil)
* **Página y Vista:** `frontend/src/app/features/cliente/pages/wishlist-page.component.ts` (`wishlist-page.component.html`)
* **Componente de Botón:** `frontend/src/app/features/cliente/components/wishlist-toggle-button.component.ts`
* **Servicio API:** `frontend/src/app/features/shared/services/wishlist-api.service.ts`
* **Modelo TypeScript:** `frontend/src/app/features/shared/models/wishlist.model.ts`
* **Ruta Angular:** `/app/cliente/wishlist` (`canActivate: [roleGuard(['cliente'])]`)
* **Integración en Menú:** Ítem `"Lista de deseos"` en la barra de navegación del Cliente y enlace en la pantalla de Perfil.
* **Móvil Flutter:** `mobile/lib/features/profile/wishlist_page.dart` accesible desde el Menú de Perfil.
* **Mensajes en UI:** Toast con `res.message`: `"Prenda añadida a tu lista de deseos"`.

##### Checklist de Implementación
- [ ] Backend: Modelo `WishlistItem` con claves `user_id`, `product_id`, `tenant_id` y restricción de unicidad.
- [ ] Backend: Endpoints CRUD `/api/wishlist/...` y acción `/move-to-cart`.
- [ ] Frontend: Crear `WishlistApiService` e integrarlo en tarjetas de producto y detalle.
- [ ] Frontend: Desarrollar página `wishlist-page` con grilla de favoritos y botón para mover al carrito.
- [ ] Móvil: Pantalla de favoritos en Flutter integrada al menú de perfil.
- [ ] Verificación: Añadir prenda a favoritos y verificar persistencia entre sesiones.

---

#### CU17 – Fidelización y billetera de puntos (*Loyalty*)
* **Módulo:** M5: Promociones y Fidelización
* **Actor Principal:** Cliente, Cajero
* **Estado:** Pendiente | **Plataforma:** Ambas
* **Descripción Funcional:** Motor de fidelización basado en los `garment_points` configurados en las prendas. Acumula puntos tras compras completadas y permite canjearlos como descuento monetario en compras digitales o en caja física.

##### Endpoints Backend
```http
GET /api/loyalty/balance
Headers: Authorization: Bearer <jwt>
Response 200 OK:
{
  "statusCode": 200,
  "message": "Saldo de puntos de fidelización obtenido",
  "data": {
    "total_points": 450,
    "cash_equivalent": 45.00,
    "tier": "Gold"
  }
}
```
```http
POST /api/loyalty/redeem
Headers: Authorization: Bearer <jwt>
Request Body:
{
  "order_or_sale_id": "ord_9901",
  "points_to_redeem": 200
}
Response 200 OK:
{
  "statusCode": 200,
  "message": "Puntos canjeados correctamente en la compra",
  "data": {
    "discount_applied": 20.00,
    "remaining_points": 250
  }
}

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "Puntos insuficientes para realizar el canje solicitado",
  "error": "HTTPException"
}

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "El valor del canje no puede superar el importe total de la orden",
  "error": "HTTPException"
}
```

##### Ubicación en Frontend (Angular & Móvil)
* **Páginas y Vistas:** `frontend/src/app/features/cliente/pages/loyalty-page.component.ts` (`loyalty-page.component.html`), `frontend/src/app/features/cajero/pages/caja-page.component.ts` (Canje en mostrador)
* **Servicio API:** `frontend/src/app/features/shared/services/loyalty-api.service.ts`
* **Modelo TypeScript:** `frontend/src/app/features/shared/models/loyalty.model.ts`
* **Rutas Angular:** `/app/cliente/loyalty`, `/app/cajero/caja`
* **Móvil Flutter:** `mobile/lib/features/profile/loyalty_points_page.dart` accesible desde el Menú de Perfil.
* **Mensajes en UI:** La vista muestra directamente el mensaje del backend: `"Puntos canjeados correctamente en la compra"`.

##### Checklist de Implementación
- [ ] Backend: Modelar tablas `loyalty_accounts` y `loyalty_ledger_transactions` vinculadas a `tenant_id`.
- [ ] Backend: Hook post-venta para acreditar puntos automáticos según las prendas adquiridas.
- [ ] Backend: Endpoints `/api/loyalty/balance` y `/api/loyalty/redeem`.
- [ ] Frontend: Crear `LoyaltyApiService` y pantalla `loyalty-page` con nivel de cliente e historial.
- [ ] Frontend: Integrar selector de canje de puntos en el módulo de caja (`caja-page.component.ts`).
- [ ] Verificación: Completar compra presencial y constatar acreditación inmediata de puntos.

---

#### CU18 – Emitir y comprar tarjetas de regalo (*Gift Cards*)
* **Módulo:** M5: Promociones y Fidelización
* **Actor Principal:** Cliente
* **Estado:** Pendiente | **Plataforma:** Ambas
* **Descripción Funcional:** Proceso de compra de vouchers prepagados con saldo configurable ($20, $50, $100), dedicatoria personalizada y generación de código alfanumérico único con código QR descargable y enviado por email.

##### Endpoints Backend
```http
POST /api/gift-cards/purchase
Headers: Authorization: Bearer <client_jwt>
Request Body:
{
  "amount": 50.00,
  "recipient_name": "Camila Morales",
  "recipient_email": "camila@gmail.com",
  "custom_message": "¡Feliz cumpleaños Cami!",
  "payment_method": "stripe"
}
Response 201 Created:
{
  "statusCode": 201,
  "message": "Tarjeta de regalo adquirida y enviada por correo al destinatario",
  "data": {
    "card_code": "GIFT-2026-X89Q",
    "qr_code_url": "https://storage.plataforma.com/qr/gift_x89q.png",
    "amount": 50.00
  }
}

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "El importe de la tarjeta de regalo debe ser mayor o igual a $10.00",
  "error": "HTTPException"
}
```
```http
GET /api/gift-cards/my-purchases
GET /api/gift-cards/verify/{code}
Response 404 Not Found:
{
  "statusCode": 404,
  "message": "Tarjeta de regalo no encontrada con el código ingresado",
  "error": "HTTPException"
}
```

##### Ubicación en Frontend (Angular & Móvil)
* **Página y Vista:** `frontend/src/app/features/cliente/pages/gift-cards-page.component.ts` (`gift-cards-page.component.html`)
* **Servicio API:** `frontend/src/app/features/shared/services/gift-card-api.service.ts`
* **Modelo TypeScript:** `frontend/src/app/features/shared/models/gift-card.model.ts`
* **Ruta Angular:** `/app/cliente/gift-cards` (`canActivate: [roleGuard(['cliente'])]`)
* **Móvil Flutter:** `mobile/lib/features/profile/gift_cards_page.dart`
* **Mensajes en UI:** Toast: `"Tarjeta de regalo adquirida y enviada por correo al destinatario"`.

##### Checklist de Implementación
- [ ] Backend: Modelar tabla `gift_cards` con código hash único, saldos y estado.
- [ ] Backend: Generador de código QR y envío de correo con plantilla HTML.
- [ ] Frontend: Desarrollar pantalla `gift-cards-page` con previsualizador visual de tarjeta de regalo.
- [ ] Móvil: Pantalla de compra y listado de Gift Cards en Flutter.
- [ ] Verificación: Adquirir una Gift Card y comprobar la validez del código QR generado.

---

#### CU19 – Gestionar billetera digital (*Store Wallet*)
* **Módulo:** M5: Promociones y Fidelización
* **Actor Principal:** Cliente, Cajero
* **Estado:** Pendiente | **Plataforma:** Ambas
* **Descripción Funcional:** Billetera digital unificada del usuario. Permite canjear Gift Cards acreditando saldo, consultar el balance monetario disponible y pagar total o parcialmente en checkout web/móvil o en caja escaneando el código de usuario. Recibe además los reembolsos por devoluciones (RMA).

##### Regla de Navegación e Integración UI
* **Ubicación en el Menú de Perfil (App Móvil y Web):**
  - **En la App Móvil (Flutter):** En la pantalla de perfil (`ProfilePage`), en el mismo listado donde se accede a "Mis reservas" y "Mis pedidos", debe existir la opción destacada **"Mi Billetera Digital"** con ícono de billetera, que muestra el saldo actual y permite ingresar códigos de Gift Cards.
  - **En el Frontend Web (Angular):** En la página de perfil (`/app/perfil`) y en el sidebar del cliente (`app-shell.component.ts`), opción directa hacia `/app/cliente/wallet`.

##### Endpoints Backend
```http
GET /api/wallet/balance
Headers: Authorization: Bearer <jwt>
Response 200 OK:
{
  "statusCode": 200,
  "message": "Saldo de billetera virtual obtenido",
  "data": {
    "balance": 175.50,
    "currency": "BOB"
  }
}
```
```http
POST /api/wallet/redeem-gift-card
Headers: Authorization: Bearer <client_jwt>
Request Body: { "card_code": "GIFT-2026-X89Q" }
Response 200 OK:
{
  "statusCode": 200,
  "message": "Gift Card canjeada exitosamente. Se acreditaron $50.00 en tu saldo.",
  "data": {
    "credited_amount": 50.00,
    "new_balance": 225.50
  }
}

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "El código de la tarjeta de regalo no es válido o ya fue canjeado",
  "error": "HTTPException"
}

Response 404 Not Found:
{
  "statusCode": 404,
  "message": "La tarjeta de regalo no existe o ha expirado",
  "error": "HTTPException"
}
```
```http
POST /api/wallet/pay
Request Body: { "order_id": "ord_1020", "amount_to_debit": 120.00 }
Response 200 OK:
{
  "statusCode": 200,
  "message": "Pago debitado exitosamente de la billetera virtual"
}

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "Saldo insuficiente en la billetera virtual para completar la operación",
  "error": "HTTPException"
}
```
```http
GET /api/wallet/transactions
```

##### Ubicación en Frontend (Angular & Móvil)
* **Página y Vista Web:** `frontend/src/app/features/cliente/pages/wallet-page.component.ts` (`wallet-page.component.html`)
* **Integración en Perfil Web:** Componente `profile-page.component.html` con tarjeta de saldo y enlace a `/app/cliente/wallet`.
* **Servicio API:** `frontend/src/app/features/shared/services/wallet-api.service.ts`
* **Modelo TypeScript:** `frontend/src/app/features/shared/models/wallet.model.ts`
* **Ruta Angular:** `/app/cliente/wallet` (`canActivate: [roleGuard(['cliente'])]`)
* **Móvil Flutter:** `mobile/lib/features/profile/wallet_page.dart` con acceso directo desde `ProfilePage`.
* **Mensajes en UI:** Muestra en pantalla el mensaje exacto del backend: `"Gift Card canjeada exitosamente. Se acreditaron $50.00 en tu saldo."` o `"Saldo insuficiente en la billetera virtual para completar la operación"`.

##### Checklist de Implementación
- [ ] Backend: Modelar tablas `user_wallets` y `wallet_transactions` con concurrencia segura y aislamiento por `tenant_id`.
- [ ] Backend: Endpoints `/api/wallet/balance`, `/api/wallet/redeem-gift-card`, `/api/wallet/pay` y transacciones.
- [ ] Frontend: Desarrollar pantalla `wallet-page` y tarjeta de saldo en la vista de perfil.
- [ ] Frontend: Agregar medio de pago "Billetera Virtual" en el checkout del carrito (`cart-page.component.ts`).
- [ ] Móvil: Añadir botón "Mi Billetera Digital" en el menú de `ProfilePage` en Flutter y vista de saldo.
- [ ] Verificación: Cargar una tarjeta de regalo y realizar el pago total de un pedido descontando del saldo.

---

### Módulo 6: Logística, Despacho y Posventa

#### CU20 – Delivery y despacho a domicilio
* **Módulo:** M6: Logística y Posventa
* **Actor Principal:** Cliente (solicita y certifica con PIN), Delivery (despacha)
* **Estado:** Pendiente | **Plataforma:** Ambas
* **Descripción Funcional:** Despacho de pedidos a domicilio con libreta de direcciones, cotización de flete por distancia y estados (`shipped`, `in_transit`, `delivered`). Incorpora hoja de ruta para el repartidor y validación de entrega mediante código PIN de seguridad provisto por el cliente.

##### Regla de Navegación e Integración UI
1. **Seguimiento Activo en la Pantalla Principal (Web y App Móvil):**
   - Cuando el cliente tenga un pedido en curso (`in_transit` o `shipped`), la **pantalla principal (Home)** desplegará una **Tarjeta de Seguimiento en Vivo (*Active Delivery Card*)** destacada en la parte superior.
   - Mostrará el estado en tiempo real (ej. *"Tu pedido va en camino"*), el nombre del repartidor y el **Código PIN de seguridad de 4 dígitos** que el cliente debe mostrar para recibir su paquete.
2. **Opción en la Sección de Perfil:**
   - En la sección del perfil donde se listan "Mis reservas" y "Mis pedidos", debe agregarse la opción **"Mis Envíos" / "Mis Deliverys"** tanto en la web (`/app/cliente/deliveries`) como en la app móvil (`ProfilePage`), permitiendo ver el historial completo de envíos a domicilio.

##### Endpoints Backend
```http
POST /api/delivery/quotes
Headers: Authorization: Bearer <client_jwt>
Request Body:
{
  "branch_id": "branch_central",
  "destination_address": "Av. San Martín 450",
  "latitude": -17.7833,
  "longitude": -63.1821
}
Response 200 OK:
{
  "statusCode": 200,
  "message": "Cotización de envío calculada",
  "data": {
    "distance_km": 4.2,
    "shipping_cost": 15.00,
    "estimated_minutes": 35
  }
}

Response 422 Unprocessable Entity:
{
  "statusCode": 422,
  "message": "La dirección de entrega se encuentra fuera del radio de cobertura",
  "error": "HTTPException"
}
```
```http
GET /api/delivery/routes
Headers: Authorization: Bearer <delivery_jwt>
Response 200 OK:
{
  "statusCode": 200,
  "message": "Hoja de ruta del día obtenida",
  "data": [
    {
      "order_id": "ord_5521",
      "client_name": "Lucía Méndez",
      "address": "Av. San Martín 450",
      "status": "in_transit"
    }
  ]
}
```
```http
POST /api/delivery/confirm-delivery
Headers: Authorization: Bearer <delivery_jwt>
Request Body:
{
  "order_id": "ord_5521",
  "security_pin": "8492"
}
Response 200 OK:
{
  "statusCode": 200,
  "message": "Entrega confirmada y registrada exitosamente",
  "data": { "delivered_at": "2026-04-10T16:45:00Z" }
}

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "El código PIN de seguridad es incorrecto",
  "error": "HTTPException"
}

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "La orden no se encuentra en estado en tránsito para ser entregada",
  "error": "HTTPException"
}
```
```http
GET /api/delivery/my-orders
```

##### Ubicación en Frontend (Angular & Móvil)
* **Páginas y Vistas Web:**
  - Carrito de compras (sección flete): `frontend/src/app/features/cliente/pages/cart-page.component.ts`
  - Tarjeta de seguimiento en Home: `frontend/src/app/features/cliente/components/active-delivery-card.component.ts` (en `cliente-home-page.component.html`)
  - Listado de envíos en Perfil: `frontend/src/app/features/cliente/pages/my-deliveries-page.component.ts` (`/app/cliente/deliveries`)
  - Hoja de ruta para Delivery: `frontend/src/app/features/delivery/pages/delivery-routes-page.component.ts` (`/app/delivery/routes`)
* **Servicio API:** `frontend/src/app/features/shared/services/delivery-api.service.ts`
* **Modelo TypeScript:** `frontend/src/app/features/shared/models/delivery.model.ts`
* **Móvil Flutter:**
  - Tarjeta de seguimiento activo en `mobile/lib/features/catalog/catalog_page.dart` (Home).
  - Ítem "Mis Envíos" en `mobile/lib/features/profile/profile_page.dart` hacia `deliveries_page.dart`.
* **Mensajes en UI:** El toast proyecta `res.message`: `"Entrega confirmada y registrada exitosamente"` o `"El código PIN de seguridad es incorrecto"` según la respuesta del backend.

##### Checklist de Implementación
- [ ] Backend: Modelar tablas `delivery_addresses` y `delivery_orders` con generación de `security_pin` de 4 dígitos.
- [ ] Backend: Servicio de cotización de flete geográfico y endpoint `/api/delivery/confirm-delivery`.
- [ ] Frontend: Implementar `ActiveDeliveryCardComponent` en `cliente-home-page`.
- [ ] Frontend: Añadir página `my-deliveries-page` y enlace en el menú de perfil / sidebar.
- [ ] Frontend: Pantalla de hoja de ruta y validación de PIN para el rol delivery (`delivery-routes-page`).
- [ ] Móvil: Tarjeta en Home de pedido en curso con PIN visible y listado en Menú de Perfil.
- [ ] Verificación: Crear pedido con delivery, verificar tarjeta activa en Home y confirmar con PIN correcto/incorrecto.

---

#### CU21 – Solicitar y procesar cambios y devoluciones (RMA)
* **Módulo:** M6: Logística y Posventa
* **Actor Principal:** Cliente (solicita), Encargado de sucursal / Administrador (inspecciona y resuelve)
* **Estado:** Pendiente | **Plataforma:** Ambas
* **Descripción Funcional:** Circuito de logística inversa (RMA). El cliente solicita el cambio o devolución de una prenda dentro de los 30 días posteriores a la compra. El encargado inspecciona la prenda en sucursal y la aprueba o rechaza; el sistema reingresa la prenda a stock (o merma) y acredita automáticamente el reembolso en la billetera virtual (`Store Wallet`).

##### Endpoints Backend
```http
POST /api/rma/requests
Headers: Authorization: Bearer <client_jwt>
Request Body:
{
  "order_id": "ord_8812",
  "order_item_id": "item_221",
  "reason": "wrong_size",
  "customer_notes": "Me quedó chico de hombros, solicito crédito en tienda",
  "preferred_resolution": "store_credit"
}
Response 201 Created:
{
  "statusCode": 201,
  "message": "Solicitud de devolución registrada exitosamente",
  "data": {
    "rma_number": "RMA-2026-0914",
    "status": "pending_inspection"
  }
}

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "La prenda supera el plazo máximo permitido de 30 días para cambios y devoluciones",
  "error": "HTTPException"
}
```
```http
PATCH /api/rma/requests/{rma_id}/status
Headers: Authorization: Bearer <encargado_jwt>
Request Body:
{
  "status": "approved",
  "inspection_notes": "Prenda en perfecto estado con etiqueta original",
  "return_to_inventory": true,
  "branch_id": "branch_central"
}
Response 200 OK:
{
  "statusCode": 200,
  "message": "Devolución aprobada. Se acreditó el saldo en la billetera digital del cliente y se restauró el stock.",
  "data": { "rma_id": "rma_9901", "credited_wallet_amount": 140.00 }
}

Response 409 Conflict:
{
  "statusCode": 409,
  "message": "La solicitud de devolución para este ítem ya fue procesada anteriormente",
  "error": "HTTPException"
}
```
```http
GET /api/rma/requests
```

##### Ubicación en Frontend (Angular & Móvil)
* **Páginas y Vistas Web:**
  - Solicitud desde historial de órdenes: `frontend/src/app/features/cliente/pages/rma-request-page.component.ts` (`/app/cliente/returns`)
  - Panel de dictamen para Encargado: `frontend/src/app/features/encargado/pages/rma-review-page.component.ts` (`/app/encargado/returns`)
* **Servicio API:** `frontend/src/app/features/shared/services/rma-api.service.ts`
* **Modelo TypeScript:** `frontend/src/app/features/shared/models/rma.model.ts`
* **Móvil Flutter:** `mobile/lib/features/orders/rma_request_dialog.dart`
* **Mensajes en UI:** Toast proyecta `res.message`: `"Devolución aprobada. Se acreditó el saldo en la billetera digital del cliente y se restauró el stock."`.

##### Checklist de Implementación
- [ ] Backend: Modelar tabla `rma_requests` con estados (`pending_inspection`, `approved`, `rejected`).
- [ ] Backend: Transacción atómica en aprobación para restaurar stock y acreditar `Store Wallet` (CU19).
- [ ] Frontend: Desarrollar pantalla `rma-request-page` para clientes y `rma-review-page` para encargados.
- [ ] Móvil: Botón "Solicitar devolución" en el detalle de pedido de Flutter.
- [ ] Verificación: Aprobar devolución y constatar el incremento de stock y del balance en la billetera virtual.

---

#### CU22 – Progressive Web App (PWA) e Instalabilidad
* **Módulo:** M6: Logística y Posventa
* **Actor Principal:** Cliente, Administrador, Encargado, Cajero (Usuarios Web)
* **Estado:** Pendiente | **Plataforma:** Web
* **Descripción Funcional:** Transformación del frontend Angular en una Progressive Web App (PWA) instalable y de alto rendimiento. Implementa Web App Manifest dinámico/estático (`manifest.webmanifest`), Service Worker con estrategias de caché (`ngsw-config.json` para assets estáticos, fuentes, íconos y vistas del shell), soporte de instalación en pantalla de inicio (*Add to Home Screen* / A2HS), captura del evento `beforeinstallprompt` con prompt personalizado, y detección automática de nuevas versiones para actualizar la app en segundo plano sin fricción.

##### Endpoints Backend
```http
GET /api/pwa/manifest
Response 200 OK:
{
  "statusCode": 200,
  "message": "Configuración de manifiesto PWA obtenida",
  "data": {
    "name": "Boutique Elegance",
    "short_name": "Elegance",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#ffffff",
    "theme_color": "#111827",
    "icons": [
      { "src": "/icons/icon-192x192.png", "sizes": "192x192", "type": "image/png" },
      { "src": "/icons/icon-512x512.png", "sizes": "512x512", "type": "image/png" }
    ]
  }
}
```

##### Ubicación en Frontend (Angular)
* **Manifiesto y Configuración:** `frontend/public/manifest.webmanifest`, `frontend/ngsw-config.json`
* **Servicio PWA:** `frontend/src/app/core/services/pwa.service.ts`
* **Componente Prompt de Instalación:** `frontend/src/app/features/shared/components/pwa-install-prompt.component.ts`
* **Componente Notificador de Actualización:** `frontend/src/app/features/shared/components/pwa-update-prompt.component.ts`
* **Mensajes en UI:**
  - Banner de instalación: `"Instalá nuestra app en tu dispositivo para un acceso rápido y directo."`
  - Alerta de actualización: `"Hay una nueva versión disponible de la plataforma. Hacé clic para actualizar."`

##### Checklist de Implementación
- [ ] Frontend: Configurar paquete `@angular/pwa` y archivo de configuración `ngsw-config.json` con grupos de recursos de aplicación y assets.
- [ ] Frontend: Diseñar y registrar `manifest.webmanifest` con iconos en múltiples resoluciones (192x192, 512x512, maskable) y colores corporativos.
- [ ] Frontend: Implementar `PwaService` para interceptar el evento `beforeinstallprompt` del navegador y exponer el trigger de instalación.
- [ ] Frontend: Desarrollar componente `pwa-install-prompt` integrado de forma no invasiva en el layout principal (`app-shell.component.html`).
- [ ] Frontend: Suscribirse a `SwUpdate.versionUpdates` para notificar al usuario cuando haya un nuevo release desplegado y forzar la recarga limpia.
- [ ] Verificación: Realizar auditoría Lighthouse PWA validando que cumple los criterios de instalabilidad y probar la instalación en escritorio y navegador móvil.

---

#### CU23 – Modo Offline y Sincronización Diferida (Offline-First)
* **Módulo:** M6: Logística y Posventa
* **Actor Principal:** Cajero, Cliente, Encargado, Delivery
* **Estado:** Pendiente | **Plataforma:** Ambas
* **Descripción Funcional:** Arquitectura de tolerancia a desconexión (*Offline-First*). Permite consultar el catálogo cacheado sin conexión a internet y, fundamentalmente, habilita al cajero en la terminal POS de sucursal física (o repartidor en entrega) para registrar ventas y cobros en contingencia. Las transacciones se encolan localmente en IndexedDB (Web) y SQLite (Móvil) con identificadores únicos locales (`operation_id`). Al restablecerse la red, un despachador en segundo plano sincroniza automáticamente los lotes pendientes contra el backend, gestionando el impacto en inventario y resolviendo potenciales conflictos.

##### Endpoints Backend
```http
GET /api/offline/catalog-sync?last_sync_timestamp=2026-04-09T00:00:00Z
Headers: Authorization: Bearer <jwt>
Response 200 OK:
{
  "statusCode": 200,
  "message": "Delta de catálogo para sincronización offline obtenido",
  "data": {
    "server_timestamp": "2026-04-10T12:00:00Z",
    "updated_products": [ ... ],
    "removed_product_ids": [ ... ]
  }
}
```
```http
POST /api/offline/queue-sync
Headers: Authorization: Bearer <jwt>
Request Body:
{
  "queued_operations": [
    {
      "operation_id": "op_local_01",
      "entity": "sale",
      "action": "create",
      "payload": { "branch_id": "b1", "total": 120.00 },
      "created_at_offline": "2026-04-10T11:20:00Z"
    }
  ]
}
Response 200 OK:
{
  "statusCode": 200,
  "message": "Sincronización completada. Se procesaron 1 operaciones locales.",
  "data": { "processed_count": 1, "conflicts": [] }
}

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "Conflicto en sincronización: una o más operaciones offline no pudieron ser aplicadas por inconsistencia de datos",
  "error": "HTTPException"
}
```

##### Ubicación en Frontend (Angular & Móvil)
* **Servicio de Sincronización:** `frontend/src/app/core/services/offline-sync.service.ts`
* **Persistencia Local Web (IndexedDB):** `frontend/src/app/core/services/indexeddb.service.ts`
* **Banner de Conexión:** `frontend/src/app/features/shared/components/offline-indicator-banner.component.ts`
* **Módulo de Caja (Modo Contingencia):** `frontend/src/app/features/cajero/pages/caja-page.component.ts`
* **Móvil Flutter:** Base de datos SQLite y `SyncManager` en `mobile/lib/core/services/offline_sync_service.dart`.
* **Mensajes en UI:** Banner: `"Estás trabajando en modo sin conexión. Tus ventas y cambios se guardan localmente y se sincronizarán al recuperar internet."` Toast: `"Sincronización completada. Se procesaron 1 operaciones locales."`.

##### Checklist de Implementación
- [ ] Backend: Endpoints `/api/offline/catalog-sync` y `/api/offline/queue-sync` con procesamiento atómico de lotes e idempotencia por `operation_id`.
- [ ] Frontend: Servicio `IndexedDbService` para cachear catálogo de productos y almacenar la cola `pending_sales_queue`.
- [ ] Frontend: Habilitar emisión de ventas en modo contingencia en `caja-page.component.ts` cuando `navigator.onLine == false`.
- [ ] Frontend: Escucha reactiva de eventos `online` / `offline` para mostrar `OfflineIndicatorBannerComponent`.
- [ ] Frontend: Despacho automático de la cola en `offline-sync.service.ts` en cuanto se restablece la conexión.
- [ ] Móvil: Cola de mutaciones locales en SQLite con sincronización automática en reconexión.
- [ ] Verificación: Registrar venta en caja sin conexión, reconectar y validar guardado exitoso en base de datos sin duplicados.

---

## 5. Cuadro Resumen de Entregables para el Segundo Parcial

| Módulo | Casos de Uso Implementados (Base) | Casos de Uso Nuevos a Desarrollar | Total |
| :--- | :---: | :---: | :---: |
| **M1: Plataforma SaaS y Seguridad** | 0 | 4 (`CU1`, `CU2`, `CU3`, `CU4`) | 4 |
| **M2: Inteligencia Artificial** | 3 (`CU5`, `CU6`, `CU7`) | 3 (`CU8`, `CU9`, `CU10`) | 6 |
| **M3: Inventario y Operaciones** | 2 (`CU11`, `CU12`) | 0 | 2 |
| **M4: Business Intelligence** | 2 (`CU13`, `CU14`) | 0 | 2 |
| **M5: Promociones y Fidelización** | 1 (`CU15`) | 4 (`CU16`, `CU17`, `CU18`, `CU19`) | 5 |
| **M6: Logística y Posventa** | 0 | 4 (`CU20`, `CU21`, `CU22`, `CU23`) | 4 |
| **TOTALES** | **8 HECHOS** | **15 PENDIENTES** | **23** |
