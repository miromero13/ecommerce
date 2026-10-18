# Casos de Uso – Segundo Parcial

Documento de especificación de requisitos y arquitectura funcional para el **Segundo Parcial**. Consolida el estado actual del software (MVP base implementado) y define el nuevo alcance requerido: transformación a **Plataforma SaaS Multi-Tenant**, cobertura total de las **6 ramas de Inteligencia Artificial**, **fidelización omnicanal con billetera digital**, **logística de delivery y devoluciones**, y **soporte PWA/Offline**.

---

## 1. Módulos de Arquitectura del Sistema

El sistema se estructura en **6 Módulos Cohesivos** que agrupan los 22 Casos de Uso:

* **Módulo 1: Plataforma SaaS, Seguridad y Comercial:** Multi-tenancy con aislamiento estricto de empresas (`tenant_id`), planes y cobro recurrente de suscripciones B2B, gestión granular de roles y permisos (RBAC dinámico), y Landing Page pública institucional.
* **Módulo 2: Inteligencia Artificial y Automatización:** Cobertura de las 6 ramas de IA: Visión por Computadora, Machine Learning (filtrado colaborativo ALS), Procesamiento de Lenguaje Natural (PLN), IA Generativa (Google Gemini y Decart AI), Sistemas Expertos (reglas de reabastecimiento de stock) y RPA con IA (procesamiento automatizado de remitos y catálogos de proveedores).
* **Módulo 3: Inventario y Operaciones de Sucursal:** Gestión multi-sucursal, traspasos entre tiendas con ajuste automático de existencias y despacho de notificaciones push móviles en tiempo real.
* **Módulo 4: Business Intelligence y Reportes:** Dashboard gerencial con KPIs comerciales por sucursal y fechas, junto a generación de reportes tabulares detallados con exportación a CSV.
* **Módulo 5: Promociones, Fidelización y Experiencia de Cliente:** Cupones promocionales, lista de deseos (*Wishlist*), acumulación y canje de puntos de lealtad, compra de Gift Cards con código QR y gestión de la billetera digital (*Store Wallet*) para pagos y saldos a favor.
* **Módulo 6: Logística, Despacho y Posventa:** Despacho de pedidos a domicilio con cálculo de flete (última milla), gestión integral de cambios y devoluciones (*RMA*), y arquitectura offline-first con soporte PWA en web y persistencia local en app móvil.

---

## 2. Matriz General de Casos de Uso (CU1 al CU22)

| **ID** | **Caso de uso** | **Módulo** | **Estado en Código** | **Actor(es) principal** | **Plataforma** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CU1** | **Plataforma Multi-Tenant (Multi-empresa)** | M1: Plataforma SaaS y Seguridad | **Pendiente** | Superadministrador | Web |
| **CU2** | **Gestión de planes y suscripciones B2B** | M1: Plataforma SaaS y Seguridad | **Pendiente** | Superadministrador, Administrador | Web |
| **CU3** | **Gestión granular de roles y permisos (RBAC)** | M1: Plataforma SaaS y Seguridad | **Pendiente** | Superadministrador, Administrador | Web |
| **CU4** | **Landing page y catálogo de planes** | M1: Plataforma SaaS y Seguridad | **Pendiente** | Prospecto / Marca B2B | Web |
| **CU5** | **Usar vestidor virtual en tiempo real** | M2: Inteligencia Artificial | **Hecho** | Cliente | Móvil / Web |
| **CU6** | **Recibir recomendaciones de catálogo** | M2: Inteligencia Artificial | **Hecho** | Cliente | Ambas |
| **CU7** | **Consultar asistente virtual / Chatbot** | M2: Inteligencia Artificial | **Hecho** | Cliente | Ambas |
| **CU8** | **Generar reportes por voz y lenguaje natural** | M2: Inteligencia Artificial | **Hecho** | Administrador | Web |
| **CU9** | **Reabastecimiento automático de stock** | M2: Inteligencia Artificial | **Pendiente** | Administrador, Sistema | Web |
| **CU10** | **Ingesta de mercadería con RPA e IA** | M2: Inteligencia Artificial | **Pendiente** | Proveedor, Sistema | Web |
| **CU11** | **Traspaso manual de inventario** | M3: Inventario y Operaciones | **Hecho** | Administrador, Encargado | Web |
| **CU12** | **Notificaciones push móviles** | M3: Inventario y Operaciones | **Hecho** | Cliente, Sistema | Móvil |
| **CU13** | **Dashboard de control y métricas** | M4: Business Intelligence | **Hecho** | Administrador | Web |
| **CU14** | **Generación y exportación de reportes** | M4: Business Intelligence | **Hecho** | Administrador | Web |
| **CU15** | **Gestionar y aplicar cupones promocionales** | M5: Promociones y Fidelización | **Hecho** | Cliente, Admin, Encargado | Ambas |
| **CU16** | **Gestionar lista de deseos (*Wishlist*)** | M5: Promociones y Fidelización | **Pendiente** | Cliente | Ambas |
| **CU17** | **Fidelización y billetera de puntos** | M5: Promociones y Fidelización | **Pendiente** | Cliente, Cajero | Ambas |
| **CU18** | **Emitir y comprar tarjetas de regalo (*Gift Cards*)** | M5: Promociones y Fidelización | **Pendiente** | Cliente | Ambas |
| **CU19** | **Gestionar billetera digital (*Store Wallet*)** | M5: Promociones y Fidelización | **Pendiente** | Cliente, Cajero | Ambas |
| **CU20** | **Delivery y despacho a domicilio** | M6: Logística y Posventa | **Pendiente** | Cliente, Delivery | Ambas |
| **CU21** | **Solicitar y procesar cambios y devoluciones (RMA)** | M6: Logística y Posventa | **Pendiente** | Cliente, Encargado, Admin | Ambas |
| **CU22** | **PWA y soporte Offline (Web y App móvil)** | M6: Logística y Posventa | **Pendiente** | Todos | Ambas |

