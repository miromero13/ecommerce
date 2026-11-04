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

## 3. Matriz General de Casos de Uso (CU1 al CU28)

| **ID** | **Caso de uso** | **Módulo** | **Estado en Código** | **Actor(es) principal** | **Plataforma** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CU1** | **Aprovisionamiento y gestión de organizaciones (Tenants)** | M1: Plataforma SaaS y Seguridad | **Hecho** | Superadministrador | Web |
| **CU2** | **Gestión del catálogo de planes de suscripción SaaS** | M1: Plataforma SaaS y Seguridad | **Hecho** | Superadministrador | Web |
| **CU3** | **Gestión granular de roles y permisos (RBAC)** | M1: Plataforma SaaS y Seguridad | **Hecho** | Superadministrador, Administrador | Web |
| **CU4** | **Landing page y catálogo de planes** | M1: Plataforma SaaS y Seguridad | **Hecho** | Prospecto / Marca B2B | Web |
| **CU5** | **Usar vestidor virtual en tiempo real** | M2: Inteligencia Artificial | **Hecho** | Cliente | Móvil / Web |
| **CU6** | **Recibir recomendaciones de catálogo** | M2: Inteligencia Artificial | **Hecho** | Cliente | Ambas |
| **CU7** | **Consultar asistente virtual / Chatbot** | M2: Inteligencia Artificial | **Hecho** | Cliente | Ambas |
| **CU8** | **Generar reportes inteligentes con IA y Machine Learning** | M2: Inteligencia Artificial | **Hecho** | Administrador | Web |
| **CU9** | **Reabastecimiento automático de stock (Sistema Experto)** | M2: Inteligencia Artificial | **Hecho** | Administrador, Sistema | Web |
| **CU10** | **Ingesta de mercadería con RPA e IA** | M2: Inteligencia Artificial | **Hecho** | Proveedor, Sistema | Web |
| **CU11** | **Traspaso manual de inventario** | M3: Inventario y Operaciones | **Hecho** | Administrador, Encargado | Web |
| **CU12** | **Notificaciones push móviles** | M3: Inventario y Operaciones | **Hecho** | Cliente, Sistema | Móvil |
| **CU13** | **Dashboard de control y métricas** | M4: Business Intelligence | **Hecho** | Administrador | Web |
| **CU14** | **Generación y exportación de reportes** | M4: Business Intelligence | **Hecho** | Administrador | Web |
| **CU15** | **Gestionar y aplicar cupones promocionales** | M5: Promociones y Fidelización | **Hecho** | Cliente, Admin, Encargado | Ambas |
| **CU16** | **Gestionar lista de deseos (*Wishlist*)** | M5: Promociones y Fidelización | **Hecho** | Cliente | Ambas |
| **CU17** | **Fidelización y billetera de puntos (*Loyalty*)** | M5: Promociones y Fidelización | **Hecho** | Cliente, Cajero | Ambas |
| **CU18** | **Emitir y comprar tarjetas de regalo (*Gift Cards*)** | M5: Promociones y Fidelización | **Pendiente** | Cliente | Ambas |
| **CU19** | **Gestionar billetera digital (*Store Wallet*)** | M5: Promociones y Fidelización | **Pendiente** | Cliente, Cajero | Ambas |
| **CU20** | **Delivery y despacho a domicilio** | M6: Logística y Posventa | **Pendiente** | Cliente, Delivery | Ambas |
| **CU21** | **Solicitar y procesar cambios y devoluciones (RMA)** | M6: Logística y Posventa | **Pendiente** | Cliente, Encargado, Admin | Ambas |
| **CU22** | **Progressive Web App (PWA) e Instalabilidad** | M6: Logística y Posventa | **Pendiente** | Cliente, Todos | Web |
| **CU23** | **Modo Offline y Sincronización Diferida (Offline-First)** | M6: Logística y Posventa | **Pendiente** | Cajero, Cliente, Delivery | Ambas |
| **CU24** | **Restablecimiento y control de inventario por devoluciones y mermas** | M6: Logística y Posventa | **Pendiente** | Encargado, Administrador | Web |
| **CU25** | **Resolución de conflictos de inventario y notificación en ventas offline** | M6: Logística y Posventa | **Pendiente** | Cajero, Cliente, Sistema | Ambas |
| **CU26** | **Personalización de identidad y marca del tenant (Branding)** | M1: Plataforma SaaS y Seguridad | **Hecho** | Administrador, Superadministrador | Web / Móvil |
| **CU27** | **Contratación y onboarding de suscripción B2B** | M1: Plataforma SaaS y Seguridad | **Hecho** | Prospecto / Marca B2B, Superadmin | Web |
| **CU28** | **Monitoreo de consumo y cambio de plan B2B** | M1: Plataforma SaaS y Seguridad | **Hecho** | Administrador | Web |

---

## 4. Especificación Técnica Detallada por Caso de Uso

---

### Módulo 1: Plataforma SaaS, Seguridad y Comercial

