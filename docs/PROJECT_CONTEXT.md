# 1. PERFIL 

## 1.1. INTRODUCCIÓN 

Actualmente el comercio de indumentaria es uno de los sectores más dinámicos del retail a nivel mundial, y en las últimas dos décadas ha experimentado una transformación profunda impulsada por la digitalización. Las tiendas de ropa físicas tradicionales han evolucionado hacia modelos omnicanal, en los que el cliente puede investigar, comparar y comprar prendas tanto en establecimientos físicos como en plataformas digitales, integrando catálogos en línea, aplicaciones móviles, pasarelas de pago electrónicas y sistemas de gestión de inventario en tiempo real. 
Grandes cadenas internacionales de moda han incorporado tecnologías como la realidad aumentada para permitir a sus clientes visualizar prendas antes de probárselas físicamente, así como sistemas de inteligencia artificial para ofrecer recomendaciones personalizadas según el historial de compra y las preferencias de cada usuario. Estas innovaciones, además de modernizar la experiencia de compra, también han optimizado la gestión logística e interna de las empresas del rubro, permitiendo administrar de manera centralizada múltiples sucursales, proveedores y temporadas de colección. 
En Bolivia, el sector de venta de ropa mantiene una fuerte presencia de comercio presencial, aunque en los últimos años se ha observado un crecimiento sostenido de tiendas que incorporan canales digitales complementarios, como catálogos web, redes sociales y aplicaciones de venta, especialmente en las principales ciudades del eje troncal. Las cadenas de tiendas de ropa que operan con varias sucursales enfrentan el reto particular de coordinar de manera integrada el inventario, la disponibilidad de tallas y colores, y los procesos de venta entre sus distintos puntos físicos, a la par de ofrecer canales digitales que complementen —y no reemplacen— la experiencia de prueba física de las prendas, que continúa siendo un factor determinante en la decisión de compra del cliente. 
En este contexto se enmarca FashionStore, una cadena de tiendas de ropa que opera con múltiples sucursales distribuidas en distintas ciudades de Bolivia. FashionStore ha construido su presencia comercial ofreciendo prendas de vestir organizadas por categorías, temporadas y colecciones, trabajando con diversos proveedores que abastecen de manera periódica su catálogo de acuerdo a las tendencias de cada temporada comercial (primavera-verano, otoño-invierno, entre otras). Actualmente, la empresa gestiona sus operaciones de manera independiente en cada sucursal: el cliente puede acudir físicamente a cualquiera de sus tiendas para conocer el catálogo disponible, seleccionar prendas de las tallas y colores que desea, probárselas en los vestidores físicos y realizar la compra directamente en el punto de caja de la sucursal correspondiente. La actualización del inventario y el registro de las ventas se realizan a nivel de cada sucursal, y la comunicación entre estas y la administración central se da de forma periódica para consolidar la información de existencias, movimientos de mercadería y desempeño comercial de la cadena. 
Frente al crecimiento de la demanda de experiencias de compra más ágiles y flexibles, FashionStore ha identificado la oportunidad de complementar su operación presencial con una plataforma digital que integre sus canales web y móvil, permitiendo a sus clientes explorar el catálogo completo de la cadena, verificar la disponibilidad de prendas por sucursal y reservar productos antes de acudir a probárselos físicamente, incorporando además tecnologías emergentes como la realidad aumentada y la inteligencia artificial para enriquecer la experiencia de compra tanto presencial como digital. 

## 1.2. ANTECEDENTES

