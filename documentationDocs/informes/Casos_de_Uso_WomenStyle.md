# Casos de Uso – FashionStore

Documento resumen del flujo de trabajo **1. Captura de Requisitos** (PUDS) — Parte II del informe.

> **Nota:** el sistema base cubre 23 CU trazables a los RF01–RF25 del examen. Se agrega **CU24 – Recibir notificaciones push** como funcionalidad adicional (plus) propuesta por el equipo, sin RF numerado de origen, ubicada en el Ciclo 3 y en el Paquete P6.

---

## 1. Lista de Casos de Uso

**Módulo 1 – Usuarios y Roles**

- **CU01 – Registrar cliente**: Alta de cuenta con datos personales y credenciales de acceso. *Actor: Cliente.*
- **CU02 – Iniciar sesión**: Autenticación mediante JWT según el rol del usuario. *Actores: Cliente, Administrador, Encargado de sucursal, Cajero, Proveedor.*
- **CU03 – Gestionar usuarios internos**: Alta, edición y baja de administradores, encargados de sucursal y cajeros. *Actor: Administrador.*
- **CU04 – Gestionar sucursales**: Registro y administración de sucursales por ciudad. *Actor: Administrador.*
- **CU05 – Gestionar cuentas de proveedor**: Alta, aprobación o suspensión de la cuenta que usará el proveedor. *Actor: Administrador.*
- **CU06 – Consultar y actualizar perfil**: Edición de datos personales del cliente. *Actor: Cliente.*

**Módulo 2 – Inventario**

- **CU07 – Registrar y enviar información de productos**: El proveedor envía datos de sus prendas (características, disponibilidad, temporada/colección); el administrador valida antes de publicar. *Actor principal: Proveedor. Actor secundario: Administrador.*
- **CU08 – Gestionar catálogo y productos**: Alta, edición y baja de prendas ya validadas, incluyendo promociones y condiciones comerciales. *Actor: Administrador.*
- **CU09 – Gestionar atributos del catálogo**: Administración de categorías, tallas, colores, temporadas y colecciones. *Actor: Administrador.*
- **CU10 – Consultar y filtrar catálogo**: Búsqueda por categoría, talla, color, temporada y precio desde web/móvil. *Actor: Cliente.*
- **CU11 – Consultar disponibilidad por sucursal**: Verificación de stock en tiempo real por talla, color y sucursal. *Actor: Cliente.*
- **CU12 – Registrar movimiento de inventario**: Registro de ingresos, salidas y traspasos entre sucursales. *Actores: Encargado de sucursal, Cajero.*
- **CU13 – Consultar inventario consolidado**: Vista global de existencias de todas las sucursales. *Actor: Administrador.*

**Módulo 3 – Compra**

- **CU14 – Gestionar reservas de prendas**: Selección de prendas, sucursal y horario; consulta y cancelación de la reserva. *Actor: Cliente.*
- **CU15 – Gestionar carrito de compras**: Adición y edición de productos antes de la compra. *Actor: Cliente.*
- **CU16 – Realizar compra digital y consultar estado del pedido**: Checkout vía web/móvil con pasarela de pago electrónica, y seguimiento del estado (pagado, en preparación, listo). *Actor: Cliente.*

**Módulo 4 – Venta**

- **CU17 – Atender reserva en sucursal**: Preparación de prendas reservadas y confirmación de la llegada del cliente. *Actor: Encargado de sucursal.*
- **CU18 – Registrar venta presencial y procesar pago en caja**: Registro de venta física (con o sin reserva previa), cobro y emisión de comprobante. *Actor: Cajero.*

**Módulo 5 – Realidad Aumentada**

- **CU19 – Usar vestidor virtual**: Visualización de la prenda sobre la imagen del cliente vía cámara del dispositivo móvil. *Actor: Cliente.*

**Módulo 6 – Reportes**

- **CU20 – Generar reportes y dashboards**: Reportes de ventas e inventario por sucursal, producto y periodo, con indicadores visuales y exportación. *Actor: Administrador.*

**Módulo 7 – Asistencia Inteligente**

