# Second Partial – Use Cases Testing Guide

Guía detallada paso a paso para probar **cada uno de los 28 casos de uso (CU1 a CU28)** definidos en `docs/SECOND_PARTIAL_USE_CASES.md`. Cada caso especifica el actor, las credenciales exactas de inicio de sesión, la pestaña de acceso, la ruta en la interfaz y las acciones a realizar.

---

### MÓDULO 1: Plataforma SaaS, Seguridad y Comercial

#### CU1 – Gestionar organizaciones (Tenants) de la plataforma
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:** Superadministrador
* **Credenciales:** `superadmin@fashionstore.com` / `SuperAdmin2026!` (Pestaña: *Administrativos*)
* **Ruta UI:** `/app/superadmin/tenants` (Menú lateral: *"Empresas / Tenants"*)

##### Pasos para probar:
1. Iniciá sesión con la cuenta de Superadministrador en `http://localhost:4200/auth/login`.
2. El sistema te redirige a `/app/superadmin/dashboard`. Hacé clic en el menú lateral en **"Empresas / Tenants"** (`/app/superadmin/tenants`).
3. Observá el listado de organizaciones existentes (*Ayni Moda, Kantuta Boutique, Urbana Denim, Luna Satén*). Verificá que cada una muestra su plan, subdominio, moneda y estado.
4. Hacé clic en el botón **"Nueva Empresa"** o **"Crear Organización"**.
5. Completá el formulario modal:
   * **Nombre comercial:** `Boutique Paris`
   * **Subdominio / Slug:** `paris`
   * **Correo de contacto:** `contacto@boutiqueparis.com`
   * **Moneda:** `BOB`
   * **País:** `BO`
6. Presioná **"Guardar"** / **"Crear"**.
7. **Resultado esperado:**
   * Notificación Toast verde: `"Organización creada exitosamente"`.
   * La nueva empresa aparece en la tabla con estado inicial.
8. **Prueba de Aislamiento:** Ingresá con el admin de *Ayni Moda* (`carolina.quiroga@ayni-moda.demo.bo`) a `/app/admin/inventory`. Comprobá que **solo** se visualiza el inventario y las sucursales de Ayni Moda, sin ver jamás registros de Boutique Paris ni de Kantuta Boutique.

* **Endpoint API equivalente:**
  ```bash
  curl -X POST http://localhost:8000/api/saas/tenants \
    -H "Authorization: Bearer <SUPERADMIN_TOKEN>" \
    -H "Content-Type: application/json" \
    -d '{"name":"Boutique Paris","slug":"paris","subdomain":"paris","contact_email":"contacto@boutiqueparis.com","currency":"BOB","country":"BO"}'
  ```

---

#### CU2 – Gestionar planes de suscripción SaaS
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:** Superadministrador (`superadmin@fashionstore.com` / `SuperAdmin2026!`)
* **Ruta UI:** `/app/superadmin/plans` (Menú lateral: *"Planes de Suscripción"*)

##### Pasos para probar:
1. Iniciá sesión como Superadministrador e ingresá a `/app/superadmin/plans`.
2. Verificá la tabla de planes configurados: *Básico, Profesional, Enterprise*, con sus precios mensual/anual y límites de cupos.
3. Hacé clic en **"Nuevo Plan"** o seleccioná **"Editar"** en uno existente:
   * Modificá los cupos de sucursales (`max_branches`) o prendas (`max_garments`).
   * Seleccioná o desmarcá módulos adicionales (IA vestidor virtual, chatbot, smart reports).
4. Podés alternar el interruptor de estado activo/inactivo del plan para comprobar la desactivación comercial (un plan desactivado no se oferta a nuevas marcas en la landing).
5. Hacé clic en **"Guardar Plan"**.
6. **Resultado esperado:**
   * Notificación Toast: `"Plan actualizado exitosamente"` o `"Plan creado exitosamente"`.
   * Los cambios quedan disponibles de inmediato en la base de datos para futuras suscripciones.

* **Endpoint API equivalente:**
  ```bash
  curl -X GET http://localhost:8000/api/saas/plans/admin \
    -H "Authorization: Bearer <SUPERADMIN_TOKEN>"
  ```

---

#### CU3 – Gestionar roles y permisos de usuario (RBAC)
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:** Administrador de Tenant
* **Credenciales:** `carolina.quiroga@ayni-moda.demo.bo` / `Fashion2026!` (Pestaña: *Administrativos*)
* **Ruta UI:** `/app/admin/roles` (Menú lateral: *"Roles y Permisos"*)

##### Pasos para probar:
1. Iniciá sesión como Administrador de Ayni Moda.
2. Accedé a la ruta `/app/admin/roles`.
3. Verificá la lista de permisos del sistema agrupados por módulo (`inventory:read`, `inventory:transfer`, `sales:create`, `rpa:upload`, etc.).
4. Hacé clic en **"Crear Rol"**.
5. Ingresá:
   * **Nombre:** `Auditor de Stock`
   * **Código:** `stock_auditor`
   * **Permisos:** Seleccioná únicamente `inventory:read` y `reports:read`.
6. Hacé clic en **"Guardar Rol"**.
7. **Resultado esperado:**
   * Toast verde: `"Rol creado exitosamente"`.
   * El nuevo rol queda disponible para asignarse a usuarios de la propia organización.

* **Endpoint API equivalente:**
  ```bash
  curl -X GET http://localhost:8000/api/rbac/permissions \
    -H "Authorization: Bearer <ADMIN_TOKEN>"
  ```

---

#### CU4 – Consultar página comercial y planes de suscripción
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:** Prospecto / Visitante público (Sin autenticación)
* **Ruta UI:** `/landing` o `/` (`http://localhost:4200/landing`)

##### Pasos para probar:
1. Abrí una pestaña de incógnito o cerrá sesión activa y navegá a `http://localhost:4200/landing`.
2. Recorré las secciones del portal institucional:
   * Hero banner con propuesta de valor para marcas de moda.
   * Sección de funcionalidades clave (IA, Vestidor Virtual, Omnicanalidad).
   * **Tabla de Precios y Planes Comparativa:** Verificá que los planes y límites provienen dinámicamente del backend.