#### CU1 – Aprovisionamiento y gestión de organizaciones (Tenants)
* **Módulo:** M1: Plataforma SaaS y Seguridad
* **Actor Principal:** Superadministrador
* **Estado:** Hecho | **Plataforma:** Web
* **Descripción Funcional y Alcance:**
  Aprovisionamiento administrativo y gobierno del ciclo de vida de organizaciones/inquilinos (*Tenants*) en la plataforma SaaS. El Superadministrador registra nuevas empresas asignando su razón social, identificador único (*slug*), subdominio exclusivo (`{subdomain}.plataforma.com`), correo de contacto principal, país y moneda comercial.
  1. **Aislamiento Multi-Tenant:** Cada tenant creado opera sobre un entorno lógico estrictamente aislado mediante `tenant_id` (ver especificación de arquitectura y migración transversal en la **Sección 1.5**).
  2. **Ciclo de Vida y Estados:** El Superadministrador consulta el listado global de organizaciones con su estado (`pending_subscription`, `active`, `suspended`), planes asignados y fechas de registro. Puede modificar datos de contacto o suspender una empresa (`suspended`), lo que inhabilita de inmediato el acceso a todo su personal y oculta sus productos del catálogo público.
  3. **Sesión de Soporte / Impersonación:** El Superadministrador puede acceder directamente al panel administrativo de cualquier empresa cliente con un token delegado (`POST /api/saas/tenants/{tenant_id}/panel-session`) para resolver incidencias técnicas o configuración asistida sin necesidad de conocer las credenciales del cliente.

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
POST /api/saas/tenants/{tenant_id}/panel-session
```

##### Ubicación en Frontend (Angular)
* **Página y Vista:** `frontend/src/app/features/admin/pages/tenant-management-page.component.ts` (`tenant-management-page.component.html`)
* **Servicio API:** `frontend/src/app/features/shared/services/tenant-api.service.ts`
* **Modelo TypeScript:** `frontend/src/app/features/shared/models/tenant.model.ts`
* **Ruta Angular:** `/app/superadmin/tenants` o `/app/admin/tenants` (`canActivate: [roleGuard(['superadministrador'])]`)
* **Integración en Menú:** Ítem `"Empresas / Tenants"` en `sidebarSections` de Superadministrador en `app-shell.component.ts`.
* **Mensajes en UI:** La vista consume y muestra directamente el `message` del backend vía `toast.success(res.message)` o `toast.error(getErrorMessage(err, 'No se pudo crear la empresa'))`.

##### Checklist de Implementación
- [x] Backend: Modelo SQLAlchemy `Tenant` con campos de organización, subdominio, contacto y estado.
- [x] Backend: Endpoints CRUD `/api/saas/tenants` para provisionamiento y configuración de organizaciones por el Superadministrador.
- [x] Backend: Endpoint `/panel-session` para acceso administrativo directo del Superadmin a inquilinos.
- [x] Frontend: Pantalla `tenant-management-page` con listado de organizaciones, filtros, formulario modal de alta y botón de ingreso a panel de empresa.
- [x] Verificación: Registrar un tenant nuevo y verificar unicidad de subdominio y aislamiento estricto de datos con respecto a organizaciones previas.

---

#### CU2 – Gestión del catálogo de planes de suscripción SaaS
* **Módulo:** M1: Plataforma SaaS y Seguridad
* **Actor Principal:** Superadministrador
* **Estado:** **Hecho** | **Plataforma:** Web
* **Descripción Funcional:** Administración comercial de la oferta de suscripciones B2B de la plataforma. El Superadministrador define, crea y actualiza los tiers comerciales (Básico, Profesional, Enterprise), configurando sus tarifas (mensual y anual con descuento), límites operativos estructurales (`max_branches` y `max_garments`) y módulos habilitados (`catalog`, `pos`, `inventory`, `virtual_try_on_2d`, `chatbot`, `smart_reports`).
* **Reglas de negocio:**
  1. Los planes desactivados dejan de ofrecerse inmediatamente a nuevas empresas en la landing pública, pero las empresas con suscripción activa previa conservan sus condiciones hasta el término del período facturado.
  2. La modificación de tarifas o límites de un plan afecta a las nuevas contrataciones y renovaciones futuras, sin alterar retroactivamente el período en curso de los inquilinos.
  3. Los módulos habilitados en el plan condicionan la disponibilidad de funcionalidades en la empresa: si un plan carece de `virtual_try_on_2d`, el vestidor virtual queda inhabilitado en sus productos; si carece de `chatbot`, el asistente virtual excluye los artículos de esa marca.

##### Endpoints Backend
```http
GET /api/saas/plans/admin
Headers: Authorization: Bearer <superadmin_jwt>
Response 200 OK:
{
  "statusCode": 200,
  "message": "Listado completo de planes recuperado",
  "data": [
    {
      "id": "plan_basic_01",
      "name": "Básico",
      "price_monthly": 49.00,
      "price_yearly": 490.00,
      "max_branches": 2,
      "max_garments": 500,
      "features": ["catalog", "pos", "inventory"],
      "is_active": true
    },
    {
      "id": "plan_pro_02",
      "name": "Profesional",
      "price_monthly": 129.00,
      "price_yearly": 1290.00,
      "max_branches": 5,
      "max_garments": 3000,
      "features": ["catalog", "pos", "inventory", "virtual_try_on_2d", "chatbot"],
      "is_active": true
    }
  ]
}
```
```http
POST /api/saas/plans
Headers: Authorization: Bearer <superadmin_jwt>
Request Body:
{
  "name": "Enterprise",
  "price_monthly": 299.00,
  "price_yearly": 2990.00,
  "max_branches": 20,
  "max_garments": 15000,
  "features": ["catalog", "pos", "inventory", "virtual_try_on_2d", "chatbot", "smart_reports"]
}
Response 201 Created:
{
  "statusCode": 201,
  "message": "Plan creado exitosamente",
  "data": { "id": "plan_enterprise_03", "name": "Enterprise", "max_branches": 20, "max_garments": 15000 }
}
```
```http
PATCH /api/saas/plans/{plan_id}
Headers: Authorization: Bearer <superadmin_jwt>
Request Body:
{
  "is_active": false
}
Response 200 OK:
{
  "statusCode": 200,
  "message": "Plan actualizado exitosamente",
  "data": { "id": "plan_basic_01", "is_active": false }
}
```
```http
GET /api/saas/plans                                    (catálogo público de planes vigentes)
```

##### Ubicación en Frontend (Angular)
* **Página y Vista:** `frontend/src/app/features/superadmin/pages/plan-management-page.component.ts` (`plan-management-page.component.html`)
* **Servicio API:** `frontend/src/app/features/shared/services/subscription-api.service.ts`
* **Modelo TypeScript:** `frontend/src/app/features/shared/models/subscription.model.ts`
* **Ruta Angular:** `/app/superadmin/plans` (`canActivate: [roleGuard(['superadministrador'])]`)
* **Integración en Menú:** Ítem `"Planes de Suscripción"` en `sidebarSections` de Superadministrador en `app-shell.component.ts`.
* **Mensajes en UI:** Notificaciones Toast al guardar o editar planes basadas en `response.message`.

##### Checklist de Implementación
- [x] Backend: Modelo SQLAlchemy `SaaSPlan` con campos de tarifa mensual/anual, cupos y lista de características.
- [x] Backend: Endpoints `/api/saas/plans/admin` (listado con inactivos), `POST /api/saas/plans` y `PATCH /api/saas/plans/{id}`.
- [x] Backend: Filtro de planes públicos activos en `GET /api/saas/plans`.
- [x] Frontend: Pantalla `plan-management-page` con tabla de planes, edición de cuotas, selección de módulos y switch de activación.
- [x] Verificación: Probar creación y desactivación de planes verificando su reflejo en la landing y protección de suscriptores previos.

---

#### CU3 – Gestión granular de roles y permisos (RBAC dinámico)
* **Módulo:** M1: Plataforma SaaS y Seguridad
* **Actor Principal:** Superadministrador, Administrador
* **Estado:** **Hecho** (`rbac_service.py`, `rbac_routes.py`, migración `0042`, `rbac-roles-page`) | **Plataforma:** Web
* **Regla implementada:** un rol personalizado **reemplaza** los permisos del rol base (perfil restrictivo); sin roles personalizados rigen los permisos por defecto del rol base. Administrador y superadministrador tienen todos los permisos. Solo se asignan roles al personal de la propia empresa (encargado, cajero, proveedor).
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
  "message": "No tienes permisos suficientes para realizar esta acción",
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
- [x] Backend: Modelar tablas `permissions`, `roles`, `role_permissions` y `user_roles`.
- [x] Backend: Inyectar matriz de permisos en el payload del token JWT (`permissions: [...]`).
- [x] Backend: Crear dependencia FastAPI `require_permission("permission_name")`.
- [x] Frontend: Crear directiva `*hasPermission="'inventory:transfer'"` para ocultar elementos en el DOM.
- [x] Frontend: Desarrollar pantalla `rbac-roles-page` con checkboxes de permisos agrupados por módulo.
- [x] Verificación: Asignar rol restrictivo a un usuario de prueba y validar bloqueo en endpoints y UI (`tests/test_rbac.py`).

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

#### CU26 – Personalización de identidad y marca del tenant (Branding)
* **Módulo:** M1: Plataforma SaaS y Seguridad
* **Actor Principal:** Administrador de Empresa, Superadministrador
* **Estado:** **Hecho** | **Plataforma:** Web / Móvil
* **Descripción Funcional:** Parametrización visual e identidad corporativa de la organización cliente. Permite cargar el logotipo de la empresa (PNG/JPEG/SVG), definir el color primario corporativo (código hexadecimal) y la moneda comercial operativa (`BOB`). Los atributos de branding se inyectan dinámicamente mediante el servicio `BrandingService` en el shell web (`AppShell`), en la cabecera y pie de los comprobantes PDF de venta y recibos (`simple-pdf.util`), y se descargan en la aplicación móvil Flutter según la tienda activa.
* **Reglas de negocio:**
  1. El logotipo no debe exceder 2 MB y debe ser en formato de imagen estándar (PNG, JPG, SVG, WebP).
  2. Los cambios de logotipo o color primario se reflejan inmediatamente en la sesión de los usuarios que pertenecen a ese tenant sin requerir reinicio del servidor.
  3. Cada empresa mantiene su propia moneda por defecto (`BOB`), la cual rige los precios y cálculos transaccionales de sus órdenes y ventas.

##### Endpoints Backend
```http
GET /api/saas/tenants/me/branding
Headers: Authorization: Bearer <tenant_jwt>
Response 200 OK:
{
  "statusCode": 200,
  "message": "Configuración de branding obtenida",
  "data": {
    "name": "Ayni Moda",
    "logo_url": "/static/tenants/logos/ayni-moda.png",
    "primary_color": "#800020",
    "currency": "BOB"
  }
}
```
```http
POST /api/saas/tenants/me/logo
Headers: Authorization: Bearer <admin_jwt>, Content-Type: multipart/form-data
Body: file: <logo_file>
Response 200 OK:
{
  "statusCode": 200,
  "message": "Logotipo actualizado exitosamente",
  "data": {
    "logo_url": "/static/tenants/logos/ayni-moda-updated.png"
  }
}
```
```http
GET /api/saas/tenants/{tenant_id}/branding
POST /api/saas/tenants/{tenant_id}/logo
PATCH /api/saas/tenants/{tenant_id}                    (actualizar primary_color, name, currency)
```

##### Ubicación en Frontend (Angular & Móvil)
* **Componente:** `frontend/src/app/features/shared/components/tenant-branding-editor/tenant-branding-editor.component.ts`
* **Servicio:** `frontend/src/app/core/services/branding.service.ts`
* **Integración en Shell:** `frontend/src/app/core/layouts/app-shell.component.ts`
* **Generación de Documentos:** `frontend/src/app/core/utils/simple-pdf.util.ts`
* **Mensajes en UI:** Toast: `"Logotipo actualizado exitosamente"` / `"Configuración de marca guardada"`.

##### Checklist de Implementación
- [x] Backend: Campos `logo_url`, `primary_color` y `currency` en el modelo `Tenant`.
- [x] Backend: Endpoints `/api/saas/tenants/me/branding`, `/api/saas/tenants/me/logo` y variantes por `{id}`.
- [x] Frontend: `BrandingService` reactivo que aplica variables CSS (`--primary-color`) en el DOM según la empresa activa.
- [x] Frontend: Componente de edición de branding e inyección de logo/colores en el encabezado de navegación y PDFs.
- [x] Móvil: Consumo del endpoint de branding para personalizar la barra de título y paleta de la tienda.
- [x] Verificación: Subir logo para una empresa y comprobar que no altera el branding de otros tenants.

---

#### CU27 – Contratación y onboarding de suscripción B2B
* **Módulo:** M1: Plataforma SaaS y Seguridad
* **Actor Principal:** Prospecto / Nueva Marca B2B, Superadministrador
* **Estado:** **Hecho** | **Plataforma:** Web
* **Descripción Funcional:** Proceso de suscripción y aprovisionamiento integral de una nueva empresa en la plataforma. La marca interesada selecciona un plan de suscripción del catálogo público, elige ciclo de facturación (mensual o anual con descuento), completa los datos comerciales y de su administrador, e ingresa la tarjeta de pago en la pasarela simulada (Sandbox).
* **Reglas de negocio:**
  1. La transacción es atómica: crea la organización (`Tenant`), el usuario Administrador y el registro de suscripción activa con su respectiva fecha de vencimiento (`end_date`).
  2. El pago es simulado mediante pasarela sandbox con tarjetas de prueba (ej. `4242424242424242`).
  3. Tras la confirmación, se emite el primer recibo/comprobante de pago en PDF y se despacha automáticamente un correo de bienvenida con credenciales seguras mediante la API de Mailtrap.
  4. El Superadministrador dispone de un endpoint administrativo para registrar directamente empresas con pago presencial en efectivo (`/with-subscription`).

##### Endpoints Backend
```http
POST /api/saas/subscriptions/purchase-simulated
Request Body:
{
  "company_name": "Boutique Elegance",
  "admin_name": "Ana Pérez",
  "admin_email": "admin@elegance.com",
  "plan_id": "plan_pro_02",
  "billing_cycle": "monthly",
  "card_number": "4242424242424242",
  "card_holder": "Ana Pérez",
  "card_exp": "12/28",
  "card_cvv": "123"
}
Response 201 Created:
{
  "statusCode": 201,
  "message": "Suscripción activada con éxito. Te enviamos un correo con los datos de acceso.",
  "data": {
    "tenant_id": "e3b0c442-98fc-1c14-9afb-4c72e0500001",
    "tenant_slug": "boutique-elegance",
    "admin_email": "admin@elegance.com",
    "plan_name": "Profesional",
    "subscription_status": "active",
    "end_date": "2026-05-10T12:00:00Z"
  }
}