---

## 3. Especificación Detallada de los Casos de Uso

### Módulo 1: Plataforma SaaS, Seguridad y Comercial

#### CU1 – Plataforma Multi-Tenant (Multi-empresa)
* **Actor principal:** Superadministrador.
* **Estado:** Pendiente.
* **Descripción:** Transforma la arquitectura de base de datos a un modelo multi-inquilino (*Row-Level Multi-Tenancy*). Permite registrar empresas/marcas independientes con subdominio propio (`marca.plataforma.com`), logotipo, moneda y aislamiento estricto de catálogos, sucursales, usuarios e inventarios mediante la clave foránea `tenant_id` en todas las entidades transaccionales.
* **Precondición:** El usuario debe estar autenticado con rol global `Superadministrador`.
* **Flujo Principal:**
  1. El superadministrador registra un nuevo Tenant especificando nombre comercial, slug/subdominio, correo de contacto y configuración regional.
  2. El sistema valida la unicidad del subdominio y crea la organización en la base de datos.
  3. El sistema provisiona al usuario Administrador inicial del tenant y le envía credenciales de acceso.
  4. Toda consulta posterior efectuada bajo ese subdominio resuelve automáticamente el `tenant_id` en middleware, impidiendo accesos cruzados entre marcas.
* **Postcondición:** El nuevo tenant queda operativo y aislado para su parametrización.

#### CU2 – Gestión de planes y suscripciones B2B
* **Actor principal:** Superadministrador (crea planes), Administrador de Tenant (contrata).
* **Estado:** Pendiente.
* **Descripción:** Administración de tiers de suscripción mensual/anual para las marcas que contratan la plataforma SaaS (ej. Básico, Profesional, Enterprise). Controla límites por plan (sucursales máximas, número de prendas, acceso a vestidor virtual IA) y automatiza el cobro recurrente mediante integración con Stripe Billing.
* **Precondición:** Tenant registrado en la plataforma.
* **Flujo Principal:**
  1. El administrador del tenant selecciona el plan deseado y ciclo de facturación (mensual o anual).
  2. El sistema redirige al portal de pago seguro para ingresar tarjeta de crédito.
  3. Stripe confirma la suscripción activa mediante webhook y el sistema actualiza el estado del tenant a `active`.
  4. El sistema habilita los límites y funcionalidades acordes al plan adquirido.
* **Flujos Alternativos:**
  * **3a. Pago rechazado o suscripción vencida:** El sistema degrada el tenant a estado `read_only` o `suspended` hasta la regularización del cobro.