3. Hacé clic en el botón **"Comenzar Prueba Gratuita"** o **"Contratar"** en uno de los planes.
4. Completá el formulario de onboarding para crear una tienda de prueba (empresa, admin, email y contraseña).
5. **Resultado esperado:**
   * Mensaje de éxito informando el inicio de la prueba gratuita y la asignación del subdominio de la marca.

---

#### CU26 – Personalizar la marca de la tienda (Branding)
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:** Administrador de Tenant (`carolina.quiroga@ayni-moda.demo.bo` / `Fashion2026!`) o Superadministrador
* **Ruta UI:** `/app/admin/settings` (o editor de branding en encabezado de cuenta)

##### Pasos para probar:
1. Iniciá sesión como Administrador de *Ayni Moda*.
2. Accedé a la sección de configuración de marca de la empresa.
3. Cargá un archivo de imagen para el nuevo logotipo (formato PNG o JPG).
4. Seleccioná un color primario corporativo (ej. `#800020` borgoña o `#1A5276` azul marino).
5. Confirmá el guardado de la personalización.
6. **Resultado esperado:**
   * Toast verde: `"Logotipo actualizado exitosamente"` / `"Configuración de marca guardada"`.
   * El encabezado del AppShell web adopta el nuevo logotipo y las variables de color primario en tiempo real.
   * Al emitir o imprimir una orden/comprobante de venta en PDF (`simple-pdf.util`), el documento incluye el logo y nombre de la tienda.
   * La app móvil Flutter descarga automáticamente el branding de la tienda al sincronizar.

* **Endpoint API equivalente:**
  ```bash
  curl -X GET http://localhost:8000/api/saas/tenants/me/branding \
    -H "Authorization: Bearer <ADMIN_TOKEN>"
  ```

---

#### CU27 – Contratar suscripción B2B (Onboarding)
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:** Prospecto / Nueva Marca B2B (Sin autenticación)
* **Ruta UI:** `http://localhost:4200/landing` (Sección Precios / Planes)

##### Pasos para probar:
1. Navegá a la landing pública `http://localhost:4200/landing`.
2. En la tabla de precios comparativa, seleccioná el plan **"Profesional"** y elegí facturación mensual o anual.
3. Completá el formulario modal de contratación:
   * **Empresa:** `Boutique Elegance`
   * **Nombre del Admin:** `Ana Pérez`
   * **Correo de contacto:** `ana.perez@elegance.demo.bo`
   * **Datos de tarjeta simulada:** Número `4242424242424242`, exp `12/28`, CVV `123`, titular `Ana Pérez`.
4. Hacé clic en **"Confirmar y Suscribirse"**.
5. **Resultado esperado:**
   * Notificación Toast: `"Suscripción activada con éxito. Te enviamos un correo con los datos de acceso."`.
   * Se crea atómicamente la empresa con subdominio, el usuario admin y la suscripción con `end_date` calculada.
   * En la bandeja de Mailtrap se verifica la llegada del correo de bienvenida con credenciales seguras.

* **Endpoint API equivalente:**
  ```bash
  curl -X POST http://localhost:8000/api/saas/subscriptions/purchase-simulated \
    -H "Content-Type: application/json" \
    -d '{"company_name":"Boutique Elegance","admin_name":"Ana Pérez","admin_email":"ana.perez@elegance.demo.bo","plan_id":"plan_pro_02","billing_cycle":"monthly","card_number":"4242424242424242","card_holder":"Ana Pérez","card_exp":"12/28","card_cvv":"123"}'
  ```

---

#### CU28 – Monitorear consumo y cambiar plan de suscripción
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:** Administrador de Tenant (`veronica.pinto@luna-saten.demo.bo` / `Fashion2026!`)
* **Ruta UI:** `/app/admin/subscription` (Menú lateral: *"Suscripción y Plan"*)

##### Pasos para probar:
1. Iniciá sesión como Administrador de *Luna Satén* (empresa con Plan Básico inicial).
2. Hacé clic en el menú lateral en **"Suscripción y Plan"** (`/app/admin/subscription`).
3. Verificá en pantalla:
   * Tarjeta con el plan actual (*Básico*), estado *Activo* y fecha de vigencia del período.
   * Barras de consumo: sucursales utilizadas vs. límite (`max_branches: 2`), prendas en catálogo vs. límite (`max_garments: 500`).
4. **Prueba de Upgrade:** Hacé clic en **"Cambiar Plan"**, seleccioná el plan **"Profesional"**, completá la tarjeta de prueba (`4242424242424242`) y confirmá.
5. **Resultado esperado:**
   * Toast: `"Plan actualizado con éxito. Tu empresa ahora tiene el plan Profesional."`.
   * Las barras de cuota se expanden de inmediato a 5 sucursales y 3.000 prendas.
6. **Prueba de Enforcement de Límites:** Si se intenta crear una sucursal adicional que supere el cupo permitido por el plan, el backend rechaza la operación con código HTTP 403: `"Límite de sucursales alcanzado para el plan actual. Actualizá tu suscripción."`.

* **Endpoint API equivalente:**
  ```bash
  curl -X GET http://localhost:8000/api/saas/subscriptions/current \
    -H "Authorization: Bearer <ADMIN_TOKEN>"
  ```

---

---

### MÓDULO 2: Inteligencia Artificial y Automatización

#### CU5 – Probar prendas en el vestidor virtual
* **Rama de IA:** **Visión por Computadora** (*Pose Estimation*) + **IA Generativa de Video**
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:** Cliente
* **Credenciales:** `maria.quispe@clientes.demo.bo` / `Cliente2026!` (Pestaña: *Clientes*)
* **Ruta UI:** Web en `/app/cliente/catalog` o detalle de prenda `/app/cliente/products/:productId`; y en Móvil en `virtual_try_on_page.dart`.