- **CU21 – Recibir recomendaciones de IA**: Sugerencias de productos según historial, temporada y disponibilidad. *Actor: Cliente.*
- **CU22 – Consultar asistente virtual/chatbot**: Resolución de dudas del cliente sobre productos. *Actor: Cliente.*
- **CU23 – Generar reporte por voz/lenguaje natural**: Solicitud de reportes generativos mediante comando de voz. *Actor: Administrador.*

**Funcionalidad adicional (plus del equipo, sin RF numerado de origen)**

- **CU24 – Recibir notificaciones push**: Envío de alertas automáticas en tiempo real al dispositivo móvil sobre eventos relevantes del sistema (cambios de estado, alertas operativas, recomendaciones, nuevas temporadas/prendas), sin que el usuario tenga que consultarlos manualmente. Cada actor recibe un tipo distinto de notificación según los eventos que le corresponden. *Actores: Administrador, Cliente, Encargado de sucursal (Proveedor: pendiente de confirmación del equipo).*

---

## 2. Distribución de Casos de Uso por Ciclos

Proyecto dividido en **3 ciclos**, aumentando progresivamente la complejidad técnica. La columna **Plataforma** indica dónde estará disponible cada CU (Web, Móvil o Ambas), según lo definido en el alcance y el enunciado del examen.

### Ciclo 1 (10 CU) — Base del sistema / MVP inicial

| ID | Caso de uso | Prioridad | Riesgo | Estado | Actor(es) principal | Plataforma |
|---|---|---|---|---|---|---|
| CU01 | Registrar cliente | Alta | Bajo | Pendiente | Cliente | Ambas |
| CU02 | Iniciar sesión | Alta | Medio | Pendiente | Cliente, Administrador, Encargado de sucursal, Cajero, Proveedor | Ambas |
| CU03 | Gestionar usuarios internos | Alta | Medio | Pendiente | Administrador | Web |
| CU04 | Gestionar sucursales | Alta | Bajo | Pendiente | Administrador | Web |
| CU05 | Gestionar cuentas de proveedor | Media | Medio | Pendiente | Administrador | Web |
| CU06 | Consultar y actualizar perfil | Media | Bajo | Pendiente | Cliente | Ambas |
| CU07 | Registrar y enviar información de productos | Alta | Medio | Pendiente | Proveedor (principal), Administrador (secundario) | Web |
| CU08 | Gestionar catálogo y productos | Alta | Medio | Pendiente | Administrador | Web |
| CU09 | Gestionar atributos del catálogo | Alta | Medio | Pendiente | Administrador | Web |
| CU10 | Consultar y filtrar catálogo | Alta | Medio | Pendiente | Cliente | Ambas |

### Ciclo 2 (8 CU) — Procesos transaccionales del negocio

| ID | Caso de uso | Prioridad | Riesgo | Estado | Actor(es) principal | Plataforma |
|---|---|---|---|---|---|---|
| CU11 | Consultar disponibilidad por sucursal | Alta | Medio | Pendiente | Cliente | Ambas |
| CU12 | Registrar movimiento de inventario | Alta | Medio | Pendiente | Encargado de sucursal, Cajero | Web |
| CU13 | Consultar inventario consolidado | Media | Bajo | Pendiente | Administrador | Web |
| CU14 | Gestionar reservas de prendas | Alta | Medio | Pendiente | Cliente | Ambas |
| CU15 | Gestionar carrito de compras | Alta | Bajo | Pendiente | Cliente | Ambas |
| CU16 | Realizar compra digital y consultar estado del pedido | Alta | Alto | Pendiente | Cliente | Ambas |
| CU17 | Atender reserva en sucursal | Alta | Medio | Pendiente | Encargado de sucursal | Web |
| CU18 | Registrar venta presencial y procesar pago en caja | Alta | Medio | Pendiente | Cajero | Web |

### Ciclo 3 (6 CU) — Realidad Aumentada, Inteligencia Artificial, Reportes avanzados y Notificaciones