#### CU3 – Gestión granular de roles y permisos (RBAC dinámico)
* **Actor principal:** Superadministrador, Administrador.
* **Estado:** Pendiente.
* **Descripción:** Reemplazo del enum rígido de roles actual por un esquema de Control de Acceso Basado en Roles (RBAC) dinámico. Tablas `roles`, `permissions` y `role_permissions` que permiten crear perfiles personalizados (ej. *Encargado de inventario*, *Supervisor de sucursal*, *Auditor*) y asignar permisos granulares por módulo y verbo HTTP.
* **Precondición:** Usuario autenticado con privilegios de gestión de seguridad.
* **Flujo Principal:**
  1. El administrador accede al panel de roles y selecciona crear nuevo rol.
  2. Asigna un nombre al rol y tilda los permisos específicos requeridos (ej. `inventory:read`, `inventory:transfer`, `sales:create`).
  3. Asocia usuarios internos al nuevo rol.
  4. Los endpoints del backend validan los permisos individuales inyectados en el token JWT.

#### CU4 – Landing page y catálogo de planes
* **Actor principal:** Prospecto / Marca B2B (Visitante público).
* **Estado:** Pendiente.
* **Descripción:** Portal web público y responsivo diseñado para marketing y captación B2B. Presenta los diferenciales del software (Omnicanalidad, Vestidor Virtual con IA, Chatbot inteligente, Gestión multi-sucursal), tabla comparativa de planes con precios y pasarela de registro para iniciar pruebas gratuitas (*Free Trial*).
* **Flujo Principal:**
  1. El visitante accede a la URL pública principal de la plataforma.
  2. Visualiza las características del software, capturas de la app móvil y demostraciones interactivas del vestidor virtual.
  3. Compara los planes de suscripción en la tabla interactiva de precios.
  4. Presiona el botón *"Comenzar prueba gratis"* y completa el formulario de registro de su empresa.

---

### Módulo 2: Inteligencia Artificial y Automatización

#### CU5 – Usar vestidor virtual en tiempo real
* **Rama de IA:** **Visión por Computadora** (*Pose Estimation*) + **IA Generativa de Video** (Decart AI).
* **Actor principal:** Cliente.
* **Estado:** **Hecho** (Implementado en `mobile/lib/features/catalog/virtual_try_on_page.dart` y `frontend/public/decart-try-on.html`).
* **Descripción:** Proyección en vivo de prendas del catálogo sobre el cuerpo del cliente mediante el stream de la cámara del dispositivo móvil. El motor detecta los puntos anatómicos del cuerpo y genera la prenda adaptada en movimiento respetando caída, perspectiva y rotación.

#### CU6 – Recibir recomendaciones personalizadas de catálogo
* **Rama de IA:** **Machine Learning** (Filtrado Colaborativo con Implicit ALS en NumPy).
* **Actor principal:** Cliente.
* **Estado:** **Hecho** (Implementado en `backend/app/services/recommendation_service.py`).
* **Descripción:** Generación de sugerencias personalizadas de prendas en pantalla de inicio y detalle. El modelo entrena factores latentes (*embeddings*) cruzando vistas (peso 1), agregados al carrito (peso 2) y compras completadas (peso 5) para predecir afinidad matemática mediante producto punto vectorial. Incluye fallback automático para usuarios nuevos (*Cold Start*).

#### CU7 – Consultar asistente virtual / Chatbot
* **Rama de IA:** **Procesamiento de Lenguaje Natural (PLN)** + **IA Generativa** (Google Gemini).
* **Actor principal:** Cliente.
* **Estado:** **Hecho** (Implementado en `backend/app/services/chatbot_service.py`).
* **Descripción:** Chatbot conversacional que clasifica intenciones (`CATALOGO`, `PEDIDOS`, `TALLES`, `POLITICAS`, `OFERTAS`), aplica respuestas determinísticas para políticas comerciales y utiliza Google Gemini para consultas abiertas de moda y estilo, consultando el stock real.

#### CU8 – Generar reportes por voz y lenguaje natural
* **Rama de IA:** **Procesamiento de Lenguaje Natural (PLN)** + **IA Generativa** (*Text-to-Filters* con Gemini).
* **Actor principal:** Administrador.
* **Estado:** **Hecho** (Implementado en `backend/app/services/natural_report_service.py`).
* **Descripción:** Interpretación de preguntas de negocio formuladas en lenguaje natural (escritas o dictadas por audio). El modelo de lenguaje extrae entidades semánticas y las traduce a filtros SQL estructurados (`branch_id`, fechas, métricas de venta), devolviendo reportes analíticos al instante.