##### Pasos para probar:
1. Iniciá sesión como cliente y navegá al catálogo (`/app/cliente/catalog`).
2. Seleccioná una prenda que tenga habilitado el vestidor virtual (ej. un vestido o chaqueta de Ayni Moda).
3. En la página de detalle del producto, hacé clic en el botón **"Probar Prenda"** / **"Vestidor Virtual"**.
4. Se abrirá el modal interactivo (o visor en `/decart-try-on.html`) solicitando permisos de cámara.
5. Permití el acceso a la webcam o cargá una silueta de prueba.
6. **Resultado esperado:**
   * Inicialización de la sesión de vestidor virtual.
   * Detección de puntos corporales y superposición de la textura recortada de la prenda sobre la silueta.

* **Endpoint API equivalente:**
  ```bash
  curl -X POST http://localhost:8000/api/ai/virtual-try-on/session \
    -H "Authorization: Bearer <CLIENT_TOKEN>" \
    -H "Content-Type: application/json" \
    -d '{"garment_id": "<GARMENT_UUID>", "stream_provider": "decart"}'
  ```

---

#### CU6 – Recibir recomendaciones personalizadas de prendas
* **Rama de IA:** **Machine Learning** (Filtrado Colaborativo con Implicit ALS)
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:** Cliente
* **Credenciales:** `maria.quispe@clientes.demo.bo` / `Cliente2026!` (Pestaña: *Clientes*)
* **Ruta UI:** `/app/cliente/catalog` (Web) o portada de catálogo en Móvil Flutter.

##### Pasos para probar:
1. Iniciá sesión como cliente.
2. Ingresá a la sección de Catálogo (`/app/cliente/catalog`).
3. En la parte superior de la página, observá la sección o carrusel **"Recomendados para ti"**.
4. Hacé clic en 2 o 3 prendas de un estilo específico (por ejemplo vestidos formales) para registrar eventos de `view` y agregá una al carrito.
5. Regresá al catálogo o recargá la página.
6. **Resultado esperado:**
   * El carrusel se actualiza con prendas afines calculadas por el modelo ALS vectorial (o popular fallback para nuevos clientes).
   * Se excluyen prendas sin stock o de empresas con suscripción suspendida.

* **Endpoint API equivalente:**
  ```bash
  curl -X GET http://localhost:8000/api/recommendations/collaborative/user/<USER_ID> \
    -H "Authorization: Bearer <CLIENT_TOKEN>"
  ```

---

#### CU7 – Consultar al asistente virtual (Chatbot)
* **Rama de IA:** **Procesamiento de Lenguaje Natural (PLN)** + **IA Generativa (Gemini)**
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:** Cliente o Visitante
* **Credenciales:** `maria.quispe@clientes.demo.bo` / `Cliente2026!` (o sin sesión)
* **Ruta UI:** Widget flotante en la esquina inferior derecha en cualquier pantalla de `/app/cliente` o `/landing`. En móvil: icono de Chatbot en el AppBar.

##### Pasos para probar:
1. Hacé clic sobre la burbuja flotante del Chatbot para abrir la ventana de conversación.
2. Escribí una consulta sobre disponibilidad real en lenguaje natural:
   * *"¿Tenés vestidos de seda en talle M en la sucursal Centro?"*
   * *"¿Qué opciones en color negro me recomendás para una fiesta?"*
3. Presioná Enviar.
4. **Resultado esperado:**
   * El bot responde reconociendo la intención (`CATALOGO` / `TALLES`).
   * Devuelve un texto coherente indicando el stock disponible real y tarjetas interactivas de los productos sugeridos con acceso directo a verlos.

* **Endpoint API equivalente:**
  ```bash
  curl -X POST http://localhost:8000/api/chatbot/message \
    -H "Content-Type: application/json" \
    -d '{"message": "¿Tienen blusas en talle S en la sucursal de La Paz?"}'
  ```

---

#### CU8 – Generar reportes inteligentes con IA
* **Rama de IA:** **PLN / Text-to-Query** + **IA Generativa (Gemini)** + **ML Supervisado y No Supervisado (Scikit-Learn)**
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:** Administrador de Tenant
* **Credenciales:** `carolina.quiroga@ayni-moda.demo.bo` / `Fashion2026!` (Pestaña: *Administrativos*)
* **Ruta UI:** `/app/admin/reports` (Menú lateral: *"Reportes con IA"*)

##### Pasos para probar:
1. Iniciá sesión como Administrador de Ayni Moda e ingresá a `/app/admin/reports`.
2. **Prueba A: Consulta en Lenguaje Natural (Escrita o Voz):**
   * En la barra de consulta, escribí:
     *"Ventas por sucursal del último mes"* o *"Top 10 productos más vendidos"*.
   * (Opcional) Presioná el botón de micrófono para dictar la consulta por voz mediante Web Speech API.
   * Hacé clic en **"Consultar con IA"**.
   * **Resultado:** La IA interpreta la intención, muestra el desglose seguro y genera la tabla interactiva de resultados con los datos reales de PostgreSQL.
3. **Prueba B: Predicción de Demanda (ML Supervisado - Regresión):**
   * Hacé clic en la pestaña o botón **"Predicción de Demanda (ML)"**.
   * Opcionalmente activá o desactivá el interruptor *«Modo demostración (solo datos sintéticos)»*.
   * Hacé clic en **"Ejecutar Pronóstico"**.
   * **Resultado:** Muestra el gráfico de proyección por semanas y las métricas de evaluación del modelo de regresión ($R^2$ Score y MSE).
4. **Prueba C: Segmentación de Clientes (ML No Supervisado - K-Means Clustering):**
   * Hacé clic en **"Segmentación de Clientes (Clustering)"**.
   * Hacé clic en **"Segmentar Clientes"**.
   * **Resultado:** Muestra la agrupación de clientes en 3 clusters (ej. *Compradores Frecuentes Alto Ticket, Cazadores de Ofertas, Clientes Ocasionales*) junto con el **Silhouette Score** de evaluación.
5. **Prueba D: Exportación a Excel y PDF:**
   * En cualquier reporte generado, hacé clic en **"Exportar a Excel (.xlsx)"** o **"Exportar a PDF"**.
   * **Resultado:** El archivo se descarga automáticamente con formato limpio y tipografía corporativa.

---