| ID | Caso de uso | Prioridad | Riesgo | Estado | Actor(es) principal | Plataforma |
|---|---|---|---|---|---|---|
| CU19 | Usar vestidor virtual | Alta | Alto | Pendiente | Cliente | Móvil |
| CU20 | Generar reportes y dashboards | Media | Medio | Pendiente | Administrador | Web |
| CU21 | Recibir recomendaciones de IA | Media | Alto | Pendiente | Cliente | Ambas |
| CU22 | Consultar asistente virtual/chatbot | Baja | Alto | Pendiente | Cliente | Ambas |
| CU23 | Generar reporte por voz/lenguaje natural | Baja | Alto | Pendiente | Administrador | Web |
| CU24 | Recibir notificaciones push | Media | Alto | Pendiente | Administrador, Cliente, Encargado de sucursal | Móvil |

> CU24 es una **funcionalidad adicional (plus)** propuesta por el equipo, no exigida por el examen. Se ubica en el Ciclo 3 por su dependencia de eventos generados en CU07, CU12, CU14, CU16, CU17 y CU20, y por su riesgo técnico alto (integración con servicio de notificaciones push, ej. Firebase Cloud Messaging).

---

## 3. Paquetes de Arquitectura (Análisis de Arquitectura – PUDS)

Para el flujo de trabajo de **Análisis**, los 23 CU se agrupan en **6 paquetes** según afinidad funcional, reduciendo la complejidad del análisis y facilitando la identificación posterior de clases y relaciones.

- **P1 – Gestión de usuarios y acceso**: Registro de clientes, autenticación y acceso al sistema, administración de usuarios internos, gestión de sucursales, cuentas de proveedores y actualización de datos de perfil.
- **P2 – Gestión de productos y catálogo**: Envío de información por parte de proveedores, gestión de productos, promociones, categorías, tallas, colores, temporadas y colecciones; consulta y filtrado del catálogo por parte del cliente.
- **P3 – Gestión de inventario y disponibilidad**: Control de existencias en las diferentes sucursales, consulta de disponibilidad, registro de movimientos de inventario y consulta consolidada.
- **P4 – Gestión de compras y reservas**: Selección de prendas para reservar o comprar digitalmente, carrito de compras, checkout, pago electrónico y consulta del estado del pedido.
- **P5 – Gestión de ventas y atención en sucursal**: Operación presencial de la tienda: preparación y atención de reservas, registro de ventas presenciales, procesamiento de pago en caja y emisión de comprobante.
- **P6 – Experiencia inteligente y analítica**: Vestidor virtual mediante realidad aumentada, generación de reportes y dashboards, recomendaciones de IA, asistente virtual, generación de reportes por lenguaje natural, y envío de notificaciones push como canal proactivo de estos y otros módulos (compras, inventario, reservas).

---

## 4. Distribución de Casos de Uso en los 6 Paquetes

| Paquete | Casos de uso incluidos |
|---|---|
| **P1 – Gestión de usuarios y acceso** | CU01, CU02, CU03, CU04, CU05, CU06 |
| **P2 – Gestión de productos y catálogo** | CU07, CU08, CU09, CU10 |
| **P3 – Gestión de inventario y disponibilidad** | CU11, CU12, CU13 |
| **P4 – Gestión de compras y reservas** | CU14, CU15, CU16 |
| **P5 – Gestión de ventas y atención en sucursal** | CU17, CU18 |
| **P6 – Experiencia inteligente y analítica** | CU19, CU20, CU21, CU22, CU23, CU24 |

Nota: esta agrupación en paquetes es independiente de la distribución por ciclos — los ciclos organizan el **orden de desarrollo**, mientras que los paquetes organizan la **arquitectura lógica** del sistema.

---

## 5. Relaciones entre Casos de Uso (Include, Extend, Generalización)

### 5.1. Sobre CU02 – Iniciar sesión (aclaración importante)

Confirmando tu duda: **CU02 no debería modelarse como `<<include>>` hacia ningún otro CU**, ni siquiera hacia CU06. La razón es una regla de buena práctica en UML:

> Un `<<include>>` representa un **paso obligatorio dentro del flujo del caso base** (algo que el caso de uso *hace* como parte de su comportamiento). En cambio, estar autenticado es una **condición que debe cumplirse antes** de que el caso de uso pueda siquiera comenzar — es decir, una **precondición**, no un paso del flujo.

Si se modelara CU02 como `<<include>>` de todos los demás CU (o incluso de uno solo, como CU06), se rompe la consistencia del diagrama: o se aplica a los 22 CU restantes (lo cual generaría un diagrama saturado de flechas repetidas sin aportar información nueva) o se aplica arbitrariamente a uno solo, lo cual no tiene justificación distinta frente a los demás CU (todos requieren sesión iniciada por igual).

**Recomendación:** documentar "Usuario autenticado" como **precondición general del sistema** (una nota aparte en el diagrama o en la ficha de cada CU), y no dibujar flechas de `<<include>>` desde CU02.

**Alternativa más elegante (opcional):** en vez de listar los 5 actores por separado en CU02, se puede modelar una **generalización de actores**: crear un actor abstracto "Usuario del sistema" del cual heredan (generalización) Cliente, Administrador, Encargado de sucursal, Cajero y Proveedor, y hacer que sea ese actor abstracto quien se conecte a CU02. Esto es más limpio visualmente, aunque no es obligatorio — la lista explícita de 5 actores también es válida académicamente.

### 5.2. Relaciones `<<include>>` identificadas

- **CU18 (Registrar venta presencial y procesar pago en caja) `<<include>>` CU12 (Registrar movimiento de inventario)**
 Justificación: toda venta presencial completada **obligatoriamente** actualiza el inventario de la sucursal (RF20, RF22) — no es opcional ni condicional, siempre ocurre como parte del flujo de CU18. Además, ambos casos comparten actor (Cajero), lo que hace la relación consistente.

- **CU16 (Realizar compra digital y consultar estado del pedido) `<<include>>` CU12 (Registrar movimiento de inventario)**
 Justificación: por el mismo motivo que CU18, toda compra digital aprobada actualiza automáticamente el inventario (RF20). Para que esto sea consistente, CU12 se entiende con **dos modos de activación**: manual (el encargado de sucursal o el cajero registran explícitamente un ingreso, salida o traspaso) y automático (el sistema lo ejecuta como efecto interno de una venta ya confirmada, sin acción directa del actor sobre la pantalla de movimientos en ese momento). Ambos modos comparten el mismo efecto sobre el inventario y se modelan bajo el mismo caso de uso para evitar duplicar comportamiento.

- **CU14 (Gestionar reservas de prendas) `<<include>>` CU11 (Consultar disponibilidad por sucursal)**
 Justificación: el flujo de CU14 exige, en cada reserva y sin excepción, verificar la disponibilidad de las prendas seleccionadas en la sucursal elegida antes de poder confirmarla — es un paso obligatorio del flujo base, no una consulta opcional. Ambos casos comparten actor (Cliente).

- **CU14 (Gestionar reservas de prendas) `<<include>>` CU24 (Recibir notificaciones push)**
 Justificación: toda reserva nueva notifica **siempre** al Encargado de sucursal correspondiente, sin condición ni excepción, por lo que corresponde `<<include>>` y no `<<extend>>` (ver detalle en la sección 5.5).

### 5.3. Relaciones `<<extend>>` identificadas

Dentro de los 10 CU del Ciclo 1 no se identificó ninguna relación de `<<extend>>` clara y necesaria. Esto se debe a que los candidatos naturales para `<<extend>>` (por ejemplo, "cancelar reserva" como variante opcional de "gestionar reservas") ya fueron **fusionados dentro del mismo CU** (CU14) en la etapa de reducción de casos de uso, por lo que no queda un flujo alternativo/opcional independiente que amerite esta relación en ese ciclo.

Sin embargo, al detallar los Ciclos 2 y 3 sí se identificaron pasos verdaderamente **opcionales o condicionales** —que se insertan solo bajo ciertas circunstancias dentro del flujo del caso base, sin ser parte obligatoria de su ejecución—, por lo que corresponden a `<<extend>>`:

- **CU11 (Consultar disponibilidad por sucursal) `<<extend>>` CU10 (Consultar y filtrar catálogo)**
 Justificación: el cliente puede navegar y filtrar todo el catálogo sin verificar nunca la disponibilidad por sucursal; es un paso opcional que el cliente activa solo si lo decide para una prenda puntual. Ambos comparten actor (Cliente).

- **CU19 (Usar vestidor virtual) `<<extend>>` CU10 (Consultar y filtrar catálogo)**
 Justificación: mismo patrón que CU11 — el vestidor virtual es una función opcional, exclusiva de la aplicación móvil, que el cliente activa sobre una prenda ya visualizada en el catálogo, sin ser parte obligatoria de la navegación.

- **CU23 (Generar reporte por voz/lenguaje natural) `<<extend>>` CU20 (Generar reportes y dashboards)**
 Justificación: CU23 logra el mismo resultado que CU20 (generar reportes/dashboards) pero por un canal alternativo (comando de voz) en vez de la interacción manual habitual con filtros y exportación; es una forma opcional de disparar el mismo comportamiento base, no un paso obligatorio de CU20.

- **CU12 (Registrar movimiento de inventario) `<<extend>>` CU24 (Recibir notificaciones push)**
 Justificación: se activa únicamente si el movimiento deja el stock por debajo del umbral mínimo definido; notifica a Administrador y Encargado de sucursal (ver detalle en la sección 5.5).

- **CU16 (Realizar compra digital y consultar estado del pedido) `<<extend>>` CU24 (Recibir notificaciones push)**
 Justificación: se activa ante cada cambio de estado del pedido (pagado, en preparación, listo); notifica al Cliente (ver detalle en la sección 5.5).

- **CU17 (Atender reserva en sucursal) `<<extend>>` CU24 (Recibir notificaciones push)**
 Justificación: se activa al confirmar la preparación de la reserva; notifica al Cliente (ver detalle en la sección 5.5).

- **CU07 (Registrar y enviar información de productos) `<<extend>>` CU24 (Recibir notificaciones push)**
 Justificación: se activa cuando el Administrador valida y publica un producto nuevo enviado por el Proveedor; notifica al Cliente sobre nuevas prendas disponibles (ver detalle en la sección 5.5).

- **CU20 (Generar reportes y dashboards) `<<extend>>` CU24 (Recibir notificaciones push)**
 Justificación: se activa cuando el dashboard detecta un indicador crítico (ej. stock consolidado bajo, meta de ventas alcanzada); notifica al Administrador (ver detalle en la sección 5.5).

### 5.4. Generalización (herencia)

No se identificaron relaciones de generalización **entre casos de uso** (es decir, un CU que sea una versión más específica de otro). La única generalización aplicable en este modelo es la **de actores** mencionada en el punto 5.1 (actor abstracto "Usuario del sistema" → Cliente, Administrador, Encargado de sucursal, Cajero, Proveedor), y es opcional.

### 5.5. Relaciones de CU24 – Recibir notificaciones push

CU24 es un caso de uso particular: no tiene un actor humano que lo "dispare" directamente (el actor iniciador es el propio sistema), sino que se activa como reacción a eventos ocurridos en otros CU. Por eso concentra varias relaciones `<<include>>`/`<<extend>>` con los CU que generan esos eventos:

- **CU14 (Gestionar reservas de prendas) `<<include>>` CU24**: relación obligatoria — toda reserva nueva **siempre** notifica al Encargado de sucursal correspondiente, sin excepción, por lo que corresponde `<<include>>` y no `<<extend>>`.
- **CU12 (Registrar movimiento de inventario) `<<extend>>` CU24**: relación condicional — solo se activa si el movimiento deja el stock por debajo del umbral mínimo definido; notifica a Administrador y Encargado de sucursal.
- **CU16 (Realizar compra digital y consultar estado del pedido) `<<extend>>` CU24**: relación condicional — se activa ante cada cambio de estado del pedido (pagado, en preparación, listo); notifica al Cliente.
- **CU17 (Atender reserva en sucursal) `<<extend>>` CU24**: relación condicional — se activa al confirmar la preparación de la reserva; notifica al Cliente.
- **CU07 (Registrar y enviar información de productos) `<<extend>>` CU24**: relación condicional — se activa cuando el Administrador valida y publica un producto nuevo enviado por el Proveedor; notifica al Cliente sobre nuevas prendas disponibles.
- **CU20 (Generar reportes y dashboards) `<<extend>>` CU24**: relación condicional — se activa cuando el dashboard detecta un indicador crítico (ej. stock consolidado bajo, caída de ventas); notifica al Administrador.