#### CU9 – Reabastecimiento automático de stock mediante Sistema Experto
* **Rama de IA:** **Sistemas Expertos** (Motor de Inferencia de Reglas Lógicas Determinísticas).
* **Actor principal:** Administrador / Sistema.
* **Estado:** Pendiente.
* **Descripción:** Motor de inferencia autónomo que evalúa periódicamente la base de conocimiento de inventario (umbrales mínimos `threshold`, velocidad de rotación de ventas de los últimos 7 días y stock disponible en depósitos y sucursales cercanas). Aplica encadenamiento de reglas lógicas para emitir en automático órdenes de traspaso de inventario (`inventory_movements` tipo `transfer`) entre sucursales, previniendo quiebres de stock.

#### CU10 – Ingesta y catalogación automática con RPA e IA
* **Rama de IA:** **RPA con IA** (*Intelligent Process Automation* - IDP).
* **Actor principal:** Proveedor / Sistema (Bot RPA).
* **Estado:** Pendiente.
* **Descripción:** Bot de software desatendido que monitorea la llegada de remitos, listas de precios y catálogos desestructurados en formato PDF o planillas Excel enviados por proveedores. Emplea modelos de extracción de documentos para identificar atributos de prendas (talle, color, costo, cantidades) y crea automáticamente borradores de reabastecimiento en el sistema sin tipeo manual.

---

### Módulo 3: Inventario y Operaciones de Sucursal

#### CU11 – Traspaso manual de inventario
* **Actor principal:** Administrador, Encargado.
* **Estado:** **Hecho** (Implementado en `backend/app/routes/inventory_routes.py` endpoint `/inventory/movements/transfer`).
* **Descripción:** Registro de movimientos de transferencia de prendas entre dos sucursales físicas. Genera atómicamente los movimientos `transfer_out` en la sucursal de origen y `transfer_in` en la sucursal de destino, actualizando existencias.

#### CU12 – Notificaciones push móviles
* **Actor principal:** Cliente, Sistema.
* **Estado:** **Hecho** (Implementado con Firebase Cloud Messaging FCM en backend y Flutter móvil).
* **Descripción:** Despacho automatizado de notificaciones push a dispositivos móviles ante eventos de negocio: pedido listo para retiro, confirmación de reserva, recordatorio de vencimiento y alertas de stock bajo. Incluye bandeja de historial de notificaciones in-app.

---

### Módulo 4: Business Intelligence y Reportes

#### CU13 – Dashboard de control y métricas
* **Actor principal:** Administrador.
* **Estado:** **Hecho** (Implementado en `backend/app/routes/dashboard_routes.py` y `admin-home-page`).
* **Descripción:** Panel de visualización de indicadores comerciales clave (KPIs): volumen de ingresos, prendas vendidas, ranking de productos más demandados y nivel de inventario consolidado, con filtros por sucursal y períodos (día, semana, mes, año).

#### CU14 – Generación y exportación de reportes
* **Actor principal:** Administrador.
* **Estado:** **Hecho** (Implementado en `backend/app/routes/report_routes.py`).
* **Descripción:** Consultas tabulares detalladas de ventas, movimientos de mercadería y existencias por sucursal con filtros combinados por fecha, categoría y producto, con opción de descarga de datos en formato CSV.

---

### Módulo 5: Promociones, Fidelización y Experiencia de Cliente

#### CU15 – Gestionar y aplicar cupones promocionales
* **Actor principal:** Cliente, Administrador, Encargado.
* **Estado:** **Hecho** (Implementado en `promotion_routes.py`, `cart_service.py` y `promotions-page`).
* **Descripción:** Emisión de códigos de descuento alfanuméricos (`promotion_codes`) con porcentaje o monto fijo, ámbito global o de sucursal, fechas de vigencia y tope de uso. El cliente ingresa el cupón en el carrito de compras obteniendo la rebaja directa en el subtotal.

#### CU16 – Gestionar lista de deseos (*Wishlist*)
* **Actor principal:** Cliente.
* **Estado:** Pendiente.
* **Descripción:** Permite a los clientes autenticados marcar prendas como favoritas mediante el botón *"Añadir a lista de deseos"* en el catálogo y detalle de producto. Dispone de una vista consolidada para gestionar favoritos y transferir prendas directamente al carrito o a reserva.