#### CU9 – Reabastecer stock automáticamente entre sucursales
* **Rama de IA:** **Sistemas Expertos** (Motor de Inferencia de Reglas Determinísticas)
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:** Administrador de Tenant
* **Credenciales:** `carolina.quiroga@ayni-moda.demo.bo` / `Fashion2026!` (Pestaña: *Administrativos*)
* **Ubicación UI:** Notificaciones en `/app/notifications` (Campanita superior).
* **Nota sobre la navegación:** La sección `/app/admin/expert-replenishment` está **desactivada del menú lateral** (igual que la de reportes); el flujo opera de forma proactiva mediante notificaciones interactivas cuando se produce un quiebre de stock. La URL `/app/admin/expert-replenishment` sigue disponible directamente por compatibilidad.

##### Pasos para probar el flujo reactivo de notificaciones:
1. Iniciá sesión como Administrador de Ayni Moda (`carolina.quiroga@ayni-moda.demo.bo` / `Fashion2026!`).
2. Navegá a **Inventario** (`/app/admin/inventory`) y registrá un movimiento de **Salida** en una sucursal destino (ej. *Sucursal Mall Ventura*) de forma que el stock quede por debajo del mínimo de seguridad.
3. El motor de inferencia del Sistema Experto se ejecuta automáticamente por evento en segundo plano al detectar el stock crítico.
4. Observá el contador en la **campanita de notificaciones** arriba a la derecha. Hacé clic en ella o ingresá a `/app/notifications`.
5. **Resultado:**
   * La lista muestra una tarjeta interactiva con el sello **🧠 Sistema Experto IA**:
     * Detalle: Prenda, Sucursal Origen (con excedente), Sucursal Destino (con stock crítico), Cantidad sugerida y Justificación lógica de inferencia ($R_1$-$R_4$).
     * Botones de acción directa: **"Aprobar traspaso"** y **"Descartar sugerencia"**.
6. Hacé clic en **"Aprobar traspaso"**.
7. **Resultado:**
   * Toast: `"Órdenes de traspaso automático aplicadas al inventario"`.
   * El stock se actualiza atómicamente entre ambas sucursales.

##### Pasos para probar la vista tradicional directa (compatibilidad):
1. Ingresá directamente por URL a `/app/admin/expert-replenishment`.
2. Hacé clic en el botón **"Evaluar Reabastecimiento"**.
3. Marcá las sugerencias pendientes y hacé clic en **"Aplicar Traspasos"**.

---

#### CU10 – Registrar ingreso de mercadería con RPA e IA
* **Rama de IA:** **RPA con IA** (*Intelligent Document Processing* - OCR + Extracción Semántica Gemini)
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:** Proveedor o Administrador
* **Credenciales:**
  * Proveedor: `carlos.aliaga@ayni-moda-proveedores.demo.bo` / `Fashion2026!`
  * O Administrador: `carolina.quiroga@ayni-moda.demo.bo` / `Fashion2026!`
* **Ruta UI:**
  * Proveedor: `/app/proveedor/rpa-ingest`
  * Administrador: `/app/admin/rpa-ingest`

##### Pasos para probar:
1. Iniciá sesión como Proveedor o Administrador.
2. Ingresá a la sección **"Ingesta RPA"**.
3. En la zona de arrastre de archivos, seleccioná o arrastrá el documento de prueba del repositorio:
   * **Ruta del archivo de prueba:** `docs/demo/remito_demo.pdf`.
4. Hacé clic en **"Procesar Documento con RPA"**.
5. **Resultado esperado:**
   * Se genera un trabajo de extracción (`job_id`) en segundo plano.
   * La interfaz muestra un indicador de procesamiento y luego presenta la **grilla de ítems extraídos automáticamente**: SKU, Nombre de prenda, Talla, Color, Cantidad y Costo Unitario.
6. Hacé clic en **"Confirmar Ingreso al Inventario"**.
7. **Resultado esperado:**
   * Toast: `"Mercadería ingresada al inventario y catálogo sincronizado exitosamente"`.
   * El stock de las prendas asociadas se incrementa de forma inmediata.

---

### MÓDULO 3: Inventario y Operaciones de Sucursal

#### CU11 – Transferir inventario entre sucursales
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:** Administrador o Encargado de Sucursal
* **Credenciales:**
  * Administrador: `carolina.quiroga@ayni-moda.demo.bo` / `Fashion2026!`
  * Encargado: `rodrigo.choque@ayni-moda.demo.bo` / `Fashion2026!`
* **Ruta UI:** `/app/admin/inventory` o `/app/encargado/inventory`

##### Pasos para probar:
1. Iniciá sesión con el Administrador o Encargado.
2. Dirigite a **"Inventario"** (`/app/admin/inventory`).
3. Localizá una prenda con stock disponible y hacé clic en el botón de acción **"Traspaso"** / **"Transferir Stock"**.
4. En el modal emergente:
   * Seleccioná la **Sucursal Origen** (debe tener existencias).
   * Seleccioná la **Sucursal Destino** (distinta a la de origen).
   * Indicá la variante (talle/color) y la **Cantidad** (menor o igual al stock disponible).
   * Ingresá una nota opcional: *"Refuerzo por campaña"*.
5. Hacé clic en **"Confirmar Traspaso"**.
6. **Resultado esperado:**
   * Toast verde: `"Traspaso de inventario registrado exitosamente"`.
   * El stock de origen disminuye y el de destino se incrementa de inmediato.

---

#### CU12 – Recibir notificaciones push en el móvil
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:** Cliente (en Móvil) y Sistema/Encargado (en Web)
* **Credenciales:** Cliente `maria.quispe@clientes.demo.bo` / `Cliente2026!`
* **Plataforma:** Móvil (Flutter) y Web (`/app/notifications`)

##### Pasos para probar:
1. Abrí la app Flutter en emulador o dispositivo e iniciá sesión con la cuenta de cliente.
2. Aceptá el diálogo de permisos de notificaciones del sistema operativo (se registra el token FCM en `/api/notifications/push/register-token`).
3. Desde la web, ingresá como Cajero o Encargado y cambiá el estado de un pedido del cliente a `"Listo para retirar"` o confirmá una entrega.
4. **Resultado esperado:**
   * El emulador/dispositivo móvil recibe el banner push en la barra de notificaciones del sistema operativo.
   * Al tocar la notificación, abre la app y muestra el detalle del evento en la campana de notificaciones.