Response 409 Conflict:
{
  "statusCode": 409,
  "message": "El correo o subdominio ya se encuentra registrado",
  "error": "HTTPException"
}
```
```http
POST /api/saas/tenants/with-subscription               (Superadministrador: alta directa con pago en efectivo)
```

##### Ubicación en Frontend (Angular)
* **Página y Vista:** `frontend/src/app/features/shared/pages/landing-page.component.ts`
* **Componente de Precios y Checkout:** `frontend/src/app/features/shared/components/pricing-table.component.ts`
* **Servicio API:** `frontend/src/app/features/shared/services/subscription-api.service.ts`
* **Ruta Angular:** `/landing` o `/precios`
* **Mensajes en UI:** Notificación de éxito: `"Suscripción activada con éxito. Te enviamos un correo con los datos de acceso."`.

##### Checklist de Implementación
- [x] Backend: Servicio `subscription_service.purchase_simulated` atómico con creación de tenant, admin y suscripción.
- [x] Backend: Integración de despacho de credenciales por email con Mailtrap API.
- [x] Backend: Generación y almacenamiento del primer comprobante de pago de la suscripción.
- [x] Frontend: Formulario de checkout simulado reactivo integrado en `pricing-table.component`.
- [x] Verificación: Contratar un plan Profesional con tarjeta sandbox y comprobar recepción de correo y login de la nueva empresa (`tests/test_saas_subscriptions.py`).

---

#### CU28 – Monitoreo de consumo y cambio de plan B2B
* **Módulo:** M1: Plataforma SaaS y Seguridad
* **Actor Principal:** Administrador de Tenant
* **Estado:** **Hecho** | **Plataforma:** Web
* **Descripción Funcional:** Gestión operativa de la suscripción vigente por parte de la empresa inquilina. El Administrador monitorea el estado del plan, fecha de vencimiento (`end_date`), historial de facturación y cuotas de consumo en tiempo real mediante barras de progreso (sucursales creadas vs. `max_branches`, prendas registradas vs. `max_garments`). Permite ejecutar el cambio de plan (*Upgrade* o *Downgrade*) mediante pasarela simulada.
* **Reglas de negocio:**
  1. Una suscripción activa permite operar normalmente. Si la fecha `end_date` expira, se bloquea la creación de recursos y se inhabilitan módulos de IA hasta su renovación.
  2. **Upgrade de Plan:** El cambio a un plan superior cancela el período anterior, inicia uno nuevo e incrementa de forma inmediata los límites de sucursales y prendas.
  3. **Downgrade Restringido:** No se permite bajar a un plan inferior si el uso actual supera las cuotas del nuevo plan (ej. si la empresa tiene 4 sucursales activas, el backend rechaza cambiar al plan Básico que solo admite 2 con error 400).
  4. **Enforcement de Límites:** Los endpoints de creación de sucursales (`POST /api/branches/`) y prendas (`POST /api/catalog/products`) consultan la cuota vigente y rechazan con HTTP 403 si se alcanzó el tope del plan.

##### Endpoints Backend
```http
GET /api/saas/subscriptions/current
Headers: Authorization: Bearer <admin_jwt>
Response 200 OK:
{
  "statusCode": 200,
  "message": "Suscripción actual obtenida",
  "data": {
    "has_active_subscription": true,
    "plan": {
      "id": "plan_basic_01",
      "name": "Básico",
      "max_branches": 2,
      "max_garments": 500,
      "features": ["catalog", "pos", "inventory"]
    },
    "subscription": {
      "status": "active",
      "billing_cycle": "monthly",
      "end_date": "2026-05-15T00:00:00Z"
    },
    "usage": {
      "branches_count": 2,
      "garments_count": 140
    }
  }
}
```
```http
POST /api/saas/subscriptions/change-plan
Headers: Authorization: Bearer <admin_jwt>
Request Body:
{
  "plan_id": "plan_pro_02",
  "billing_cycle": "yearly",
  "card_number": "4242424242424242"
}
Response 200 OK:
{
  "statusCode": 200,
  "message": "Plan actualizado con éxito. Tu empresa ahora tiene el plan Profesional.",
  "data": {
    "has_active_subscription": true,
    "plan": { "id": "plan_pro_02", "name": "Profesional", "max_branches": 5, "max_garments": 3000 }
  }
}

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "No podés cambiar al plan Básico: tenés 3 sucursales y permite 2.",
  "error": "HTTPException"
}
```
```http
Límites aplicados al crear sucursales o prendas:
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
* **Mensajes en UI:** Notificación de éxito y alertas de límite consumiendo directamente `response.message`.