#### CU17 – Acumular y canjear puntos de fidelización (*Loyalty*)
* **Actor principal:** Cliente, Cajero.
* **Estado:** Pendiente.
* **Descripción:** Motor de fidelización basado en los `garment_points` configurados en las prendas. Acumula puntos automáticamente tras compras completadas (online o presenciales identificando al cliente en mostrador). Permite al cliente o al cajero canjear puntos acumulados como descuento directo en el importe final de la compra.

#### CU18 – Emitir y comprar tarjetas de regalo (*Gift Cards*)
* **Actor principal:** Cliente.
* **Estado:** Pendiente.
* **Descripción:** Proceso de adquisición de vouchers de saldo prepagado como regalo. El cliente elige un importe ($20, $50, $100), redacta una dedicatoria personalizada e indica el correo del agasajado. Al pagar, el sistema emite un código alfanumérico único con código QR descargable y enviado por email.

#### CU19 – Gestionar billetera digital y saldo de tienda (*Store Wallet*)
* **Actor principal:** Cliente, Cajero.
* **Estado:** Pendiente.
* **Descripción:** Billetera digital asociada a la cuenta del usuario. Permite ingresar el código o escanear el QR de una Gift Card para acreditar el saldo en la cuenta, consultar el balance monetario disponible y utilizar dicho saldo como medio de pago (total o parcial) en el checkout web/móvil o en la caja física escaneando el código de usuario. También recibe las acreditaciones por devoluciones de mercadería.

---

### Módulo 6: Logística, Despacho y Posventa

#### CU20 – Delivery y despacho de pedidos a domicilio
* **Actor principal:** Cliente, Delivery.
* **Estado:** Pendiente.
* **Descripción:** Extensión del checkout actual para admitir envío a domicilio: administración de libreta de direcciones (calle, ciudad, coordenadas GPS y referencias), cotización de costo de flete y nuevos estados de ciclo de vida (`shipped`, `in_transit`, `delivered`). Provee una vista de hoja de ruta para el rol repartidor con certificación de entrega mediante código PIN de seguridad provisto por el cliente.

#### CU21 – Solicitar y procesar cambios y devoluciones (RMA)
* **Actor principal:** Cliente, Encargado de sucursal, Administrador.
* **Estado:** Pendiente.
* **Descripción:** Circuito de logística inversa. El cliente puede solicitar el cambio de talle/color o la devolución de una prenda dentro de los 30 días posteriores a la compra. El encargado inspecciona la prenda en sucursal y aprueba o rechaza el trámite; el sistema reingresa la prenda al stock vendible o la manda a merma por falla, y acredita automáticamente el saldo correspondiente en la billetera virtual del cliente (`Store Wallet`).

#### CU22 – PWA y soporte Offline (Web y App móvil)
* **Actor principal:** Todos (Cliente, Cajero, Encargado, Administrador).
* **Estado:** Pendiente.
* **Descripción:** Implementación de Service Workers y Web App Manifest en la aplicación web para permitir instalación como PWA y navegación del catálogo sin internet. En la aplicación móvil Flutter, integración de base de datos local embebida con cola de sincronización diferida para permitir registrar ventas, pedidos o consultas de inventario en sucursales ante caídas de conectividad, sincronizando los datos al restablecerse la red.

---

## 4. Cuadro Resumen de Entregables para el Segundo Parcial

| Módulo | Casos de Uso Implementados (Base) | Casos de Uso Nuevos a Desarrollar | Total |
| :--- | :---: | :---: | :---: |
| **M1: Plataforma SaaS y Seguridad** | 0 | 4 (`CU1`, `CU2`, `CU3`, `CU4`) | 4 |
| **M2: Inteligencia Artificial** | 4 (`CU5`, `CU6`, `CU7`, `CU8`) | 2 (`CU9`, `CU10`) | 6 |
| **M3: Inventario y Operaciones** | 2 (`CU11`, `CU12`) | 0 | 2 |
| **M4: Business Intelligence** | 2 (`CU13`, `CU14`) | 0 | 2 |
| **M5: Promociones y Fidelización** | 1 (`CU15`) | 4 (`CU16`, `CU17`, `CU18`, `CU19`) | 5 |
| **M6: Logística y Posventa** | 0 | 3 (`CU20`, `CU21`, `CU22`) | 3 |
| **TOTALES** | **9 HECHOS** | **13 PENDIENTES** | **22** |