---

### MÓDULO 4: Business Intelligence y Reportes

#### CU13 – Consultar dashboard de métricas comerciales
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:** Administrador de Tenant
* **Credenciales:** `carolina.quiroga@ayni-moda.demo.bo` / `Fashion2026!` (Pestaña: *Administrativos*)
* **Ruta UI:** `/app/admin` (Dashboard principal)

##### Pasos para probar:
1. Iniciá sesión como Administrador de empresa.
2. Ingresá a la vista principal `/app/admin`.
3. Verificá los 4 KPIs superiores: **Facturación Total, Unidades Vendidas, Ticket Promedio y Clientes Activos**.
4. Cambiá el selector de sucursales (ej. *Todas las sucursales* vs *Ayni La Paz Centro*).
5. Observá cómo los gráficos (ventas por día, ventas por categoría y productos más vendidos) se recalculan dinámicamente según el filtro.

---

#### CU14 – Generar y exportar reportes operativos
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:** Administrador o Encargado
* **Credenciales:** `carolina.quiroga@ayni-moda.demo.bo` / `Fashion2026!`
* **Ruta UI:** `/app/admin/reports` (Sección tradicional de reportes o ventas `/app/admin/sales`)

##### Pasos para probar:
1. Accedé a la sección de reportes o historial de ventas.
2. Establecé un rango de fechas (ej. desde el 01 del mes corriente hasta hoy).
3. Hacé clic en **"Exportar a CSV"** o **"Exportar a Excel"**.
4. **Resultado:**
   * Toast: `"Archivo generado exitosamente. La descarga comenzará automáticamente."`
   * Se descarga el archivo tabulado con el detalle de cada transacción, cajero, sucursal e importes.

---

### MÓDULO 5: Promociones, Fidelización y Experiencia de Cliente

#### CU15 – Gestionar y aplicar cupones de descuento
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:**
  * Parte A (Crear cupón): Administrador (`carolina.quiroga@ayni-moda.demo.bo` / `Fashion2026!`)
  * Parte B (Aplicar cupón): Cliente (`maria.quispe@clientes.demo.bo` / `Cliente2026!`)
* **Ruta UI:**
  * Admin: `/app/admin/promotions`
  * Cliente: `/app/cliente/cart`

##### Pasos para probar:
1. **Crear Cupón (Admin):**
   * Ingresá a `/app/admin/promotions` y hacé clic en **"Crear Cupón"**.
   * Código: `PROMO20`, Descuento: `20%`, Límite de usos: `100`, Vigencia: Fechas del mes actual.
   * Guardá el cupón.
2. **Aplicar Cupón (Cliente):**
   * En otra ventana o tras cerrar sesión, ingresá como cliente.
   * Agregá cualquier prenda al carrito y andá a `/app/cliente/cart`.
   * En la caja de texto **"Cupón de descuento"**, ingresá `PROMO20` y presioná **"Aplicar"**.
3. **Resultado esperado:**
   * Toast verde: `"Cupón de descuento aplicado exitosamente"`.
   * El desglose del carrito refleja el descuento aplicado y el nuevo total a pagar disminuye.

---

#### CU16 – Gestionar lista de deseos (*Wishlist*)
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:** Cliente
* **Credenciales:** `maria.quispe@clientes.demo.bo` / `Cliente2026!` (Pestaña: *Clientes*)
* **Ruta UI:** `/app/cliente/catalog`, `/app/cliente/products/:productId` y `/app/cliente/wishlist` (Menú: *"Lista de Deseos"*)

##### Pasos para probar:
1. Iniciá sesión como cliente.
2. Navegá por el catálogo (`/app/cliente/catalog`) y hacé clic en el **icono de corazón** de una prenda, o ingresá a su detalle y presioná **"Añadir a lista de deseos"**.
3. **Resultado:**
   * El corazón se colorea de rojo.
   * Toast: `"Prenda añadida a tu lista de deseos"`.
4. Andá a tu lista de deseos en `/app/cliente/wishlist` (en el menú superior o de perfil).
5. Verificá que la prenda guardada aparece en la grilla con su precio y estado de stock.
6. Hacé clic en el botón **"Mover al Carrito"** de la tarjeta.
7. Seleccioná talle/color y confirmá.
8. **Resultado:**
   * Toast: `"Prenda movida al carrito de compras con éxito"`.
   * La prenda se quita de la lista de deseos y pasa al carrito de compras de esa empresa.

---

#### CU17 – Acumular y canjear puntos de fidelización (*Loyalty*)
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:**
  * Cliente: `maria.quispe@clientes.demo.bo` / `Cliente2026!`
  * Cajero: `lucia.apaza@ayni-moda.demo.bo` / `Fashion2026!`
* **Ruta UI:**
  * Cliente: `/app/cliente/loyalty` (Menú: *"Mis Puntos"*) y en `/app/cliente/cart`
  * Cajero: `/app/cajero/caja`

##### Pasos para probar:
1. **Consultar Puntos (Cliente):**
   * Ingresá como cliente y andá a `/app/cliente/loyalty`.
   * Verificá el saldo de puntos acumulados por empresa, el nivel alcanzado (*Bronce, Plata, Oro*) y la equivalencia en dinero (100 puntos = 1 Bs).
2. **Canje de Puntos en Checkout Web:**
   * Agregá prendas al carrito y procedé al pago en `/app/cliente/cart`.
   * En el bloque de pago, activá la opción **"Canjear Puntos"** e indicá la cantidad (en múltiplos de 10).
   * Verificá que el total se descuenta según los puntos indicados.
