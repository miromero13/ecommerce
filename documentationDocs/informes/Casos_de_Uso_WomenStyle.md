# Casos de Uso – WomenStyle

Documento resumen del flujo de trabajo **1. Captura de Requisitos** (PUDS) — Parte II del informe.

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

### Ciclo 3 (5 CU) — Realidad Aumentada, Inteligencia Artificial y Reportes avanzados

| ID | Caso de uso | Prioridad | Riesgo | Estado | Actor(es) principal | Plataforma |
|---|---|---|---|---|---|---|
| CU19 | Usar vestidor virtual | Alta | Alto | Pendiente | Cliente | Móvil |
| CU20 | Generar reportes y dashboards | Media | Medio | Pendiente | Administrador | Web |
| CU21 | Recibir recomendaciones de IA | Media | Alto | Pendiente | Cliente | Ambas |
| CU22 | Consultar asistente virtual/chatbot | Baja | Alto | Pendiente | Cliente | Ambas |
| CU23 | Generar reporte por voz/lenguaje natural | Baja | Alto | Pendiente | Administrador | Web |

---

## 3. Paquetes de Arquitectura (Análisis de Arquitectura – PUDS)

Para el flujo de trabajo de **Análisis**, los 23 CU se agrupan en **6 paquetes** según afinidad funcional, reduciendo la complejidad del análisis y facilitando la identificación posterior de clases y relaciones.

- **P1 – Gestión de usuarios y acceso**: Registro de clientes, autenticación y acceso al sistema, administración de usuarios internos, gestión de sucursales, cuentas de proveedores y actualización de datos de perfil.
- **P2 – Gestión de productos y catálogo**: Envío de información por parte de proveedores, gestión de productos, promociones, categorías, tallas, colores, temporadas y colecciones; consulta y filtrado del catálogo por parte del cliente.
- **P3 – Gestión de inventario y disponibilidad**: Control de existencias en las diferentes sucursales, consulta de disponibilidad, registro de movimientos de inventario y consulta consolidada.
- **P4 – Gestión de compras y reservas**: Selección de prendas para reservar o comprar digitalmente, carrito de compras, checkout, pago electrónico y consulta del estado del pedido.
- **P5 – Gestión de ventas y atención en sucursal**: Operación presencial de la tienda: preparación y atención de reservas, registro de ventas presenciales, procesamiento de pago en caja y emisión de comprobante.
- **P6 – Experiencia inteligente y analítica**: Vestidor virtual mediante realidad aumentada, generación de reportes y dashboards, recomendaciones de IA, asistente virtual y generación de reportes por lenguaje natural.

---

## 4. Distribución de Casos de Uso en los 6 Paquetes

| Paquete | Casos de uso incluidos |
|---|---|
| **P1 – Gestión de usuarios y acceso** | CU01, CU02, CU03, CU04, CU05, CU06 |
| **P2 – Gestión de productos y catálogo** | CU07, CU08, CU09, CU10 |
| **P3 – Gestión de inventario y disponibilidad** | CU11, CU12, CU13 |
| **P4 – Gestión de compras y reservas** | CU14, CU15, CU16 |
| **P5 – Gestión de ventas y atención en sucursal** | CU17, CU18 |
| **P6 – Experiencia inteligente y analítica** | CU19, CU20, CU21, CU22, CU23 |

Nota: esta agrupación en paquetes es independiente de la distribución por ciclos — los ciclos organizan el **orden de desarrollo**, mientras que los paquetes organizan la **arquitectura lógica** del sistema.

---

## 5. Relaciones entre Casos de Uso (Include, Extend, Generalización)

### 5.1. Sobre CU02 – Iniciar sesión (aclaración importante)

Confirmando tu duda: **CU02 no debería modelarse como `<<include>>` hacia ningún otro CU**, ni siquiera hacia CU06. La razón es una regla de buena práctica en UML:

> Un `<<include>>` representa un **paso obligatorio dentro del flujo del caso base** (algo que el caso de uso *hace* como parte de su comportamiento). En cambio, estar autenticado es una **condición que debe cumplirse antes** de que el caso de uso pueda siquiera comenzar — es decir, una **precondición**, no un paso del flujo.

Si se modelara CU02 como `<<include>>` de todos los demás CU (o incluso de uno solo, como CU06), se rompe la consistencia del diagrama: o se aplica a los 22 CU restantes (lo cual generaría un diagrama saturado de flechas repetidas sin aportar información nueva) o se aplica arbitrariamente a uno solo, lo cual no tiene justificación distinta frente a los demás CU (todos requieren sesión iniciada por igual).