##### Checklist de Implementación
- [x] Backend: Endpoint `/api/saas/subscriptions/current` con cálculo en tiempo real de recursos usados vs. cuotas.
- [x] Backend: Endpoint `/api/saas/subscriptions/change-plan` con validación estricta de downgrade e inicio de nuevo ciclo.
- [x] Backend: Decorador/dependencia de validación de límites en servicios de sucursales y prendas (HTTP 403).
- [x] Frontend: Pantalla `subscription-page` con barras de progreso de cupos, advertencia de expiración y modal de cambio de plan.
- [x] Verificación: Validar que una empresa con 2 sucursales en plan Básico sea bloqueada al intentar crear una tercera sucursal, y que tras el upgrade a Profesional se habilite de inmediato.

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
* **Estado:** **Hecho** (`backend/app/services/recommendation_service.py`, `recommendation_routes.py`) | **Plataforma:** Ambas
* **Descripción Funcional:** Sugerencias personalizadas de prendas en el catálogo a partir de la matriz de interacciones del cliente, con *fallback* por popularidad para usuarios nuevos (*Cold Start*) y un ajuste por afinidad (categoría, colección, temporada, talla, color y sucursal).
* **Reglas implementadas:**
  * Señales y pesos: vista **1**, carrito **2**, lista de deseos **3** (una vez por prenda), compra **5** (pedido web pagado o compra en caja con el cliente identificado por correo).
  * El modelo ALS se **reentrena cada noche** en segundo plano (`main.py`, junto a la tarea diaria); también se puede entrenar a pedido con `python -m app.services.recommendation_service`.
  * Solo se recomiendan prendas activas, con stock y de empresas **no suspendidas**; se excluye lo que el cliente ya compró.
  * Un cliente solo consulta sus propias recomendaciones.

##### Endpoints Backend
```http
GET /api/recommendations/collaborative/user/{user_id}?branch_id=<uuid opcional>
Headers: Authorization: Bearer <client_jwt>
Response 200 OK:
{
  "statusCode": 200,
  "message": "Recomendaciones obtenidas exitosamente",
  "data": {
    "logic_type": "implicit_als",          // o "popular_fallback" si el cliente aún no tiene vector entrenado
    "user_id": "<uuid>",
    "recommendations": [ { "product_id": "<uuid>", "score": 0.892 } ]
  }
}

Response 403 Forbidden:
{ "statusCode": 403, "message": "Solo puedes consultar tus propias recomendaciones", "error": "HTTPException" }
```
```http
POST /api/catalog/products/{product_id}/view      (cliente: registra la vista; body opcional { "variant_id", "branch_id" })
Response 201: { "statusCode": 201, "message": "Vista de producto registrada" }
```
Las demás señales se registran solas: carrito (`cart_service`), lista de deseos (`wishlist_service`), pedido pagado (`order_service._consume_order`) y venta en caja con cliente identificado (`sales_service.create_sale`).

##### Ubicación en Frontend (Angular & Móvil)
* **Página y Vista:** carrusel de recomendaciones en `frontend/src/app/features/cliente/pages/catalog-page.component.ts` (`catalog-page.component.html`)
* **Servicio API:** `frontend/src/app/features/shared/services/catalog-api.service.ts` (`getCollaborativeRecommendations`, `recordProductView`)
* **Móvil Flutter:** carrusel en `mobile/lib/features/catalog/catalog_page.dart` con `catalog_api.dart`
* **Pruebas:** `backend/tests/test_recommendation_service.py`, `backend/tests/test_recommendation_signals.py`

##### Checklist de Implementación
- [x] Backend: Algoritmo Implicit ALS con NumPy en `recommendation_service.py`.
- [x] Backend: Endpoint `/api/recommendations/collaborative/user/{user_id}` con cálculo vectorial y fallback cold-start.
- [x] Backend: Reentrenamiento nocturno automático del modelo.
- [x] Backend: Compras en caja y lista de deseos como señales; empresas suspendidas excluidas.
- [x] Frontend: Carrusel de productos recomendados en `catalog-page`.
- [x] Móvil: Integración de carrusel de recomendaciones en la portada del catálogo Flutter.
- [x] Verificación: Comprobar actualización de recomendaciones tras registrar nuevas compras (`test_recommendation_signals.py`).

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
* **Estado:** **Hecho** (NLP, regresión, K-Means, cuatro reportes y exportaciones con pruebas automatizadas; falta solo el ensayo en vivo con micrófono) | **Plataforma:** Web
* **Descripción Funcional:** Motor analítico avanzado para la generación de reportes empresariales inteligentes acorde al Desafío V del examen. Permite a usuarios autorizados formular solicitudes en lenguaje natural escrito o por voz (Web Speech API), interpretando intenciones para generar tanto reportes convencionales como reportes predictivos y de patrones:
  1. **Reportes Descriptivos e Históricos (NLP con Gemini):** Traducción de consultas en lenguaje natural a filtros SQL parametrizados y seguros contra datos reales de PostgreSQL, garantizando la demostración de al menos cuatro tipos de reportes (ventas por sucursal, ranking de productos más vendidos, existencias críticas/inventario bajo, y comparativas de ventas entre sucursales).
  2. **Reportes Predictivos con Machine Learning Supervisado:** Invocación de un modelo de regresión real de Scikit-Learn (por defecto con los datos reales de la empresa, completados con sintéticos si faltan muestras; el interruptor «Modo demostración» entrena solo con datos sintéticos reproducibles en memoria) para predecir variables objetivo como la demanda de prendas o la proyección de ventas de la próxima temporada, reportando métricas de evaluación ($R^2$, MSE).
  3. **Reportes de Patrones con Machine Learning No Supervisado:** Invocación de un modelo de clustering (K-Means) para descubrir patrones de compra o segmentar clientes según frecuencia y volumen de compra, reportando métricas de calidad (Silhouette Score).
  4. **Exportación Dinámica:** Capacidad de visualizar resultados en tablas o gráficos dinámicos y exportar los reportes generados a archivos formateados de **Excel (.xlsx)** y **PDF**.

##### Endpoints Backend
```http
POST /api/reports/query
Headers: Authorization: Bearer <admin_jwt>
Request Body:
{
  "query": "Cuánto vendimos de blusas en la sucursal Centro la semana pasada"
}
Response 200 OK:
{
  "statusCode": 200,
  "message": "Reporte interpretado exitosamente",
  "data": {
    "report_type": "sales",
    "format": "pdf",
    "columns": ["branch_name", "quantity_sold", "gross_sales"],
    "filters": { "from_date": "2026-04-01", "to_date": "2026-04-07" },
    "interpretation": "Ventas de la semana solicitada",
    "report": {
      "summary": { "total_sales": "3450.00", "total_units": 23 },
      "rows": [ ... ]
    }
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
  "target_period_weeks": 4,
  "use_synthetic_data": true
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
Request Body:
{ "use_synthetic_data": true }
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
GET /api/reports/export/excel?type=sales&from_date=2026-04-01&to_date=2026-04-10
GET /api/reports/export/pdf?type=sales&from_date=2026-04-01&to_date=2026-04-10
```

**Contrato vigente y métricas:** `/query` conserva `{report_type, format, columns, filters, interpretation, report: {summary, rows}}`; los ejemplos omiten campos secundarios por brevedad. Los identificadores son UUID reales. Los modelos agregan `data_source: {mode, real_samples, synthetic_samples, notice}`. La página usa **datos reales por defecto** (`use_synthetic_data: false`). El interruptor «Modo demostración (solo datos sintéticos)» envía `use_synthetic_data: true`: entrenamiento real de Scikit-Learn solo con datos sintéticos reproducibles en memoria, sin consultar ventas/clientes ni insertar datos o modelos; en ese modo la página avisa que no es un pronóstico del negocio y `data_source` declara `mode: "synthetic"`, `real_samples: 0`. La API mantiene `use_synthetic_data: false` por defecto si se omite: lee datos del tenant y completa con sintéticos cuando faltan muestras (menos de 26 semanas observadas o 30 clientes/3 perfiles distintos). En automático, demanda sigue admitiendo `branch_id` UUID opcional y clusters acepta `{}` o ningún cuerpo. Los ejemplos numéricos de respuesta son ilustrativos, no métricas garantizadas ni prefijadas. Descriptivos, NLP y exportaciones siguen usando datos reales. La evaluación cronológica usa el último 20 %; R² puede ser negativo. Intervalos ±1.96·RMSE aproximados, no garantías. El historial excluye la semana en curso. RFM usa pedidos pagados por cliente, nunca el cajero `Sale.user_id`; los segmentos distinguen clientes reales y sintéticos. Silhouette usa hasta 2000 muestras reproducibles.

Los endpoints ML exigen administrador y `ai_ml_smart_reports` (403 sin prestación); NLP conserva `ai_text_reports`. Nuevos GET: `/api/reports/top-products`, `/branch-comparison`, `/critical-inventory`. Exportación `type=sales|inventory|movements|top_products|branch_comparison|critical_inventory`; filtros `branch_id`, `product_id`, `variant_id`, `from_date`, `to_date`, `q`. Exporta reportes descriptivos y conserva el alcance del encargado. Top 10/comparativa cuentan operaciones completadas y pagadas; stock crítico compara disponible con el mínimo de la sucursal. JSON/CSV anteriores no cambian. Excel trata nombres/SKU como texto, no fórmulas.