3. **Canje de Puntos en Caja Física (Cajero):**
   * Iniciá sesión como Cajera (`lucia.apaza@ayni-moda.demo.bo`) en `/app/cajero/caja`.
   * Seleccioná prendas para una venta.
   * En el campo de cliente, ingresá el correo: `maria.quispe@clientes.demo.bo`.
   * El sistema consulta automáticamente el saldo de puntos de la clienta en esa empresa.
   * Ingresá los puntos a canjear en el campo correspondiente y completá la venta.
   * **Resultado:** La venta descuenta el importe equivalente de los puntos y emite el recibo oficial con el saldo restante.

---

#### CU18 – Comprar y emitir tarjetas de regalo (*Gift Cards*)
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:** Cliente
* **Credenciales:** `maria.quispe@clientes.demo.bo` / `Cliente2026!`
* **Ruta UI prevista:** `/app/cliente/gift-cards` y en perfil móvil.

##### Pasos para probar según especificación:
1. Ingresá como cliente a la sección de Gift Cards.
2. Seleccioná el monto predeterminado (ej. $50) o ingresá un monto personalizado (mínimo $10).
3. Completá los datos del destinatario:
   * **Nombre:** `Camila Morales`
   * **Correo:** `camila@gmail.com`
   * **Dedicatoria:** `¡Feliz cumpleaños!`
4. Seleccioná medio de pago y confirmá.
5. **Resultado esperado:**
   * Mensaje de éxito: `"Tarjeta de regalo adquirida y enviada por correo al destinatario"`.
   * Se genera un código único (ej. `GIFT-2026-X89Q`) con código QR para descarga.

* **Endpoint API especificado:**
  ```bash
  curl -X POST http://localhost:8000/api/gift-cards/purchase \
    -H "Authorization: Bearer <CLIENT_TOKEN>" \
    -H "Content-Type: application/json" \
    -d '{"amount":50.0,"recipient_name":"Camila Morales","recipient_email":"camila@gmail.com","custom_message":"¡Felicidades!","payment_method":"stripe"}'
  ```

---

#### CU19 – Gestionar billetera digital (*Store Wallet*)
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:** Cliente
* **Credenciales:** `maria.quispe@clientes.demo.bo` / `Cliente2026!`
* **Ruta UI prevista:** `/app/cliente/wallet` y opción *"Mi Billetera Digital"* en el menú de perfil móvil.

##### Pasos para probar según especificación:
1. Accedé a la sección de billetera digital desde el perfil o menú lateral.
2. Verificá el saldo actual monetario y el historial de transacciones.
3. En el campo **"Canjear Gift Card"**, ingresá el código recibido (ej. `GIFT-2026-X89Q`) y presioná Canjear.
4. **Resultado esperado:**
   * Toast: `"Gift Card canjeada exitosamente. Se acreditaron $50.00 en tu saldo."`
   * El balance de la billetera se actualiza de inmediato.
5. Al realizar una compra en el carrito, seleccioná como medio de pago **"Billetera Digital"** para pagar debitando directamente del saldo.

---

### MÓDULO 6: Logística, Despacho y Posventa

#### CU20 – Gestionar envío a domicilio con validación por PIN
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:**
  * Cliente: `maria.quispe@clientes.demo.bo` / `Cliente2026!`
  * Repartidor: `javier.mamani@repartidores.demo.bo` / `Fashion2026!`
  * Superadministrador: `superadmin@fashionstore.com` / `SuperAdmin2026!`
* **Ruta UI:**
  * Superadministrador: `/app/superadmin/drivers` (Gestión de repartidores de plataforma)
  * Repartidor: `/app/delivery` (Hoja de ruta del día y confirmación con PIN)
  * Cliente: `/app/cliente/cart` (Cotización de flete) y `/app/cliente/orders`

##### Pasos para probar:
1. **Cotización y Pedido con Delivery (Cliente):**
   * Iniciá como cliente, agregá prendas al carrito y seleccioná despacho a domicilio en `/app/cliente/cart`.
   * El sistema calcula el flete con `/api/delivery/quotes` según la distancia de la sucursal.
   * Pagá el pedido con tarjeta de prueba en Stripe.
   * En el detalle del pedido generado, observá el **Código PIN de seguridad de 4 dígitos** asignado a la entrega (ej. `8492`).
2. **Reclamar y Despachar Pedido (Repartidor):**
   * En otra pestaña o sesión, ingresá como Repartidor (`javier.mamani@repartidores.demo.bo`).
   * Accedé a `/app/delivery`. En la lista de pedidos disponibles, reclamá el pedido para entrega (`in_transit`).
3. **Entrega y Validación con PIN:**
   * Hacé clic en **"Confirmar Entrega"**.
   * Ingresá un PIN incorrecto (`0000`). Observá el error: `"El código PIN de seguridad es incorrecto"`.
   * Ingresá el PIN real del cliente (`8492`) y confirmá.
   * **Resultado:** Toast verde: `"Entrega confirmada y registrada exitosamente"`. El pedido pasa a estado `delivered`.

---

#### CU21 – Solicitar y procesar cambios y devoluciones (RMA)
* **Estado:** **Hecho e Implementado**
* **Actor de prueba:**
  * Cliente (Solicita): `maria.quispe@clientes.demo.bo` / `Cliente2026!`
  * Encargado (Resuelve): `rodrigo.choque@ayni-moda.demo.bo` / `Fashion2026!`
* **Ruta UI prevista:** `/app/cliente/returns/new` (desde `/app/cliente/orders`) y `/app/encargado/returns`.

##### Pasos para probar según especificación:
1. **Listado de Órdenes Elegibles (Cliente):**
   * Iniciá sesión como Cliente (`maria.quispe@clientes.demo.bo`).
   * Ingresá a la sección de devoluciones (`/app/cliente/returns/new`).
   * **Resultado esperado:** La interfaz lista **exclusivamente las ventas entregadas dentro de los últimos 30 días**. Si una compra tiene más de 30 días, no aparece o figura deshabilitada con el aviso de plazo vencido.