**Recomendación:** documentar "Usuario autenticado" como **precondición general del sistema** (una nota aparte en el diagrama o en la ficha de cada CU), y no dibujar flechas de `<<include>>` desde CU02.

**Alternativa más elegante (opcional):** en vez de listar los 5 actores por separado en CU02, se puede modelar una **generalización de actores**: crear un actor abstracto "Usuario del sistema" del cual heredan (generalización) Cliente, Administrador, Encargado de sucursal, Cajero y Proveedor, y hacer que sea ese actor abstracto quien se conecte a CU02. Esto es más limpio visualmente, aunque no es obligatorio — la lista explícita de 5 actores también es válida académicamente.

### 5.2. Relación `<<include>>` identificada

- **CU18 (Registrar venta presencial y procesar pago en caja) `<<include>>` CU12 (Registrar movimiento de inventario)**
 Justificación: toda venta presencial completada **obligatoriamente** actualiza el inventario de la sucursal (RF20, RF22) — no es opcional ni condicional, siempre ocurre como parte del flujo de CU18. Además, ambos casos comparten actor (Cajero), lo que hace la relación consistente.

### 5.3. Relaciones `<<extend>>`

No se identificó una relación de `<<extend>>` clara y necesaria entre los 23 CU actuales. Esto se debe a que los candidatos naturales para `<<extend>>` (por ejemplo, "cancelar reserva" como variante opcional de "gestionar reservas") ya fueron **fusionados dentro del mismo CU** (CU14) en la etapa de reducción de casos de uso, por lo que no queda un flujo alternativo/opcional independiente que amerite esta relación.

Si más adelante detectan un comportamiento verdaderamente opcional y no siempre ejecutado (ej. "aplicar código de descuento" dentro de CU15, o "generar alerta de stock bajo" dentro de CU12), ahí sí correspondería usar `<<extend>>`.

### 5.4. Generalización (herencia)

No se identificaron relaciones de generalización **entre casos de uso** (es decir, un CU que sea una versión más específica de otro). La única generalización aplicable en este modelo es la **de actores** mencionada en el punto 5.1 (actor abstracto "Usuario del sistema" → Cliente, Administrador, Encargado de sucursal, Cajero, Proveedor), y es opcional.

### 5.5. Resumen de relaciones para el diagrama

| Relación | Origen | Destino | Tipo |
|---|---|---|---|
| CU18 → CU12 | Registrar venta presencial y procesar pago en caja | Registrar movimiento de inventario | `<<include>>` |
| (Opcional) Usuario del sistema → Cliente, Administrador, Encargado de sucursal, Cajero, Proveedor | — | — | Generalización de actor |

Todo lo demás se mantiene como **casos de uso independientes**, conectados únicamente a su(s) actor(es) correspondiente(s), sin relaciones adicionales de inclusión, extensión o herencia entre sí.

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
| RF20 | Actualizar automáticamente el inventario tras una venta | CU12 (incluido desde CU18, ver sección 5.2) |
| RF21 | Controlar las existencias por sucursal | CU11, CU13 |
| RF22 | Registrar movimientos de inventario | CU12 |
| RF23 | Gestionar temporadas y colecciones | CU09 |
| RF24 | Consultar reportes de ventas e inventario | CU20 |
| RF25 | Proporcionar al menos una funcionalidad basada en IA | CU21, CU22, CU23 |

**Resultado:** los 25 RF quedan cubiertos por los 23 CU definidos, sin excepciones ni requisitos huérfanos.

### Nota sobre los RNF y otras indicaciones

Los Requisitos No Funcionales (RNF01–RNF09: seguridad, rendimiento, disponibilidad, escalabilidad, usabilidad, mantenibilidad, integración REST, compatibilidad con Flutter, seguridad transaccional) no se asocian a CU específicos, ya que son atributos de calidad transversales al sistema completo. Se documentarán en flujos de trabajo posteriores (Diseño de Arquitectura, Diagrama de Despliegue), no en la captura de requisitos.

El único punto sin RF numerado explícito es la **gestión de promociones**, mencionada en el enunciado pero no en la lista RF01–RF25. Se decidió incorporarla dentro de **CU08 – Gestionar catálogo y productos**, sin necesidad de crear un CU adicional.