##### Ubicación en Frontend (Angular)
* **Página y Vista:** `frontend/src/app/features/admin/pages/admin-reports-page.component.ts` (`admin-reports-page.component.html`)
* **Servicio API:** `frontend/src/app/features/shared/services/reports-api.service.ts`
* **Ruta Angular:** `/app/admin/reports`
* **Mensajes en UI:** El toast proyecta `res.message`: `"Reporte interpretado exitosamente"` y los mensajes de estado del modelo. Las tablas NLP respetan las columnas solicitadas; las descargas descriptivas usan columnas estándar por tipo.

##### Checklist de Implementación
- [x] Backend: Servicio `natural_report_service.py` con prompt estructurado JSON hacia Gemini para interpretar intenciones.
- [x] Backend: Endpoint `/api/reports/query` con ejecución de consultas dinámicas de ventas, inventario y movimientos.
- [x] Frontend: Barra de consulta por voz/texto en `admin-reports-page` con Web Speech API.
- [x] Backend (Datos Sintéticos): Implementar generador de datos sintéticos (`synthetic_data_generator.py`) para entrenamiento y validación de los modelos de Machine Learning.
- [x] Backend (ML Supervisado): Desarrollar y entrenar modelo supervisado de regresión para proyección de demanda y ventas con cálculo de métricas ($R^2$ / MSE).
- [x] Backend (ML No Supervisado): Desarrollar y entrenar modelo no supervisado de clustering (K-Means) para segmentación de clientes y detección de patrones de compra con Silhouette Score.
- [x] Backend (Exportación Excel/PDF): Implementar generación y exportación de reportes dinámicos a Excel (.xlsx con `openpyxl`) y PDF formateado.
- [x] Backend (4 Tipos de Reportes): Probar y asegurar la demostración de los 4 tipos de reportes obligatorios con datos reales (ventas por sucursal, top 10 productos, inventario con menor stock, y comparativa temporal/proyección).
- [x] Frontend: Visualización de gráficos para clusters y proyecciones en `admin-reports-page` y botones de exportación a Excel y PDF.
- [ ] Verificación: Ejecutar en vivo consultas por voz y texto demostrando reportes históricos de PostgreSQL, reportes predictivos de ML supervisado y segmentaciones de ML no supervisado.

---

#### CU9 – Reabastecimiento automático de stock (Sistema Experto)
* **Rama de IA:** **Sistemas Expertos** (Motor de Inferencia de Reglas Determinísticas)
* **Actor Principal:** Administrador, Sistema
* **Estado:** **Hecho** (`expert_replenishment_service.py`, `expert_replenishment_routes.py`, migración `0043`, tarea periódica en `main.py`, `admin-expert-replenishment-page`) | **Plataforma:** Web
* **Regla implementada:** un excedente nunca se promete dos veces; solo participan sucursales activas; aprobar traspasos es atómico (todos o ninguno).
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
* **Integración Principal (Notificaciones Interactivas):** Centro de Notificaciones en `/app/notifications`. Cada sugerencia emitida por el sistema experto genera una tarjeta interactiva con la insignia **🧠 Sistema Experto IA**, detallando sucursal origen con excedente, sucursal destino con stock crítico, justificación de inferencia, y botones de decisión directa: *"Aprobar traspaso"* y *"Descartar sugerencia"*.
* **DESACTIVADO EN NAVEGACIÓN LATERAL:** La sección `/app/admin/expert-replenishment` no se usa como página de navegación en el menú lateral para evitar sobrecargar la interfaz. El reabastecimiento inteligente opera de forma proactiva y por eventos en Notificaciones. La ruta Angular `/app/admin/expert-replenishment` se mantiene registrada únicamente por compatibilidad técnica.
* **Servicio API:** `frontend/src/app/features/shared/services/expert-replenishment-api.service.ts`
* **Modelo TypeScript:** `frontend/src/app/features/shared/models/expert-replenishment.model.ts`
* **Mensajes en UI:** Toast con `res.message`: `"Evaluación del sistema experto finalizada"`, `"Sugerencias de traspaso descartadas"` y `"Órdenes de traspaso automático aplicadas al inventario"`.

##### Checklist de Implementación
- [x] Backend: Servicio `expert_replenishment_service.py` con motor de reglas lógicas basadas en hechos.
- [x] Backend: Endpoints `/api/inventory/expert-replenishment/...` para evaluar, descartar y confirmar transferencias.
- [x] Backend: Disparador reactivo por evento ante quiebre de stock (`notify_low_stock`) + tarea periódica de fondo.
- [x] Frontend: Tarjetas interactivas en `/app/notifications` con aprobación/descarte en 1 clic.
- [x] Frontend: Crear `ExpertReplenishmentApiService` y modelo con soporte de descarte y aprobación.
- [x] Verificación: Provocar nivel de stock crítico en una sucursal y validar la recomendación generada por el motor (`tests/test_expert_replenishment.py`).

---

#### CU10 – Ingesta de mercadería con RPA e IA
* **Rama de IA:** **RPA con IA** (*Intelligent Document Processing* - IDP)
* **Actor Principal:** Proveedor, Sistema
* **Estado:** **Hecho** (`rpa_ingest_service.py`, `rpa_ingest_routes.py`, migración `0044`, `provider-rpa-ingest-page`) | **Plataforma:** Web
* **Regla implementada:** el proveedor, el administrador o el encargado suben el documento (PDF, PNG, JPG o WEBP, máx. 10 MB); Gemini extrae las líneas en segundo plano; confirman el ingreso el administrador o el encargado (solo de su sucursal). Los SKU desconocidos se informan y **nunca se crean**; la confirmación es atómica. Documento de prueba: `docs/demo/remito_demo.pdf`.
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
- [x] Backend: Servicio `rpa_ingest_service.py` con OCR y extracción estructurada con Gemini Flash / Vision.
- [x] Backend: Endpoints `/api/rpa/ingest/...` para subida de documentos, consulta de job y confirmación.
- [x] Frontend: Desarrollar vista `provider-rpa-ingest-page` con zona de arrastre de archivos y grilla de ítems detectados.
- [x] Verificación: Subir un PDF de prueba de remito y corroborar la carga en existencias (`tests/test_rpa_ingest.py`, `docs/demo/remito_demo.pdf`).

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
  "message": "No tienes permisos para visualizar métricas globales de otras sucursales",
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
* **Estado:** **Hecho** (`wishlist_service.py`, `wishlist_routes.py`, migración `0045`) | **Plataforma:** Ambas
* **Regla implementada:** una prenda se guarda una sola vez por cliente; el favorito pertenece a la empresa de la prenda. Mover al carrito exige elegir talla/color, respeta la regla de un carrito por empresa y quita la prenda de la lista solo si se agregó al carrito.
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
Response 200 OK: { "statusCode": 200, "message": "Prenda eliminada de tu lista de deseos" }

POST /api/wishlist/items/{product_id}/move-to-cart
Request Body: { "variant_id": "<uuid>", "branch_id": "<uuid opcional>", "quantity": 1 }
Response 200 OK (data = carrito):
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
* **Página y Vista:** `frontend/src/app/features/cliente/pages/wishlist-page.component.ts` (plantilla en línea)
* **Componente de Botón:** `frontend/src/app/features/cliente/components/wishlist-toggle-button.component.ts`
* **Servicio API:** `frontend/src/app/features/shared/services/wishlist-api.service.ts`
* **Modelo TypeScript:** `frontend/src/app/features/shared/models/wishlist.model.ts`
* **Ruta Angular:** `/app/cliente/wishlist` (`canActivate: [roleGuard(['cliente'])]`)
* **Integración en Menú:** Ítem `"Lista de deseos"` en la barra de navegación del Cliente y enlace en la pantalla de Perfil.
* **Móvil Flutter:** `mobile/lib/features/wishlist/wishlist_page.dart` y `wishlist_api.dart` (tarjeta «Lista de deseos» en `management_page.dart`; corazón en `catalog/product_detail_page.dart`).
* **Mensajes en UI:** Toast con `res.message`: `"Prenda añadida a tu lista de deseos"`.