2. **Armado de Solicitud Multilínea (Cliente):**
   * Seleccioná una orden que contenga 2 o más prendas.
   * **Prenda 1:** Seleccioná motivo *"Talle incorrecto"*, resolución *"Cambio de prenda"* y elegí la variante deseada (ej. talle L). Si el selector indica *"Sin stock en esta variante"*, elegí una variante/prenda alternativa de igual valor o conmutá a *"Crédito en tienda"*.
   * **Prenda 2:** Seleccioná motivo *"Defecto de fábrica"*, resolución *"Crédito en tienda"* y redactá la nota explicativa.
   * Presioná **"Enviar Solicitud de RMA"**.
   * **Resultado:** Notificación verde con el número de reclamo generado (ej. `RMA-2026-0914`) en estado `pending_inspection` conteniendo los ítems seleccionados.
3. **Inspección Física y Dictamen Ítem por Ítem (Encargado):**
   * Iniciá sesión como Encargado (`rodrigo.choque@ayni-moda.demo.bo`) e ingresá a `/app/encargado/returns`.
   * Abrí la solicitud `RMA-2026-0914`.
   * **Ítem 1 (Cambio por talle):** Inspeccioná la prenda física.
     * Si está **Intacta** (con etiquetas y sin uso): Marcá `Aprobado`, reingreso a stock comercial (`rma_restock`) y confirmá el despacho de la nueva prenda. Si la variante solicitada no tuviese stock en la sucursal, el modal te permite seleccionar una prenda alternativa en acuerdo con el cliente o conmutar a reembolso en billetera.
     * Si presenta **Daño atribuible al cliente** (mancha, uso): Marcá `Rechazado` con nota de rechazo.
   * **Ítem 2 (Defecto de fábrica):**
     * Constatá la falla de origen. Marcá `Aprobado por defecto de fábrica`, derivando el ítem físico a **merma/cuarentena** (`scrap_quarantine`) y autorizando el saldo a la billetera digital.
   * **Resultado final:**
     * La solicitud padre pasa a estado `approved` (si todos los ítems fueron aprobados) o `partially_approved` (si uno fue aprobado y otro rechazado).
     * El saldo de las prendas con reembolso queda programado con fecha al cierre del mes corriente (`scheduled_month_end`) para preservar el control contable y de inventario.
     * **Notificación al Cliente:** El cliente recibe inmediatamente una notificación push y alerta interna: *"Tu solicitud de devolución fue dictaminada. Se programó la acreditación de Bs. 220.00 en tu Billetera Digital al cierre del mes."*
     * El botón **"Descargar Ficha PDF"** permite obtener la ficha actualizada con el dictamen técnico y firmas de sucursal.
     * El stock comercial de la prenda devuelta intacta aumenta en +1, la reposición entregada en el acto se descuenta en -1, y la prenda defectuosa queda radicada en el libro de mermas técnicas.

---

#### CU22 – Instalar la aplicación web progresiva (PWA)
* **Estado:** **Hecho e Implementado**
* **Plataforma:** **Web**
* **Actor de prueba:** Cualquier usuario en navegador Chromium / Safari
* **Ruta:** Raíz de la aplicación web `http://localhost:4200`

##### Pasos para probar según especificación:
1. Abrí la aplicación web en Google Chrome, Edge o navegador móvil.
2. Verificá la presencia del endpoint dinámico y archivo en `http://localhost:4200/api/pwa/manifest` y `/manifest.webmanifest`.
3. Observá el botón o banner emergente **"Instalar aplicación"** provisto por el componente de interceptación de `beforeinstallprompt`.
4. Hacé clic en el icono de instalación de la barra de direcciones de Chrome ("Instalar FashionStore").
5. **Resultado esperado:**
   * La app se instala como aplicación independiente de escritorio (*standalone*), abriendo en su propia ventana sin barra de URL del navegador.
   * Al desconectar la red, los assets principales y vistas cacheadas por el Service Worker continúan visualizándose (App Shell sin pantalla de dinosaurio).

---

#### CU23 – Consultar catálogo sin conexión (Offline)
* **Estado:** **Especificado / En Proceso**
* **Plataforma:** **Ambas (Web y Móvil)**
* **Actor de prueba:** Cajero en POS físico (`lucia.apaza@ayni-moda.demo.bo`) o Cliente
* **Ruta UI:** `/app/cajero/caja` (Web) y Catálogo (Móvil)

##### Pasos para probar según especificación:
1. Iniciá sesión en la terminal de caja (`/app/cajero/caja`). El sistema precarga automáticamente el snapshot de catálogo de la sucursal en **IndexedDB** (`cached_catalog`) en Web o **SQLite** en Móvil.
2. Desconectá la red (F12 -> Red -> Offline o apagá Wi-Fi).
3. Escribí en el buscador de la caja el nombre de un producto o ingresá un SKU.
4. **Resultado esperado:**
   * Las prendas coinciden y se renderizan al instante con sus talles, colores, precios y stock conocido, sin lanzar errores de red.

---

#### CU24 – Reintegrar inventario por devoluciones y registrar mermas
* **Estado:** **Hecho / Verificado**
* **Plataforma:** **Web**
* **Actor de prueba:** Encargado de Sucursal o Administrador
* **Credenciales:** `rodrigo.choque@ayni-moda.demo.bo` / `Fashion2026!`
* **Ruta UI:** `/app/encargado/returns`

##### Pasos para probar según especificación:
1. Iniciá sesión como Encargado e ingresá al módulo de inspección técnica de devoluciones sobre un ítem de RMA.
2. Evaluá los siguientes escenarios operativos:
   * **Escenario A (Reintegro comercial por prenda intacta):** Prenda devuelta en perfecto estado se reintegra al stock comercializable y reposición apartada.
   * **Escenario B (Falta de stock para el cambio y selección de alternativa):** Se selecciona prenda alternativa o se conmuta a saldo en billetera.
   * **Escenario C (Descarte a merma técnica por defecto de fábrica):** Se genera acta oficial de cuarentena `QR-2026-XXXX` y merma técnica.
   * **Escenario D (Rechazo por uso/daño del cliente):** Se emite acta de rechazo formal sin alterar existencias.

---

#### CU25 – Registrar ventas y reservas sin conexión (POS Offline)
* **Estado:** **Especificado / En Proceso**
* **Plataforma:** **Ambas (Web y Móvil)**
* **Actor de prueba:** Cajero en POS físico (`lucia.apaza@ayni-moda.demo.bo`)
* **Ruta UI:** `/app/cajero/caja`