Se usó `<<include>>` únicamente para CU14 porque es el único caso donde la notificación ocurre **siempre**, sin condición; el resto son `<<extend>>` porque dependen de una condición específica del evento (umbral de stock, cambio de estado, validación de producto, alerta de dashboard).

### 5.6. Nota sobre CU21 – Recibir recomendaciones de IA (relación pospuesta)

CU21 fue considerado como candidato a `<<extend>>` de CU10, de forma análoga a CU11 y CU19 (el cliente podría recibir sugerencias de IA de manera opcional mientras navega el catálogo). **Esta relación no se incorpora por el momento.** La razón es que la interfaz de recomendaciones todavía está en definición por el equipo: no se ha decidido si las sugerencias se mostrarán integradas dentro de la navegación del catálogo (lo que confirmaría el `<<extend>>` hacia CU10) o en una pantalla independiente, por ejemplo un apartado "Para ti" en el inicio de la app (en cuyo caso CU21 se mantendría como CU independiente, sin relación con CU10).

Se formalizará esta relación una vez que esa decisión de diseño de interfaz quede cerrada. Mientras tanto, **CU21 se documenta como caso de uso independiente**, sin flechas de `<<include>>`/`<<extend>>` hacia ningún otro CU.

### 5.7. Resumen consolidado de relaciones para el diagrama

| Relación | Origen | Destino | Tipo | Justificación breve |
|---|---|---|---|---|
| CU11 → CU10 | Consultar disponibilidad por sucursal | Consultar y filtrar catálogo | `<<extend>>` | Consulta opcional durante la navegación del catálogo |
| CU14 → CU11 | Gestionar reservas de prendas | Consultar disponibilidad por sucursal | `<<include>>` | Verificación de stock obligatoria antes de confirmar toda reserva |
| CU18 → CU12 | Registrar venta presencial y procesar pago en caja | Registrar movimiento de inventario | `<<include>>` | Toda venta presencial actualiza obligatoriamente el inventario |
| CU16 → CU12 | Realizar compra digital y consultar estado del pedido | Registrar movimiento de inventario | `<<include>>` | Toda compra digital aprobada actualiza obligatoriamente el inventario (modo automático de CU12) |
| CU19 → CU10 | Usar vestidor virtual | Consultar y filtrar catálogo | `<<extend>>` | Función opcional de RA sobre una prenda ya visualizada en el catálogo |
| CU23 → CU20 | Generar reporte por voz/lenguaje natural | Generar reportes y dashboards | `<<extend>>` | Canal alternativo (voz) para disparar el mismo resultado de CU20 |
| CU14 → CU24 | Gestionar reservas de prendas | Recibir notificaciones push | `<<include>>` | Toda reserva nueva notifica siempre al Encargado de sucursal |
| CU12 → CU24 | Registrar movimiento de inventario | Recibir notificaciones push | `<<extend>>` | Se activa solo si el stock cruza el umbral mínimo definido |
| CU16 → CU24 | Realizar compra digital y consultar estado del pedido | Recibir notificaciones push | `<<extend>>` | Se activa ante cada cambio de estado del pedido |
| CU17 → CU24 | Atender reserva en sucursal | Recibir notificaciones push | `<<extend>>` | Se activa al confirmar la preparación de la reserva |
| CU07 → CU24 | Registrar y enviar información de productos | Recibir notificaciones push | `<<extend>>` | Se activa al validar y publicar un producto nuevo del proveedor |
| CU20 → CU24 | Generar reportes y dashboards | Recibir notificaciones push | `<<extend>>` | Se activa ante un indicador crítico detectado en el dashboard |