2.1. Fundamentación teórica 
El desarrollo de plataformas de comercio electrónico inteligentes para el rubro de la moda responde a una transformación real y medible del sector, no a una tendencia pasajera. La incorporación de tecnologías como la inteligencia artificial y la realidad aumentada en la experiencia de compra tiene relevancia porque ataca dos de los mayores desafíos históricos del e-commerce de ropa: la incertidumbre sobre cómo lucirá una prenda antes de comprarla, y la dificultad de ofrecer al cliente una experiencia de descubrimiento de productos verdaderamente personalizada. Un sistema de este tipo es relevante en la medida en que logra articular, bajo una misma plataforma, la operación física de una cadena de tiendas (sucursales, inventario, punto de venta) con sus canales digitales (catálogo web, aplicación móvil, pasarela de pago), evitando que ambos mundos funcionen como sistemas aislados.
Lo que este proyecto se propone hacer es diseñar y modelar (siguiendo el Proceso Unificado de Desarrollo de Software (PUDS) y la notación UML) una plataforma que permita a FashionStore centralizar la gestión de su catálogo, sus reservas de prendas, su inventario multisucursal y sus ventas (tanto presenciales como digitales), incorporando además un módulo de vestidores virtuales mediante realidad aumentada y funcionalidades de inteligencia artificial orientadas a la recomendación de productos.
El aporte de este documento consiste en traducir ese conjunto de necesidades de negocio en una especificación técnica completa y trazable: captura y análisis de requisitos, modelado de casos de uso y de la arquitectura del sistema, diseño de la base de datos y de los flujos de trabajo entre sucursales, y una propuesta tecnológica concreta (FastAPI, Angular, Flutter/Dart y PostgreSQL) que sirva de base para la implementación de un MVP funcional dentro del plazo académico establecido.
2.2. Sistemas similares 
Para fundamentar el diseño de FashionStore se revisaron casos de sistemas reales que ya implementan, de forma independiente, algunas de las funcionalidades que la plataforma busca integrar:
**Probador virtual con inteligencia artificial (Zara).** En años recientes Zara incorporó a su aplicación móvil una herramienta de prueba virtual basada en IA generativa: el cliente sube una fotografía de su rostro y una de cuerpo completo, con las cuales el sistema genera un avatar personalizado que se viste con la prenda elegida y gira 360° para mostrar el ajuste desde distintos ángulos. Este caso es relevante porque el beneficio reportado por la marca ha sido una reducción de dos dígitos en las devoluciones asociadas a errores de talla, lo que confirma que un vestidor virtual no es solo una mejora estética de la experiencia, sino una herramienta que reduce costos logísticos concretos. FashionStore retoma esta idea, aunque orientada a realidad aumentada sobre la cámara del dispositivo en lugar de un avatar generado por IA.
**Recomendaciones personalizadas basadas en IA (Amazon).** Amazon construyó desde hace más de una década un sistema de recomendaciones que analiza el historial de navegación y compra de cada usuario mediante técnicas como el filtrado colaborativo, comparando patrones de comportamiento entre usuarios similares para sugerir productos. Este enfoque tiene un peso comercial considerable: la propia empresa ha reportado que cerca del 35% de sus ventas provienen de estas recomendaciones personalizadas. Este caso sirve de referencia para el módulo de recomendación de prendas de FashionStore, que buscará sugerir productos considerando preferencias, historial y disponibilidad del cliente.[ ](https://vwo.com/blog/es/personalizacion-de-amazon-y-netflix/)
**Reserva y recogida en tienda — Click & Collect (Decathlon, Zara, H&M).** Distintas cadenas de retail han consolidado un modelo en el que el cliente reserva o compra en línea y recoge (o se prueba) el producto físicamente en la sucursal de su preferencia. En el caso de Decathlon, los clientes pueden reservar productos en la tienda más cercana y recogerlos en pocas horas, un esquema especialmente útil para artículos de alta demanda. Este modelo es el antecedente directo del proceso de reserva de prendas que FashionStore plantea: el cliente selecciona varias prendas desde la app, indica sucursal y horario, y acude posteriormente a probárselas antes de decidir la compra.
Estos tres casos (vestidor virtual, motor de recomendación e integración de reserva digital con atención físicaI) constituyen la base conceptual sobre la cual se diseñará la plataforma de FashionStore, adaptando cada una de estas ideas a la escala y al contexto de una cadena de tiendas de ropa que opera en Bolivia.

## 1.3. OBJETIVOS 

### 1.3.1. Objetivo General 

Desarrollar una plataforma inteligente e-commerce con gestión de venta, reservas, inventario y probadores virtuales vía realidad aumentada para la cadena de tiendas Fashion Store.

### 1.3.2. Objetivo Específicos

- **Recolectar información** sobre sistemas de e-commerce de moda similares y sobre los procesos actuales de venta, reserva e inventario en las sucursales de FashionStore, mediante investigación de mercado y relevamiento de los flujos operativos de la cadena, con el fin de identificar los requerimientos funcionales y no funcionales del sistema.
- **Analizar y especificar** los requisitos funcionales y no funcionales del sistema mediante el levantamiento de casos de uso, siguiendo el flujo de trabajo de captura de requisitos del PUDS.
- **Diseñar el módulo de gestión de usuarios, roles y sucursales**, permitiendo administrar clientes, administradores, encargados de sucursal, cajeros y proveedores.
- **Diseñar el catálogo de prendas**, con gestión de categorías, tallas, colores, temporadas y colecciones, filtrable desde web y móvil.
- **Diseñar el módulo de inventario multisucursal**, que actualice automáticamente las existencias por producto, talla, color y sucursal tras cada reserva, venta o recepción de mercadería.
- **Diseñar el proceso de reserva de prendas**, permitiendo al cliente seleccionar múltiples prendas, indicar sucursal y horario de atención, y a la sucursal confirmar la recepción de la reserva.
- **Diseñar el módulo de vestidores virtuales mediante realidad aumentada**, integrado con el catálogo, que permita al cliente visualizar una prenda sobre su propia imagen desde la cámara del dispositivo móvil.
- **Diseñar los dos flujos de venta del sistema** (compra digital vía web/app con pasarela de pago electrónica, y compra presencial en punto de caja), garantizando el registro de cada transacción.
- **Diseñar la funcionalidad de recomendación de prendas basada en inteligencia artificial**, que sugiera productos al cliente considerando su historial de navegación o compra, temporada y disponibilidad.
- **Modelar la arquitectura y los procesos del sistema utilizando UML 2.5+**, documentando los diagramas correspondientes a cada flujo de trabajo del PUDS.
- **Implementar el backend del sistema utilizando Python y el framework FastAPI**, exponiendo los servicios REST necesarios para la gestión de usuarios, catálogo, inventario, reservas y ventas.
- **Implementar el frontend web utilizando Angular**, consumiendo los servicios REST para el catálogo, las reservas, el carrito de compras y el panel administrativo.
- **Implementar la aplicación móvil utilizando Flutter y Dart**, incorporando el vestidor virtual con realidad aumentada y el flujo de compra digital.
- **Integrar PostgreSQL** como sistema gestor de base de datos relacional para la persistencia del catálogo, el inventario, las reservas y las ventas.
- **Generar reportes y dashboards** de ventas e inventario que permitan a la administración consultar el desempeño consolidado de todas las sucursales.

## 1.4. DESCRIPCIÓN DEL PROBLEMA 

Trabajando dentro de la operación diaria de FashionStore, se identifican las siguientes situaciones en la cadena:
**1. Desconocimiento de la disponibilidad de prendas entre sucursales.**
Cuando un cliente acude a una sucursal buscando una prenda en una talla o color específico y esta no se encuentra disponible en ese punto de venta, el personal no cuenta con una manera inmediata y confiable de verificar si esa misma prenda está disponible en otra sucursal cercana. 
En la práctica, la única alternativa es llamar telefónicamente a las demás tiendas de la ciudad y esperar a que alguien revise físicamente el estante o la bodega, un proceso que puede tomar varios minutos y que muchas veces se descarta directamente por falta de tiempo durante horas de alta afluencia. Esto obliga al cliente a trasladarse físicamente sin certeza de encontrar el producto, a esperar sin saber si vale la pena hacerlo, o a desistir de la compra por completo. Desde la perspectiva de la cadena, esto significa que una prenda que sí existe en stock —solo que en otra ubicación— no logra venderse, mientras que esa misma sucursal probablemente termine con excedente de esa prenda en la temporada siguiente por no haber podido colocarla a tiempo.
**2. Riesgo de pérdida o duplicación de prendas apartadas para un cliente. **
Cuando un cliente solicita que se le aparte una o varias prendas para probárselas más adelante, esa solicitud se comunica de manera informal —por llamada telefónica, mensaje de WhatsApp o simplemente de palabra durante una visita previa— y queda a criterio de la persona que atiende recordarla y comunicarla al resto del equipo de turno. 
No existe un registro único y verificable de qué prendas están comprometidas, para quién, ni hasta qué hora se mantiene la reserva. Como consecuencia, se han dado casos donde la prenda apartada termina siendo vendida a otro cliente antes de que el interesado original llegue a la tienda, generando una situación incómoda que el personal debe resolver improvisando (ofreciendo un descuento, buscando una prenda similar, o simplemente disculpándose sin poder cumplir lo prometido). También ocurre lo contrario: dos empleados distintos, sin saberlo, confirman la misma prenda a dos clientes diferentes para el mismo horario de atención, lo que genera fricción tanto con el cliente como entre el personal.
**3. Desactualización de la información consolidada de inventario entre sucursales y administración central.**
Cada sucursal registra sus propios movimientos de mercadería —ventas del día, ingresos de proveedores, prendas dadas de baja por daño o devolución— de forma independiente, y esta información se traslada a la administración central mediante reportes que se consolidan cada cierto número de días, no en tiempo real. Esto provoca que, al momento de decidir si conviene redistribuir stock entre tiendas o realizar un nuevo pedido a un proveedor, la administración esté tomando esas decisiones con datos que ya tienen varios días de desfase respecto a la situación real en tienda. 
El resultado observado es que, mientras una sucursal enfrenta quiebre de stock de una prenda de alta rotación y pierde ventas por no tenerla disponible, otra sucursal de la misma ciudad puede tener esa misma prenda acumulada sin movimiento, sin que exista visibilidad oportuna para corregir esa descompensación a tiempo. 
**4. Fragmentación de la información entre las ventas presenciales y las ventas digitales.**
Las ventas que se realizan en el punto de caja de una sucursal y las que eventualmente se gestionan a través de canales digitales (redes sociales, catálogos enviados por mensajería, pedidos telefónicos) se registran en sistemas o cuadernos distintos, sin un punto único que las una. Esto dificulta obtener una visión real y oportuna de cuánto se vendió en total de una prenda específica en un día, considerando ambos canales, lo cual es especialmente problemático durante el lanzamiento de una nueva colección o una promoción por temporada, donde la demanda puede superar rápidamente al stock disponible sin que el equipo lo note a tiempo por estar mirando cada canal de forma aislada. Esto también complica la elaboración de reportes de desempeño comercial consolidados que reflejen el comportamiento real de venta de la cadena como un todo. 

## 1.5. ALCANCE 

El alcance del proyecto comprende el diseño, modelado y posterior implementación del MVP de una plataforma inteligente de comercio electrónico para FashionStore. A continuación, se detallan los requisitos funcionales organizados por módulos:

### 1. MÓDULO DE USUARIOS Y ROLES

Este módulo permitirá administrar el acceso a la plataforma y la estructura organizacional de la cadena, controlando qué puede hacer cada tipo de usuario según su rol.
Funcionalidades:

- Registro e inicio de sesión de clientes.
- Autenticación y autorización mediante roles (JWT).
- Gestión de usuarios internos: administradores, encargados de sucursal y cajeros.
- Registro y administración de sucursales por ciudad.
- Registro y gestión de proveedores.
- Control de acceso a funcionalidades según el rol del usuario.
- Consulta y actualización de datos de perfil del cliente.

### 2. MÓDULO DE INVENTARIO

Este módulo permitirá administrar el catálogo de prendas de la cadena y mantener actualizadas y sincronizadas las existencias de cada sucursal.
Funcionalidades:

- Registro, edición y baja de prendas.
- Gestión de categorías, tallas, colores, temporadas comerciales y colecciones.
- Registro y envío de información de productos por parte del proveedor, indicando características, disponibilidad y su asociación a temporadas y colecciones.
- Validación por parte del administrador de la información enviada por el proveedor antes de su publicación en el catálogo.
- Búsqueda y filtrado del catálogo (por categoría, talla, color, temporada, precio) desde web y móvil.
- Consulta de disponibilidad de una prenda por sucursal, talla y color en tiempo real.
- Indicador de estado del producto (disponible, reservado, agotado, próximo a ingresar).
- Actualización automática del inventario tras reservas, compras, ventas, devoluciones y recepción de productos.
- Registro de movimientos de inventario (ingresos, salidas, traspasos entre sucursales).
- Alertas de stock bajo o próximo a agotarse.
- Consulta de inventario consolidado a nivel de administración central.

### 3. MÓDULO DE COMPRA

Este módulo permitirá al cliente reservar prendas para probárselas en tienda y/o completar una compra digital desde la plataforma web o móvil.
Funcionalidades:

- Selección de múltiples prendas para reservar, indicando sucursal y horario aproximado de atención.
- Notificación de la reserva a la sucursal correspondiente y consulta de su estado (pendiente, confirmada, atendida, cancelada).
- Cancelación de reservas y definición de un tiempo límite de validez.
- Adición y edición de productos en el carrito de compras.
- Cálculo automático de totales, considerando promociones vigentes.
- Compra digital desde plataforma web o aplicación móvil.
- Integración con pasarela de pago electrónica.
- Confirmación y comprobante de compra digital.
- Seguimiento del estado del pedido (pagado, en preparación, listo para entrega o recogida).

### 4. MÓDULO DE VENTA

Este módulo permitirá registrar las ventas realizadas directamente en el punto de caja de la sucursal, incluyendo aquellas derivadas de una reserva previa.
Funcionalidades:

- Preparación y confirmación de recepción de prendas reservadas por parte del encargado de sucursal.
- Registro de ventas presenciales por parte del cajero.
- Asociación de la venta presencial con una reserva previa, si corresponde.
- Procesamiento de pagos en punto de caja.
- Emisión de comprobantes de venta.
- Actualización automática del inventario tras cada venta presencial.

### 5. MÓDULO DE REALIDAD AUMENTADA

Este módulo permitirá al cliente visualizar de manera virtual cómo luciría una prenda, utilizando la cámara de su dispositivo móvil, sin necesidad de probársela físicamente.
Funcionalidades:

- Visualización de la prenda seleccionada sobre la imagen del cliente mediante realidad aumentada.
- Integración con el catálogo de productos y sus características (color, talla, modelo).
- Disponibilidad exclusiva desde la aplicación móvil.
- Opción de guardar o compartir la visualización generada.

### 6. MÓDULO DE REPORTES Y DASHBOARD

Este módulo permitirá a la administración de FashionStore visualizar de manera consolidada el desempeño comercial y operativo de la cadena.
Funcionalidades:

- Reportes de ventas y compras por sucursal, producto y periodo.
- Reportes de inventario y movimientos de mercadería.
- Indicadores de reservas atendidas, canceladas y expiradas.
- Dashboards visuales para apoyo a la toma de decisiones.
- Exportación de reportes.

### 7. MÓDULO DE ASISTENCIA INTELIGENTE

Este módulo permitirá ofrecer sugerencias personalizadas de productos y asistencia mediante inteligencia artificial, tanto al cliente como a la administración.
Funcionalidades:

- Recomendación de prendas según historial de navegación o compra.
- Recomendación considerando temporada, categoría, talla y disponibilidad.
- Asistente virtual/chatbot para consultas del cliente sobre productos.
- Generación de reportes bajo demanda para la administración, mediante comando de voz o lenguaje natural.

# PARTE I. FUNDAMENTACIÓN TEÓRICA

## 1. E-commerce

El comercio electrónico (e-commerce) se define como la práctica de comprar y vender bienes o servicios a través de Internet, abarcando todas las transacciones en línea, desde que un cliente navega por un sitio web hasta la entrega final de su compra. Detrás de toda plataforma de este tipo existen componentes técnicos comunes: escaparates en línea donde las empresas muestran sus productos, carritos de compra que permiten seleccionar artículos y proceder al pago, pasarelas de pago que procesan las transacciones de forma segura, y sistemas de gestión de inventario que actualizan la disponibilidad en tiempo real.
Existen distintas formas de clasificar el e-commerce según el tipo de actores que participan en la transacción: 

- el modelo B2B (business to business) involucra transacciones entre empresas conectadas mediante la red; 
- el modelo B2C (business to consumer) involucra transacciones entre una empresa y su clientela, usualmente a través de portales de venta oficiales; 
- el modelo C2B (consumer to business), donde la transacción se origina en el interés del propio cliente. 

A esta clasificación se suman modelos más recientes como el C2C (venta directa entre consumidores) y el social commerce, que traslada la venta a redes sociales como Instagram o TikTok sin que el usuario deba salir de la aplicación. 
Este marco conceptual es la base sobre la cual se analizan a continuación seis plataformas reales, tanto desde la perspectiva de quien compra como de quien desarrolla una tienda online.

### **Como usuario**

#### **Amazon.**

Es mucho más que una tienda online: es un ecosistema de servicios que conecta compradores, vendedores, marcas, empresas, desarrolladores y usuarios que consumen contenido digital o servicios en la nube. Desde la perspectiva del comprador es importante distinguir entre Amazon Retail y Amazon Marketplace: cuando el cliente compra directamente a Amazon.com, la empresa se queda con todo el beneficio de la venta; cuando compra a un vendedor externo dentro del Marketplace, Amazon retiene una comisión fija y el resto va al vendedor. 
Para el usuario final, esta diferencia se traduce en variedad y precio: el Marketplace le da acceso a una selección más amplia de productos, incluyendo artículos de nicho, con precios más competitivos gracias a la competencia entre vendedores, todo bajo la garantía y el sistema de pagos de Amazon. Como usuario final, la experiencia gira en torno a la búsqueda, la comparación de precios, las reseñas de otros compradores y el seguimiento del pedido hasta la entrega. 

#### **Alibaba.**

A diferencia de Amazon, Alibaba opera principalmente bajo un modelo B2B (empresa a empresa): proporciona un espacio en línea donde las empresas pueden comprar y vender productos al por mayor, ofreciendo herramientas para la búsqueda de productos, la negociación de precios y el pago. Su escala es considerable: la plataforma conecta a fabricantes, proveedores y distribuidores, principalmente de China, con compradores de todo el mundo, reuniendo más de 200 millones de productos en cientos de categorías. 
Como usuario/comprador, la experiencia difiere bastante de Amazon: en Alibaba los proveedores publican catálogos de productos, establecen una cantidad mínima de pedido (MOQ) y ofrecen precios bajo condiciones comerciales internacionales (FOB/CIF), por lo que el proceso de compra suele incluir negociación directa con el proveedor antes de cerrar el pedido, algo poco común en plataformas orientadas al consumidor final.

#### **Shopify.**

Desde la óptica del usuario/comprador, Shopify no es una tienda en sí misma sino la infraestructura sobre la que operan miles de tiendas independientes: es una plataforma de comercio que ayuda a emprendedores, minoristas y marcas internacionales a vender online y en persona, gestionar su tienda y hacer crecer sus negocios. 
Al comprar en una tienda construida sobre Shopify, el usuario normalmente encuentra un proceso de compra estandarizado (catálogo, carrito, checkout, confirmación) independientemente de la marca, ya que Shopify centraliza en una sola herramienta todo lo necesario para vender por internet: diseño de la tienda, gestión de productos, pagos y pedidos. Además, muchas tiendas Shopify integran su catálogo con redes sociales y marketplaces externos, lo que amplía los puntos de contacto para el comprador.

### **Como desarrollador**

#### **Magento (Adobe Commerce).**

Es una de las plataformas más utilizadas por equipos de desarrollo para construir tiendas complejas y a gran escala. Al ser una plataforma de código abierto, ofrece una infraestructura completa que las empresas pueden usar para construir, gestionar y hacer crecer sus tiendas online, permitiendo a los desarrolladores modificar y expandir sus funcionalidades libremente. Actualmente coexisten dos versiones: Magento Open Source, gratuita y de código abierto, pensada para equipos que buscan control total sobre su tienda; y Adobe Commerce, la versión comercial en la nube con funciones empresariales adicionales. 
Para un desarrollador, el beneficio principal de Magento es que permite crear experiencias de compra multicanal tanto para clientes B2B como B2C en una sola plataforma, aunque su configuración exige conocimientos técnicos más avanzados que otras alternativas.

#### **PrestaShop.**

Es un sistema de gestión de contenidos (CMS) especializado en comercio electrónico, popular especialmente en Europa y América Latina. Está desarrollado completamente en PHP, MySQL y Smarty, y desde su versión 1.7 incorpora el framework Symfony para mejorar el rendimiento de la plataforma. 
Su arquitectura está pensada para que el desarrollador construya la tienda de forma incremental: permite crear comercios electrónicos modulares, es decir, se puede empezar con una tienda simple e ir añadiendo módulos según se necesiten, como métodos de pago adicionales, mejoras de SEO o sistemas de promoción. A nivel técnico, utiliza el patrón Modelo-Vista-Controlador (MVC) como arquitectura de software, además de tecnologías como JavaScript, HTML, CSS y jQuery, lo que la hace una opción intermedia entre la simplicidad de Shopify y la complejidad de Magento.

#### **WooCommerce.**

Es la opción más ligada al ecosistema WordPress: se trata específicamente de un plugin de WordPress que convierte un blog o sitio web en una tienda online. Su principal ventaja para un desarrollador es la rapidez de implementación sobre un sitio ya existente en WordPress, sin necesidad de migrar a una plataforma completamente distinta. Su adopción es muy amplia: cuenta con más de 5 millones de usuarios activos e impulsa alrededor del 40% del total de tiendas online del mundo. 
A diferencia de Shopify (que es un servicio SaaS con costo mensual fijo), WooCommerce es gratuito, pero requiere que el desarrollador contrate por separado el hosting, los plugins adicionales y otros servicios necesarios para mantener la tienda, lo que le da más flexibilidad de personalización a cambio de asumir la responsabilidad del mantenimiento técnico.

## 2. Pasarelas de pago

1. **¿Cómo funcionan las distintas formas de pago online?**

Una pasarela de pago es la tecnología que actúa como puente entre el comercio, el cliente y las entidades financieras, comunicando de forma segura los datos necesarios para autorizar y procesar cada transacción. Es, en esencia, el equivalente digital de un datáfono físico, pero operando completamente en línea.
**Tarjetas de crédito y débito.** Es el método más extendido. El proceso general sigue una secuencia de pasos: el comprador ingresa al checkout de la tienda y digita los datos de su tarjeta; la pasarela encripta esa información y verifica la autenticidad del sitio; luego la envía al procesador de pagos del comercio, que la reenvía a la red de tarjetas (Visa, Mastercard, etc.); esta red consulta al banco emisor de la tarjeta del comprador para validar que existan fondos suficientes; y finalmente el banco responde aprobando o rechazando la operación, todo en cuestión de segundos. Para operar de forma legal y segura, cualquier plataforma que maneje datos de tarjetas debe cumplir con el estándar internacional PCI DSS (Payment Card Industry Data Security Standard).
**Transferencias bancarias.** En este caso, el dinero se mueve directamente entre la cuenta del comprador y la del comercio, sin la intermediación de una red de tarjetas. La pasarela de pago puede automatizar la confirmación (verificando electrónicamente que el depósito llegó) o depender de que el cliente suba un comprobante que luego se valida manualmente, un modelo aún común entre plataformas locales bolivianas para transacciones de comercio electrónico de menor escala.
**Códigos QR.** En Bolivia, este método adquirió especial relevancia a partir del sistema QR BCB Bolivia, desarrollado por el Banco Central de Bolivia como infraestructura oficial de pagos inmediatos. El código QR contiene, de forma encriptada, la información de la cuenta del beneficiario (nombre, número de cuenta, entidad financiera); el cliente lo escanea desde la aplicación móvil de su propio banco (que puede ser distinto al del comercio, gracias a que el sistema es interoperable entre todas las entidades financieras del país), confirma el monto y el dinero se transfiere de manera inmediata entre cuentas. El modelo más usado en comercios bolivianos es el "Merchant-Presented", donde es el negocio quien muestra el código QR (en pantalla, impreso o dentro de una tienda online) y el cliente lo escanea. Este sistema ha tenido una adopción muy rápida en el país: los pagos por QR crecieron más de 4.700% en menos de tres años desde su implementación, impulsados en gran parte porque no genera comisión adicional para quien paga ni para quien cobra.

2. **Libélula: pasarela de pago local**

Libélula es una pasarela de pagos desarrollada en Bolivia que permite a negocios digitales recibir pagos desde tarjetas de débito y crédito nacionales e internacionales (Visa, Mastercard, Amex), así como cobros mediante el código QR interoperable del sistema financiero boliviano, operando tanto en bolivianos (BOB) como en dólares (USD). Además de la pasarela propiamente dicha, Libélula ofrece un ecosistema más amplio de herramientas para comercios: facturación electrónica integrada, generación de enlaces de pago (para compartir por WhatsApp u otros medios sin necesidad de un checkout completo), un sistema de punto de venta (POS) y gestión de cobros desde una sola plataforma centralizada.
Para un desarrollador, su principal ventaja frente a pasarelas internacionales como Stripe es que está diseñada específicamente para las condiciones del mercado boliviano: cumple con la normativa de ASFI (Autoridad de Supervisión del Sistema Financiero) y del SIN (Servicio de Impuestos Nacionales) en materia de facturación, y se integra de forma relativamente sencilla con plataformas de e-commerce comunes como WooCommerce o tiendas personalizadas, mediante plugins ya construidos que no requieren conocimientos avanzados de programación. Su modelo de cobro es simple: no tiene costos de afiliación ni mensualidades fijas, sino una comisión por transacción (alrededor de 2,5% sobre los pagos recibidos a través de la pasarela).

3. **PayPal y Stripe: opciones de pasarela internacional**

**PayPal** es históricamente la pasarela de pago más reconocida a nivel mundial, con más de 400 millones de usuarios activos y presencia en más de 200 países. Su fortaleza principal es la simplicidad: no requiere manejo de código ni un equipo de desarrollo avanzado para integrarla, sus funciones vienen preconfiguradas, y su marca genera confianza inmediata en el comprador porque es ampliamente reconocida. A cambio, su estructura de comisiones (cercana al 2,9% más una tarifa fija por transacción en Estados Unidos, con variaciones según el país y la divisa) es en general más alta que la de sus competidores más orientados a desarrolladores.
**Stripe**, por su parte, se ha consolidado como la gran alternativa a PayPal para equipos de desarrollo que buscan mayor flexibilidad técnica. Es una pasarela pensada "API-first": estructurada específicamente para que los desarrolladores la integren mediante código directamente en su plataforma, en lugar de depender de un botón o widget preconfigurado, lo que le da mayor control sobre la experiencia de checkout. Stripe procesa pagos en más de 30 países, soporta múltiples métodos (tarjetas, Apple Pay, Google Pay) y gestiona automáticamente la conversión de divisas cuando el comercio y el cliente operan en monedas distintas. Su comisión estándar es de aproximadamente 2,9% más una tarifa fija por transacción, sin costos mensuales ni de instalación.

## 3. Deliverys

### **¿Cómo funcionan los servicios de delivery?**

Los servicios de delivery (o de "última milla") son plataformas tecnológicas que conectan a tres actores: 

- el comercio (restaurante, tienda o negocio que ofrece el producto), 
- el repartidor o socio conductor (quien realiza físicamente el traslado)
- el cliente final (quien recibe el pedido). 

El funcionamiento general sigue una lógica común entre las distintas apps: el cliente selecciona productos desde un catálogo dentro de la aplicación, confirma la dirección de entrega y el método de pago, un algoritmo asigna el pedido al repartidor disponible más cercano y traza la ruta óptima, y tanto el cliente como el negocio pueden seguir el estado del envío en tiempo real hasta que el paquete llega a destino. Este modelo se apoya en tres piezas tecnológicas clave: geolocalización (para ubicar repartidores y calcular rutas), un motor de asignación de pedidos (que decide qué repartidor atiende cada solicitud) y un sistema de seguimiento en vivo que informa al cliente sobre el progreso de su pedido.
A continuación se describen tres ejemplos que operan actualmente en Bolivia.

1. **Yango**

Yango es una empresa tecnológica global (originaria de Yandex) que opera como una "superapp": bajo una misma aplicación ofrece transporte de pasajeros, envío de paquetes (Yango Delivery), transporte de carga más pesada (Yango Cargo) y, desde 2024, entrega de comida (Yango Comida) en ciudades bolivianas como Santa Cruz. Su funcionamiento para envío de paquetes es similar al de solicitar un viaje: el usuario indica el punto de recojo y de entrega desde la app, y un repartidor cercano recoge el paquete en minutos y lo traslada usando el vehículo que el cliente elija (moto, auto, etc.), mientras tanto el remitente como el destinatario pueden seguir la ubicación del envío en tiempo real y reciben notificaciones. 
Para el caso de negocios, Yango ofrece cuentas empresariales con dashboards que permiten supervisar múltiples entregas simultáneas. A nivel de asignación, Yango utiliza algoritmos de distribución inteligente de pedidos y trazado de rutas que buscan optimizar el tiempo de entrega y reducir los tiempos muertos de los repartidores, un principio de optimización logística común entre las plataformas de delivery modernas.

2. **Yummy (ex YAIGO)**

Yummy es una superapp de delivery de origen venezolano que, en Bolivia, absorbió a la plataforma local YAIGO (fundada como un emprendimiento boliviano que llegó a ser la app más descargada del país antes de la adquisición). Bajo su modelo actual, Yummy no se limita a comida: dentro de la misma aplicación integra supermercados, farmacias, entradas a eventos y, en algunos mercados de la región, incluso venta de ropa. Su funcionamiento se apoya en una flota de repartidores ("Yummers") activa los siete días de la semana, y ofrece múltiples métodos de pago tanto en moneda local como internacional dentro de la misma app. Este ejemplo es relevante para el proyecto porque ilustra cómo una plataforma de delivery puede evolucionar de una app enfocada en comida hacia un marketplace más amplio que incluye retail, algo conceptualmente cercano a lo que FashionStore necesitaría si en el futuro decidiera tercerizar la entrega a domicilio de sus compras digitales en lugar de operarla internamente.

3. **PedidosYa**

PedidosYa es una de las plataformas de delivery más consolidadas en Bolivia y en general en América Latina. Además de su servicio tradicional de comida, opera un servicio específico de "Envíos" para mensajería de paquetes y documentos, disponible en varias ciudades bolivianas (Santa Cruz, Cochabamba, La Paz, El Alto, entre otras). Es particularmente útil como referencia porque su mecánica de cálculo de tarifa es explícita y basada en distancia: el sistema cobra una tarifa fija por los primeros kilómetros de recorrido, y a partir de ahí aplica un recargo adicional por cada kilómetro extra que deba recorrer el repartidor entre el punto de recojo y el de entrega, calculado automáticamente por la app según la ruta real. Además, el servicio impone restricciones de tamaño y peso al paquete (máximo 5 kg y dimensiones límite), lo cual es un patrón común entre los servicios de última milla: la tarifa y la elegibilidad del envío dependen tanto de la distancia recorrida como del tamaño/peso de la carga.

### **Cómo calculan las plataformas el costo de una entrega**

De los casos revisados se pueden extraer los factores que, en general, determinan el costo de una entrega en este tipo de plataformas:

- **Distancia recorrida**: es el factor más determinante; normalmente se cobra una tarifa base por un primer tramo (por ejemplo, los primeros kilómetros) y luego un costo incremental por cada unidad de distancia adicional.
- **Peso y tamaño del paquete**: los servicios de mensajería suelen limitar el peso y volumen máximo aceptado, y algunos aplican recargos si el paquete excede ciertas dimensiones estándar.
- **Tiempo/demanda**: en varias plataformas de este tipo, la tarifa puede variar según la hora del día o la disponibilidad de repartidores en la zona (mecanismos de precio dinámico), aunque este componente varía según cada empresa y no siempre es visible para el usuario final.
- **Frecuencia y volumen para negocios**: cuando el servicio se contrata a nivel empresarial (como es el caso de las cuentas B2B de Yango o PedidosYa), suele existir facturación consolidada periódica y, en algunos casos, tarifas preferenciales por volumen de envíos.

## 4. PUDS

### **Concepto general**

El Proceso Unificado de Desarrollo de Software (PUDS), también conocido como Proceso Unificado (UP) o, en su implementación más difundida y documentada, como Proceso Unificado de Rational (RUP), es un marco de trabajo para el desarrollo de software que se caracteriza por tres rasgos definitorios: está **dirigido por casos de uso**, está **centrado en la arquitectura**, y es **iterativo e incremental**. En esencia, es un conjunto de actividades necesarias para transformar los requisitos de un usuario en un sistema de software funcional.
Que el proceso esté "dirigido por casos de uso" significa que cada iteración del desarrollo se organiza alrededor de un conjunto de casos de uso o escenarios que se llevan de principio a fin a través de todas las disciplinas del proyecto (requisitos, análisis, diseño, implementación y pruebas), en lugar de completar cada disciplina para todo el sistema antes de pasar a la siguiente, como ocurriría en un modelo en cascada tradicional. Que sea "iterativo e incremental" implica que el sistema no se entrega de una sola vez al final del proyecto, sino que se construye en ciclos sucesivos, cada uno de los cuales añade o mejora funcionalidades sobre la versión anterior, permitiendo detectar riesgos y ajustar el rumbo tempranamente en lugar de descubrir problemas graves al final del desarrollo.

### **Fases del PUDS**

El PUDS organiza el trabajo de desarrollo en cuatro fases secuenciales, cada una de las cuales puede subdividirse a su vez en una o más iteraciones:

1. **Inicio.** Se define el alcance y los objetivos del negocio, se evalúa la factibilidad del proyecto, se identifican los riesgos críticos y se esboza una arquitectura candidata inicial. El énfasis está en comprender qué se va a construir y por qué.
2. **Elaboración.** Se profundiza en el análisis del dominio del problema, se establece una arquitectura base sólida para la construcción posterior, y se planifican las actividades necesarias para completar el proyecto, mientras se sigue monitoreando activamente los riesgos identificados.
3. **Construcción.** Es la fase donde se desarrolla la mayor parte del sistema: se implementan los casos de uso restantes en iteraciones sucesivas hasta obtener un producto funcional con todos los requisitos acordados con el cliente, típicamente entregando una versión beta hacia el final de la fase.
4. **Transición.** El sistema se entrega formalmente a los usuarios finales: se corrigen errores detectados durante las pruebas, se ajusta el software al entorno real de producción (hardware, sistemas operativos), se elaboran los manuales correspondientes y se genera la versión formal del sistema.

### **Disciplinas (flujos de trabajo)**

De forma transversal a las cuatro fases, el PUDS organiza el trabajo técnico en un conjunto de disciplinas (también llamadas flujos de trabajo), que en cada iteración desarrollan un modelo específico: 

- **Requisitos** (produce el modelo de casos de uso), 
- **Análisis y Diseño** (produce el modelo de diseño y el modelo de despliegue), 
- **Implementación** (produce el modelo de implementación, es decir, el código),
- **Pruebas** (produce el modelo de pruebas). 

A estas se suman disciplinas de apoyo como la gestión de proyecto y la gestión de configuración y cambios. Es importante notar que todas las disciplinas participan en todas las fases, pero con distinto nivel de esfuerzo: por ejemplo, la disciplina de Requisitos tiene mucho peso en la fase de Inicio y va disminuyendo hacia la fase de Construcción, mientras que Implementación ocurre lo contrario.
Este esquema de fases y disciplinas es el que se seguirá para organizar el desarrollo de la plataforma FashionStore, documentando en cada flujo de trabajo (captura de requisitos, análisis, diseño e implementación) los artefactos y diagramas correspondientes.

## 5. UML

### **Concepto general**

UML (Lenguaje Unificado de Modelado) es un lenguaje de modelado visual estandarizado que permite a los equipos de desarrollo visualizar, especificar, construir y documentar los artefactos de un sistema de software. Fue desarrollado en la década de 1990 por tres ingenieros de software —Grady Booch, Ivar Jacobson y James Rumbaugh, trabajando en Rational Software— con el objetivo de unificar en una sola notación los distintos métodos de modelado orientado a objetos que existían hasta entonces (cada uno de ellos había desarrollado previamente su propio método por separado). Hoy UML es mantenido como estándar por el OMG (Object Management Group) y está reconocido como estándar ISO/IEC 19505.
La relación entre PUDS y UML es estrecha y complementaria: mientras que el PUDS define las actividades, fases y criterios para construir un sistema —desde la idea inicial hasta el software terminado—, UML aporta la notación gráfica con la que se representan y documentan los distintos modelos que se producen en cada iteración del proceso. Es decir, PUDS dice "qué hacer y cuándo", y UML aporta "cómo dibujarlo".

### **Categorías de diagramas**

La especificación UML 2.5 define un total de 14 tipos de diagramas, agrupados en dos grandes categorías:

- **Diagramas estructurales**, que representan la vista estática del sistema (qué elementos lo componen y cómo se relacionan entre sí, independientemente del tiempo). Incluyen, entre otros: diagrama de clases (el más utilizado, muestra las clases del sistema, sus atributos, operaciones y las relaciones entre ellas), diagrama de objetos, diagrama de componentes, diagrama de despliegue, diagrama de paquetes, diagrama de estructura compuesta y diagrama de perfiles.
- **Diagramas de comportamiento**, que capturan la vista dinámica del sistema (cómo interactúan sus elementos a lo largo del tiempo). Incluyen: diagrama de casos de uso (representa las funcionalidades del sistema desde la perspectiva de los actores que interactúan con él), diagrama de actividades (modela flujos de trabajo y procesos), diagrama de máquina de estados, y los diagramas de interacción (un subgrupo dentro de los de comportamiento) que comprenden el diagrama de secuencia, el diagrama de comunicación, el diagrama de temporización y el diagrama de vista de interacción.

### **Diagramas relevantes para este proyecto**

Para el desarrollo de FashionStore, siguiendo el flujo de trabajo del PUDS, se emplearán principalmente:

- **Diagrama de casos de uso**, en la disciplina de Requisitos, para representar las funcionalidades del sistema por cada actor identificado (cliente, administrador, encargado de sucursal, cajero, proveedor, sistema de pagos, servicio de IA).
- **Diagrama de clases**, en la disciplina de Análisis y Diseño, para modelar las entidades del sistema (usuarios, prendas, sucursales, reservas, inventario, ventas) y sus relaciones.
- **Diagrama de secuencia**, para representar la interacción entre los componentes del sistema en procesos clave como la reserva de una prenda, el flujo de compra digital con pasarela de pago, o la actualización de inventario tras una venta.
- **Diagrama de actividades**, para modelar procesos de negocio más amplios, como el flujo completo de atención de una reserva desde que el cliente la solicita hasta que retira o compra la prenda en sucursal.
- **Diagrama de despliegue**, en la disciplina de Implementación, para representar cómo se distribuyen los componentes del sistema (backend FastAPI, frontend Angular, app Flutter, base de datos PostgreSQL) sobre la infraestructura en la nube.


### **Identificar actores y casos de uso**

#### **Actores**

- **Cliente**: Usuario que compra en la plataforma web o móvil. Consulta el catálogo, reserva y compra prendas, usa el vestidor virtual con realidad aumentada y recibe recomendaciones mediante IA.
- **Administrador**: Supervisa el funcionamiento de la plataforma. Gestiona usuarios, sucursales, cuentas de proveedor y catálogo, valida la información enviada por proveedores, consulta el inventario consolidado y genera reportes.
- **Encargado de sucursal**: Gestiona la operación diaria de su sucursal. Prepara las reservas, confirma la llegada del cliente y registra los movimientos de inventario locales.
- **Cajero**: Atiende el punto de venta físico. Registra ventas presenciales, procesa pagos en caja y emite comprobantes.
- **Proveedor**: Suministra prendas a la cadena. Registra y envía información de sus productos, indica disponibilidad y los asocia a temporadas o colecciones, sujeto a validación del administrador.

#### **Casos de Uso**

| **ID** | **Caso de uso**                                       |
| ------ | ----------------------------------------------------- |
| CU01   | Registrar cliente                                     |
| CU02   | Iniciar sesión                                        |
| CU03   | Gestionar usuarios internos                           |
| CU04   | Gestionar sucursales                                  |
| CU05   | Gestionar cuentas de proveedor                        |
| CU06   | Consultar y actualizar perfil                         |
| CU07   | Registrar y enviar información de productos           |
| CU08   | Gestionar catálogo y productos                        |
| CU09   | Gestionar atributos del catálogo                      |
| CU10   | Consultar y filtrar catálogo                          |
| CU11   | Consultar disponibilidad por sucursal                 |
| CU12   | Registrar movimiento de inventario                    |
| CU13   | Consultar inventario consolidado                      |
| CU14   | Gestionar reservas de prendas                         |
| CU15   | Gestionar carrito de compras                          |
| CU16   | Realizar compra digital y consultar estado del pedido |
| CU17   | Atender reserva en sucursal                           |
| CU18   | Registrar venta presencial y procesar pago en caja    |
| CU19   | Usar vestidor virtual                                 |
| CU20   | Generar reportes y dashboards                         |
| CU21   | Recibir recomendaciones de IA                         |
| CU22   | Consultar asistente virtual/chatbot                   |
| CU23   | Generar reporte por voz/lenguaje natural              |

### **Priorizar los Casos de Uso**

### Tablas por ciclo (solo 5 actores con usuario)

#### Ciclo 1 (10 CU) — Base del sistema / MVP inicial

| **ID** | **Caso de uso**                             | **Prioridad** | **Riesgo** | **Estado** | **Actor(es) principal**                           |
| ------ | ------------------------------------------- | ------------- | ---------- | ---------- | ------------------------------------------------- |
| CU01   | Registrar cliente                           | Alta          | Bajo       | Pendiente  | Cliente                                           |
| CU02   | Iniciar sesión                              | Alta          | Medio      | Pendiente  | Todos                                             |
| CU03   | Gestionar usuarios internos                 | Alta          | Medio      | Pendiente  | Administrador                                     |
| CU04   | Gestionar sucursales                        | Alta          | Bajo       | Pendiente  | Administrador                                     |
| CU05   | Gestionar cuentas de proveedor              | Media         | Medio      | Pendiente  | Administrador                                     |
| CU06   | Consultar y actualizar perfil               | Media         | Bajo       | Pendiente  | Cliente                                           |
| CU07   | Registrar y enviar información de productos | Alta          | Medio      | Pendiente  | Proveedor (principal), Administrador (secundario) |
| CU08   | Gestionar catálogo y productos              | Alta          | Medio      | Pendiente  | Administrador                                     |
| CU09   | Gestionar atributos del catálogo            | Alta          | Medio      | Pendiente  | Administrador                                     |
| CU10   | Consultar y filtrar catálogo                | Alta          | Medio      | Pendiente  | Cliente                                           |

### Casos de Uso – FashionStore (23 CU)

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

2. **CU21 – Recibir recomendaciones de IA**: Sugerencias de productos según historial, temporada y disponibilidad. *Actor: Cliente.*
3. **CU22 – Consultar asistente virtual/chatbot**: Resolución de dudas del cliente sobre productos. *Actor: Cliente.*
4. **CU23 – Generar reporte por voz/lenguaje natural**: Solicitud de reportes generativos mediante comando de voz. *Actor: Administrador.*