##### Pasos para probar según especificación:
1. En `/app/cajero/caja`, desconectá la red (**Offline**).
2. Observá la barra de alerta ámbar: *"Estás trabajando en modo sin conexión. Tus ventas se guardan localmente."*
3. Seleccioná productos del catálogo cacheado para agregar al carrito.
4. Intentá cobrar: verificá que las opciones de pasarela electrónica / tarjeta estén inhabilitadas y solo se permita **Efectivo / Contado** o **Reserva presencial**.
5. Confirmá el cobro.
6. **Resultado esperado:**
   * La transacción genera un identificador local único (`operation_id`) y se encola en `pending_operations_queue`.
   * Se emite un comprobante provisional de venta/reserva con la leyenda oficial de contingencia.

---

#### CU29 – Gestionar cola de operaciones pendientes (Offline Queue)
* **Estado:** **Especificado / En Proceso**
* **Plataforma:** **Ambas (Web y Móvil)**
* **Actor de prueba:** Cajero y Administrador
* **Ruta UI:** Barra superior de `/app/cajero/caja` y modal de auditoría

##### Pasos para probar según especificación:
1. Tras registrar una o más ventas o reservas en contingencia sin internet, observá el badge numérico en la barra de caja: *"X transacciones pendientes"*.
2. Hacé clic en el badge para abrir el modal `OfflineQueueModal`.
3. Verificá que se listen todas las operaciones encoladas con hora, cliente, tipo (`sale`/`reservation`) y total cobrado.
4. Cerrá y volvé a abrir el navegador; comprobá que la cola se mantiene intacta (persistencia garantizada RNF03).
5. Observá el botón **"Sincronizar ahora"** disponible para forzar el despacho manual cuando vuelva el internet.

---

#### CU30 – Sincronizar operaciones offline y resolver conflictos de inventario
* **Estado:** **Especificado / En Proceso**
* **Plataforma:** **Ambas (Web y Móvil)**
* **Actor de prueba:** Cajero, Administrador y Cliente
* **Ruta UI:** `/app/cajero/caja` y `/app/cajero/offline-conflicts`

##### Pasos para probar según especificación:
1. **Prueba de Sincronización Exitosa (Sin colisión):**
   * Teniendo ventas offline en cola, restablecé la red (**Online**).
   * El despachador envía el lote a `/api/offline/queue-sync`.
   * **Resultado:** Toast verde: *"Sincronización completada. Se procesaron X operaciones locales."* El stock en PostgreSQL se descuenta y la cola local queda vacía.
2. **Prueba de Colisión de Stock (Conflicto de inventario):**
   * Simulá una venta offline de la última prenda (stock = 1).
   * Por otro navegador (tienda online o admin), vendé o transferí esa misma prenda para dejar el stock en 0.
   * Reconectá la caja offline.
   * **Resultado:** El backend rechaza la operación con código `conflict_rejected` / `inventory_collision` y la caja muestra alerta: *"Se detectaron colisiones de inventario"*.
3. **Resolución en Consola de Conflictos (`/app/cajero/offline-conflicts`):**
   * Ingresá a la consola de conflictos. Observá la venta resaltada en rojo con el detalle del quiebre.
   * Seleccioná la resolución:
     - **Opción A:** Devolución de efectivo físico.
     - **Opción B:** Acreditación de saldo en la Billetera Digital (`Store Wallet`) con bono de cortesía del 10%.
     - **Opción C:** Ajuste de rotura de inventario negativo si la prenda ya fue retirada.
   * Confirmá y validá la conciliación contable y la notificación enviada al cliente.

---

## Cuadro Resumen de Pruebas Rápidas por Rol

| Para probar... | Iniciar sesión como... | Correo / Contraseña | Pestaña | Ruta directa |
|---|---|---|---|---|
| **Multi-Tenant y Planes** | Superadmin | `superadmin@fashionstore.com`<br>`SuperAdmin2026!` | Administrativos | `/app/superadmin/tenants`<br>`/app/superadmin/plans` |
| **Suscripción y Cuotas** | Admin Ayni Moda | `carolina.quiroga@ayni-moda.demo.bo`<br>`Fashion2026!` | Administrativos | `/app/admin/subscription` |
| **RBAC / Roles dinámicos** | Admin Ayni Moda | `carolina.quiroga@ayni-moda.demo.bo`<br>`Fashion2026!` | Administrativos | `/app/admin/roles` |
| **Reportes IA y ML** | Admin Ayni Moda | `carolina.quiroga@ayni-moda.demo.bo`<br>`Fashion2026!` | Administrativos | `/app/admin/reports` |
| **Sistema Experto Stock** | Admin Ayni Moda | `carolina.quiroga@ayni-moda.demo.bo`<br>`Fashion2026!` | Administrativos | `/app/notifications`<br>*(o directa `/app/admin/expert-replenishment`)* |
| **Ingesta RPA con PDF** | Proveedor | `carlos.aliaga@ayni-moda-proveedores.demo.bo`<br>`Fashion2026!` | Administrativos | `/app/proveedor/rpa-ingest` |
| **Traspaso de Inventario** | Encargado | `rodrigo.choque@ayni-moda.demo.bo`<br>`Fashion2026!` | Administrativos | `/app/encargado/inventory` |
| **Venta en Caja y Puntos** | Cajera | `lucia.apaza@ayni-moda.demo.bo`<br>`Fashion2026!` | Administrativos | `/app/cajero/caja` |
| **Hoja de Ruta y PIN Delivery** | Repartidor | `javier.mamani@repartidores.demo.bo`<br>`Fashion2026!` | Administrativos | `/app/delivery` |
| **Catálogo, Wishlist, Chatbot, VTO** | Cliente | `maria.quispe@clientes.demo.bo`<br>`Cliente2026!` | Clientes | `/app/cliente/catalog`<br>`/app/cliente/wishlist` |
| **Landing y Onboarding** | Público | Sin sesión | — | `/landing` |