**Total: 12 relaciones** (5 `<<include>>`, 7 `<<extend>>`) entre los 24 CU del proyecto.

Todo lo demás se mantiene como **casos de uso independientes**, conectados únicamente a su(s) actor(es) correspondiente(s), sin relaciones adicionales de inclusión, extensión o herencia entre sí. La generalización opcional de actor "Usuario del sistema" (mencionada en las secciones 5.1 y 5.4) se utiliza únicamente para simplificar el diagrama específico de CU02 – Iniciar sesión, y no forma parte de esta lista de relaciones entre casos de uso.

---

## 6. Trazabilidad: Casos de Uso vs. Requisitos Funcionales (Ecommerce.md)

Verificación de que los 23 CU cubren la totalidad de los Requisitos Funcionales (RF01–RF25) definidos en la guía del examen.

| RF | Descripción | CU que lo cubre |
|---|---|---|
| RF01 | Registrar clientes | CU01 |
| RF02 | Gestionar usuarios y roles | CU02, CU03 |
| RF03 | Administrar múltiples ciudades y sucursales | CU04 |
| RF04 | Gestionar productos de ropa | CU08 |
| RF05 | Gestionar tallas, colores, categorías y temporadas | CU09 |
| RF06 | Gestionar proveedores | CU05, CU07 |
| RF07 | Consultar catálogo desde web y móvil | CU10 |
| RF08 | Consultar disponibilidad por sucursal | CU11 |
| RF09 | Seleccionar múltiples prendas para una reserva | CU14 |
| RF10 | Registrar y gestionar reservas | CU14 |
| RF11 | Notificar las reservas a la sucursal correspondiente | CU14, CU17 |
| RF12 | Consultar el estado de una reserva | CU14 |
| RF13 | Utilizar el vestidor virtual (app móvil) | CU19 |
| RF14 | Agregar productos al carrito | CU15 |
| RF15 | Comprar mediante la plataforma web | CU16 |
| RF16 | Comprar mediante la aplicación móvil | CU16 |
| RF17 | Registrar ventas presenciales | CU18 |
| RF18 | Permitir pagos en punto de caja | CU18 |
| RF19 | Integrar pasarela de pago para compras digitales | CU16 |
| RF20 | Actualizar automáticamente el inventario tras una venta | CU12 (incluido desde CU18 y CU16, ver sección 5.2) |
| RF21 | Controlar las existencias por sucursal | CU11, CU13 |
| RF22 | Registrar movimientos de inventario | CU12 |
| RF23 | Gestionar temporadas y colecciones | CU09 |
| RF24 | Consultar reportes de ventas e inventario | CU20 |
| RF25 | Proporcionar al menos una funcionalidad basada en IA | CU21, CU22, CU23 |

**Resultado:** los 25 RF quedan cubiertos por los 23 CU base, sin excepciones ni requisitos huérfanos.

### CU24 – Recibir notificaciones push (funcionalidad adicional)

**CU24 no corresponde a ningún RF numerado del examen (RF01–RF25).** Es una funcionalidad adicional propuesta por el equipo para enriquecer la experiencia del usuario mediante alertas proactivas, apoyándose en eventos ya cubiertos por CU07, CU12, CU14, CU16, CU17 y CU20. Se documenta como un **plus** del proyecto, no como cobertura de un requisito faltante.

### Nota sobre los RNF y otras indicaciones

Los Requisitos No Funcionales (RNF01–RNF09: seguridad, rendimiento, disponibilidad, escalabilidad, usabilidad, mantenibilidad, integración REST, compatibilidad con Flutter, seguridad transaccional) no se asocian a CU específicos, ya que son atributos de calidad transversales al sistema completo. Se documentarán en flujos de trabajo posteriores (Diseño de Arquitectura, Diagrama de Despliegue), no en la captura de requisitos.

El único punto sin RF numerado explícito es la **gestión de promociones**, mencionada en el enunciado pero no en la lista RF01–RF25. Se decidió incorporarla dentro de **CU08 – Gestionar catálogo y productos**, sin necesidad de crear un CU adicional.