##### Checklist de Implementación
- [x] Backend: Modelo `WishlistItem` con claves `user_id`, `product_id`, `tenant_id` y restricción de unicidad.
- [x] Backend: Endpoints CRUD `/api/wishlist/...` y acción `/move-to-cart`.
- [x] Frontend: Crear `WishlistApiService` e integrarlo en tarjetas de producto y detalle.
- [x] Frontend: Desarrollar página `wishlist-page` con grilla de favoritos y botón para mover al carrito.
- [x] Móvil: Pantalla de favoritos en Flutter integrada al menú del cliente.
- [x] Verificación: Añadir prenda a favoritos y verificar persistencia (`tests/test_wishlist.py`).

---

#### CU17 – Fidelización y billetera de puntos (*Loyalty*)
* **Módulo:** M5: Promociones y Fidelización
* **Actor Principal:** Cliente, Cajero
* **Estado:** **Hecho** (`loyalty_service.py`, `loyalty_routes.py`, migración `0046`) | **Plataforma:** Ambas
* **Descripción Funcional:** Billetera de puntos **por empresa**. Acumula puntos cuando una compra queda pagada (pedido web o venta en caja con el cliente identificado) y permite canjearlos como descuento en el checkout web/móvil o en caja.
* **Reglas implementadas:**
  * Se gana **1 punto por cada 10 Bs** pagados por prendas (el envío no suma; el anticipo de una reserva sí). Un pedido suma puntos una sola vez, al quedar pagado.
  * Se canjean **100 puntos = 1 Bs**, en múltiplos de 100, sin superar el monto de las prendas; el canje se elige al confirmar el pedido (pagado con tarjeta vía Stripe o Billetera Digital) o en caja.
  * Si un pedido con puntos canjeados vence o se cancela, los puntos se devuelven.
  * Nivel por puntos acumulados (nunca baja): **Bronce** (< 500), **Plata** (500–1499), **Oro** (≥ 1500).
  * En caja el canje y la acumulación exigen el correo de un cliente registrado.

##### Endpoints Backend
```http
GET /api/loyalty/balance
Headers: Authorization: Bearer <client_jwt>
Response 200 OK:
{
  "statusCode": 200,
  "message": "Puntos obtenidos exitosamente",
  "data": [
    {
      "tenant_id": "<uuid>",
      "tenant_name": "Moda Andina",
      "points_balance": 450,
      "lifetime_points": 620,
      "tier": "Plata",
      "balance_value": 45.00
    }
  ]
}

GET /api/loyalty/transactions          (cliente: movimientos earn | redeem | refund)
GET /api/loyalty/customer?email=...    (cajero: saldo del cliente en su empresa)
```
```http
El canje viaja en la compra misma (no hay endpoint aparte, así el monto del QR o de Stripe ya incluye el descuento):

POST /api/payments/cash/checkout | /api/payments/stripe/checkout | /api/payments/qr/checkout
Request Body: { "pickup_branch_id": "<uuid>", "points_to_redeem": 200 }
Response 201: el pedido incluye "loyalty_discount": 20.00 y el total ya descontado.

POST /api/sales/   (cajero)
Request Body: { "items": [...], "customer_email": "cliente@correo.com", "points_to_redeem": 200 }

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "Puntos insuficientes: tienes 120 puntos en esta empresa",
  "error": "HTTPException"
}

Response 400 Bad Request:
{
  "statusCode": 400,
  "message": "Los puntos canjeados superan el monto a pagar",
  "error": "HTTPException"
}
```

##### Ubicación en Frontend (Angular & Móvil)
* **Páginas y Vistas:** `frontend/src/app/features/cliente/pages/loyalty-page.component.ts` (plantilla en línea), campo «Usar puntos» en `cliente/pages/cart-page`, `frontend/src/app/features/cajero/pages/caja-page.component.ts` (consulta y canje en mostrador)
* **Servicio API:** `frontend/src/app/features/shared/services/loyalty-api.service.ts`
* **Modelo TypeScript:** `frontend/src/app/features/shared/models/loyalty.model.ts`
* **Rutas Angular:** `/app/cliente/loyalty`, `/app/cajero/caja`
* **Móvil Flutter:** `mobile/lib/features/loyalty/loyalty_page.dart` (tarjeta «Mis puntos» en `management_page.dart`) y campo «Puntos a canjear» en `orders/checkout_page.dart`.
* **Mensajes en UI:** La vista muestra directamente el mensaje del backend (por ejemplo `"Los puntos se canjean en múltiplos de 10"`).

##### Checklist de Implementación
- [x] Backend: Modelar tablas `loyalty_accounts` y `loyalty_ledger` vinculadas a `tenant_id`.
- [x] Backend: Hook post-venta (`order_service._consume_order`, `sales_service._apply_loyalty`) para acreditar puntos.
- [x] Backend: Endpoints `/api/loyalty/balance`, `/transactions`, `/customer` y `points_to_redeem` en checkout y caja.
- [x] Frontend: Crear `LoyaltyApiService` y pantalla `loyalty-page` con nivel de cliente e historial.
- [x] Frontend: Integrar selector de canje de puntos en el módulo de caja (`caja-page.component.ts`).
- [x] Verificación: Completar compra presencial y constatar acreditación inmediata de puntos (`tests/test_loyalty.py`).

---

#### CU18 – Emitir y comprar tarjetas de regalo (*Gift Cards*)
* **Módulo:** M5: Promociones y Fidelización
* **Actor Principal:** Cliente
* **Estado:** **Hecho** (`gift_card_service.py`, `gift_card_routes.py`, migración `0053`) | **Plataforma:** Ambas
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
- [x] Backend: Modelar tabla `gift_cards` con código hash único, saldos y estado.
- [x] Backend: Generador de código QR y envío de correo con plantilla HTML.
- [x] Frontend: Desarrollar pantalla `gift-cards-page` con previsualizador visual de tarjeta de regalo.
- [x] Móvil: Pantalla de compra y listado de Gift Cards en Flutter.
- [x] Verificación: Adquirir una Gift Card y comprobar la validez del código QR generado.

---

#### CU19 – Gestionar billetera digital (*Store Wallet*)
* **Módulo:** M5: Promociones y Fidelización
* **Actor Principal:** Cliente, Cajero
* **Estado:** **Hecho** (`wallet_service.py`, `wallet_routes.py`, migración `0053`) | **Plataforma:** Ambas
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
- [x] Backend: Modelar tablas `user_wallets` y `wallet_transactions` con concurrencia segura y aislamiento por `tenant_id`.
- [x] Backend: Endpoints `/api/wallet/balance`, `/api/wallet/redeem-gift-card`, `/api/wallet/pay` y transacciones.
- [x] Frontend: Desarrollar pantalla `wallet-page` y tarjeta de saldo en la vista de perfil.
- [x] Frontend: Agregar medio de pago "Billetera Virtual" en el checkout del carrito (`cart-page.component.ts`).
- [x] Móvil: Añadir botón "Mi Billetera Digital" en el menú de `ProfilePage` en Flutter y vista de saldo.
- [x] Verificación: Cargar una tarjeta de regalo y realizar el pago total de un pedido descontando del saldo.

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
* **Descripción Funcional:** Circuito integral de logística inversa y posventa (RMA). Permite al cliente gestionar cambios de prendas o devoluciones de sus compras realizadas dentro de los **30 días** posteriores a la entrega.
  1. **Vista "Mis Devoluciones y Cambios":** El cliente visualiza el listado histórico de sus solicitudes de RMA con estado en tiempo real (`pending_inspection`, `approved`, `partially_approved`, `rejected`, `completed`) y el botón para **Descargar la Ficha Oficial en PDF**. Si no posee trámites, dispone de un botón principal para iniciar una nueva solicitud.
  2. **Filtrado de Compras Elegibles:** Al crear una solicitud, el sistema filtra y lista exclusivamente las ventas del cliente entregadas en los últimos 30 días.
  3. **Solicitud Multilínea (Selección granular):** El cliente selecciona una o varias prendas del pedido e indica para cada una:
     * **Motivo:** Talle incorrecto (`wrong_size`), Color no deseado (`wrong_color`), Defecto de fábrica / confección (`factory_defect`) o Cambio de opinión / arrepentimiento (`change_of_mind`).
     * **Resolución Deseada:**
       * **Cambio de prenda (`exchange`):** Restringido estrictamente a **variantes del mismo producto** (otra talla u otro color; no por productos ajenos). La entrega y el canje físico se ejecutan en el acto en la sucursal al momento de la inspección.
       * **Crédito en billetera (`store_credit`):** Reembolso del monto a la billetera digital (`Store Wallet`). Por política de control contable y cierre de inventarios mensuales, **la acreditación en la billetera se programa para el cierre de mes** (`scheduled_month_end`), evitando descalces en el inventario activo.
  4. **Emisión de Ficha de Solicitud en PDF:** Al confirmarse la solicitud, el sistema genera la **Ficha de RMA descargable en PDF** con código QR/barras, resumen de prendas, motivos y casillas para el dictamen y firma del encargado en mostrador.
  5. **Inspección Física y Dictamen Ítem por Ítem:**
     * **Impecable (`intact`):** Prenda sin uso y con etiquetas de origen. Si pidió cambio por talla/color, el cambio se entrega en el acto en sucursal, reingresando la prenda devuelta a stock vendible (`rma_restock`) y descontando la nueva variante entregada (`exchange_dispatch`).
     * **Defecto de Fábrica (`factory_defect`):** Se aprueba el reclamo al cliente. La prenda defectuosa **va a merma / cuarentena técnica** (`scrap_quarantine`, CU24) y se programa la acreditación del saldo a billetera a fin de mes.
     * **Dañada / Usada por el cliente (`customer_damaged`):** Se rechaza el ítem con acta de rechazo, devolviéndose la prenda al cliente sin alteración de inventario ni entrega de dinero.
  6. **Notificación Automática al Cliente:** Al aprobarse la devolución y programarse la acreditación, el sistema envía una **notificación push y alerta en la app** al cliente informando el monto aprobado y la fecha de liquidación mensual. Al llegar el cierre de mes y efectivizarse el saldo en `Store Wallet`, se dispara una segunda notificación confirmando el saldo disponible para compras.

##### Endpoints Backend
```http
GET /api/rma/eligible-orders
Headers: Authorization: Bearer <client_jwt>
Response 200 OK:
{
  "statusCode": 200,
  "message": "Órdenes elegibles para cambio o devolución obtenidas",
  "data": [
    {
      "order_id": "ord_8812",
      "order_number": "PED-2026-0044",
      "delivered_at": "2026-03-25T14:30:00Z",
      "days_since_delivery": 6,
      "items": [
        {
          "order_item_id": "item_221",
          "product_id": "prod_551",
          "product_name": "Camisa Clásica Popelín",
          "variant_id": "var_101",
          "size": "M",
          "color": "Azul",
          "unit_price": 140.00,
          "quantity": 1,
          "eligible_for_rma": true,
          "available_same_product_variants": [
            { "variant_id": "var_102", "size": "L", "color": "Azul", "stock": 4 },
            { "variant_id": "var_103", "size": "M", "color": "Blanco", "stock": 2 }
          ]
        }
      ]
    }
  ]
}
```

```http
POST /api/rma/requests
Headers: Authorization: Bearer <client_jwt>
Request Body:
{
  "order_id": "ord_8812",
  "customer_notes": "Cambio de talle para la camisa y devolución por falla de tela",
  "items": [
    {
      "order_item_id": "item_221",
      "quantity": 1,
      "reason": "wrong_size",
      "preferred_resolution": "exchange",
      "requested_variant_id": "var_102",
      "notes": "Me quedó chica, solicito talle L misma prenda"
    },
    {
      "order_item_id": "item_222",
      "quantity": 1,
      "reason": "factory_defect",
      "preferred_resolution": "store_credit",
      "notes": "Costura abierta de origen en hombro"
    }
  ]
}
Response 201 Created:
{
  "statusCode": 201,
  "message": "Solicitud de cambio/devolución registrada exitosamente",
  "data": {
    "rma_id": "rma_9901",
    "rma_number": "RMA-2026-0914",
    "status": "pending_inspection",
    "total_items": 2,
    "pdf_url": "/api/rma/requests/rma_9901/pdf",
    "created_at": "2026-03-31T10:00:00Z"
  }
}
```

```http
GET /api/rma/requests/{rma_id}/pdf
Headers: Authorization: Bearer <jwt>
Response 200 OK:
Content-Type: application/pdf
Content-Disposition: attachment; filename="Ficha_RMA_2026_0914.pdf"
```

```http
PATCH /api/rma/requests/{rma_id}/items/{rma_item_id}/review
Headers: Authorization: Bearer <encargado_jwt>
Request Body (Aprobación de devolución a billetera con fecha de fin de mes y notificación):
{
  "status": "approved",
  "item_condition": "factory_damaged",
  "action": "scrap_quarantine",
  "resolution": "store_credit",
  "branch_id": "branch_central",
  "inspection_notes": "Defecto de confección en sisa. Se envía a merma y se programa crédito en billetera a fin de mes."
}
Response 200 OK:
{
  "statusCode": 200,
  "message": "Ítem dictaminado: Aprobado. Se programó acreditación a fin de mes y se notificó al cliente.",
  "data": {
    "rma_id": "rma_9901",
    "rma_item_id": "item_222",
    "item_status": "approved_refund",
    "quarantine_record": "QR-2026-0044",
    "refund_amount": 220.00,
    "wallet_settlement_date": "2026-04-30T23:59:59Z",
    "notification_sent": true
  }
}
```

##### Ubicación en Frontend (Angular & Móvil)
* **Páginas y Vistas Web:**
  - Panel "Mis Devoluciones y Cambios": `frontend/src/app/features/cliente/pages/rma-history-page.component.ts` (`/app/cliente/returns`)
  - Formulario de solicitud multilínea: `frontend/src/app/features/cliente/pages/rma-request-page.component.ts` (`/app/cliente/returns/new`)
  - Consola de dictamen para Encargado: `frontend/src/app/features/encargado/pages/rma-review-page.component.ts` (`/app/encargado/returns`)
* **Servicio API:** `frontend/src/app/features/shared/services/rma-api.service.ts`
* **Servicio PDF:** `backend/app/services/rma_pdf_service.py`
* **Notificaciones:** Integración con `create_notification()` en `notification_service.py`.

##### Checklist de Implementación
- [ ] Backend: Modelar tablas `rma_requests` y `rma_request_items` con soporte multilínea y estados compuestos (`pending_inspection`, `approved`, `partially_approved`, `rejected`, `completed`).
- [ ] Backend: Endpoint `GET /api/rma/eligible-orders` con validación estricta de plazo de 30 días posteriores a la entrega.
- [ ] Backend: Selector de variante alternativa para cambios si la requerida carece de existencias, o conversión a crédito en `Store Wallet` (CU19).
- [ ] Backend: Lógica de dictamen granular: aceptación/rechazo independiente por ítem y bifurcación según condición física (`intact`, `factory_damaged`, `customer_damaged`).
- [ ] Frontend: Desarrollar pantalla de selección de ítems para cliente con verificación de variantes y stock.
- [ ] Frontend: Desarrollar consola de inspección para encargado con dictamen independiente por prenda.
- [ ] Verificación: Probar solicitud mixta (1 cambio de talle intacto + 1 falla de fábrica a merma + 1 prenda usada rechazada) y verificar inventario, billetera y actas.

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

#### CU24 – Restablecimiento y control de inventario por devoluciones y mermas
* **Módulo:** M6: Logística y Posventa
* **Actor Principal:** Encargado de sucursal, Administrador
* **Estado:** Pendiente | **Plataforma:** Web
* **Descripción Funcional:** Gestión física, contable y operativa del inventario derivado de procesos de cambio y devolución (RMA). Cuando una o varias prendas son recibidas físicamente en sucursal tras la solicitud de un cliente (CU21), el encargado efectúa la inspección técnica de cada ítem:
  1. **Reingreso Comercial (`restock_available`):** Si la prenda devuelta por talle, color o arrepentimiento se encuentra **intacta** (sin uso, limpia y con etiquetas de origen), el sistema registra un reingreso de existencias (`rma_restock`), incrementando atómicamente el stock comercializable en la sucursal receptora.
  2. **Baja Técnica a Merma / Cuarentena (`scrap_quarantine`):** Si la prenda fue aceptada por **defecto de fábrica comprobado** (`factory_defect`), el sistema prohíbe terminantemente su reincorporación al catálogo vendible. Genera un movimiento de baja por merma y aislamiento físico en cuarentena técnica (`scrap_quarantine`) con código identificador oficial (`quarantine_record`), justificación técnica y registro de auditoría.
  3. **Rechazo y Devolución al Cliente (`return_to_customer`):** Si una prenda en reclamo por talle/gusto presenta daños atribuibles al cliente (`customer_damaged`: lavado, manchas, roturas), el sistema no altera el inventario de la tienda y emite un acta formal de rechazo para su entrega o reenvío al comprador.
  4. **Despacho y Sustitución de Prendas por Cambio (`exchange_dispatch`):** En resoluciones de cambio de prenda (`exchange`), el sistema descuenta la nueva variante del stock de la sucursal (`exchange_out`). Si la variante solicitada inicialmente no cuenta con stock disponible en tienda, el sistema ofrece:
     * **Sustitución por variante/prenda alternativa:** El encargado, previa coordinación o preferencia del cliente, selecciona otra variante disponible en el catálogo de igual valor.
     * **Conversión a saldo en billetera:** Si no hay alternativa de agrado o disponibilidad, se conmuta automáticamente la resolución a crédito en tienda (`store_credit`), reembolsando el monto a la billetera digital del cliente.

##### Endpoints Backend
```http
POST /api/rma/inspections/{rma_id}/items/{rma_item_id}/process
Headers: Authorization: Bearer <encargado_jwt>
Request Body (Caso 1 - Reingreso comercial por prenda intacta):
{
  "item_condition": "intact",
  "action": "restock_available",
  "branch_id": "branch_central",
  "quantity": 1,
  "inspection_notes": "Prenda en perfecto estado, etiquetas y precintos originales intactos",
  "resolution": "exchange",
  "replacement_variant_id": "var_102"
}
Response 200 OK:
{
  "statusCode": 200,
  "message": "Prenda reintegrada exitosamente al inventario comercializable y reposición apartada",
  "data": {
    "rma_id": "rma_9901",
    "rma_item_id": "item_221",
    "restock_movement_id": "mov_88210",
    "dispatch_movement_id": "mov_88215",
    "status": "restocked_and_exchanged",
    "branch_id": "branch_central",
    "new_available_stock": 14
  }
}

Request Body (Caso 2 - Falta de stock original y selección de variante alternativa):
{
  "item_condition": "intact",
  "action": "restock_available",
  "branch_id": "branch_central",
  "quantity": 1,
  "inspection_notes": "No había stock de talle L azul; cliente aceptó talle L azul marino como alternativa",
  "resolution": "exchange",
  "replacement_variant_id": "var_108",
  "is_alternative_item": true
}
Response 200 OK:
{
  "statusCode": 200,
  "message": "Prenda devuelta reintegrada y variante alternativa asignada y apartada exitosamente",
  "data": {
    "rma_id": "rma_9901",
    "rma_item_id": "item_221",
    "restock_movement_id": "mov_88210",
    "dispatch_movement_id": "mov_88216",
    "replacement_variant_id": "var_108",
    "status": "restocked_and_exchanged"
  }
}

Request Body (Caso 3 - Descarte a merma por falla de confección de origen):
{
  "item_condition": "factory_damaged",
  "action": "scrap_quarantine",
  "branch_id": "branch_central",
  "quantity": 1,
  "inspection_notes": "Falla de costura abierta en hombro derecho de fábrica. Derivado a merma técnica.",
  "resolution": "store_credit"
}
Response 200 OK:
{
  "statusCode": 200,
  "message": "Prenda registrada en inventario de merma y baja técnica",
  "data": {
    "rma_id": "rma_9901",
    "rma_item_id": "item_222",
    "movement_id": "mov_88211",
    "status": "scrapped",
    "quarantine_record": "QR-2026-0044",
    "credited_wallet_amount": 220.00
  }
}
```

##### Ubicación en Frontend (Angular)
* **Página y Vista:** `frontend/src/app/features/encargado/pages/rma-inspection-page.component.ts` (`rma-inspection-page.component.html`)
* **Servicio API:** `frontend/src/app/features/shared/services/rma-api.service.ts`
* **Ruta Angular:** `/app/encargado/rma/inspection` (`canActivate: [roleGuard(['encargado', 'administrador'])]`)
* **Mensajes en UI:**
  - Toast Reingreso: `"Stock actualizado. La prenda fue devuelta al catálogo disponible de la sucursal."`
  - Toast Merma: `"Baja registrada. Ítem derivado a cuarentena/merma bajo el registro oficial."`
  - Modal Alternativas: `"La variante solicitada no tiene stock disponible en esta sucursal. Seleccioná una variante alternativa o acreditá saldo en billetera."`

---

#### CU25 – Resolución de conflictos de inventario y notificación en ventas offline
* **Módulo:** M6: Logística y Posventa
* **Actor Principal:** Cajero, Cliente, Administrador, Sistema
* **Estado:** Pendiente | **Plataforma:** Ambas
* **Descripción Funcional:** Circuito transaccional de contingencia y compensación ante quiebres de inventario durante sincronizaciones diferidas. Cuando una venta de contado o reserva en efectivo se emite localmente sin conexión (CU23) y, al recuperar la conectividad, el backend detecta que el stock fue consumido en paralelo por otro canal o sucursal (colisión transaccional), el servidor rechaza la transacción con código `conflict_rejected` / `inventory_collision`. El sistema activa automáticamente el protocolo de resolución:
  1. **Rollback de Orden:** Si la orden corresponde a una reserva o despacho pendiente, se cancela automáticamente en base de datos.
  2. **Compensación Económica:** Se instruye al cajero la devolución física del efectivo en caja o se acredita de forma inmediata el importe equivalente en la billetera virtual (`Store Wallet`) del cliente con un bono de cortesía.
  3. **Rotura de Stock en Mostrador:** Si la prenda ya fue entregada físicamente en mostrador durante la caída de red, se genera una alerta prioritaria de auditoría para forzar el ajuste manual de inventario negativo controlado por el Administrador.
  4. **Notificación Multicanal:** Se despacha una notificación push a la aplicación móvil del cliente y un correo electrónico formal informando la causa del quiebre y las opciones de reembolso o sustitución; simultáneamente, la pantalla del cajero resalta la transacción en rojo con el detalle del conflicto para su atención inmediata.

##### Endpoints Backend
```http
POST /api/offline/conflicts/{operation_id}/resolve
Headers: Authorization: Bearer <cajero_jwt>
Request Body:
{
  "resolution_type": "store_credit",
  "refund_amount": 180.00,
  "client_id": "usr_9912",
  "reason": "inventory_collision_out_of_stock",
  "notes": "Cliente aceptó acreditación en billetera virtual con 10% adicional"
}
Response 200 OK:
{
  "statusCode": 200,
  "message": "Conflicto resuelto. Saldo compensatorio acreditado y notificación enviada al cliente.",
  "data": {
    "operation_id": "op_98124",
    "status": "resolved_compensated",
    "wallet_credited": 198.00
  }
}
```

##### Ubicación en Frontend (Angular & Móvil)
* **Página y Vista:** `frontend/src/app/features/cajero/pages/offline-conflicts-page.component.ts`
* **Móvil Flutter:** `mobile/lib/features/cajero/offline_conflicts_page.dart`
* **Servicio API:** `frontend/src/app/core/services/offline-sync.service.ts`
* **Mensajes en UI:** Modal: `"Conflicto de sincronización: El producto ya no contaba con existencias al reconectar. Seleccioná el mecanismo de compensación para el cliente."` Toast: `"Rollback ejecutado exitosamente."`.

---

## 5. Cuadro Resumen de Entregables para el Segundo Parcial

| Módulo | Casos de Uso Implementados (Base) | Casos de Uso Nuevos a Desarrollar | Total |
| :--- | :---: | :---: | :---: |
| **M1: Plataforma SaaS y Seguridad** | 0 | 7 (`CU1`, `CU2`, `CU3`, `CU4`, `CU26`, `CU27`, `CU28`) | 7 |
| **M2: Inteligencia Artificial** | 3 (`CU5`, `CU6`, `CU7`) | 3 (`CU8`, `CU9`, `CU10`) | 6 |
| **M3: Inventario y Operaciones** | 2 (`CU11`, `CU12`) | 0 | 2 |
| **M4: Business Intelligence** | 2 (`CU13`, `CU14`) | 0 | 2 |
| **M5: Promociones y Fidelización** | 1 (`CU15`) | 4 (`CU16`, `CU17`, `CU18`, `CU19`) | 5 |
| **M6: Logística y Posventa** | 0 | 6 (`CU20`, `CU21`, `CU22`, `CU23`, `CU24`, `CU25`) | 6 |
| **TOTALES** | **11 HECHOS** | **17 PENDIENTES** | **28** |
