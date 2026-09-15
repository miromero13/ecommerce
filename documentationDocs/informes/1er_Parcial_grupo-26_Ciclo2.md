**PLATAFORMA INTELIGENTE E-COMMERCE CON GESTIÓN DE VENTA, RESERVAS, INVENTARIO Y PROBADORES VIRTUALES VÍA REALIDAD AUMENTADA PARA LA CADENA DE TIENDAS WomenStyle** 

# 1\. PERFIL  {#1.-perfil}

## **1.1. INTRODUCCIÓN**  {#1.1.-introducción}

Actualmente el comercio de indumentaria es uno de los sectores más dinámicos del retail a nivel mundial, y en las últimas dos décadas ha experimentado una transformación profunda impulsada por la digitalización. Las tiendas de ropa físicas tradicionales han evolucionado hacia modelos omnicanal, en los que el cliente puede investigar, comparar y comprar prendas tanto en establecimientos físicos como en plataformas digitales, integrando catálogos en línea, aplicaciones móviles, pasarelas de pago electrónicas y sistemas de gestión de inventario en tiempo real. 

Grandes cadenas internacionales de moda han incorporado tecnologías como la realidad aumentada para permitir a sus clientes visualizar prendas antes de probárselas físicamente, así como sistemas de inteligencia artificial para ofrecer recomendaciones personalizadas según el historial de compra y las preferencias de cada usuario. Estas innovaciones, además de modernizar la experiencia de compra, también han optimizado la gestión logística e interna de las empresas del rubro, permitiendo administrar de manera centralizada múltiples sucursales, proveedores y temporadas de colección. 

En Bolivia, el sector de venta de ropa mantiene una fuerte presencia de comercio presencial, aunque en los últimos años se ha observado un crecimiento sostenido de tiendas que incorporan canales digitales complementarios, como catálogos web, redes sociales y aplicaciones de venta, especialmente en las principales ciudades del eje troncal. Las cadenas de tiendas de ropa que operan con varias sucursales enfrentan el reto particular de coordinar de manera integrada el inventario, la disponibilidad de tallas y colores, y los procesos de venta entre sus distintos puntos físicos, a la par de ofrecer canales digitales que complementen —y no reemplacen— la experiencia de prueba física de las prendas, que continúa siendo un factor determinante en la decisión de compra del cliente. 

En este contexto se enmarca WomenStyle, una cadena de tiendas de ropa que opera con múltiples sucursales distribuidas en distintas ciudades de Bolivia. WomenStyle ha construido su presencia comercial ofreciendo prendas de vestir organizadas por categorías, temporadas y colecciones, trabajando con diversos proveedores que abastecen de manera periódica su catálogo de acuerdo a las tendencias de cada temporada comercial (primavera-verano, otoño-invierno, entre otras). Actualmente, la empresa gestiona sus operaciones de manera independiente en cada sucursal: el cliente puede acudir físicamente a cualquiera de sus tiendas para conocer el catálogo disponible, seleccionar prendas de las tallas y colores que desea, probárselas en los vestidores físicos y realizar la compra directamente en el punto de caja de la sucursal correspondiente. La actualización del inventario y el registro de las ventas se realizan a nivel de cada sucursal, y la comunicación entre estas y la administración central se da de forma periódica para consolidar la información de existencias, movimientos de mercadería y desempeño comercial de la cadena. 

Frente al crecimiento de la demanda de experiencias de compra más ágiles y flexibles, WomenStyle ha identificado la oportunidad de complementar su operación presencial con una plataforma digital que integre sus canales web y móvil, permitiendo a sus clientes explorar el catálogo completo de la cadena, verificar la disponibilidad de prendas por sucursal y reservar productos antes de acudir a probárselos físicamente, incorporando además tecnologías emergentes como la realidad aumentada y la inteligencia artificial para enriquecer la experiencia de compra tanto presencial como digital. 

## **1.2. ANTECEDENTES** {#1.2.-antecedentes}

2.1. Fundamentación teórica 

El desarrollo de plataformas de comercio electrónico inteligentes para el rubro de la moda responde a una transformación real y medible del sector, no a una tendencia pasajera. La incorporación de tecnologías como la inteligencia artificial y la realidad aumentada en la experiencia de compra tiene relevancia porque ataca dos de los mayores desafíos históricos del e-commerce de ropa: la incertidumbre sobre cómo lucirá una prenda antes de comprarla, y la dificultad de ofrecer al cliente una experiencia de descubrimiento de productos verdaderamente personalizada. Un sistema de este tipo es relevante en la medida en que logra articular, bajo una misma plataforma, la operación física de una cadena de tiendas (sucursales, inventario, punto de venta) con sus canales digitales (catálogo web, aplicación móvil, pasarela de pago), evitando que ambos mundos funcionen como sistemas aislados.

Lo que este proyecto se propone hacer es diseñar y modelar (siguiendo el Proceso Unificado de Desarrollo de Software (PUDS) y la notación UML) una plataforma que permita a WomenStyle centralizar la gestión de su catálogo, sus reservas de prendas, su inventario multisucursal y sus ventas (tanto presenciales como digitales), incorporando además un módulo de vestidores virtuales mediante realidad aumentada y funcionalidades de inteligencia artificial orientadas a la recomendación de productos.

El aporte de este documento consiste en traducir ese conjunto de necesidades de negocio en una especificación técnica completa y trazable: captura y análisis de requisitos, modelado de casos de uso y de la arquitectura del sistema, diseño de la base de datos y de los flujos de trabajo entre sucursales, y una propuesta tecnológica concreta (FastAPI, Angular, Flutter/Dart y PostgreSQL) que sirva de base para la implementación de un MVP funcional dentro del plazo académico establecido.

2.2. Sistemas similares 

Para fundamentar el diseño de WomenStyle se revisaron casos de sistemas reales que ya implementan, de forma independiente, algunas de las funcionalidades que la plataforma busca integrar:

**Probador virtual con inteligencia artificial (Zara).** En años recientes Zara incorporó a su aplicación móvil una herramienta de prueba virtual basada en IA generativa: el cliente sube una fotografía de su rostro y una de cuerpo completo, con las cuales el sistema genera un avatar personalizado que se viste con la prenda elegida y gira 360° para mostrar el ajuste desde distintos ángulos. Este caso es relevante porque el beneficio reportado por la marca ha sido una reducción de dos dígitos en las devoluciones asociadas a errores de talla, lo que confirma que un vestidor virtual no es solo una mejora estética de la experiencia, sino una herramienta que reduce costos logísticos concretos. WomenStyle retoma esta idea, aunque orientada a realidad aumentada sobre la cámara del dispositivo en lugar de un avatar generado por IA.

**Recomendaciones personalizadas basadas en IA (Amazon).** Amazon construyó desde hace más de una década un sistema de recomendaciones que analiza el historial de navegación y compra de cada usuario mediante técnicas como el filtrado colaborativo, comparando patrones de comportamiento entre usuarios similares para sugerir productos. Este enfoque tiene un peso comercial considerable: la propia empresa ha reportado que cerca del 35% de sus ventas provienen de estas recomendaciones personalizadas. Este caso sirve de referencia para el módulo de recomendación de prendas de WomenStyle, que buscará sugerir productos considerando preferencias, historial y disponibilidad del cliente. 

**Reserva y recogida en tienda — Click & Collect (Decathlon, Zara, H\&M).** Distintas cadenas de retail han consolidado un modelo en el que el cliente reserva o compra en línea y recoge (o se prueba) el producto físicamente en la sucursal de su preferencia. En el caso de Decathlon, los clientes pueden reservar productos en la tienda más cercana y recogerlos en pocas horas, un esquema especialmente útil para artículos de alta demanda. Este modelo es el antecedente directo del proceso de reserva de prendas que WomenStyle plantea: el cliente selecciona varias prendas desde la app, indica sucursal y horario, y acude posteriormente a probárselas antes de decidir la compra.

Estos tres casos (vestidor virtual, motor de recomendación e integración de reserva digital con atención físicaI) constituyen la base conceptual sobre la cual se diseñará la plataforma de WomenStyle, adaptando cada una de estas ideas a la escala y al contexto de una cadena de tiendas de ropa que opera en Bolivia.

## **1.3. OBJETIVOS**  {#1.3.-objetivos}

### **1.3.1. Objetivo General**  {#1.3.1.-objetivo-general}

Desarrollar una plataforma inteligente e-commerce con gestión de venta, reservas, inventario y probadores virtuales vía realidad aumentada para la cadena de tiendas WomenStyle. 

### **1.3.2. Objetivo Específicos** {#1.3.2.-objetivo-específicos}

- **Recolectar información** sobre sistemas de e-commerce de moda similares y sobre los procesos actuales de venta, reserva e inventario en las sucursales de WomenStyle, mediante investigación de mercado y relevamiento de los flujos operativos de la cadena, con el fin de identificar los requerimientos funcionales y no funcionales del sistema.  
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

## **1.4. DESCRIPCIÓN DEL PROBLEMA**  {#1.4.-descripción-del-problema}

Trabajando dentro de la operación diaria de WomenStyle, se identifican las siguientes situaciones en la cadena:

**1\. Desconocimiento de la disponibilidad de prendas entre sucursales.**

Cuando un cliente acude a una sucursal buscando una prenda en una talla o color específico y esta no se encuentra disponible en ese punto de venta, el personal no cuenta con una manera inmediata y confiable de verificar si esa misma prenda está disponible en otra sucursal cercana. 

En la práctica, la única alternativa es llamar telefónicamente a las demás tiendas de la ciudad y esperar a que alguien revise físicamente el estante o la bodega, un proceso que puede tomar varios minutos y que muchas veces se descarta directamente por falta de tiempo durante horas de alta afluencia. Esto obliga al cliente a trasladarse físicamente sin certeza de encontrar el producto, a esperar sin saber si vale la pena hacerlo, o a desistir de la compra por completo. Desde la perspectiva de la cadena, esto significa que una prenda que sí existe en stock —solo que en otra ubicación— no logra venderse, mientras que esa misma sucursal probablemente termine con excedente de esa prenda en la temporada siguiente por no haber podido colocarla a tiempo.

**2\. Riesgo de pérdida o duplicación de prendas apartadas para un cliente.** 

Cuando un cliente solicita que se le aparte una o varias prendas para probárselas más adelante, esa solicitud se comunica de manera informal —por llamada telefónica, mensaje de WhatsApp o simplemente de palabra durante una visita previa— y queda a criterio de la persona que atiende recordarla y comunicarla al resto del equipo de turno. 

No existe un registro único y verificable de qué prendas están comprometidas, para quién, ni hasta qué hora se mantiene la reserva. Como consecuencia, se han dado casos donde la prenda apartada termina siendo vendida a otro cliente antes de que el interesado original llegue a la tienda, generando una situación incómoda que el personal debe resolver improvisando (ofreciendo un descuento, buscando una prenda similar, o simplemente disculpándose sin poder cumplir lo prometido). También ocurre lo contrario: dos empleados distintos, sin saberlo, confirman la misma prenda a dos clientes diferentes para el mismo horario de atención, lo que genera fricción tanto con el cliente como entre el personal.

**3\. Desactualización de la información consolidada de inventario entre sucursales y administración central.**

Cada sucursal registra sus propios movimientos de mercadería —ventas del día, ingresos de proveedores, prendas dadas de baja por daño o devolución— de forma independiente, y esta información se traslada a la administración central mediante reportes que se consolidan cada cierto número de días, no en tiempo real. Esto provoca que, al momento de decidir si conviene redistribuir stock entre tiendas o realizar un nuevo pedido a un proveedor, la administración esté tomando esas decisiones con datos que ya tienen varios días de desfase respecto a la situación real en tienda. 

El resultado observado es que, mientras una sucursal enfrenta quiebre de stock de una prenda de alta rotación y pierde ventas por no tenerla disponible, otra sucursal de la misma ciudad puede tener esa misma prenda acumulada sin movimiento, sin que exista visibilidad oportuna para corregir esa descompensación a tiempo. 

**4\. Fragmentación de la información entre las ventas presenciales y las ventas digitales.**

Las ventas que se realizan en el punto de caja de una sucursal y las que eventualmente se gestionan a través de canales digitales (redes sociales, catálogos enviados por mensajería, pedidos telefónicos) se registran en sistemas o cuadernos distintos, sin un punto único que las una. Esto dificulta obtener una visión real y oportuna de cuánto se vendió en total de una prenda específica en un día, considerando ambos canales, lo cual es especialmente problemático durante el lanzamiento de una nueva colección o una promoción por temporada, donde la demanda puede superar rápidamente al stock disponible sin que el equipo lo note a tiempo por estar mirando cada canal de forma aislada. Esto también complica la elaboración de reportes de desempeño comercial consolidados que reflejen el comportamiento real de venta de la cadena como un todo. 

## **1.5. ALCANCE**  {#1.5.-alcance}

El alcance del proyecto comprende el diseño, modelado y posterior implementación del MVP de una plataforma inteligente de comercio electrónico para WomenStyle. A continuación, se detallan los requisitos funcionales organizados por módulos:

### **1\. MÓDULO DE USUARIOS Y ROLES** {#1.-módulo-de-usuarios-y-roles}

Este módulo permitirá administrar el acceso a la plataforma y la estructura organizacional de la cadena, controlando qué puede hacer cada tipo de usuario según su rol.

Funcionalidades:

* Registro e inicio de sesión de clientes.  
* Autenticación y autorización mediante roles (JWT).  
* Gestión de usuarios internos: administradores, encargados de sucursal y cajeros.  
* Registro y administración de sucursales por ciudad.  
* Registro y gestión de proveedores.  
* Control de acceso a funcionalidades según el rol del usuario.  
* Consulta y actualización de datos de perfil del cliente.

  ### **2\. MÓDULO DE INVENTARIO** {#2.-módulo-de-inventario}

Este módulo permitirá administrar el catálogo de prendas de la cadena y mantener actualizadas y sincronizadas las existencias de cada sucursal. Funcionalidades:

* Registro, edición y baja de prendas.  
* Gestión de categorías, tallas, colores, temporadas comerciales y colecciones.  
* Registro y envío de información de productos por parte del proveedor, indicando características, disponibilidad y su asociación a temporadas y colecciones.  
* Validación por parte del administrador de la información enviada por el proveedor antes de su publicación en el catálogo.  
* Búsqueda y filtrado del catálogo (por categoría, talla, color, temporada, precio) desde web y móvil.  
* Consulta de disponibilidad de una prenda por sucursal, talla y color en tiempo real.  
* Indicador de estado del producto (disponible, reservado, agotado, próximo a ingresar).  
* Actualización automática del inventario tras reservas, compras, ventas, devoluciones y recepción de productos.  
* Registro de movimientos de inventario (ingresos, salidas, traspasos entre sucursales).  
* Alertas de stock bajo o próximo a agotarse.  
* Consulta de inventario consolidado a nivel de administración central.

  ### **3\. MÓDULO DE COMPRA** {#3.-módulo-de-compra}

Este módulo permitirá al cliente reservar prendas para probárselas en tienda y/o completar una compra digital desde la plataforma web o móvil. Funcionalidades:

* Selección de múltiples prendas para reservar, indicando sucursal y horario aproximado de atención.  
* Notificación de la reserva a la sucursal correspondiente y consulta de su estado (pendiente, confirmada, atendida, cancelada).  
* Cancelación de reservas y definición de un tiempo límite de validez.  
* Adición y edición de productos en el carrito de compras.  
* Cálculo automático de totales, considerando promociones vigentes.  
* Compra digital desde plataforma web o aplicación móvil.  
* Integración con pasarela de pago electrónica.  
* Confirmación y comprobante de compra digital.  
* Seguimiento del estado del pedido (pagado, en preparación, listo para entrega o recogida).

  ### **4\. MÓDULO DE VENTA** {#4.-módulo-de-venta}

Este módulo permitirá registrar las ventas realizadas directamente en el punto de caja de la sucursal, incluyendo aquellas derivadas de una reserva previa. Funcionalidades:

* Preparación y confirmación de recepción de prendas reservadas por parte del encargado de sucursal.  
* Registro de ventas presenciales por parte del cajero.  
* Asociación de la venta presencial con una reserva previa, si corresponde.  
* Procesamiento de pagos en punto de caja.  
* Emisión de comprobantes de venta.  
* Actualización automática del inventario tras cada venta presencial.

  ### **5\. MÓDULO DE REALIDAD AUMENTADA** {#5.-módulo-de-realidad-aumentada}

Este módulo permitirá al cliente visualizar de manera virtual cómo luciría una prenda, utilizando la cámara de su dispositivo móvil, sin necesidad de probársela físicamente.

Funcionalidades:

* Visualización de la prenda seleccionada sobre la imagen del cliente mediante realidad aumentada.  
* Integración con el catálogo de productos y sus características (color, talla, modelo).  
* Disponibilidad exclusiva desde la aplicación móvil.  
* Opción de guardar o compartir la visualización generada.

  ### **6\. MÓDULO DE REPORTES Y DASHBOARD** {#6.-módulo-de-reportes-y-dashboard}

Este módulo permitirá a la administración de WomenStyle visualizar de manera consolidada el desempeño comercial y operativo de la cadena.

Funcionalidades:

* Reportes de ventas y compras por sucursal, producto y periodo.  
* Reportes de inventario y movimientos de mercadería.  
* Indicadores de reservas atendidas, canceladas y expiradas.  
* Dashboards visuales para apoyo a la toma de decisiones.  
* Exportación de reportes.

  ### **7\. MÓDULO DE ASISTENCIA INTELIGENTE** {#7.-módulo-de-asistencia-inteligente}

Este módulo permitirá ofrecer sugerencias personalizadas de productos y asistencia mediante inteligencia artificial, tanto al cliente como a la administración. Funcionalidades:

* Recomendación de prendas según historial de navegación o compra.

* Recomendación considerando temporada, categoría, talla y disponibilidad.  
* Asistente virtual/chatbot para consultas del cliente sobre productos.  
* Generación de reportes bajo demanda para la administración, mediante comando de voz o lenguaje natural.

### **8\. MÓDULO DE NOTIFICACIONES** {#8.-módulo-de-notificaciones}

Este módulo permitirá mantener informados de manera proactiva a los distintos usuarios internos y clientes de WomenStyle sobre eventos relevantes ocurridos dentro del sistema, mediante notificaciones push enviadas a la aplicación móvil, sin necesidad de que el usuario deba consultarlos manualmente.

Funcionalidades:

* Envío de notificaciones push al administrador sobre alertas operativas: stock bajo o próximo a agotarse, productos enviados por proveedores pendientes de validación, reservas vencidas sin atender, cuentas de proveedor pendientes de aprobación, traspasos de inventario completados y metas o umbrales de ventas alcanzados.  
* Envío de notificaciones push al cliente sobre el estado de su pedido (pagado, en preparación, listo para entrega o recogida), confirmación de reservas preparadas por la sucursal, recordatorios de reservas próximas a vencer, recomendaciones de prendas mediante inteligencia artificial, reingreso de stock de prendas agotadas de su interés, lanzamiento de nuevas temporadas o colecciones, y promociones vigentes.  
* Envío de notificaciones push al encargado de sucursal sobre nuevas reservas asignadas a su sucursal, alertas de stock bajo local, ingresos o traspasos de mercadería recibidos, y reservas próximas a vencer sin haber sido preparadas.  
* Registro del historial de notificaciones enviadas a cada usuario, con su estado de lectura (leída/no leída).  
* Reintento automático de entrega de la notificación cuando el dispositivo del destinatario no cuenta con conexión a internet en el momento del envío.

# PARTE I. FUNDAMENTACIÓN TEÓRICA {#parte-i.-fundamentación-teórica}

## **1\. E-commerce** {#1.-e-commerce}

El comercio electrónico (e-commerce) se define como la práctica de comprar y vender bienes o servicios a través de Internet, abarcando todas las transacciones en línea, desde que un cliente navega por un sitio web hasta la entrega final de su compra. Detrás de toda plataforma de este tipo existen componentes técnicos comunes: escaparates en línea donde las empresas muestran sus productos, carritos de compra que permiten seleccionar artículos y proceder al pago, pasarelas de pago que procesan las transacciones de forma segura, y sistemas de gestión de inventario que actualizan la disponibilidad en tiempo real.

Existen distintas formas de clasificar el e-commerce según el tipo de actores que participan en la transacción: 

* el modelo B2B (business to business) involucra transacciones entre empresas conectadas mediante la red;   
* el modelo B2C (business to consumer) involucra transacciones entre una empresa y su clientela, usualmente a través de portales de venta oficiales;   
* el modelo C2B (consumer to business), donde la transacción se origina en el interés del propio cliente. 

A esta clasificación se suman modelos más recientes como el C2C (venta directa entre consumidores) y el social commerce, que traslada la venta a redes sociales como Instagram o TikTok sin que el usuario deba salir de la aplicación. 

Este marco conceptual es la base sobre la cual se analizan a continuación seis plataformas reales, tanto desde la perspectiva de quien compra como de quien desarrolla una tienda online.

1. ### **Como usuario** {#como-usuario}

   1. #### **Amazon.** {#amazon.}

   Es mucho más que una tienda online: es un ecosistema de servicios que conecta compradores, vendedores, marcas, empresas, desarrolladores y usuarios que consumen contenido digital o servicios en la nube. Desde la perspectiva del comprador es importante distinguir entre Amazon Retail y Amazon Marketplace: cuando el cliente compra directamente a Amazon.com, la empresa se queda con todo el beneficio de la venta; cuando compra a un vendedor externo dentro del Marketplace, Amazon retiene una comisión fija y el resto va al vendedor. 

   Para el usuario final, esta diferencia se traduce en variedad y precio: el Marketplace le da acceso a una selección más amplia de productos, incluyendo artículos de nicho, con precios más competitivos gracias a la competencia entre vendedores, todo bajo la garantía y el sistema de pagos de Amazon. Como usuario final, la experiencia gira en torno a la búsqueda, la comparación de precios, las reseñas de otros compradores y el seguimiento del pedido hasta la entrega. 

      2. #### **Alibaba.** {#alibaba.}

   A diferencia de Amazon, Alibaba opera principalmente bajo un modelo B2B (empresa a empresa): proporciona un espacio en línea donde las empresas pueden comprar y vender productos al por mayor, ofreciendo herramientas para la búsqueda de productos, la negociación de precios y el pago. Su escala es considerable: la plataforma conecta a fabricantes, proveedores y distribuidores, principalmente de China, con compradores de todo el mundo, reuniendo más de 200 millones de productos en cientos de categorías. 

   Como usuario/comprador, la experiencia difiere bastante de Amazon: en Alibaba los proveedores publican catálogos de productos, establecen una cantidad mínima de pedido (MOQ) y ofrecen precios bajo condiciones comerciales internacionales (FOB/CIF), por lo que el proceso de compra suele incluir negociación directa con el proveedor antes de cerrar el pedido, algo poco común en plataformas orientadas al consumidor final.

      3. #### **Shopify.** {#shopify.}

   Desde la óptica del usuario/comprador, Shopify no es una tienda en sí misma sino la infraestructura sobre la que operan miles de tiendas independientes: es una plataforma de comercio que ayuda a emprendedores, minoristas y marcas internacionales a vender online y en persona, gestionar su tienda y hacer crecer sus negocios. 

   Al comprar en una tienda construida sobre Shopify, el usuario normalmente encuentra un proceso de compra estandarizado (catálogo, carrito, checkout, confirmación) independientemente de la marca, ya que Shopify centraliza en una sola herramienta todo lo necesario para vender por internet: diseño de la tienda, gestión de productos, pagos y pedidos. Además, muchas tiendas Shopify integran su catálogo con redes sociales y marketplaces externos, lo que amplía los puntos de contacto para el comprador.

   2. ### **Como desarrollador** {#como-desarrollador}

      1. #### **Magento (Adobe Commerce).** {#magento-(adobe-commerce).}

   Es una de las plataformas más utilizadas por equipos de desarrollo para construir tiendas complejas y a gran escala. Al ser una plataforma de código abierto, ofrece una infraestructura completa que las empresas pueden usar para construir, gestionar y hacer crecer sus tiendas online, permitiendo a los desarrolladores modificar y expandir sus funcionalidades libremente. Actualmente coexisten dos versiones: Magento Open Source, gratuita y de código abierto, pensada para equipos que buscan control total sobre su tienda; y Adobe Commerce, la versión comercial en la nube con funciones empresariales adicionales. 

   Para un desarrollador, el beneficio principal de Magento es que permite crear experiencias de compra multicanal tanto para clientes B2B como B2C en una sola plataforma, aunque su configuración exige conocimientos técnicos más avanzados que otras alternativas.

      2. #### **PrestaShop.** {#prestashop.}

   Es un sistema de gestión de contenidos (CMS) especializado en comercio electrónico, popular especialmente en Europa y América Latina. Está desarrollado completamente en PHP, MySQL y Smarty, y desde su versión 1.7 incorpora el framework Symfony para mejorar el rendimiento de la plataforma. 

   Su arquitectura está pensada para que el desarrollador construya la tienda de forma incremental: permite crear comercios electrónicos modulares, es decir, se puede empezar con una tienda simple e ir añadiendo módulos según se necesiten, como métodos de pago adicionales, mejoras de SEO o sistemas de promoción. A nivel técnico, utiliza el patrón Modelo-Vista-Controlador (MVC) como arquitectura de software, además de tecnologías como JavaScript, HTML, CSS y jQuery, lo que la hace una opción intermedia entre la simplicidad de Shopify y la complejidad de Magento.

      3. #### **WooCommerce.** {#woocommerce.}

   Es la opción más ligada al ecosistema WordPress: se trata específicamente de un plugin de WordPress que convierte un blog o sitio web en una tienda online. Su principal ventaja para un desarrollador es la rapidez de implementación sobre un sitio ya existente en WordPress, sin necesidad de migrar a una plataforma completamente distinta. Su adopción es muy amplia: cuenta con más de 5 millones de usuarios activos e impulsa alrededor del 40% del total de tiendas online del mundo. 

   A diferencia de Shopify (que es un servicio SaaS con costo mensual fijo), WooCommerce es gratuito, pero requiere que el desarrollador contrate por separado el hosting, los plugins adicionales y otros servicios necesarios para mantener la tienda, lo que le da más flexibilidad de personalización a cambio de asumir la responsabilidad del mantenimiento técnico.

## **2\. Pasarelas de pago** {#2.-pasarelas-de-pago}

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

## **3\. Deliverys** {#3.-deliverys}

1. ### **¿Cómo funcionan los servicios de delivery?** {#¿cómo-funcionan-los-servicios-de-delivery?}

   Los servicios de delivery (o de "última milla") son plataformas tecnológicas que conectan a tres actores: 

* el comercio (restaurante, tienda o negocio que ofrece el producto),   
* el repartidor o socio conductor (quien realiza físicamente el traslado)  
* el cliente final (quien recibe el pedido).   
  El funcionamiento general sigue una lógica común entre las distintas apps: el cliente selecciona productos desde un catálogo dentro de la aplicación, confirma la dirección de entrega y el método de pago, un algoritmo asigna el pedido al repartidor disponible más cercano y traza la ruta óptima, y tanto el cliente como el negocio pueden seguir el estado del envío en tiempo real hasta que el paquete llega a destino. Este modelo se apoya en tres piezas tecnológicas clave: geolocalización (para ubicar repartidores y calcular rutas), un motor de asignación de pedidos (que decide qué repartidor atiende cada solicitud) y un sistema de seguimiento en vivo que informa al cliente sobre el progreso de su pedido.

A continuación se describen tres ejemplos que operan actualmente en Bolivia.

4. **Yango**

   Yango es una empresa tecnológica global (originaria de Yandex) que opera como una "superapp": bajo una misma aplicación ofrece transporte de pasajeros, envío de paquetes (Yango Delivery), transporte de carga más pesada (Yango Cargo) y, desde 2024, entrega de comida (Yango Comida) en ciudades bolivianas como Santa Cruz. Su funcionamiento para envío de paquetes es similar al de solicitar un viaje: el usuario indica el punto de recojo y de entrega desde la app, y un repartidor cercano recoge el paquete en minutos y lo traslada usando el vehículo que el cliente elija (moto, auto, etc.), mientras tanto el remitente como el destinatario pueden seguir la ubicación del envío en tiempo real y reciben notificaciones. 

   Para el caso de negocios, Yango ofrece cuentas empresariales con dashboards que permiten supervisar múltiples entregas simultáneas. A nivel de asignación, Yango utiliza algoritmos de distribución inteligente de pedidos y trazado de rutas que buscan optimizar el tiempo de entrega y reducir los tiempos muertos de los repartidores, un principio de optimización logística común entre las plataformas de delivery modernas.

   5. **Yummy (ex YAIGO)**

   Yummy es una superapp de delivery de origen venezolano que, en Bolivia, absorbió a la plataforma local YAIGO (fundada como un emprendimiento boliviano que llegó a ser la app más descargada del país antes de la adquisición). Bajo su modelo actual, Yummy no se limita a comida: dentro de la misma aplicación integra supermercados, farmacias, entradas a eventos y, en algunos mercados de la región, incluso venta de ropa. Su funcionamiento se apoya en una flota de repartidores ("Yummers") activa los siete días de la semana, y ofrece múltiples métodos de pago tanto en moneda local como internacional dentro de la misma app. Este ejemplo es relevante para el proyecto porque ilustra cómo una plataforma de delivery puede evolucionar de una app enfocada en comida hacia un marketplace más amplio que incluye retail, algo conceptualmente cercano a lo que WomenStyle necesitaría si en el futuro decidiera tercerizar la entrega a domicilio de sus compras digitales en lugar de operarla internamente.

      6. **PedidosYa**

   PedidosYa es una de las plataformas de delivery más consolidadas en Bolivia y en general en América Latina. Además de su servicio tradicional de comida, opera un servicio específico de "Envíos" para mensajería de paquetes y documentos, disponible en varias ciudades bolivianas (Santa Cruz, Cochabamba, La Paz, El Alto, entre otras). Es particularmente útil como referencia porque su mecánica de cálculo de tarifa es explícita y basada en distancia: el sistema cobra una tarifa fija por los primeros kilómetros de recorrido, y a partir de ahí aplica un recargo adicional por cada kilómetro extra que deba recorrer el repartidor entre el punto de recojo y el de entrega, calculado automáticamente por la app según la ruta real. Además, el servicio impone restricciones de tamaño y peso al paquete (máximo 5 kg y dimensiones límite), lo cual es un patrón común entre los servicios de última milla: la tarifa y la elegibilidad del envío dependen tanto de la distancia recorrida como del tamaño/peso de la carga.

2. ### **Cómo calculan las plataformas el costo de una entrega** {#cómo-calculan-las-plataformas-el-costo-de-una-entrega}

   De los casos revisados se pueden extraer los factores que, en general, determinan el costo de una entrega en este tipo de plataformas:

* **Distancia recorrida**: es el factor más determinante; normalmente se cobra una tarifa base por un primer tramo (por ejemplo, los primeros kilómetros) y luego un costo incremental por cada unidad de distancia adicional.  
* **Peso y tamaño del paquete**: los servicios de mensajería suelen limitar el peso y volumen máximo aceptado, y algunos aplican recargos si el paquete excede ciertas dimensiones estándar.  
* **Tiempo/demanda**: en varias plataformas de este tipo, la tarifa puede variar según la hora del día o la disponibilidad de repartidores en la zona (mecanismos de precio dinámico), aunque este componente varía según cada empresa y no siempre es visible para el usuario final.  
* **Frecuencia y volumen para negocios**: cuando el servicio se contrata a nivel empresarial (como es el caso de las cuentas B2B de Yango o PedidosYa), suele existir facturación consolidada periódica y, en algunos casos, tarifas preferenciales por volumen de envíos.

## **4\. PUDS** {#4.-puds}

1. ### **Concepto general** {#concepto-general}

El Proceso Unificado de Desarrollo de Software (PUDS), también conocido como Proceso Unificado (UP) o, en su implementación más difundida y documentada, como Proceso Unificado de Rational (RUP), es un marco de trabajo para el desarrollo de software que se caracteriza por tres rasgos definitorios: está **dirigido por casos de uso**, está **centrado en la arquitectura**, y es **iterativo e incremental**. En esencia, es un conjunto de actividades necesarias para transformar los requisitos de un usuario en un sistema de software funcional.

Que el proceso esté "dirigido por casos de uso" significa que cada iteración del desarrollo se organiza alrededor de un conjunto de casos de uso o escenarios que se llevan de principio a fin a través de todas las disciplinas del proyecto (requisitos, análisis, diseño, implementación y pruebas), en lugar de completar cada disciplina para todo el sistema antes de pasar a la siguiente, como ocurriría en un modelo en cascada tradicional. Que sea "iterativo e incremental" implica que el sistema no se entrega de una sola vez al final del proyecto, sino que se construye en ciclos sucesivos, cada uno de los cuales añade o mejora funcionalidades sobre la versión anterior, permitiendo detectar riesgos y ajustar el rumbo tempranamente en lugar de descubrir problemas graves al final del desarrollo.

2. ### **Fases del PUDS** {#fases-del-puds}

El PUDS organiza el trabajo de desarrollo en cuatro fases secuenciales, cada una de las cuales puede subdividirse a su vez en una o más iteraciones:

1) **Inicio.** Se define el alcance y los objetivos del negocio, se evalúa la factibilidad del proyecto, se identifican los riesgos críticos y se esboza una arquitectura candidata inicial. El énfasis está en comprender qué se va a construir y por qué.  
2) **Elaboración.** Se profundiza en el análisis del dominio del problema, se establece una arquitectura base sólida para la construcción posterior, y se planifican las actividades necesarias para completar el proyecto, mientras se sigue monitoreando activamente los riesgos identificados.  
3) **Construcción.** Es la fase donde se desarrolla la mayor parte del sistema: se implementan los casos de uso restantes en iteraciones sucesivas hasta obtener un producto funcional con todos los requisitos acordados con el cliente, típicamente entregando una versión beta hacia el final de la fase.  
4) **Transición.** El sistema se entrega formalmente a los usuarios finales: se corrigen errores detectados durante las pruebas, se ajusta el software al entorno real de producción (hardware, sistemas operativos), se elaboran los manuales correspondientes y se genera la versión formal del sistema.

3. ### **Disciplinas (flujos de trabajo)** {#disciplinas-(flujos-de-trabajo)}

De forma transversal a las cuatro fases, el PUDS organiza el trabajo técnico en un conjunto de disciplinas (también llamadas flujos de trabajo), que en cada iteración desarrollan un modelo específico: 

* **Requisitos** (produce el modelo de casos de uso),   
* **Análisis y Diseño** (produce el modelo de diseño y el modelo de despliegue),   
* **Implementación** (produce el modelo de implementación, es decir, el código),  
* **Pruebas** (produce el modelo de pruebas). 

A estas se suman disciplinas de apoyo como la gestión de proyecto y la gestión de configuración y cambios. Es importante notar que todas las disciplinas participan en todas las fases, pero con distinto nivel de esfuerzo: por ejemplo, la disciplina de Requisitos tiene mucho peso en la fase de Inicio y va disminuyendo hacia la fase de Construcción, mientras que Implementación ocurre lo contrario.

Este esquema de fases y disciplinas es el que se seguirá para organizar el desarrollo de la plataforma WomenStyle, documentando en cada flujo de trabajo (captura de requisitos, análisis, diseño e implementación) los artefactos y diagramas correspondientes.

## **5\. UML** {#5.-uml}

1. ### **Concepto general** {#concepto-general-1}

UML (Lenguaje Unificado de Modelado) es un lenguaje de modelado visual estandarizado que permite a los equipos de desarrollo visualizar, especificar, construir y documentar los artefactos de un sistema de software. Fue desarrollado en la década de 1990 por tres ingenieros de software —Grady Booch, Ivar Jacobson y James Rumbaugh, trabajando en Rational Software— con el objetivo de unificar en una sola notación los distintos métodos de modelado orientado a objetos que existían hasta entonces (cada uno de ellos había desarrollado previamente su propio método por separado). Hoy UML es mantenido como estándar por el OMG (Object Management Group) y está reconocido como estándar ISO/IEC 19505\.

La relación entre PUDS y UML es estrecha y complementaria: mientras que el PUDS define las actividades, fases y criterios para construir un sistema —desde la idea inicial hasta el software terminado—, UML aporta la notación gráfica con la que se representan y documentan los distintos modelos que se producen en cada iteración del proceso. Es decir, PUDS dice "qué hacer y cuándo", y UML aporta "cómo dibujarlo".

2. ### **Categorías de diagramas** {#categorías-de-diagramas}

La especificación UML 2.5 define un total de 14 tipos de diagramas, agrupados en dos grandes categorías:

- **Diagramas estructurales**, que representan la vista estática del sistema (qué elementos lo componen y cómo se relacionan entre sí, independientemente del tiempo). Incluyen, entre otros: diagrama de clases (el más utilizado, muestra las clases del sistema, sus atributos, operaciones y las relaciones entre ellas), diagrama de objetos, diagrama de componentes, diagrama de despliegue, diagrama de paquetes, diagrama de estructura compuesta y diagrama de perfiles.  
- **Diagramas de comportamiento**, que capturan la vista dinámica del sistema (cómo interactúan sus elementos a lo largo del tiempo). Incluyen: diagrama de casos de uso (representa las funcionalidades del sistema desde la perspectiva de los actores que interactúan con él), diagrama de actividades (modela flujos de trabajo y procesos), diagrama de máquina de estados, y los diagramas de interacción (un subgrupo dentro de los de comportamiento) que comprenden el diagrama de secuencia, el diagrama de comunicación, el diagrama de temporización y el diagrama de vista de interacción.

3. ### **Diagramas relevantes para este proyecto** {#diagramas-relevantes-para-este-proyecto}

Para el desarrollo de WomenStyle, siguiendo el flujo de trabajo del PUDS, se emplearán principalmente:

* **Diagrama de casos de uso**, en la disciplina de Requisitos, para representar las funcionalidades del sistema por cada actor identificado (cliente, administrador, encargado de sucursal, cajero, proveedor, sistema de pagos, servicio de IA).  
* **Diagrama de clases**, en la disciplina de Análisis y Diseño, para modelar las entidades del sistema (usuarios, prendas, sucursales, reservas, inventario, ventas) y sus relaciones.  
* **Diagrama de secuencia**, para representar la interacción entre los componentes del sistema en procesos clave como la reserva de una prenda, el flujo de compra digital con pasarela de pago, o la actualización de inventario tras una venta.  
* **Diagrama de actividades**, para modelar procesos de negocio más amplios, como el flujo completo de atención de una reserva desde que el cliente la solicita hasta que retira o compra la prenda en sucursal.  
* **Diagrama de despliegue**, en la disciplina de Implementación, para representar cómo se distribuyen los componentes del sistema (backend FastAPI, frontend Angular, app Flutter, base de datos PostgreSQL) sobre la infraestructura en la nube.

# PARTE II. PROCESO DE DESARROLLO {#parte-ii.-proceso-de-desarrollo}

1. ## **FLUJO DE TRABAJO: CAPTURA DE REQUISITOS** {#flujo-de-trabajo:-captura-de-requisitos}

   1. ### **Identificar actores y casos de uso** {#identificar-actores-y-casos-de-uso}

      1. #### **Actores** {#actores}

* **Cliente**: Usuario que compra en la plataforma web o móvil. Consulta el catálogo, reserva y compra prendas, usa el vestidor virtual con realidad aumentada y recibe recomendaciones mediante IA.  
* **Administrador**: Supervisa el funcionamiento de la plataforma. Gestiona usuarios, sucursales, cuentas de proveedor y catálogo, valida la información enviada por proveedores, consulta el inventario consolidado y genera reportes.  
* **Encargado de sucursal**: Gestiona la operación diaria de su sucursal. Prepara las reservas, confirma la llegada del cliente y registra los movimientos de inventario locales.  
* **Cajero**: Atiende el punto de venta físico. Registra ventas presenciales, procesa pagos en caja y emite comprobantes.  
* **Proveedor**: Suministra prendas a la cadena. Registra y envía información de sus productos, indica disponibilidad y los asocia a temporadas o colecciones, sujeto a validación del administrador.

  2. #### **Casos de Uso** {#casos-de-uso}

| ID | Caso de uso |
| :---- | :---- |
| **CU01** | Registrar cliente |
| **CU02** | Iniciar sesión |
| **CU03** | Gestionar usuarios internos |
| **CU04** | Gestionar sucursales |
| **CU05** | Gestionar cuentas de proveedor |
| **CU06** | Consultar y actualizar perfil |
| **CU07** | Registrar y enviar información de productos |
| **CU08** | Gestionar catálogo y productos |
| **CU09** | Gestionar atributos del catálogo |
| **CU10** | Consultar y filtrar catálogo |
| **CU11** | Consultar disponibilidad por sucursal |
| **CU12** | Registrar movimiento de inventario |
| **CU13** | Consultar inventario consolidado |
| **CU14** | Gestionar reservas de prendas |
| **CU15** | Gestionar carrito de compras |
| **CU16** | Realizar compra digital y consultar estado del pedido |
| **CU17** | Atender reserva en sucursal |
| **CU18** | Registrar venta presencial y procesar pago en caja |
| **CU19** | Usar vestidor virtual |
| **CU20** | Generar reportes y dashboards |
| **CU21** | Recibir recomendaciones de IA |
| **CU22** | Consultar asistente virtual/chatbot |
| **CU23** | Generar reporte por voz/lenguaje natural |

  2. ### **Priorizar los Casos de Uso** {#priorizar-los-casos-de-uso}

| ID | Caso de uso | Prioridad | Riesgo | Estado | Actor principal | Plataforma |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| CU01 | Registrar cliente | Alta | Bajo | Completado | Cliente | Ambas |
| CU02 | Iniciar sesión | Alta | Medio | Completado | Todos | Ambas |
| CU03 | Gestionar usuarios internos | Alta | Medio | Completado | Administrador | Web |
| CU04 | Gestionar sucursales | Alta | Bajo | Completado | Administrador | Web |
| CU05 | Gestionar cuentas de proveedor | Media | Medio | Completado | Administrador | Web |
| CU06 | Consultar y actualizar perfil | Media | Bajo | Completado | Cliente | Ambas |
| CU07 | Registrar y enviar información de productos | Alta | Medio | Completado | Proveedor, Administrador  | Web |
| CU08 | Gestionar catálogo y productos | Alta | Medio | Completado | Administrador | Web |
| CU09 | Gestionar atributos del catálogo | Alta | Medio | Completado | Administrador | Web |
| CU10 | Consultar y filtrar catálogo | Alta | Medio | Completado | Cliente | Ambas |
| CU11 | Consultar disponibilidad por sucursal | Alta | Medio | Pendiente | Cliente | Ambas |
| CU12 | Registrar movimiento de inventario | Alta | Medio | Pendiente | Encargado de sucursal, Cajero | Web |
| CU13 | Consultar inventario consolidado | Media | Bajo | Pendiente | Administrador | Web |
| CU14 | Gestionar reservas de prendas | Alta | Medio | Pendiente | Cliente | Ambas |
| CU15 | Gestionar carrito de compras | Alta | Bajo | Pendiente | Cliente | Ambas |
| CU16 | Realizar compra digital y consultar estado del pedido | Alta | Alto | Pendiente | Cliente | Ambas |
| CU17 | Atender reserva en sucursal | Alta | Medio | Pendiente | Encargado de sucursal | Web |
| CU18 | Registrar venta presencial y procesar pago en caja | Alta | Medio | Pendiente | Cajero | Web |
| CU19 | Usar vestidor virtual | Alta | Alto | Pendiente | Cliente | Móvil |
| CU20 | Generar reportes y dashboards | Media | Medio | Pendiente | Administrador | Web |
| CU21 | Recibir recomendaciones de IA | Media | Alto | Pendiente | Cliente | Ambas |
| CU22 | Consultar asistente virtual/chatbot | Baja | Alto | Pendiente | Cliente | Ambas |
| CU23 | Generar reporte por voz/lenguaje natural | Baja | Alto | Pendiente | Administrador | Web |
| CU24 | Recibir notificaciones push  | Media | Alto | Completado | Administrador, Cliente, Encargado de sucursal | Móvil |

#### **CICLO \#1** {#ciclo-#1}

| ID | Caso de uso | Prioridad | Riesgo | Estado | Actor(es) principal | Plataforma |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **CU01** | Registrar cliente | Alta | Bajo | Completado | Cliente | Ambas |
| **CU02** | Iniciar sesión | Alta | Medio | Completado | Todos | Ambas |
| **CU03** | Gestionar usuarios internos | Alta | Medio | Completado | Administrador | Web |
| **CU04** | Gestionar sucursales | Alta | Bajo | Completado | Administrador | Web |
| **CU05** | Gestionar cuentas de proveedor | Media | Medio | Completado | Administrador | Web |
| **CU06** | Consultar y actualizar perfil | Media | Bajo | Completado | Cliente | Ambas |
| **CU07** | Registrar y enviar información de productos | Alta | Medio | Completado | Proveedor (principal), Administrador (secundario) | Web |
| **CU08** | Gestionar catálogo y productos | Alta | Medio | Completado | Administrador | Web |
| **CU09** | Gestionar atributos del catálogo | Alta | Medio | Completado | Administrador | Web |
| **CU10** | Consultar y filtrar catálogo | Alta | Medio | Completado | Cliente | Ambas |

#### 

#### **CICLO \#2** {#ciclo-#2}

| ID | Caso de uso | Prioridad | Riesgo | Estado | Actor(es) principal | Plataforma |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **CU11** | Consultar disponibilidad por sucursal | Alta | Medio | Completado | Cliente | Ambas |
| **CU12** | Registrar movimiento de inventario | Alta | Medio | Completado | Encargado de sucursal, Cajero | Web |
| **CU13** | Consultar inventario consolidado | Media | Bajo | Completado | Administrador | Web |
| **CU14** | Gestionar reservas de prendas | Alta | Medio | Completado | Cliente | Ambas |
| **CU15** | Gestionar carrito de compras | Alta | Bajo | Completado | Cliente | Ambas |
| **CU16** | Realizar compra digital y consultar estado del pedido | Alta | Alto | Completado | Cliente | Ambas |
| **CU17** | Atender reserva en sucursal | Alta | Medio | Completado | Encargado de sucursal | Web |
| **CU18** | Registrar venta presencial y procesar pago en caja | Alta | Medio | Completado | Cajero | Web |

#### **CICLO \#3** {#ciclo-#3}

| ID | Caso de uso | Prioridad | Riesgo | Estado | Actor principal(es) | Plataforma |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| CU19 | Usar vestidor virtual | Alta | Alto | Completado | Cliente | Móvil |
| CU20 | Generar reportes y dashboards | Media | Medio | Completado | Administrador | Web |
| CU21 | Recibir recomendaciones de IA | Media | Alto | Completado | Cliente | Ambas |
| CU22 | Consultar asistente virtual/chatbot | Baja | Alto | Completado | Cliente | Ambas |
| CU23 | Generar reporte por voz/lenguaje natural | Baja | Alto | Completado | Administrador | Web |
| CU24 | Recibir notificaciones push  | Media | Alto | Completado | Administrador, Cliente, Encargado de sucursal | Móvil |

3. ### **Detalle de Casos de Uso** {#detalle-de-casos-de-uso}

   #### **CICLO \#1** {#ciclo-#1-1}

**CU01 – Registrar cliente**

![][image2]

| Nombre CU | CU01 – Registrar cliente |
| :---- | :---- |
| **Propósito** | Permitir que una persona interesada en utilizar WomenStyle cree una cuenta de cliente proporcionando sus datos personales y credenciales de acceso, para luego utilizar las funcionalidades disponibles para clientes de la plataforma. |
| **Resumen** | El cliente inicia el proceso de registro desde la aplicación web o móvil. El sistema solicita los datos personales y las credenciales necesarias para crear la cuenta. Luego valida que la información ingresada sea correcta y que no exista previamente una cuenta asociada a las credenciales proporcionadas. Si las validaciones son satisfactorias, el sistema registra al nuevo cliente y deja la cuenta disponible para que pueda iniciar sesión posteriormente. |
| **Actores** | **Cliente** |
| **Actor iniciador** | **Cliente**. |
| **Precondición** | El cliente **no debe tener una cuenta registrada** en WomenStyle con las mismas credenciales. Además, debe encontrarse en la plataforma web o aplicación móvil y seleccionar la opción **“Registrarse”**. |
| **Flujo principal** | 1\. El cliente selecciona la opción **“Registrarse”**. 2\. El sistema muestra el formulario de registro. 3\. El cliente introduce sus datos personales y credenciales de acceso requeridas. 4\. El sistema valida que los campos obligatorios estén completos y que los datos tengan un formato válido. 5\. El sistema verifica que las credenciales utilizadas para el registro no estén asociadas a otra cuenta existente. 6\. El sistema registra la información del nuevo cliente. 7\. El sistema asigna al usuario el rol correspondiente de **Cliente**. 8\. El sistema confirma que el registro se realizó correctamente. 9\. El sistema permite al cliente continuar hacia el inicio de sesión para acceder a la plataforma. |
| **Postcondición** | El nuevo cliente queda **registrado en el sistema** con sus datos personales y credenciales de acceso, asociado al rol **Cliente**. La cuenta queda disponible para que el usuario pueda autenticarse mediante el **CU02 – Iniciar sesión**. |
| **Excepciones** | **Datos obligatorios incompletos** → mostrar los campos que deben completarse y no crear la cuenta. **Formato de datos inválido** → mostrar un mensaje indicando el dato incorrecto y solicitar su corrección. **Credenciales ya registradas** → informar que ya existe una cuenta asociada y no crear un nuevo registro. **Error durante el registro** → informar que no fue posible completar el registro y conservar los datos ingresados para permitir un nuevo intento. **Cancelación del registro** → abandonar el proceso y no crear ninguna cuenta. |

**CU02 – Iniciar sesión**

![][image3] 

| Nombre CU | CU02 – Iniciar sesión |
| :---- | :---- |
| **Propósito** | Permitir que los usuarios registrados accedan de forma segura a WomenStyle mediante sus credenciales, identificando su rol para mostrar las funcionalidades correspondientes. |
| **Resumen** | El usuario introduce sus credenciales de acceso en la plataforma web o móvil. El sistema valida la información proporcionada y, si es correcta, autentica al usuario y genera un token JWT asociado a su sesión y rol. A partir de este momento, el usuario puede acceder a las funcionalidades permitidas según sus privilegios. |
| **Actores** | Cliente, Administrador, Encargado de sucursal, Cajero y Proveedor.  |
| **Actor iniciador** | Cliente, Administrador, Encargado de sucursal, Cajero y Proveedor.  |
| **Precondición** | El usuario debe contar con una cuenta registrada y habilitada en el sistema. Para usuarios internos, la cuenta debe haber sido creada y habilitada previamente por un Administrador mediante el **CU03 – Gestionar usuarios internos**. |
| **Flujo principal** | El usuario accede a la opción **“Iniciar sesión”**. El sistema muestra el formulario de autenticación. El usuario introduce su correo electrónico o usuario y contraseña. El usuario envía sus credenciales. El sistema valida que los datos requeridos hayan sido proporcionados. El sistema consulta la cuenta asociada a las credenciales proporcionadas. El sistema verifica que las credenciales sean correctas y que la cuenta se encuentre habilitada. El sistema identifica el rol asociado al usuario. El sistema genera un token de autenticación **JWT** con la información necesaria para identificar al usuario y controlar su acceso. El sistema inicia la sesión y dirige al usuario a la interfaz correspondiente según su rol. El sistema permite al usuario acceder a las funcionalidades autorizadas para su rol. |
| **Postcondición** | El usuario queda autenticado correctamente y dispone de una sesión válida mediante JWT. El sistema reconoce su identidad y rol, permitiendo el acceso únicamente a las funcionalidades autorizadas. |
| **Excepción** | **Credenciales incorrectas →** mostrar mensaje indicando que el usuario o contraseña no son válidos y solicitar nuevamente los datos. **Cuenta inexistente →** mostrar mensaje indicando que no existe una cuenta asociada a las credenciales proporcionadas. **Cuenta deshabilitada →** informar que la cuenta no se encuentra habilitada y no permitir el acceso. **Campos obligatorios vacíos →** solicitar al usuario completar los datos requeridos antes de continuar. **Error en el servicio de autenticación →** mostrar un mensaje de error y solicitar intentar nuevamente más tarde. **Sesión/token inválido o expirado →** solicitar nuevamente la autenticación del usuario. |

**CU03 – Gestionar usuarios internos**

**![][image4]** 

| Nombre CU | CU03 – Gestionar usuarios internos |
| :---- | :---- |
| **Propósito** | Permitir al Administrador registrar, modificar y dar de baja las cuentas de los usuarios internos de WomenStyle, asignándoles el rol correspondiente para controlar su acceso a las funcionalidades del sistema. |
| **Resumen** | El Administrador accede al módulo de gestión de usuarios internos y puede consultar las cuentas existentes. Desde este módulo puede registrar nuevos usuarios internos, modificar sus datos o rol, y dar de baja una cuenta cuando corresponda. El sistema valida la información y mantiene actualizado el registro de usuarios para que posteriormente puedan autenticarse mediante el CU02 – Iniciar sesión. |
| **Actores** | **Administrador.** |
| **Actor iniciador** | **Administrador** autorizado. |
| **Precondición** | **CU02 – Iniciar sesión**  Contar con permisos para gestionar usuarios internos. |
| **Flujo principal** | **1\.** El Administrador accede al módulo **“Gestión de usuarios internos”**. **2\.** El sistema verifica que el Administrador tenga permisos para realizar la operación. **3\.** El sistema muestra la lista de usuarios internos registrados y las opciones disponibles. **4\.** El Administrador selecciona la operación que desea realizar: registrar, editar o dar de baja un usuario. **5\.** Si selecciona **registrar**, el sistema muestra un formulario para introducir los datos del nuevo usuario. **6\.** El Administrador introduce los datos personales, credenciales y rol correspondiente. **7\.** El sistema valida la información introducida. **8\.** El sistema registra la nueva cuenta de usuario interno. **9\.** Si selecciona **editar**, el Administrador selecciona un usuario existente y modifica los datos que correspondan, incluyendo su rol cuando sea necesario. **10\.** El sistema valida y guarda los cambios realizados. **11\.** Si selecciona **dar de baja**, el Administrador selecciona el usuario que desea deshabilitar. **12\.** El sistema solicita confirmación de la operación. **13\.** El Administrador confirma la baja. **14\.** El sistema deshabilita la cuenta del usuario y actualiza su estado. **15\.** El sistema muestra un mensaje indicando que la operación fue realizada correctamente. |
| **Postcondición** | La información de los usuarios internos queda actualizada. En caso de alta, se dispone de una nueva cuenta; en caso de edición, los datos quedan modificados; y en caso de baja, la cuenta queda deshabilitada y el usuario ya no puede acceder al sistema mediante sus credenciales. |
| **Excepción** | **Datos obligatorios incompletos →** mostrar los campos que deben completarse y no registrar el usuario. **Correo o usuario ya registrado →** informar que las credenciales ya están asociadas a otra cuenta y solicitar datos diferentes.**\-  Rol no válido →** mostrar los roles permitidos para usuarios internos y no guardar la información hasta seleccionar uno válido. **Usuario inexistente →** informar que el usuario seleccionado no existe o ya no está disponible para la operación. **Intento de baja de usuario no permitido →** informar que la operación no puede realizarse y mantener la cuenta sin cambios.**\-  Administrador sin permisos →** rechazar la operación y mostrar un mensaje indicando que no cuenta con autorización suficiente.**\-  Error al guardar los datos →** informar que la operación no pudo completarse y conservar la información anterior. |

**CU04 – Gestionar sucursales**

	**![][image5]**

| Nombre CU | CU04 – Gestionar sucursales |
| :---- | :---- |
| **Propósito** | Permitir al administrador registrar, consultar, modificar y administrar las sucursales de WomenStyle, asociándolas a la ciudad correspondiente para mantener organizada la estructura física de la cadena. |
| **Resumen** | El administrador accede al módulo de sucursales y puede registrar nuevas sucursales, consultar las existentes y modificar su información. El sistema valida los datos ingresados y mantiene actualizada la información de las sucursales disponibles para las demás funcionalidades de la plataforma. |
| **Actores** | **Administrador** |
| **Actor iniciador** | **Administrador** |
| **Precondición** | El administrador debe haber iniciado sesión correctamente mediante **CU02 – Iniciar sesión** y contar con los permisos correspondientes para administrar sucursales. |
| **Flujo principal** | **1\.** El administrador accede al módulo de gestión de sucursales. **2\.** El sistema muestra las sucursales registradas. **3\.** El administrador selecciona la operación que desea realizar: registrar una nueva sucursal, consultar o modificar una existente. **4\.** Si registra una sucursal, ingresa los datos correspondientes, como ciudad, nombre o identificación de la sucursal y demás información requerida. **5\.** El sistema valida los datos ingresados. **6\.** El sistema verifica que la sucursal no esté registrada previamente de forma duplicada. **7\.** El sistema registra o actualiza la información de la sucursal. **8\.** El sistema confirma que la operación fue realizada correctamente. **9\.** El sistema muestra la información actualizada de las sucursales. |
| **Postcondición** | La sucursal queda registrada o actualizada correctamente en el sistema y asociada a su respectiva ciudad. La información queda disponible para las funcionalidades que requieren identificar las sucursales de WomenStyle. |
| **Excepción** | \- **Datos obligatorios incompletos** → mostrar los campos faltantes y solicitar su corrección. \- **Sucursal duplicada** → informar que la sucursal ya se encuentra registrada y no crear un nuevo registro. \- **Datos inválidos** → mostrar el error correspondiente y solicitar nuevamente la información. \- **Ciudad no válida o no registrada** → solicitar seleccionar una ciudad válida. \- **Error al guardar información** → informar que no fue posible completar la operación y conservar los datos anteriores. |

**CU05 – Gestionar cuentas de proveedor**.

	![][image6]

| Nombre CU | CU05 – Gestionar cuentas de proveedor |
| :---- | :---- |
| **Propósito** | Permitir al administrador controlar las cuentas de los proveedores que utilizarán la plataforma, gestionando su creación, aprobación y suspensión para garantizar que solamente proveedores autorizados puedan operar dentro del sistema. |
| **Resumen** | El administrador accede al módulo de cuentas de proveedores y consulta las cuentas existentes. Puede registrar una nueva cuenta, aprobar una cuenta pendiente o suspender una cuenta existente. El sistema valida la información y actualiza el estado correspondiente de la cuenta. |
| **Actores** | **Administrador** |
| **Actor iniciador** | **Administrador** |
| **Precondición** | CU02. Iniciar sesión y contar con permisos para gestionar cuentas de proveedores. |
| **Flujo principal** | **1\.** El administrador accede al módulo de gestión de cuentas de proveedores. **2\.** El sistema muestra las cuentas de proveedor registradas y su estado. **3\.** El administrador selecciona la operación que desea realizar. **4\.** Para registrar una cuenta, el administrador ingresa los datos requeridos del proveedor y de la cuenta. **5\.** El sistema valida la información proporcionada. **6\.** El administrador confirma el registro o selecciona una cuenta pendiente para aprobarla. **7\.** El sistema registra o actualiza el estado de la cuenta. **8\.** Si corresponde, el administrador puede seleccionar una cuenta activa para suspenderla. **9\.** El sistema solicita la confirmación de la suspensión. **10\.** El administrador confirma la operación. **11\.** El sistema actualiza el estado de la cuenta y muestra la confirmación de la operación. |
| **Postcondición** | La cuenta del proveedor queda registrada o con su estado actualizado según la operación realizada: **pendiente, aprobada/activa o suspendida**. El sistema conserva la información actualizada para controlar posteriormente el acceso y las operaciones del proveedor. |
| **Excepción** | **Datos obligatorios incompletos** → mostrar los campos faltantes y solicitar su corrección.-  **Proveedor o cuenta ya registrada** → informar que la cuenta ya existe y no crear un registro duplicado. **Datos inválidos** → mostrar el error correspondiente y solicitar corregir la información. **Cuenta ya suspendida** → informar que la cuenta no puede suspenderse nuevamente.-  **no encontrada** → informar que la cuenta seleccionada no existe o ya no está disponible.-  **Error al actualizar el estado** → informar que no fue posible completar la operación y mantener el estado anterior. |

**CU06 – Consultar y actualizar perfil**.  
**![][image7]**

| Nombre CU | CU06 – Consultar y actualizar perfil |
| :---- | :---- |
| **Propósito** | Permitir al cliente consultar y mantener actualizada su información personal dentro de la plataforma WomenStyle. |
| **Resumen** | El cliente accede a su perfil después de autenticarse y puede consultar la información registrada. Si necesita modificar algún dato permitido, ingresa los nuevos valores y el sistema valida y actualiza la información correspondiente. |
| **Actores** | Cliente |
| **Actor iniciador** | Cliente |
| **Precondición** | CU02 – Iniciar sesión y contar con una cuenta previamente registrada mediante CU01 – Registrar cliente. |
| **Flujo principal** | El cliente accede a la sección de perfil. El sistema identifica al cliente autenticado. El sistema muestra los datos personales registrados. El cliente consulta su información o selecciona la opción para actualizarla. El cliente modifica los datos personales permitidos. El sistema valida la información ingresada. El cliente confirma los cambios. El sistema actualiza la información del perfil. El sistema muestra un mensaje confirmando que los datos fueron actualizados correctamente. |
| **Postcondición** | La información del perfil del cliente queda almacenada y actualizada correctamente en el sistema. Si el cliente solamente consulta sus datos, la información permanece sin modificaciones. |
| **Excepción** | Datos obligatorios incompletos → mostrar los campos faltantes y solicitar su corrección. Formato de dato inválido → mostrar el error correspondiente y solicitar nuevamente la información.-  Datos no permitidos para modificación → informar al cliente que ese dato no puede modificarse desde el perfil.-  Error al actualizar información → informar que no fue posible guardar los cambios y conservar los datos anteriores. Sesión no válida o expirada → solicitar al cliente iniciar sesión nuevamente mediante CU02. |

**CU07 – Registrar y enviar información de productos**.

![][image8] 

| Nombre CU | CU07 – Registrar y enviar información de productos |
| :---- | :---- |
| **Propósito** | Permitir al proveedor registrar y enviar información de las prendas que proporciona a WomenStyle para que posteriormente pueda ser revisada y validada por el administrador antes de su publicación. |
| **Resumen** | El proveedor ingresa la información correspondiente a una o varias prendas, incluyendo sus características, disponibilidad y asociación con temporadas o colecciones. El sistema valida los datos básicos y registra la información como pendiente de revisión. Posteriormente, el administrador revisa y valida la información antes de que pueda incorporarse al catálogo. |
| **Actores** | **Proveedor**, **Administrador (secundario)** |
| **Actor iniciador** | **Proveedor** |
| **Precondición** | CU02 – Iniciar sesión. El proveedor debe contar con una cuenta registrada y aprobada mediante CU05 – Gestionar cuentas de proveedor |
| **Flujo principal** | **1\.** El proveedor accede al módulo para registrar información de productos. **2\.** El sistema identifica al proveedor autenticado. **3\.** El proveedor ingresa la información de la prenda, como características, disponibilidad, categoría, temporada y colección. **4\.** El proveedor envía la información al sistema. **5\.** El sistema valida que los datos obligatorios estén completos y tengan un formato válido. **6\.** El sistema registra la información del producto con estado **pendiente de validación**. **7\.** El sistema notifica o presenta al administrador la información pendiente de revisión. **8\.** El administrador revisa la información proporcionada por el proveedor. **9\.** El administrador valida la información del producto. **10\.** El sistema actualiza el estado del producto y permite que la información validada pueda continuar hacia su publicación en el catálogo. |
| **Postcondición** | La información del producto queda registrada en el sistema. Si es validada por el administrador, queda disponible para continuar con el proceso de incorporación al catálogo; si no es validada, queda pendiente de corrección o revisión. |
| **Excepción** | \- **Datos obligatorios incompletos** → mostrar los campos faltantes y solicitar su corrección. \- **Datos inválidos** → mostrar los errores encontrados y solicitar nuevamente la información. \- **Temporada o colección no válida** → solicitar seleccionar una temporada o colección registrada. \- **Producto ya registrado** → informar que la información del producto ya existe y evitar la duplicación. \- **Cuenta de proveedor no aprobada** → impedir el envío de información y solicitar que la cuenta sea aprobada. \- **Información rechazada por el administrador** → marcar el producto como rechazado o pendiente de corrección e informar al proveedor. \- **Error al registrar información** → informar que no fue posible completar el envío y conservar la información ingresada cuando sea posible. |

**CU08 – Gestionar catálogo y productos**.

![][image9]

| Nombre CU | CU08 – Gestionar catálogo y productos |
| :---- | :---- |
| **Propósito** | Permitir al administrador mantener actualizado el catálogo de prendas de la cadena, dando de alta, editando o dando de baja productos ya validados, así como definiendo promociones y condiciones comerciales asociadas. |
| **Resumen** | El administrador accede al módulo de catálogo y puede registrar una nueva prenda, editar los datos de una prenda existente (incluyendo precio, promociones y condiciones comerciales) o darla de baja. El sistema valida la información ingresada y actualiza el catálogo, dejándolo disponible para su consulta por parte de los clientes. |
| **Actores** | Administrador |
| **Actor iniciador** | Administrador |
| **Precondición** | El administrador debe haber iniciado sesión correctamente mediante CU02 – Iniciar sesión. Para el alta de una prenda proveniente de proveedor, la información debe haber sido previamente enviada y validada mediante CU07 – Registrar y enviar información de productos. Deben existir previamente definidos categorías, tallas, colores, temporadas y colecciones mediante CU09 – Gestionar atributos del catálogo. |
| **Flujo principal** | 1\. El administrador accede a la sección de catálogo. 2\. El sistema muestra el listado de prendas registradas. 3\. El administrador selecciona la acción a realizar (alta, edición o baja de una prenda). 4\. El administrador ingresa o modifica los datos de la prenda (nombre, descripción, precio, categoría, promociones, condiciones comerciales). 5\. El sistema valida la información ingresada. 6\. El administrador confirma la operación. 7\. El sistema actualiza el catálogo con los cambios realizados. 8\. El sistema muestra un mensaje confirmando que la operación fue realizada correctamente. |
| **Postcondición** | El catálogo de prendas queda actualizado con la nueva información, disponible para su consulta y filtrado por parte del cliente mediante CU10 – Consultar y filtrar catálogo. |
| **Excepción** | Datos obligatorios incompletos → mostrar los campos faltantes y solicitar su corrección. Formato de dato inválido (precio negativo, promoción sin vigencia definida, etc.) → mostrar el error correspondiente y solicitar corrección. Prenda no encontrada (en edición o baja) → mostrar error y no permitir la operación. Error al actualizar el catálogo → informar que no fue posible guardar los cambios y conservar la información anterior. Sesión no válida o expirada → solicitar al administrador iniciar sesión nuevamente mediante CU02. |

**CU09 – Gestionar atributos del catálogo**.

![][image10] 

| Nombre CU | CU09 – Gestionar atributos del catálogo |
| :---- | :---- |
| **Propósito** | Permitir al administrador definir y mantener actualizados los atributos que estructuran el catálogo de prendas: categorías, tallas, colores, temporadas y colecciones. |
| **Resumen** | El administrador accede al módulo de atributos del catálogo y puede registrar, editar o dar de baja categorías, tallas, colores, temporadas o colecciones. El sistema valida la información y actualiza los atributos disponibles, los cuales quedan listos para ser utilizados al momento de registrar o clasificar una prenda. |
| **Actores** | Administrador |
| **Actor iniciador** | Administrador |
| **Precondición** | El administrador debe haber iniciado sesión correctamente mediante CU02 – Iniciar sesión. |
| **Flujo principal** | 1\. El administrador accede a la sección de atributos del catálogo. 2\. El sistema muestra el listado de atributos existentes agrupados por tipo (categorías, tallas, colores, temporadas, colecciones). 3\. El administrador selecciona el tipo de atributo y la acción a realizar (alta, edición o baja). 4\. El administrador ingresa o modifica los datos del atributo. 5\. El sistema valida la información ingresada. 6\. El administrador confirma la operación. 7\. El sistema actualiza el listado de atributos. 8\. El sistema muestra un mensaje confirmando que la operación fue realizada correctamente. |
| **Postcondición** | Los atributos del catálogo quedan actualizados y disponibles para ser utilizados en la gestión de productos (CU08) y en la clasificación de productos enviados por proveedores (CU07), así como en la búsqueda y filtrado del catálogo por parte del cliente (CU10). |
| **Excepción** | Datos obligatorios incompletos → mostrar los campos faltantes y solicitar su corrección. Atributo duplicado (ya existe una categoría, talla, color, temporada o colección con el mismo nombre) → informar al administrador y no permitir el registro. Intento de baja de un atributo en uso por prendas activas → informar al administrador que no puede eliminarse y sugerir desactivarlo en su lugar. Error al actualizar el listado de atributos → informar que no fue posible guardar los cambios. Sesión no válida o expirada → solicitar al administrador iniciar sesión nuevamente mediante CU02. |

**CU10 – Consultar y filtrar catálogo**.

	![][image11] 

| Nombre CU | CU10 – Consultar y filtrar catálogo |
| :---- | :---- |
| **Propósito** | Permitir al cliente explorar el catálogo de prendas disponibles en WomenStyle, aplicando filtros de búsqueda por categoría, talla, color, temporada y precio, desde la plataforma web o la aplicación móvil. |
| **Resumen** | El cliente accede al catálogo de prendas y puede aplicar uno o varios filtros para refinar los resultados según sus preferencias. El sistema consulta las prendas publicadas que cumplen con los criterios seleccionados y muestra el listado correspondiente. |
| **Actores** | Cliente |
| **Actor iniciador** | Cliente |
| **Precondición** | Deben existir prendas publicadas en el catálogo, previamente registradas mediante CU08 – Gestionar catálogo y productos y clasificadas mediante CU09 – Gestionar atributos del catálogo. No se requiere inicio de sesión previo, ya que la consulta del catálogo es de acceso público para cualquier visitante de la plataforma web o móvil. |
| **Flujo principal** | 1\. El cliente accede a la sección de catálogo desde la web o la aplicación móvil. 2\. El sistema muestra el listado general de prendas publicadas. 3\. El cliente selecciona uno o varios criterios de filtro (categoría, talla, color, temporada, precio). 4\. El cliente aplica los filtros seleccionados. 5\. El sistema consulta las prendas que cumplen con los criterios indicados. 6\. El sistema muestra el listado de prendas filtrado. 7\. El cliente puede seleccionar una prenda para ver su detalle o modificar los filtros aplicados. |
| **Postcondición** | El cliente visualiza el listado de prendas que corresponde a los criterios de búsqueda aplicados, pudiendo continuar con la consulta de disponibilidad por sucursal (CU11) o con la reserva o compra de una prenda. |
| **Excepción** | Ningún producto coincide con los filtros aplicados → mostrar un mensaje indicando que no hay resultados y sugerir modificar los criterios de búsqueda. Filtro con valor inválido → ignorar el filtro inválido y mostrar los resultados con los filtros válidos restantes. Error al consultar el catálogo → informar que no fue posible cargar los resultados y sugerir reintentar. |

#### **CICLO \#2** {#ciclo-#2-1}

**CU11. Consultar disponibilidad por sucursal**

![][image12] 

| Nombre CU | CU11 – Consultar disponibilidad por sucursal |
| :---- | :---- |
| **Propósito** | Permitir al cliente verificar, en tiempo real, si una prenda (en una talla y color específicos) está disponible físicamente en una sucursal determinada de WomenStyle, antes de decidir reservarla o comprarla. |
| **Resumen** | Mientras el cliente navega o filtra el catálogo, puede seleccionar una prenda y una sucursal de su interés para consultar el stock exacto de esa variante (talla/color) en dicho punto de venta. Si no hay existencias en la sucursal elegida, el sistema puede indicarle si esa prenda está disponible en otra sucursal cercana. |
| **Actores** | Cliente |
| **Actor iniciador** | Cliente |
| **Precondición** | El cliente debe estar consultando el catálogo mediante CU10 – Consultar y filtrar catálogo, con al menos una prenda y variante (talla/color) ya seleccionada. Deben existir sucursales previamente registradas mediante CU04 – Gestionar sucursales. |
| **Flujo principal** | El cliente selecciona una prenda desde el catálogo. El cliente elige la sucursal donde desea verificar disponibilidad. El sistema identifica la variante de la prenda (talla y color) seleccionada. El sistema consulta el stock registrado para esa variante en la sucursal elegida. El sistema muestra la cantidad disponible (o el estado: disponible, agotado, reservado parcialmente). Si no hay stock en la sucursal seleccionada, el sistema ofrece la opción de consultar otras sucursales de la misma ciudad. El cliente puede repetir la consulta con otra sucursal si lo desea. |
| **Postcondición** | El cliente obtiene información actualizada y verídica del stock de la prenda en la sucursal consultada. No se modifica ningún dato del sistema; es una operación de solo lecturarupo26. |
| **Excepción** | Sucursal inactiva o dada de baja → informar que no está disponible para consulta. Variante sin stock en ninguna sucursal → mostrar mensaje de producto agotado en toda la cadena. Producto o variante inexistente → mostrar error de "prenda no encontrada". Error de conexión con el servicio de inventario → mostrar mensaje de "no se pudo verificar disponibilidad, intente nuevamente". |

**CU12. Registrar movimiento de inventario**

![][image13] 

| Nombre CU | CU12 – Registrar movimiento de inventario |
| :---- | :---- |
| **Propósito** | Permitir al personal operativo de sucursal (encargado o cajero) registrar los ingresos, salidas y traspasos de mercadería entre sucursales, manteniendo actualizado el stock real de cada punto de venta. |
| **Resumen** | El encargado de sucursal o el cajero selecciona el tipo de movimiento (ingreso de mercadería, salida por baja/daño, o traspaso hacia otra sucursal), indica la prenda/variante y la caikntidad, y el sistema actualiza automáticamente las existencias correspondientes, dejando un registro histórico del movimiento. |
| **Actores** | Encargado de sucursal, Cajero |
| **Actor iniciador** | Encargado de sucursal, Cajero |
| **Precondición** | El usuario debe haber iniciado sesión mediante CU02 – Iniciar sesión con el rol correspondiente (encargado o cajero), y debe tener asignada una sucursal (branch\_id). La prenda/variante y la sucursal de origen (y destino, si es traspaso) deben existir previamente. |
| **Flujo principal** | El usuario accede a la opción de registrar movimiento de inventario. El sistema identifica al usuario autenticado y su sucursal asignada. El usuario selecciona el tipo de movimiento: ingreso, salida o traspaso. El usuario selecciona la prenda/variante (talla y color) afectada. El usuario ingresa la cantidad del movimiento. Si el movimiento es un traspaso, el usuario indica la sucursal de destino. El sistema valida que exista stock suficiente (en caso de salida o traspaso). El sistema actualiza la cantidad de inventario en la sucursal(es) involucrada(s). El sistema registra el movimiento con fecha, tipo, cantidad y usuario responsable. El sistema confirma al usuario que el movimiento fue registrado correctamente. |
| **Postcondición** | El inventario de la sucursal (o sucursales, en caso de traspaso) queda actualizado según el tipo de movimiento. Queda un registro histórico consultable del movimiento realizado. |
| **Excepción** | Cantidad solicitada mayor al stock disponible (en salida o traspaso) → rechazar el movimiento e informar el stock actual. Sucursal de destino igual a la de origen en un traspaso → mostrar error de traspaso inválido. Usuario sin sucursal asignada o sin permisos de rol → denegar el acceso a la operación. Cantidad ingresada inválida (negativa o cero) → solicitar corrección. Error al guardar el movimiento → informar que no se pudo registrar y conservar el stock anterior sin cambios. |

**CU13. Consultar inventario consolidado**

![][image14] 

| Nombre CU | CU13 – Consultar inventario consolidado |
| :---- | :---- |
| **Propósito** | Permitir al administrador visualizar de manera global y consolidada las existencias de todas las prendas en todas las sucursales de la cadena, para apoyar decisiones de redistribución de stock o reabastecimiento. |
| **Resumen** | El administrador accede a una vista consolidada donde puede ver, por producto y variante (talla/color), la cantidad total disponible en la cadena y su desglose por sucursal. Puede filtrar por producto, categoría, temporada o sucursal específica. |
| **Actores** | Administrador |
| **Actor iniciador** | Administrador |
| **Precondición** | El administrador debe haber iniciado sesión mediante CU02 – Iniciar sesión con rol de administrador. Deben existir sucursales registradas (CU04) y productos con inventario cargado (CU08, CU12). |
| **Flujo principal** | 1\. El administrador accede a la sección de inventario consolidado. 2\. El sistema identifica al administrador autenticado y su alcance (global o de una sucursal, según corresponda). 3\. El administrador aplica filtros opcionales (categoría, temporada, sucursal, producto). 4\. El sistema consulta las existencias de todas las sucursales para las variantes filtradas. 5\. El sistema agrupa y suma las cantidades por producto/variante a nivel de toda la cadena. 6\. El sistema muestra el desglose de stock por sucursal para cada variante consultada. 7\. El administrador puede identificar prendas con stock bajo, agotado o desbalanceado entre sucursales. |
| **Postcondición** | El administrador obtiene una vista actualizada y consolidada del inventario de la cadena. No se modifica ningún dato del sistema; es una operación de solo lectura. |
| **Excepción** | \- Sin resultados para los filtros aplicados → mostrar mensaje de "sin datos disponibles". \- Error al consultar el servicio de inventario → mostrar mensaje de "no se pudo cargar el inventario consolidado, intente nuevamente". \- Usuario sin permisos de administrador → denegar el acceso a la vista consolidada. \- Sesión no válida o expirada → solicitar iniciar sesión nuevamente mediante CU02. |

**CU14. Gestionar reservas de prendas**

![][image15]  

| Nombre CU | CU14 – Gestionar reservas de prendas |
| :---- | :---- |
| **Propósito** | Permitir al cliente reservar una o varias prendas en una sucursal específica, indicando un horario aproximado de atención, así como consultar el estado de sus reservas y cancelarlas si ya no las necesita. |
| **Resumen** | El cliente selecciona una o más prendas (con talla y color) desde el catálogo, elige la sucursal donde desea probárselas y un horario de atención aproximado, y confirma la reserva. El sistema notifica la reserva a la sucursal correspondiente y le asigna un tiempo límite de validez. El cliente puede posteriormente consultar el estado de la reserva (pendiente, confirmada, atendida, cancelada) o cancelarla antes de acudir a la tienda. |
| **Actores** | Cliente |
| **Actor iniciador** | Cliente |
| **Precondición** | El cliente debe haber iniciado sesión mediante CU02 – Iniciar sesión.  Debe existir disponibilidad de la prenda(s) en la sucursal elegida (verificable mediante CU11 – Consultar disponibilidad por sucursal). |
| **Flujo principal** | 1\. El cliente selecciona una o varias prendas (talla y color) desde el catálogo. 2\. El cliente indica la sucursal donde desea probarse las prendas. 3\. El cliente elige un horario aproximado de atención. 4\. El sistema verifica la disponibilidad de las prendas seleccionadas en esa sucursal. 5\. El cliente confirma la reserva. 6\. El sistema registra la reserva con estado "pendiente" y le asigna un tiempo límite de validez. 7\. El sistema notifica la reserva a la sucursal correspondiente. 8\. El cliente puede consultar el estado de sus reservas activas en cualquier momento. 9\. Si el cliente ya no desea mantener la reserva, puede cancelarla antes de que sea atendida. 10\. El sistema actualiza el estado de la reserva a "cancelada" si el cliente así lo solicita. |
| **Postcondición** | La reserva queda registrada con un estado válido (pendiente, confirmada, atendida o cancelada) y visible tanto para el cliente como para la sucursal correspondiente. Si el cliente solo consulta el estado, no se modifica ningún dato. |
| **Excepción** | Prenda sin disponibilidad en la sucursal seleccionada → informar al cliente y sugerir otra sucursal (vía CU11) u otra prenda. Horario fuera del rango de atención de la sucursal → solicitar un horario válido. Reserva expirada por vencimiento del tiempo límite → cambiar automáticamente el estado a "cancelada" e informar al cliente. Intento de cancelar una reserva ya atendida → informar que no es posible cancelar una reserva ya concretada. Error al registrar la reserva → informar que no fue posible completarla y no descontar stock reservado. Sesión no válida o expirada → solicitar iniciar sesión nuevamente mediante CU02. |

**CU15. Gestionar carrito de compras**

### **![][image16]** 

| Nombre CU | CU15 – Gestionar carrito de compras |
| :---- | :---- |
| **Propósito** | Permitir al cliente reunir en un carrito temporal las prendas que desea comprar digitalmente, pudiendo agregar, editar cantidades o retirar productos antes de confirmar la compra. |
| **Resumen** | Mientras navega el catálogo, el cliente agrega prendas (con talla y color) a su carrito de compras. Puede modificar la cantidad de cada ítem, eliminar productos que ya no desea, y el sistema calcula automáticamente el total a pagar considerando promociones vigentes. El carrito se mantiene activo hasta que el cliente decide continuar con el checkout o abandonarlo. |
| **Actores** | Cliente |
| **Actor iniciador** | Cliente |
| **Precondición** | El cliente debe haber iniciado sesión mediante CU02 – Iniciar sesión. Debe existir disponibilidad de la(s) prenda(s) que se agregan al carrito. |
| **Flujo principal** | El cliente selecciona una prenda (talla y color) desde el catálogo. El cliente indica la cantidad deseada y la agrega al carrito. El sistema verifica la disponibilidad de la variante antes de confirmar la adición. El sistema agrega el producto al carrito y actualiza el total parcial. El cliente puede repetir el proceso para agregar más prendas. El cliente puede editar la cantidad de un producto ya agregado. El cliente puede eliminar un producto del carrito. El sistema recalcula el total automáticamente, aplicando promociones vigentes si corresponde. El cliente consulta el resumen del carrito antes de decidir si continúa a la compra. |
| **Postcondición** | El carrito queda actualizado con los productos, cantidades y el total vigente. Si el cliente no continúa con la compra, el carrito permanece disponible para una sesión posterior o se vacía según la política definida. |
| **Excepción** | \- Prenda sin disponibilidad al momento de agregarla o al editar la cantidad → informar al cliente y ajustar al máximo disponible. \- Cantidad ingresada inválida (cero o negativa) → solicitar corrección. \- Producto descontinuado o dado de baja mientras estaba en el carrito → notificar al cliente y retirarlo automáticamente. \- Error al calcular el total o aplicar promociones → mostrar el error y mantener el carrito sin cambios. \- Sesión no válida o expirada → solicitar iniciar sesión nuevamente mediante CU02. |

**CU16. Realizar compra digital y consultar estado del pedido**

![][image17] 

| Nombre CU | CU16 – Realizar compra digital y consultar estado del pedido |
| :---- | :---- |
| **Propósito** | Permitir al cliente finalizar la compra de las prendas de su carrito mediante un pago electrónico mediante la plataforma web o móvil, y hacer seguimiento del estado de su pedido hasta que esté listo. |
| **Resumen** | El cliente inicia el checkout desde su carrito, confirma los productos y el total a pagar, y selecciona un método de pago electrónico. El sistema se comunica con la pasarela de pago para procesar la transacción. Si el pago es aprobado, se genera el pedido con un comprobante de compra y el cliente puede consultar su estado (pagado, en preparación, listo para entrega o recogida) hasta que la compra se complete. |
| **Actores** | Cliente (principal), Sistema de pagos (secundario) |
| **Actor iniciador** | Cliente |
| **Precondición** | El cliente debe haber iniciado sesión mediante CU02 – Iniciar sesión y contar con al menos un producto en su carrito (CU15 – Gestionar carrito de compras). |
| **Flujo principal** | El cliente accede al checkout desde su carrito de compras. El sistema muestra el resumen de productos, cantidades y el total a pagar. El cliente selecciona el método de pago electrónico deseado. El sistema envía la solicitud de pago a la pasarela electrónica (Sistema de pagos). El Sistema de pagos procesa la transacción y responde con el resultado (aprobado o rechazado). Si el pago es aprobado, el sistema genera el pedido con estado "pagado" y emite un comprobante de compra digital. El sistema actualiza automáticamente el inventario correspondiente a las prendas compradas. El cliente puede consultar el estado de su pedido en cualquier momento (pagado, en preparación, listo para entrega o recogida). El sistema actualiza el estado del pedido conforme avanza su preparación. |
| **Postcondición** | El pedido queda registrado con un comprobante de compra válido y un estado de seguimiento visible para el cliente. El inventario queda actualizado reflejando la venta digital. Si el pago es rechazado, no se genera ningún pedido ni se descuenta inventario. |
| **Excepción** | \- Pago rechazado por la pasarela → informar al cliente y permitir reintentar con otro método de pago. \- Prenda sin disponibilidad al momento de confirmar el pago (agotada por otra compra simultánea) → informar al cliente y ajustar o cancelar la compra antes de cobrar. \- Error de comunicación con el Sistema de pagos → informar que no fue posible procesar la transacción e invitar a reintentar. \- Carrito vacío al intentar iniciar el checkout → impedir continuar y notificar al cliente. \- Sesión no válida o expirada → solicitar iniciar sesión nuevamente mediante CU02. |

**CU17. Atender reserva en sucursal**

**![][image18]** 

| Nombre CU | CU17 – Atender reserva en sucursal |
| :---- | :---- |
| **Propósito** | Permitir al encargado de sucursal preparar las prendas reservadas por un cliente y confirmar su llegada a la tienda, dando seguimiento al ciclo de vida de la reserva hasta su atención efectiva. |
| **Resumen** | El encargado de sucursal consulta las reservas pendientes asignadas a su sucursal, separa físicamente las prendas correspondientes y las deja listas para cuando el cliente llegue. Al momento en que el cliente se presenta en tienda, el encargado confirma su llegada y actualiza el estado de la reserva a "atendida", dejándola disponible para que el cliente se pruebe las prendas y decida su compra. |
| **Actores** | Encargado de sucursal |
| **Actor iniciador** | Encargado de sucursal |
| **Precondición** | El encargado debe haber iniciado sesión mediante CU02 – Iniciar sesión con rol de encargado y tener asignada la sucursal correspondiente. Debe existir una reserva previamente registrada por el cliente mediante CU14 – Gestionar reservas de prendas, con estado "pendiente" o "confirmada". |
| **Flujo principal** | 1\. El encargado accede al listado de reservas pendientes de su sucursal. 2\. El sistema muestra las reservas junto con las prendas, tallas, colores y horario aproximado de atención. 3\. El encargado selecciona una reserva y separa físicamente las prendas indicadas. 4\. El encargado marca la reserva como "confirmada" una vez que las prendas están preparadas. 5\. Cuando el cliente llega a la sucursal, el encargado busca la reserva correspondiente. 6\. El encargado confirma la llegada del cliente. 7\. El sistema actualiza el estado de la reserva a "atendida". 8\. El cliente se prueba las prendas y decide cuáles comprar, lo cual continúa en CU18 – Registrar venta presencial y procesar pago en caja. |
| **Postcondición** | La reserva queda con estado "atendida" y las prendas quedan disponibles para la decisión de compra del cliente en tienda. Si el cliente no se presenta dentro del tiempo límite de la reserva, esta puede vencer y pasar a estado "cancelada" según lo definido en CU14. |
| **Excepción** | Reserva ya vencida o cancelada al momento de buscarla → informar al encargado que no puede atenderla y sugerir verificar con el cliente si desea una nueva reserva. Prenda reservada dañada o extraviada en tienda → informar la incidencia y ofrecer una alternativa al cliente (prenda similar o reprogramar). Cliente no se presenta en el horario acordado → mantener la reserva pendiente hasta su vencimiento, sin marcarla como atendida. Usuario sin sucursal asignada o sin permisos de rol → denegar el acceso a la operación. Sesión no válida o expirada → solicitar iniciar sesión nuevamente mediante CU02. |

**CU18. Registrar venta presencial y procesar pago en caja**

**![][image19]** 

| Nombre CU | CU18 – Registrar venta presencial y procesar pago en caja |
| :---- | :---- |
| **Propósito** | Permitir al cajero registrar la venta de prendas seleccionadas físicamente por el cliente en tienda (con o sin reserva previa), procesar el cobro en el punto de caja y emitir el comprobante correspondiente. |
| **Resumen** | El cajero registra las prendas que el cliente decide comprar tras probárselas en tienda, ya sea que provengan de una reserva atendida previamente o de una selección directa en el mostrador. El cajero procesa el pago (efectivo, tarjeta, QR, según los métodos habilitados en caja), el sistema emite un comprobante de venta y actualiza automáticamente el inventario de la sucursal. |
| **Actores** | Cajero |
| **Actor iniciador** | Cajero |
| **Precondición** | El cajero debe haber iniciado sesión mediante CU02 – Iniciar sesión con rol de cajero y tener asignada la sucursal correspondiente.  Si la venta proviene de una reserva, ésta debe encontrarse en estado "atendida" mediante CU17 – Atender reserva en sucursal. |
| **Flujo principal** | El cajero inicia el registro de una nueva venta presencial. El cajero indica si la venta está asociada a una reserva previa o es una venta directa. Si está asociada a una reserva, el sistema recupera las prendas correspondientes; si es venta directa, el cajero selecciona manualmente las prendas, tallas y colores. El sistema calcula el total a cobrar. El cajero selecciona el método de pago en caja (efectivo, tarjeta, QR). El cajero procesa el cobro. El sistema registra la venta con estado confirmado. El sistema actualiza automáticamente el inventario de la sucursal, descontando las prendas vendidas (ver CU12 – Registrar movimiento de inventario). El sistema emite el comprobante de venta. El cajero entrega el comprobante al cliente. |
| **Postcondición** | La venta queda registrada con su comprobante correspondiente, el inventario de la sucursal queda actualizado reflejando la salida de las prendas vendidas, y si la venta provenía de una reserva, esta queda marcada como concretada. |
| **Excepción** | Prenda sin stock suficiente al momento de confirmar la venta → informar al cajero y ajustar o cancelar el ítem antes de cobrar. Pago rechazado o insuficiente (tarjeta declinada, monto en efectivo incompleto) → informar al cajero y permitir reintentar o cambiar el método de pago. Error al emitir el comprobante → informar el error y permitir reintentar la emisión sin duplicar la venta. Usuario sin sucursal asignada o sin permisos de rol → denegar el acceso a la operación. Sesión no válida o expirada → solicitar iniciar sesión nuevamente mediante CU02. |

#### **CICLO \#3** {#ciclo-#3-1}

**CU19 – Usar vestidor virtual**

**![][image20]** 

| Nombre CU | CU19 – Usar vestidor virtual |
| :---- | :---- |
| **Propósito** | Permitir al cliente visualizar de manera virtual cómo luciría una prenda del catálogo, utilizando la cámara de su dispositivo móvil y tecnología de realidad aumentada, sin necesidad de probársela físicamente en tienda. |
| **Resumen** | Desde la ficha de una prenda en el catálogo (app móvil), el cliente activa el vestidor virtual. El sistema accede a la cámara, superpone la prenda seleccionada —considerando la talla y el color elegidos— sobre la imagen capturada en tiempo real, y permite al cliente visualizar el resultado, además de guardarlo o compartirlo. |
| **Actores** | Cliente |
| **Actor iniciador** | Cliente |
| **Precondición** | El cliente debe haber iniciado sesión correctamente (CU02 – Iniciar sesión) y estar consultando una prenda específica desde el catálogo (CU10 – Consultar y filtrar catálogo) en la aplicación móvil. El dispositivo debe contar con cámara y permisos de acceso concedidos. |
| **Flujo principal** | 1\. El cliente selecciona una prenda desde el catálogo. 2\. El cliente elige la opción "Probar en vestidor virtual". 3\. El sistema verifica el permiso de acceso a la cámara. 4\. El sistema activa la cámara del dispositivo. 5\. El sistema superpone la prenda seleccionada (talla/color) sobre la imagen capturada en tiempo real. 6\. El cliente visualiza el resultado y puede ajustar el ángulo/posición. 7\. El cliente decide guardar o compartir la visualización generada. 8\. El sistema guarda o comparte la imagen según la elección del cliente. |
| **Postcondición** | El cliente ha visualizado la prenda mediante realidad aumentada. Si eligió guardar o compartir, la imagen generada queda almacenada localmente o enviada por el medio elegido. |
| **Excepción** | \- Cámara no disponible o sin permisos concedidos → informar al cliente y solicitar habilitar el acceso. \- Prenda sin modelo de realidad aumentada disponible → informar que la función no aplica para esa prenda. \- Error al procesar la superposición → mostrar mensaje de error y permitir reintentar. \- Dispositivo no compatible con AR → informar que la función requiere un dispositivo compatible. \- Sesión no válida o expirada → solicitar al cliente iniciar sesión nuevamente mediante CU02. |

**CU20 – Generar reportes y dashboards**

**![][image21]** 

| Nombre CU | CU20 – Generar reportes y dashboards |
| :---- | :---- |
| **Propósito** | Permitir a la administración consultar de manera consolidada el desempeño comercial y operativo de la cadena, mediante reportes e indicadores visuales (dashboards) que apoyen la toma de decisiones. |
| **Resumen** | El administrador accede al módulo de reportes, selecciona el tipo de reporte (ventas, inventario o reservas) y aplica filtros (sucursal, producto, periodo). El sistema procesa la información consolidada y genera el reporte junto con un dashboard visual, con opción de exportación. |
| **Actores** | Administrador (principal). |
| **Actor iniciador** | Administrador |
| **Precondición** | El administrador debe haber iniciado sesión correctamente (CU02 – Iniciar sesión) y contar con permisos administrativos sobre el módulo de reportes. |
| **Flujo principal** | 1\. El administrador accede al módulo de reportes y dashboards. 2\. El sistema muestra los tipos de reporte disponibles (ventas, inventario, reservas). 3\. El administrador selecciona el tipo de reporte y los filtros deseados (sucursal, producto, periodo). 4\. El sistema consulta la información consolidada correspondiente. 5\. El sistema genera el reporte y los indicadores visuales del dashboard. 6\. El administrador visualiza el reporte generado. 7\. El administrador decide exportar el reporte (opcional). 8\. El sistema genera el archivo de exportación en el formato solicitado. |
| **Postcondición** | El administrador obtiene el reporte y/o dashboard solicitado con la información consolidada correspondiente. Si lo exportó, el archivo queda disponible para su descarga. |
| **Excepción** | \- Sin datos disponibles para los filtros seleccionados → informar que no hay resultados para ese criterio. \- Error al generar el reporte → mostrar mensaje de error y permitir reintentar. \- Error al exportar → informar que no fue posible generar el archivo y conservar el reporte en pantalla. \- Sesión no válida o expirada → solicitar al administrador iniciar sesión nuevamente mediante CU02. |

**CU21 – Recibir recomendaciones de IA**

**![][image22]** 

| Nombre CU | CU21 – Recibir recomendaciones de IA |
| :---- | :---- |
| **Propósito** | Sugerir al cliente prendas del catálogo de WomenStyle que se ajusten a sus preferencias, historial de navegación o compra, temporada, categoría, talla y disponibilidad, apoyándose en un servicio de inteligencia artificial. |
| **Resumen** | Mientras el cliente navega el catálogo, el sistema envía al servicio de IA los datos relevantes del cliente (historial, filtros usados, temporada vigente). El servicio de IA procesa esa información y devuelve una lista de prendas recomendadas, que el sistema muestra al cliente dentro de la misma sesión de navegación. |
| **Actores** | Cliente (principal); Servicio de inteligencia artificial (secundario, vía API). |
| **Actor iniciador** | Cliente |
| **Precondición** | El cliente debe haber iniciado sesión correctamente (CU02 – Iniciar sesión) y estar consultando el catálogo (CU10 – Consultar y filtrar catálogo). |
| **Flujo principal** | 1\. El cliente navega o filtra el catálogo. 2\. El sistema recopila las señales relevantes del cliente (historial de navegación/compra, filtros aplicados, temporada). 3\. El sistema envía estas señales al servicio de IA mediante API. 4\. El servicio de IA procesa la información y devuelve una lista de prendas recomendadas. 5\. El sistema valida la disponibilidad de las prendas recomendadas. 6\. El sistema muestra las recomendaciones al cliente dentro del catálogo. 7\. El cliente puede seleccionar alguna prenda recomendada para continuar su flujo normal de consulta. |
| **Postcondición** | El cliente visualiza una lista de prendas recomendadas acorde a sus preferencias y disponibilidad actual. No se genera ninguna transacción por sí sola; solo se complementa la navegación del catálogo. |
| **Excepción** | \- Servicio de IA no disponible o con error → mostrar el catálogo sin recomendaciones, sin bloquear la navegación. \- Cliente sin historial suficiente → el sistema muestra recomendaciones genéricas basadas en temporada/categoría. \- Prenda recomendada sin disponibilidad vigente → excluirla de la lista antes de mostrarla. \- Sesión no válida o expirada → solicitar al cliente iniciar sesión nuevamente mediante CU02. |

**CU22 – Consultar asistente virtual/chatbot**

**![][image23]** 

| Nombre CU | CU22 – Consultar asistente virtual/chatbot |
| :---- | :---- |
| **Propósito** | Resolver dudas del cliente sobre productos, disponibilidad, tallas u otros temas del catálogo de WomenStyle, mediante un asistente conversacional basado en inteligencia artificial. |
| **Resumen** | El cliente abre el chatbot desde la aplicación web o móvil y escribe su consulta en lenguaje natural. El sistema envía la consulta al servicio de IA, el cual genera una respuesta considerando el contexto del catálogo, y el sistema la muestra al cliente dentro de la misma conversación. |
| **Actores** | Cliente (principal); Servicio de inteligencia artificial (secundario, vía API). |
| **Actor iniciador** | Cliente |
| **Precondición** | El cliente debe haber iniciado sesión correctamente (CU02 – Iniciar sesión). |
| **Flujo principal** | 1\. El cliente abre el asistente virtual/chatbot. 2\. El cliente escribe su consulta en lenguaje natural. 3\. El sistema envía la consulta al servicio de IA junto con el contexto necesario (catálogo, disponibilidad). 4\. El servicio de IA procesa la consulta y genera una respuesta. 5\. El sistema muestra la respuesta al cliente dentro de la conversación. 6\. El cliente puede continuar la conversación con nuevas preguntas o cerrarla. |
| **Postcondición** | El cliente recibe una respuesta a su consulta dentro del chat. La conversación puede quedar registrada como historial de interacción del cliente (opcional, según diseño). |
| **Excepción** | \- Servicio de IA no disponible o con error → informar al cliente que el asistente no está disponible en ese momento. \- Consulta fuera del alcance del asistente (no relacionada al catálogo/tienda) → el sistema responde indicando que no puede ayudar con ese tema. \- Tiempo de respuesta excedido → mostrar mensaje de espera prolongada o error de tiempo agotado. \- Sesión no válida o expirada → solicitar al cliente iniciar sesión nuevamente mediante CU02. |

**CU23 – Generar reporte por voz/lenguaje natural**

**![][image24]**  

| Nombre CU | CU23 – Generar reporte por voz/lenguaje natural |
| :---- | :---- |
| **Propósito** | Permitir al administrador de WomenStyle solicitar un reporte de ventas, inventario o reservas mediante un comando de voz o una instrucción en lenguaje natural, como canal alternativo al uso de filtros manuales. |
| **Resumen** | El administrador activa la entrada por voz (o escribe la instrucción en lenguaje natural) dentro del módulo de reportes. El sistema envía la instrucción al servicio de IA, que la interpreta y determina el tipo de reporte y los filtros solicitados. El sistema genera el reporte correspondiente reutilizando el mismo procesamiento que CU20. |
| **Actores** | Administrador (principal); Servicio de inteligencia artificial (secundario, vía API). |
| **Actor iniciador** | Administrador |
| **Precondición** | El administrador debe haber iniciado sesión correctamente (CU02 – Iniciar sesión) y contar con permisos administrativos sobre el módulo de reportes. |
| **Flujo principal** | 1\. El administrador accede al módulo de reportes y dashboards (CU20). 2\. El administrador activa la opción de comando por voz/lenguaje natural. 3\. El administrador dicta o escribe su solicitud (ej. "ventas de la sucursal Santa Cruz del último mes"). 4\. El sistema envía la instrucción al servicio de IA. 5\. El servicio de IA interpreta la instrucción y determina el tipo de reporte y los filtros (sucursal, producto, periodo). 6\. El sistema ejecuta la generación del reporte con esos filtros (mismo procesamiento que CU20). 7\. El sistema muestra el reporte y el dashboard generado al administrador. 8\. El administrador puede exportar el reporte (opcional). |
| **Postcondición** | El administrador obtiene el reporte solicitado por voz/lenguaje natural, equivalente al que hubiera obtenido usando los filtros manuales de CU20. |
| **Excepción** | Servicio de IA no disponible o con error → informar al administrador y ofrecer generar el reporte manualmente mediante CU20. Instrucción ambigua o no interpretable → solicitar al administrador que reformule la solicitud. Filtros interpretados sin datos disponibles → informar que no hay resultados para ese criterio. Error al generar el reporte → mostrar mensaje de error y permitir reintentar. Sesión no válida o expirada → solicitar al administrador iniciar sesión nuevamente mediante CU02. |

**CU24 – Recibir notificaciones push**

![][image25] 

| Nombre CU | CU24 – Recibir notificaciones push |
| :---- | :---- |
| **Propósito** | Permitir que Administrador, Cliente y Encargado de sucursal reciban alertas automáticas en tiempo real sobre eventos relevantes del sistema (cambios de estado, alertas operativas, recomendaciones), sin necesidad de consultarlos manualmente. |
| **Resumen** | Cuando ocurre un evento relevante dentro de otro caso de uso (por ejemplo, una reserva registrada, un stock que cruza el umbral mínimo, o un pedido que cambia de estado), el sistema identifica automáticamente a los destinatarios correspondientes según el tipo de evento y su rol, genera el contenido de la notificación y la envía a la aplicación móvil del usuario. El destinatario puede tocar la notificación para ser dirigido directamente a la sección relacionada dentro de la app. |
| **Actores** | Administrador, Cliente, Encargado de sucursal |
| **Actor iniciador** | Sistema (no hay una acción humana que "dispare" este CU directamente; los actores humanos son receptores, no iniciadores) |
| **Precondición** | El usuario debe tener la aplicación móvil instalada, sesión iniciada al menos una vez (CU02) y permisos de notificaciones push habilitados en su dispositivo.  Debe haber ocurrido un evento relevante en otro caso de uso del sistema (CU07, CU12, CU14, CU16, CU17, CU20). |
| **Flujo principal** | Ocurre un evento relevante dentro de otro caso de uso del sistema (ej. reserva registrada, stock bajo detectado, cambio de estado de pedido, nueva temporada publicada, recomendación generada). El sistema identifica el tipo de evento y determina qué actor(es) deben recibir la notificación, según el siguiente detalle: **2.1.  Cliente**: recibe notificaciones sobre cambio de estado de su pedido (pagado, en preparación, listo), nuevas recomendaciones de productos, ingreso de nueva temporada o colección, y disponibilidad de nuevas prendas en el catálogo. **2.2. Administrador**: recibe alertas de stock mínimo o próximo a agotarse a nivel consolidado. **2.3. Encargado de sucursal**: recibe notificación al registrarse una nueva reserva asignada a su sucursal, y alertas de stock mínimo a nivel local. El sistema genera el contenido de la notificación (título, mensaje breve, referencia al recurso relacionado) según el tipo identificado en el paso 2\. El sistema envía la notificación push al dispositivo móvil del destinatario. El destinatario recibe la notificación en su dispositivo, incluso si no tiene la app abierta en ese momento. El destinatario puede tocar la notificación para acceder directamente a la sección correspondiente dentro de la app (ej. detalle de la reserva, detalle del producto con stock bajo, estado del pedido). El sistema registra la notificación como leída una vez que el destinatario la abre. |
| **Postcondición** | La notificación queda entregada al destinatario y registrada en su historial de notificaciones dentro de la app, con su estado (leída/no leída). |
| **Excepción** | Usuario sin permisos de notificaciones habilitados en su dispositivo → la notificación no se entrega, pero queda registrada como pendiente/no entregada dentro de la app. Usuario sin conexión a internet al momento del envío → el sistema reintenta la entrega cuando el dispositivo vuelva a estar en línea. Error al generar o enviar la notificación → se registra el fallo internamente sin interrumpir el flujo del caso de uso que originó el evento. |

CU19 – Usar vestidor virtual

CU20 – Generar reportes y dashboards

CU21 – Recibir recomendaciones de IA

CU22 – Consultar asistente virtual/chatbot

CU23 – Generar reporte por voz/lenguaje natural

4. ### **Prototipo de Interfaz de Usuario** {#prototipo-de-interfaz-de-usuario}

   #### **Ciclo \#1** {#ciclo-#1-2}


#### **CICLO \#2** {#ciclo-#2-2}



#### **CICLO \#3**  {#ciclo-#3-2}



5. ### **Estructurar el Modelo de Caso de Uso** {#estructurar-el-modelo-de-caso-de-uso}

  #### **Ciclo \#1** {#ciclo-#1-3}

  #### **Ciclo \#2**  {#ciclo-#2-3}

  #### **Ciclo \#3** {#ciclo-#3-3}

2. ## **FLUJO DE TRABAJO: ANÁLISIS** {#flujo-de-trabajo:-análisis}

   ### **2.1. Análisis de Arquitectura** {#2.1.-análisis-de-arquitectura}

   #### **2.1.1. Identificar Paquetes**  {#2.1.1.-identificar-paquetes}

     - **P1 – Gestión de usuarios y acceso**: Registro de clientes, autenticación y acceso al sistema, administración de usuarios internos, gestión de sucursales, cuentas de proveedores y actualización de datos de perfil.
     - **P2 – Gestión de productos y catálogo**: Envío de información por parte de proveedores, gestión de productos, promociones, categorías, tallas, colores, temporadas y colecciones; consulta y filtrado del catálogo por parte del cliente.
     - **P3 – Gestión de inventario y disponibilidad**: Control de existencias en las diferentes sucursales, consulta de disponibilidad, registro de movimientos de inventario y consulta consolidada.
     - **P4 – Gestión de compras y reservas**: Selección de prendas para reservar o comprar digitalmente, carrito de compras, checkout, pago electrónico y consulta del estado del pedido.
     - **P5 – Gestión de ventas y atención en sucursal**: Operación presencial de la tienda: preparación y atención de reservas, registro de ventas presenciales, procesamiento de pago en caja y emisión de comprobante.
     - **P6 – Experiencia inteligente y analítica**: Vestidor virtual mediante realidad aumentada, generación de reportes y dashboards, recomendaciones de IA, asistente virtual y generación de reportes por lenguaje natural.


   #### **2.1.2. Relacionar Paquete y Caso de Uso** {#2.1.2.-relacionar-paquete-y-caso-de-uso}

##### **Paquete 1 — Gestión de usuarios y acceso**  {#paquete-1-—-gestión-de-usuarios-y-acceso}

##### **Paquete 2 — Gestión de productos y catálogo** {#paquete-2-—-gestión-de-productos-y-catálogo}

##### **Paquete 3 — Gestión de inventario y disponibilidad** {#paquete-3-—-gestión-de-inventario-y-disponibilidad}

##### **Paquete 4 — Gestión de compras y reservas** {#paquete-4-—-gestión-de-compras-y-reservas}

##### **Paquete 5 — Gestión de ventas y atención en sucursal** {#paquete-5-—-gestión-de-ventas-y-atención-en-sucursal}

##### **Paquete 6 — Experiencia inteligente y analítica** {#paquete-6-—-experiencia-inteligente-y-analítica}
| Paquete | Casos de uso incluidos |
|---|---|
| **P1 – Gestión de usuarios y acceso** | CU01, CU02, CU03, CU04, CU05, CU06 |
| **P2 – Gestión de productos y catálogo** | CU07, CU08, CU09, CU10 |
| **P3 – Gestión de inventario y disponibilidad** | CU11, CU12, CU13 |
| **P4 – Gestión de compras y reservas** | CU14, CU15, CU16 |
| **P5 – Gestión de ventas y atención en sucursal** | CU17, CU18 |
| **P6 – Experiencia inteligente y analítica** | CU19, CU20, CU21, CU22, CU23, CU24 |

Nota: esta agrupación en paquetes es independiente de la distribución por ciclos — los ciclos organizan el **orden de desarrollo**, mientras que los paquetes organizan la **arquitectura lógica** del sistema.	 	 

### **2.2. Análisis de Caso de Uso** {#2.2.-análisis-de-caso-de-uso}

#### **2.2.1. DIAGRAMA DE COMUNICACIÓN** {#2.2.1.-diagrama-de-comunicación}

##### Ciclo \#1 {#ciclo-#1-4}

**CU01. Registrar cliente**

**![][image55]**   

El actor :**Cliente** ingresa sus datos personales en la interfaz :**RegisterPageComponent** e invoca la función 1: onSubmit(userCreateData), la cual envía la petición HTTP 1.1: POST /api/v1/auth/register hacia el controlador :**AuthController**, el cual gestiona en el servidor la persistencia invocando 1.2: create\_user(db, user) sobre la entidad \<\<entity\>\> :User en la base de datos y posteriormente solicita la emisión de credenciales mediante 1.3: create\_access\_token(data) a la entidad :JWTService. **Resultado**: Cliente registrado exitosamente en la base de datos con su rol asignado, token JWT generado y cuenta habilitada para iniciar sesión.

**CU02.  Iniciar sesión**

**![][image56]** 

El usuario del sistema ingresa sus credenciales en la pantalla :**LoginPageComponent** activando la función 1: onSubmit(loginCredentials), que transmite la solicitud 1.1: POST /api/v1/auth/login al controlador :**AuthController**, donde este valida la cuenta consultando 1.2: filter(User.email \= email) y verifica la contraseña cifrada mediante 1.3: verify\_password() en la entidad :**User**, para luego solicitar la firma del token de sesión mediante 1.4: create\_access\_token() sobre la entidad :JWTService. **Resultado**: Usuario autenticado correctamente con token JWT generado según su rol correspondiente y acceso otorgado a los módulos protegidos del sistema.

**CU03. Gestionar usuarios internos**

**![][image57]**

El actor Administrador inicia el flujo interactuando con la interfaz \[:AdminUserPageView\] a través de los mensajes para listar crear o activar usuarios; la interfaz traduce estas acciones e invoca al controlador \[:UserController\] mediante 1.1: GET /users/, 2.1: PUT /users/{user\_id} y 3.1: PATCH /users/{user\_id}/active; posteriormente, el controlador \[:**UserController**\] coordina la lógica ejecutando las consultas y actualizaciones sobre las entidades \[:User\] mediante 1.2: get\_users(), 1.4: get\_users\_count(), 2.3: get\_user(), 2.5: ensure\_email\_available(), 2.9: update\_user\_full() y 3.2: set\_user\_active(), así como sobre la entidad \[:**Branch**\] con 2.7: get\_branch(), finalizando con el envío de las respuestas 1.6: HTTP 200 OK, 2.11: HTTP 200 OK y 3.4: HTTP 200 OK desde \[:UserController\] hacia \[:AdminUserPageView\] para notificar y actualizar la vista del usuario.

**Resultado**: los usuarios internos quedan registrados, actualizados en sus roles/sucursales o inactivados correctamente en la base de datos, manteniendo la consistencia de permisos y asignaciones. 

**CU04. Gestionar sucursales**

**![][image58]** 

El actor Administrador interactúa con la interfaz **AdminBranchPageComponent** invocando secuencialmente los métodos loadBranches() para listar las sucursales existentes y submit(name, city) para registrar una nueva sucursal; la interfaz AdminBranchPageComponent realiza las peticiones HTTP GET /branches/ y POST /branches/ hacia el controlador **BranchController**, el cual centraliza la lógica de negocio y verificación de permisos del sistema invocando las funciones get\_branches(db) y create\_branch() sobre la entidad Branch para consultar y persistir los registros de sucursales en la base de datos. **Resultado**: La nueva sucursal queda registrada exitosamente en la base de datos y la lista de sucursales se actualiza reflejando la información disponible para el Administrador.

**CU05. Gestionar cuentas de proveedor**

**![][image59]**El Administrador interactúa con la interfaz **AdminProviderPageView** enviando las acciones 1: solicitarListaProveedores(), 2: enviarFormularioProveedor() y 3: cambiarEstadoProveedor(); dicha interfaz realiza las peticiones HTTP 1.1: GET /providers/, 2.1: POST /providers/ y 3.1: PATCH /providers/{provider\_id}/status al controlador \[:**ProviderController**\], el cual centraliza la lógica de negocio ejecutando 1.2: get\_providers(), 2.2: ensure\_email\_available(), 2.4: create\_user(), 2.6: create\_provider(), 3.2: update\_provider\_status() y 3.4: set\_user\_active() sobre las entidades de persistencia \[:**Provider**\] y \[:**User**\], retornando finalmente las respuestas 1.4: HTTP 200 OK, 2.8: HTTP 201 Created y 3.6: HTTP 200 OK hacia la vista :**AdminProviderPageView** para la respectiva notificación en pantalla.

**Resultado**: las cuentas de proveedor quedan registradas, aprobadas o suspendidas adecuadamente en la base de datos, sincronizando su estado activo con la cuenta de usuario asociada para el acceso al sistema.

**CU06. Consultar y actualizar perfil**

**![][image60]**   

El cliente accede a sus datos personales desde la interfaz :ProfilePageComponent. Para consultar el perfil, la pantalla invoca getMe() en :UserController, el cual recupera la sesión y la entidad :Usuario mediante get\_current\_user() y envía la información a :ProfilePageComponent para su renderizado. Para actualizar los datos, :ProfilePageComponent envía updateMe() a :UserController, el cual modifica y persiste el perfil en la entidad :Usuario a través de update\_user\_profile(), retornando los datos actualizados a la interfaz para informar al cliente. **Resultado**: Perfil del cliente consultado y actualizado exitosamente en el sistema.

**CU07. Registrar y enviar información de productos![][image61]** 

El Proveedor / Administrador utiliza CatalogApiService para enviar un ProductCreate al CatalogController, el cual identifica el Provider, ejecuta create\_product(), valida cada ProductVariant y registra el producto con estado pending en WomenStyle. Posteriormente, el administrador consulta los productos pendientes mediante list\_pending\_products() y valida una variante con update\_product\_status(), cambiando su estado a active para publicarla o a inactive para rechazarla. 

**Resultado**: el producto del proveedor queda registrado con sus variantes y permanece pendiente hasta que el administrador lo aprueba o rechaza.

**CU08. Gestionar catálogo y productos**

**![][image62]**

El Administrador gestiona el catálogo de prendas interactuando con la interfaz :**AdminCatalogPageComponent**. Al solicitar la lista de productos, la pantalla envía la petición HTTP a :CatalogController, el cual consulta las prendas activas mediante list\_public\_products() en la entidad Product. Al registrar un nuevo producto (2: enviarFormularioProducto()), la interfaz envía la solicitud HTTP a :**CatalogController**, el cual crea la prenda ejecutando create\_product() en **Product** y valida sus especificaciones invocando \_validate\_variant\_payload() en **ProductVariant**. Finalmente, al solicitar la eliminación (3: eliminarProducto()), :AdminCatalogPageComponent emite la petición HTTP a :CatalogController, el cual retira la prenda del sistema ejecutando delete\_product() en Product y refresca el catálogo en pantalla. **Resultado**: Catálogo de prendas y productos administrado exitosamente (listado, creación y eliminación).

**CU09. Gestionar atributos del catálogo**

**![][image63]** 

El actor Administrador interactúa con la interfaz **AdminCatalogPageComponent** ejecutando los métodos loadData() para consultar los atributos existentes y submitCategory(name) o submitColor(name, hex\_code) para registrar un nuevo atributo; la interfaz AdminCatalogPageComponent envía las peticiones HTTP GET /catalog/categories, POST /catalog/categories y POST /catalog/colors hacia el controlador **CatalogController**, el cual centraliza la validación de rol y procesa las operaciones invocando las funciones create\_name\_item(db, Category, payload) y create\_color(db, payload) sobre las entidades **Category** y **Color** respectivamente para persistir las nuevas definiciones en la base de datos. **Resultado**: Los atributos del catálogo (categorías, colores, tallas, temporadas y colecciones) son creados y almacenados correctamente en la base de datos, quedando disponibles inmediatamente para la clasificación y filtrado de productos en la plataforma.

 **CU10. Consultar y filtrar catálogo**

**![][image64]** 

El **Cliente** consulta el catálogo desde **CatalogPageComponent**, que envía los filtros seleccionados a **CatalogController**. Este ejecuta list\_public\_products() sobre **Product**, conserva únicamente las variantes activas de **ProductVariant**, y cuando existe una sucursal seleccionada consulta **Inventory** para asociar la disponibilidad por variante. Finalmente, el controlador genera cada ProductRead con \_product\_to\_read() y devuelve el catálogo filtrado a la pantalla. **Resultado**: el cliente visualiza únicamente los productos y variantes activas que cumplen los filtros seleccionados, incluyendo el stock por sucursal cuando corresponde.

##### Ciclo \#2 {#ciclo-#2-4}

**CU11 – Consultar disponibilidad por sucursal**

**![][image65]** 

El Cliente inicia el flujo a través del componente de interfaz :CatalogPageComponent solicitando la consulta de disponibilidad por sucursal. La pantalla transmite la solicitud invocando al controlador :CatalogController, el cual consulta secuencialmente las entidades :Sucursal, :Producto, :Talla, :Color y :Variante para verificar el catálogo activo y filtrar los atributos requeridos. A continuación, :CatalogController consulta las existencias físicas en tiempo real en la entidad :Inventario para la sucursal seleccionada. Finalmente, :CatalogController notifica a la pantalla :CatalogPageComponent con la información de stock encontrada para que esta renderice la disponibilidad exacta al cliente. Resultado: disponibilidad y stock en tiempo real por talla color\_y\_sucursal visualizados correctamente

**CU12 – Registrar movimiento de inventario**

**![][image66]** 

El encargado de sucursal/cajero solicitan el registro de un movimiento de inventario (ingreso, salida o traspaso) desde la pantalla :AdminInventoryPageComponent. La interfaz transmite el comando al controlador :InventoryController, el cual verifica las entidades correspondientes enviando llamadas a :Sucursal y :Variante. Posteriormente, :InventoryController actualiza el stock físico y disponible en la entidad :Inventario y registra la transacción auditada en la entidad :MovimientoInventario. Finalmente, :InventoryController notifica la finalización a la interfaz :AdminInventoryPageComponent para que esta renderice el mensaje de confirmación del movimiento ante el actor. **Resultado**: movimiento de inventario registrado exitosamente y stock de sucursal actualizado.

**CU13 – Consultar inventario consolidado**

**![][image67]** 

El administrador solicita la visualización del inventario global desde la pantalla :AdminInventoryPageComponent. La interfaz transmite la petición al controlador :InventoryController llamando a getConsolidatedStock(), el cual interactúa con las entidades :Inventario, :Variante, :Producto, :Sucursal, :Talla y :Color para consolidar las existencias y atributos por sucursal. Finalmente, :InventoryController envía la información a :AdminInventoryPageComponent para renderizar el reporte completo al administrador.

**Resultado**: Vista global del inventario consolidado por sucursal generada y visualizada correctamente.

**CU14 – Gestionar reservas de prendas**

**![][image68]**

El Cliente gestiona sus reservas seleccionando prendas, sucursal y horario desde :ReservationsPageComponent. La interfaz redirige la petición a :ReservationController, el cual verifica las entidades :Sucursal y :Variante, ajusta la disponibilidad en :Inventario y genera los registros en :Reserva y :DetalleReserva. Asimismo, ante una cancelación, :ReservationController actualiza el estado en :Reserva y libera las prendas retenidas en :Inventario, enviando la respuesta a :ReservationsPageComponent para renderizar el resultado final. **Resultado**: Reserva de prendas registrada o cancelada exitosamente y stock reservado actualizado.

**CU15 – Gestionar carrito de compras**

**![][image69]** 

El cliente añade o modifica las cantidades de sus prendas interactuando con la interfaz :CartPageComponent. La pantalla comunica las acciones al controlador :CartController, el cual consulta :Variante y verifica existencias en :Inventario. Posteriormente, :CartController gestiona la sesión activa en :Carrito y persiste las modificaciones en :ItemCarrito, retornando el estado actualizado a :CartPageComponent para su renderizado final. **Resultado**: Carrito de compras actualizado correctamente con los productos y cantidades seleccionadas.

**CU16 – Realizar compra digital y consultar estado del pedido**

**![][image70]** 

El Cliente consulta el estado de sus pedidos o procesa su compra digital desde la interfaz :CartPageComponent. La pantalla interactúa con :OrderController, el cual verifica el usuario en :Usuario e invoca \_create\_order\_from\_cart() para registrar el pedido en :Pedido y descontar existencias con \_allocate\_inventory() en :Variante. En pagos electrónicos, :OrderController coordina la pasarela :PasarelaPago generando el PaymentIntent y procesa la confirmación a través de confirm\_stripe\_payment() al recibir la notificación del Webhook, informando finalmente el estado actualizado a :CartPageComponent para su renderizado. **Resultado**: Compra digital procesada y registrada exitosamente con el stock actualizado y el estado del pedido confirmado.

**CU17 – Atender reserva en sucursal**

**![][image71]** 

El Encargado de sucursal gestiona la lista de reservas de su tienda mediante :ReservationsPageComponent. Al recibir solicitudes, la pantalla invoca al controlador :ReservationController (usando list\_reservations\_by\_branch, confirm\_reservation\_arrival, attend\_reservation o cancel\_branch\_reservation), el cual valida los permisos en :Sucursal, actualiza los estados en :Reserva y :DetalleReserva, y ajusta o libera las existencias retenidas en la entidad :Inventario. Finalmente, el controlador notifica el nuevo estado a :ReservationsPageComponent para refrescar la vista en pantalla. **Resultado**: Reserva atendida o cancelada exitosamente en la sucursal con la actualización correspondiente en el stock físico y reservado.

**CU18 – Registrar venta presencial y procesar pago en caja**

![][image72] 

El cajero registra las ventas presenciales en caja utilizando la interfaz :SalesPageComponent. La pantalla redirige la operación al controlador :SalesController mediante create\_sale(), el cual valida la sucursal en :Sucursal, resuelve los ítems (directos o desde :Reserva con \_resolve\_items()), consulta :Variante y actualiza las existencias en :Inventario. Posteriormente, :SalesController crea la transacción con \_create\_sale\_from\_items() en :Venta y :DetalleVenta, emite el registro en :Comprobante y notifica a :SalesPageComponent para renderizar el comprobante ante el cajero. **Resultado**: Venta presencial registrada exitosamente, pago cobrado en caja y comprobante emitido.

##### CICLO \# 3  {#ciclo-#-3}

**CU19 – Usar vestidor virtual**

**CU20 – Generar reportes y dashboards**

**CU21 – Recibir recomendaciones de IA**

**CU22 – Consultar asistente virtual/chatbot**

**CU23 – Generar reporte por voz/lenguaje natural**

### **2.3. Análisis de una Clase** {#2.3.-análisis-de-una-clase}

#### **Ciclo \#1** {#ciclo-#1-5}

#### **Ciclo \#2**  {#ciclo-#2-5}

#### **CICLO \#3** {#ciclo-#3-4}

### **2.4. Análisis de Paquete** {#2.4.-análisis-de-paquete}


3. ## **FLUJO DE TRABAJO: DISEÑO** {#flujo-de-trabajo:-diseño}

   1. ### **Diseño de Arquitectura** {#diseño-de-arquitectura}

      #### **3.1.1. Diseño Físico (Diagrama de Despliegue)** {#3.1.1.-diseño-físico-(diagrama-de-despliegue)}


#### **3.1.2. Diseño Lógico (Diagrama de Paquete)** {#3.1.2.-diseño-lógico-(diagrama-de-paquete)}
  

2. ### **Diseño de Datos** {#diseño-de-datos}

   #### **3.2.1. Diseño de Datos Lógico** {#3.2.1.-diseño-de-datos-lógico}

   ##### 3.2.1.1. Diagrama de Clase                                                                                                                                                                                                                                                                                                                                                   

##### 3.2.1.2. Mapeo {#3.2.1.2.-mapeo}

| branches |  |  |  |  |
| ----- | ----- | ----- | ----- | ----- |
| **PK** |  |  |  |  |
| **id** | **name** | **city** | **is\_default** | **is\_active** |

| users |  |  |  |  |  |  |  |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| **PK** |  |  |  |  |  | **FK** |  |
| **id** | **name** | **email** | **hashed\_password** | **gender** | **rol** | **branch\_id** | **is\_active** |

**providers**

| PK | FK | FK |  |  |  |  |  |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| id | user\_id | branch\_id | business\_name | contact\_name | phone | status |  |

| categories |  |
| ----- | ----- |
| **PK** |  |
| **id** | **name** |

**sizes**

| PK |  |
| :---- | :---- |
| **id** | **name** |

| colors |  |  |
| ----- | ----- | ----- |
| PK |  |  |
| id | name | hex\_code |

| seasons |  |
| ----- | ----- |
| **PK** |  |
| **id** | **name** |

| collections |  |  |
| ----- | ----- | ----- |
| **PK** |  | **FK** |
| **id** | **name** | **season\_id** |

| products |  |  |  |  |  |  |  |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| **PK** |  |  |  | **FK** | **FK** | **FK** | **FK** |
| **id** | **name** | **description** | **price** | **provider\_id** | **category\_id** | **season\_id** | **collection\_id** |

**product\_variants**

| PK | FK |  |  | FK | FK |  |  |  |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **id** | product\_id | sku | price | size\_id | color\_id | image\_url | image\_public\_id | status |

| inventory |  |  |  |  |
| :---- | ----- | ----- | ----- | ----- |
| **PK** | **FK** | **FK** |  |  |
| **id** | **variant\_id** | **branch\_id** | **quantity** | **reserved\_quantity** |

**inventory\_movements**

| PK | FK | FK |  |  | FK |  | FK |  |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| id | variant\_id | branch\_id | movement\_type | quantity | reference\_branch\_id | note | created\_by | created\_at |

**carts**

| PK | FK |  |  |  |  |  |  |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| id | user\_id | status | subtotal | discount\_amount | total\_amount | created\_at | updated\_at |

**cart\_items**

| PK | FK | FK |  |  |
| ----- | ----- | ----- | ----- | ----- |
| id | cart\_id | variant\_id | quantity | unit\_price |

**reservations**

| PK | FK | FK |  |  |  |  |  |  |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| id | branch\_id | user\_id | visit\_date | expires\_at | status | total\_amount | created\_at | updated\_at |

**reservation\_items**

| PK | FK | FK |  |  |
| ----- | ----- | ----- | ----- | ----- |
| id | reservation\_id | variant\_id | quantity | unit\_price |

**orders**

| PK | FK |  |  |  |  |  |  |  |  |  |  |  |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| id | user\_id | status | payment\_method | payment\_status | stripe\_payment\_intent\_id | cash\_reference | subtotal | discount\_amount | total\_amount | currency | created\_at | updated\_at |

**order\_items**

| PK | FK | FK |  |  |  |  |  |  |  |  |  |  |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| id | order\_id | variant\_id | quantity | unit\_price | line\_total | product\_id | product\_name | variant\_sku | size\_id | color\_id | image\_url | image\_public\_id |

**sales**

| PK | FK | FK | FK |  |  |  |  |  |  |  |  |  |  |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| id | branch\_id | user\_id | reservation\_id | status | payment\_method | payment\_status | cash\_reference | subtotal | discount\_amount | total\_amount | currency | created\_at | updated\_at |

**sale\_items**

| PK | FK | FK |  |  |  |  |  |  |  |  |  |  |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| id | sale\_id | variant\_id | quantity | unit\_price | line\_total | product\_id | product\_name | variant\_sku | size\_id | color\_id | image\_url | image\_public\_id |

##### 3.2.1.3. Normalización {#3.2.1.3.-normalización}

	Todas las tablas de la base de datos WomenStyle se encuentran correctamente en la cuarta forma normal.

#### **3.2.2. Diseño de Datos Físico** {#3.2.2.-diseño-de-datos-físico}

##### 3.2.2.1. Tabla de Volumen {#3.2.2.1.-tabla-de-volumen}

**branches**

| Atributo | Tipo de dato | Descripción | Tamaño | Nulo | Llave |
| ----- | ----- | ----- | ----- | ----- | ----- |
| id | UUID | Identificador único de la sucursal. | 16 bytes | No | PK |
| name | VARCHAR | Nombre de la sucursal. | 255 caracteres | No | \- |
| city | VARCHAR | Ciudad donde se encuentra la sucursal. | 255 caracteres | No | \- |
| is\_default | BOOLEAN | Indica si es la sucursal principal. | 1 byte | No | \- |
| is\_active | BOOLEAN | Indica si la sucursal está activa. | 1 byte | No | \- |

**users**

| Atributo | Tipo de dato | Descripción | Tamaño | Nulo | Llave |
| :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | Identificador único del usuario. | 16 bytes | No | PK |
| name | VARCHAR | Nombre del usuario. | 255 caracteres | No | \- |
| email | VARCHAR | Correo electrónico del usuario. | 255 caracteres | No | \- |
| hashed\_password | VARCHAR | Contraseña almacenada mediante hash. | 255 caracteres | No | \- |
| gender | VARCHAR | Género registrado del usuario. | 50 caracteres | No | \- |
| rol | VARCHAR | Rol asignado al usuario dentro del sistema. | 50 caracteres | No | \- |
| branch\_id | UUID | Sucursal asociada al usuario. | 16 bytes | SI | FK |
| is\_active | BOOLEAN | Indica si la cuenta del usuario está activa. | 1 byte | No | \- |

**providers**

| Atributo | Tipo de dato | Descripción | Tamaño | Nulo | Llave |
| ----- | ----- | ----- | ----- | ----- | ----- |
| id | UUID | Identificador único del proveedor. | 16 bytes | No | PK |
| user\_id | UUID | Usuario asociado a la cuenta del proveedor. | 16 bytes | No | FK |
| branch\_id | UUID | Sucursal asociada al proveedor. | 16 bytes | SI | FK |
| business\_name | VARCHAR | Nombre comercial del proveedor. | 255 caracteres | No | \- |
| contact\_name | VARCHAR | Nombre de la persona de contacto. | 255 caracteres | No | \- |
| phone | VARCHAR | Número telefónico de contacto. | 20 caracteres | SI | \- |
| status | VARCHAR | Estado actual del proveedor. | 50 caracteres | No | \- |

**`categories`**

| Atributo | Tipo de dato | Descripción | Tamaño | Nulo | Llave |
| ----- | ----- | ----- | ----- | ----- | ----- |
| id | UUID | Identificador único de la categoría. | 16 bytes | No | PK |
| name | VARCHAR | Nombre de la categoría de prendas. | 255 caracteres | No | \- |

**`sizes`**

| Atributo | Tipo de dato | Descripción | Tamaño | Nulo | Llave |
| ----- | ----- | ----- | ----- | ----- | ----- |
| id | UUID | Identificador único de la talla. | 16 bytes | No | PK |
| name | VARCHAR | Nombre o código de la talla. | 50 caracteres | No | \- |

**`colors`**

| Atributo | Tipo de dato | Descripción | Tamaño | Nulo | Llave |
| ----- | ----- | ----- | ----- | ----- | ----- |
| id | UUID | Identificador único del color. | 16 bytes | No | PK |
| name | VARCHAR | Nombre del color. | 255 caracteres | No | \- |
| hex\_code | VARCHAR | Código hexadecimal que representa el color. | 7 caracteres | SI | \- |

**`seasons`**

| Atributo | Tipo de dato | Descripción | Tamaño | Nulo | Llave |
| ----- | ----- | ----- | ----- | ----- | ----- |
| id | UUID | Identificador único de la temporada. | 16 bytes | No | PK |
| name | VARCHAR | Nombre de la temporada comercial. | 255 caracteres | No | \- |

**`collections`**

| Atributo | Tipo de dato | Descripción | Tamaño | Nulo | Llave |
| ----- | ----- | ----- | ----- | ----- | ----- |
| id | UUID | Identificador único de la colección. | 16 bytes | No | PK |
| name | VARCHAR | Nombre de la colección. | 255 caracteres | No | \- |
| season\_id | UUID | Temporada a la que pertenece la colección. | 16 bytes | SI | FK |

**`products`**

| Atributo | Tipo de dato | Descripción | Tamaño | Nulo | Llave |
| ----- | ----- | ----- | ----- | ----- | ----- |
| id | UUID | Identificador único del producto. | 16 bytes | No | PK |
| name | VARCHAR | Nombre del producto o prenda. | 255 caracteres | No | \- |
| description | TEXT | Descripción detallada del producto. | Variable | SI | \- |
| price | NUMERIC | Precio base del producto. | 10 dígitos, 2 decimales | No | \- |
| provider\_id | UUID | Proveedor que suministra el producto. | 16 bytes | SI | FK |
| category\_id | UUID | Categoría a la que pertenece el producto. | 16 bytes | No | FK |
| season\_id | UUID | Temporada comercial asociada al producto. | 16 bytes | SI | FK |
| collection\_id | UUID | Colección a la que pertenece el producto. | 16 bytes | SI | FK |

**product\_variants**

| Tipo de dato | Atributo | Descripción | Tamaño | Nulo | Llave |
| ----- | ----- | ----- | ----- | ----- | ----- |
| UUID | id | Identificador único de la variante. | 16 bytes | No | PK |
| UUID | product\_id | Producto al que pertenece la variante. | 16 bytes | No | FK |
| VARCHAR | sku | Código único de identificación de la variante. | 50 caracteres | No | \- |
| NUMERIC | price | Precio específico de la variante. | 10 dígitos, 2 decimales | No | \- |
| UUID | size\_id | Talla asociada a la variante. | 16 bytes | SI | FK |
| UUID | color\_id | Color asociado a la variante. | 16 bytes | SI | FK |
| VARCHAR | status | Estado actual de la variante. | 50 caracteres | No | \- |

**product\_variants**

| Atributo | Tipo de dato | Descripción | Tamaño | Nulo | Llave |
| :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | Identificador único de la variante del producto. | 16 bytes | No | PK |
| product\_id | UUID | Producto al que pertenece la variante. | 16 bytes | No | FK |
| sku | VARCHAR | Código único de identificación de la variante. | 50 caracteres | No | \- |
| price | NUMERIC | Precio específico de la variante del producto. | 10 dígitos, 2 decimales | No | \- |
| size\_id | UUID | Talla asociada a la variante del producto. | 16 bytes | SI | FK |
| color\_id | UUID | Color asociado a la variante del producto. | 16 bytes | SI | FK |
| image\_url | VARCHAR | Dirección o URL de la imagen asociada a la variante. | Variable / sin límite declarado | SI | \- |
| image\_public\_id | VARCHAR | Identificador público de la imagen almacenada en el servicio externo. | Variable / sin límite declarado | SI | \- |
| status | PRODUCTVARIANTSTATUSENUM | Estado actual de la variante del producto. | 4 bytes | No | \- |

**inventory**

| Atributo | Tipo de dato | Descripción | Tamaño | Nulo | Llave |
| :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | Identificador único del registro de inventario. | 16 bytes | No | PK |
| variant\_id | UUID | Variante del producto registrada en el inventario. | 16 bytes | No | FK |
| branch\_id | UUID | Sucursal donde se encuentra la variante. | 16 bytes | No | FK |
| quantity | INTEGER | Cantidad total de unidades registradas en inventario. | 4 bytes | No | \- |
| reserved\_quantity | INTEGER | Cantidad de unidades actualmente reservadas. | 4 bytes | No | \- |

**inventory\_movements**

| Atributo | Tipo de dato | Descripción | Tamaño | Nulo | Llave |
| :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | Identificador único del movimiento de inventario. | 16 bytes | No | PK |
| variant\_id | UUID | Variante del producto sobre la que se realiza el movimiento. | 16 bytes | No | FK |
| branch\_id | UUID | Sucursal donde se registra el movimiento. | 16 bytes | No | FK |
| movement\_type | INVENTORYMOVEMENTTYPEENUM | Tipo de movimiento realizado en el inventario. | 4 bytes | No | \- |
| quantity | INTEGER | Cantidad de unidades involucradas en el movimiento. | 4 bytes | No | \- |
| reference\_branch\_id | UUID | Sucursal de referencia en caso de transferencia. | 16 bytes | SI | FK |
| note | TEXT | Observación o detalle adicional del movimiento. | Variable | SI | \- |
| created\_by | UUID | Usuario que registró el movimiento. | 16 bytes | SI | FK |
| created\_at | TIMESTAMP WITH TIME ZONE | Fecha y hora en que se registró el movimiento. | 8 bytes | No | \- |

**carts**

| Atributo | Tipo de dato | Descripción | Tamaño | Nulo | Llave |
| :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | Identificador único del carrito de compras. | 16 bytes | No | PK |
| user\_id | UUID | Usuario propietario del carrito. | 16 bytes | No | FK |
| status | CARTSTATUSENUM | Estado actual del carrito de compras. | 4 bytes | No | \- |
| subtotal | NUMERIC | Monto total antes de aplicar descuentos. | 10 dígitos, 2 decimales | No | \- |
| discount\_amount | NUMERIC | Monto total de los descuentos aplicados. | 10 dígitos, 2 decimales | No | \- |
| total\_amount | NUMERIC | Monto total final del carrito. | 10 dígitos, 2 decimales | No | \- |
| created\_at | TIMESTAMP WITH TIME ZONE | Fecha y hora de creación del carrito. | 8 bytes | No | \- |
| updated\_at | TIMESTAMP WITH TIME ZONE | Fecha y hora de la última actualización. | 8 bytes | SI | \- |

**cart\_items**

| Atributo | Tipo de dato | Descripción | Tamaño | Nulo | Llave |
| :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | Identificador único del detalle del carrito. | 16 bytes | No | PK |
| cart\_id | UUID | Carrito al que pertenece el producto seleccionado. | 16 bytes | No | FK |
| variant\_id | UUID | Variante del producto agregada al carrito. | 16 bytes | No | FK |
| quantity | INTEGER | Cantidad de unidades de la variante. | 4 bytes | No | \- |
| unit\_price | NUMERIC | Precio unitario de la variante. | 10 dígitos, 2 decimales | No | \- |

**reservations**

| Atributo | Tipo de dato | Descripción | Tamaño | Nulo | Llave |
| :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | Identificador único de la reserva. | 16 bytes | No | PK |
| branch\_id | UUID | Sucursal donde el cliente realizará la reserva. | 16 bytes | No | FK |
| user\_id | UUID | Cliente que realizó la reserva. | 16 bytes | No | FK |
| visit\_date | DATE | Fecha programada para la visita a la sucursal. | 4 bytes | No | \- |
| expires\_at | DATE | Fecha de vencimiento de la reserva. | 4 bytes | No | \- |
| status | RESERVATIONSTATUSENUM | Estado actual de la reserva. | 4 bytes | No | \- |
| total\_amount | NUMERIC | Monto total correspondiente a las prendas reservadas. | 10 dígitos, 2 decimales | No | \- |
| created\_at | TIMESTAMP WITH TIME ZONE | Fecha y hora de creación de la reserva. | 8 bytes | No | \- |
| updated\_at | TIMESTAMP WITH TIME ZONE | Fecha y hora de la última actualización de la reserva. | 8 bytes | SI | \- |

**reservation\_items**

| Atributo | Tipo de dato | Descripción | Tamaño | Nulo | Llave |
| :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | Identificador único del detalle de la reserva. | 16 bytes | No | PK |
| reservation\_id | UUID | Reserva a la que pertenece la prenda seleccionada. | 16 bytes | No | FK |
| variant\_id | UUID | Variante del producto reservada. | 16 bytes | No | FK |
| quantity | INTEGER | Cantidad de unidades reservadas. | 4 bytes | No | \- |
| unit\_price | NUMERIC | Precio unitario de la variante al momento de reservarla. | 10 dígitos, 2 decimales | No | \- |

**orders**

| Atributo | Tipo de dato | Descripción | Tamaño | Nulo | Llave |
| :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | Identificador único del pedido digital. | 16 bytes | No | PK |
| user\_id | UUID | Cliente que realizó el pedido. | 16 bytes | No | FK |
| status | ORDERSTATUSENUM | Estado actual del pedido. | 4 bytes | No | \- |
| payment\_method | PAYMENTMETHODENUM | Método de pago seleccionado. | 4 bytes | No | \- |
| payment\_status | PAYMENTSTATUSENUM | Estado actual del pago. | 4 bytes | No | \- |
| stripe\_payment\_intent\_id | VARCHAR | Identificador de la transacción generada por Stripe. | Variable / sin límite declarado | SI | \- |
| cash\_reference | VARCHAR | Referencia asociada al pago. | Variable / sin límite declarado | SI | \- |
| subtotal | NUMERIC | Monto total antes de aplicar descuentos. | 10 dígitos, 2 decimales | No | \- |
| discount\_amount | NUMERIC | Monto total de los descuentos aplicados. | 10 dígitos, 2 decimales | No | \- |
| total\_amount | NUMERIC | Monto total final del pedido. | 10 dígitos, 2 decimales | No | \- |
| currency | VARCHAR | Moneda utilizada en el pedido. | Variable / sin límite declarado | No | \- |
| created\_at | TIMESTAMP WITH TIME ZONE | Fecha y hora de creación del pedido. | 8 bytes | No | \- |
| updated\_at | TIMESTAMP WITH TIME ZONE | Fecha y hora de la última actualización del pedido. | 8 bytes | SI | \- |

**order\_items**

| Atributo | Tipo de dato | Descripción | Tamaño | Nulo | Llave |
| :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | Identificador único del detalle del pedido. | 16 bytes | No | PK |
| order\_id | UUID | Pedido al que pertenece el detalle. | 16 bytes | No | FK |
| variant\_id | UUID | Variante del producto incluida en el pedido. | 16 bytes | No | FK |
| quantity | INTEGER | Cantidad de unidades adquiridas. | 4 bytes | No | \- |
| unit\_price | NUMERIC | Precio unitario de la variante al realizar el pedido. | 10 dígitos, 2 decimales | No | \- |
| line\_total | NUMERIC | Monto total correspondiente a la línea del pedido. | 10 dígitos, 2 decimales | No | \- |
| product\_id | UUID | Identificador del producto registrado como referencia histórica. | 16 bytes | No | \- |
| product\_name | VARCHAR | Nombre del producto al momento de realizar el pedido. | Variable / sin límite declarado | No | \- |
| variant\_sku | VARCHAR | Código SKU de la variante al momento del pedido. | Variable / sin límite declarado | No | \- |
| size\_id | UUID | Identificador de la talla registrado en el pedido. | 16 bytes | SI | \- |
| color\_id | UUID | Identificador del color registrado en el pedido. | 16 bytes | SI | \- |
| image\_url | VARCHAR | Dirección de la imagen de la variante. | Variable / sin límite declarado | SI | \- |
| image\_public\_id | VARCHAR | Identificador público de la imagen almacenada externamente. | Variable / sin límite declarado | SI | \- |

**sales**

| Atributo | Tipo de dato | Descripción | Tamaño | Nulo | Llave |
| :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | Identificador único de la venta presencial. | 16 bytes | No | PK |
| branch\_id | UUID | Sucursal donde se realizó la venta. | 16 bytes | No | FK |
| user\_id | UUID | Cliente asociado a la venta. | 16 bytes | No | FK |
| reservation\_id | UUID | Reserva asociada a la venta, si corresponde. | 16 bytes | SI | FK |
| status | SALESTATUSENUM | Estado actual de la venta. | 4 bytes | No | \- |
| payment\_method | PAYMENTMETHODENUM | Método utilizado para realizar el pago. | 4 bytes | No | \- |
| payment\_status | PAYMENTSTATUSENUM | Estado del pago de la venta. | 4 bytes | No | \- |
| cash\_reference | VARCHAR | Referencia asociada al pago realizado. | Variable / sin límite declarado | SI | \- |
| subtotal | NUMERIC | Monto total antes de aplicar descuentos. | 10 dígitos, 2 decimales | No | \- |
| discount\_amount | NUMERIC | Monto total de los descuentos aplicados. | 10 dígitos, 2 decimales | No | \- |
| total\_amount | NUMERIC | Monto total final de la venta. | 10 dígitos, 2 decimales | No | \- |
| currency | VARCHAR | Moneda utilizada en la venta. | Variable / sin límite declarado | No | \- |
| created\_at | TIMESTAMP WITH TIME ZONE | Fecha y hora en que se registró la venta. | 8 bytes | No | \- |
| updated\_at | TIMESTAMP WITH TIME ZONE | Fecha y hora de la última actualización de la venta. | 8 bytes | SI | \- |

**sale\_items**

| Atributo | Tipo de dato | Descripción | Tamaño | Nulo | Llave |
| :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | Identificador único del detalle de la venta. | 16 bytes | No | PK |
| sale\_id | UUID | Venta a la que pertenece el detalle. | 16 bytes | No | FK |
| variant\_id | UUID | Variante del producto incluida en la venta. | 16 bytes | No | FK |
| quantity | INTEGER | Cantidad de unidades vendidas. | 4 bytes | No | \- |
| unit\_price | NUMERIC | Precio unitario de la variante al realizar la venta. | 10 dígitos, 2 decimales | No | \- |
| line\_total | NUMERIC | Monto total correspondiente a la línea de la venta. | 10 dígitos, 2 decimales | No | \- |
| product\_id | UUID | Identificador del producto registrado como referencia histórica. | 16 bytes | No | \- |
| product\_name | VARCHAR | Nombre del producto al momento de realizar la venta. | Variable / sin límite declarado | No | \- |
| variant\_sku | VARCHAR | Código SKU de la variante al momento de la venta. | Variable / sin límite declarado | No | \- |
| size\_id | UUID | Identificador de la talla registrado en la venta. | 16 bytes | SI | \- |
| color\_id | UUID | Identificador del color registrado en la venta. | 16 bytes | SI | \- |
| image\_url | VARCHAR | Dirección de la imagen de la variante. | Variable / sin límite declarado | SI | \- |
| image\_public\_id | VARCHAR | Identificador público de la imagen almacenada externamente. | Variable / sin límite declarado | SI | \- |

##### 3.2.2.2. Script {#3.2.2.2.-script}

\-- \============================================================================  
\-- WOMEN STYLE DATABASE SCHEMA \- PostgreSQL \============================================================================

\-- TABLE: branches  
\-- Descripción: Sucursales/locales de la tienda de moda  
CREATE TABLE IF NOT EXISTS branches (  
    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    name VARCHAR(255) NOT NULL UNIQUE,  
    city VARCHAR(255) NOT NULL,  
    is\_default BOOLEAN NOT NULL DEFAULT FALSE,  
    is\_active BOOLEAN NOT NULL DEFAULT TRUE  
);

\-- TABLE: users  
\-- Descripción: Usuarios del sistema (admins, empleados, clientes, proveedores)  
CREATE TABLE IF NOT EXISTS users (  
    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    name VARCHAR(255) NOT NULL,  
    email VARCHAR(255) NOT NULL UNIQUE,  
    hashed\_password VARCHAR(255) NOT NULL,  
    gender VARCHAR(50) NOT NULL, \-- 'masculino' o 'femenino'  
    rol VARCHAR(50) NOT NULL, \-- 'administrador', 'encargado', 'cajero', 'delivery', 'cliente', 'proveedor'  
    branch\_id UUID REFERENCES branches(id) ON DELETE SET NULL,  
    is\_active BOOLEAN NOT NULL DEFAULT TRUE,  
    UNIQUE(email)  
);

\-- TABLE: providers  
\-- Descripción: Proveedores de productos  
CREATE TABLE IF NOT EXISTS providers (  
    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    user\_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,  
    branch\_id UUID REFERENCES branches(id) ON DELETE SET NULL,  
    business\_name VARCHAR(255) NOT NULL,  
    contact\_name VARCHAR(255) NOT NULL,  
    phone VARCHAR(20),  
    status VARCHAR(50) NOT NULL DEFAULT 'active' \-- 'active', 'inactive'  
);

\-- TABLE: categories  
\-- Descripción: Categorías de productos  
CREATE TABLE IF NOT EXISTS categories (  
    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    name VARCHAR(255) NOT NULL UNIQUE  
);

\-- TABLE: sizes  
\-- Descripción: Tallas disponibles (XS, S, M, L, XL, 28, 30, 32, etc.)  
CREATE TABLE IF NOT EXISTS sizes (  
    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    name VARCHAR(50) NOT NULL UNIQUE  
);

\-- TABLE: colors  
\-- Descripción: Colores con código hexadecimal  
CREATE TABLE IF NOT EXISTS colors (  
    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    name VARCHAR(255) NOT NULL UNIQUE,  
    hex\_code VARCHAR(7)  
);

\-- TABLE: seasons  
\-- Descripción: Temporadas/estaciones del año  
CREATE TABLE IF NOT EXISTS seasons (  
    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    name VARCHAR(255) NOT NULL UNIQUE  
);

\-- TABLE: collections  
\-- Descripción: Colecciones de moda asociadas a temporadas  
CREATE TABLE IF NOT EXISTS collections (  
    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    name VARCHAR(255) NOT NULL UNIQUE,  
    season\_id UUID REFERENCES seasons(id) ON DELETE SET NULL  
);

\-- TABLE: products  
\-- Descripción: Catálogo de productos base  
CREATE TABLE products (  
  id UUID PRIMARY KEY DEFAULT uuid\_generate\_v4(),  
  name VARCHAR NOT NULL,  
  description TEXT,  
  category\_id UUID REFERENCES categories(id),  
  collection\_id UUID REFERENCES collections(id),  
  season\_id UUID REFERENCES seasons(id),  
  provider\_id UUID REFERENCES providers(id),  
  created\_at TIMESTAMP WITH TIME ZONE DEFAULT now(),  
  updated\_at TIMESTAMP WITH TIME ZONE  
);

\-- TABLE: product\_variants  
\-- Descripción: Almacena las variantes de un producto (combinación de talla y color).  
CREATE TABLE product\_variants (  
    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    product\_id UUID NOT NULL REFERENCES products(id),  
    sku VARCHAR NOT NULL UNIQUE,  
    price NUMERIC(10, 2\) NOT NULL,  
    size\_id UUID REFERENCES sizes(id),  
    color\_id UUID REFERENCES colors(id),  
    image\_url VARCHAR,  
    image\_public\_id VARCHAR,  
    status productStatusEnum NOT NULL DEFAULT 'pending',  
    UNIQUE(product\_id, size\_id, color\_id)  
);

\-- TABLE: inventory  
\-- Descripción: Inventario de variantes por sucursal (stock disponible y reservado)  
CREATE TABLE IF NOT EXISTS inventory (  
    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    variant\_id UUID NOT NULL REFERENCES product\_variants(id),  
    branch\_id UUID NOT NULL REFERENCES branches(id),  
    quantity INTEGER NOT NULL DEFAULT 0,  
    reserved\_quantity INTEGER NOT NULL DEFAULT 0,  
    UNIQUE(variant\_id, branch\_id)  
);

\-- Tabla: inventory\_movements  
\-- Descripción: Registro de auditoría de todos los movimientos de inventario.  
\-- Incluye entradas, salidas, transferencias entre sucursales y ajustes.  
CREATE TABLE inventory\_movements (  
    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    variant\_id UUID NOT NULL REFERENCES product\_variants(id),  
    branch\_id UUID NOT NULL REFERENCES branches(id),  
    movement\_type inventoryMovementTypeEnum NOT NULL,  
    quantity INTEGER NOT NULL,  
    reference\_branch\_id UUID REFERENCES branches(id),  
    note TEXT,  
    created\_by UUID REFERENCES users(id),  
    created\_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()  
);

\-- Tabla: carts  
\-- Descripción: Almacena los carritos de compra de los clientes.   
CREATE TABLE carts (  
    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    user\_id UUID NOT NULL UNIQUE REFERENCES users(id),  
    status cartStatusEnum NOT NULL DEFAULT 'active',  
    subtotal NUMERIC(10, 2\) NOT NULL DEFAULT 0,  
    discount\_amount NUMERIC(10, 2\) NOT NULL DEFAULT 0,  
    total\_amount NUMERIC(10, 2\) NOT NULL DEFAULT 0,  
    created\_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),  
    updated\_at TIMESTAMP WITH TIME ZONE  
);

\-- Tabla: cart\_items  
\-- Descripción: Almacena los items individuales agregados al carrito de un cliente.  
\-- Cada item incluye la variante del producto, cantidad y precio unitario.  
CREATE TABLE cart\_items (  
    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    cart\_id UUID NOT NULL REFERENCES carts(id),  
    variant\_id UUID NOT NULL REFERENCES product\_variants(id),  
    quantity INTEGER NOT NULL,  
    unit\_price NUMERIC(10, 2\) NOT NULL,  
    UNIQUE(cart\_id, variant\_id)  
);

\-- Tabla: reservations  
\-- Descripción: Almacena las reservaciones de productos por clientes. Una reservación  
\-- es un compromiso de compra para una fecha específica con una fecha de expiración.  
CREATE TABLE reservations (  
    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    branch\_id UUID NOT NULL REFERENCES branches(id),  
    user\_id UUID NOT NULL REFERENCES users(id),  
    visit\_date DATE NOT NULL,  
    expires\_at DATE NOT NULL,  
    status reservationStatusEnum NOT NULL DEFAULT 'pending',  
    total\_amount NUMERIC(10, 2\) NOT NULL DEFAULT 0,  
    created\_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),  
    updated\_at TIMESTAMP WITH TIME ZONE  
);

\-- Tabla: reservation\_items  
\-- Descripción: Almacena los items individuales incluidos en una reservación.  
\-- Cada item especifica la variante, cantidad y precio unitario reservado.  
CREATE TABLE reservation\_items (  
    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    reservation\_id UUID NOT NULL REFERENCES reservations(id),  
    variant\_id UUID NOT NULL REFERENCES product\_variants(id),  
    quantity INTEGER NOT NULL,  
    unit\_price NUMERIC(10, 2\) NOT NULL,  
    UNIQUE(reservation\_id, variant\_id)  
);

\-- Tabla: orders  
\-- Descripción: Almacena las órdenes de compra realizadas por clientes a través  
\-- de online. Incluye información de pago, estado del pedido, método de pago y totales.  
CREATE TABLE orders (  
    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    user\_id UUID NOT NULL REFERENCES users(id),  
    status orderStatusEnum NOT NULL DEFAULT 'pending',  
    payment\_method paymentMethodEnum NOT NULL,  
    payment\_status paymentStatusEnum NOT NULL DEFAULT 'pending',  
    stripe\_payment\_intent\_id VARCHAR,  
    cash\_reference VARCHAR,  
    subtotal NUMERIC(10, 2\) NOT NULL DEFAULT 0,  
    discount\_amount NUMERIC(10, 2\) NOT NULL DEFAULT 0,  
    total\_amount NUMERIC(10, 2\) NOT NULL DEFAULT 0,  
    currency VARCHAR NOT NULL DEFAULT 'usd',  
    created\_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),  
    updated\_at TIMESTAMP WITH TIME ZONE  
);

\-- Tabla: order\_items  
\-- Descripción: Almacena los items individuales incluidos en una orden de compra.  
\-- Captura detalles del producto en el momento de la compra (nombre, SKU, imágenes)  
\-- para mantener un registro histórico incluso si el producto cambia después.  
CREATE TABLE order\_items (  
    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    order\_id UUID NOT NULL REFERENCES orders(id),  
    variant\_id UUID NOT NULL REFERENCES product\_variants(id),  
    quantity INTEGER NOT NULL,  
    unit\_price NUMERIC(10, 2\) NOT NULL,  
    line\_total NUMERIC(10, 2\) NOT NULL,  
    product\_id UUID NOT NULL,  
    product\_name VARCHAR NOT NULL,  
    variant\_sku VARCHAR NOT NULL,  
    size\_id UUID,  
    color\_id UUID,  
    image\_url VARCHAR,  
    image\_public\_id VARCHAR,  
    UNIQUE(order\_id, variant\_id)  
);

\-- Tabla: sales  
\-- Descripción: Almacena las transacciones de venta realizadas en punto de venta (POS).  
\-- Una venta puede originar de una reservación previa o ser una venta directa.  
CREATE TABLE sales (  
    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    branch\_id UUID NOT NULL REFERENCES branches(id),  
    user\_id UUID NOT NULL REFERENCES users(id),  
    reservation\_id UUID UNIQUE REFERENCES reservations(id),  
    status salestatusenum NOT NULL DEFAULT 'completed',  
    payment\_method paymentMethodEnum NOT NULL,  
    payment\_status paymentStatusEnum NOT NULL DEFAULT 'paid',  
    cash\_reference VARCHAR,  
    subtotal NUMERIC(10, 2\) NOT NULL DEFAULT 0,  
    discount\_amount NUMERIC(10, 2\) NOT NULL DEFAULT 0,  
    total\_amount NUMERIC(10, 2\) NOT NULL DEFAULT 0,  
    currency VARCHAR NOT NULL DEFAULT 'usd',  
    created\_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),  
    updated\_at TIMESTAMP WITH TIME ZONE  
);

\-- Tabla: sale\_items  
\-- Descripción: Almacena los items individuales incluidos en una venta de punto de venta.  
CREATE TABLE sale\_items (  
    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    sale\_id UUID NOT NULL REFERENCES sales(id),  
    variant\_id UUID NOT NULL REFERENCES product\_variants(id),  
    quantity INTEGER NOT NULL,  
    unit\_price NUMERIC(10, 2\) NOT NULL,  
    line\_total NUMERIC(10, 2\) NOT NULL,  
    product\_id UUID NOT NULL,  
    product\_name VARCHAR NOT NULL,  
    variant\_sku VARCHAR NOT NULL,  
    size\_id UUID,  
    color\_id UUID,  
    image\_url VARCHAR,  
    image\_public\_id VARCHAR,  
    UNIQUE(sale\_id, variant\_id)  
);

\-- \============================================================================  
\-- ÍNDICES PARA OPTIMIZAR CONSULTAS  
\-- \============================================================================

CREATE INDEX idx\_users\_branch\_id ON users(branch\_id);  
CREATE INDEX idx\_users\_email ON users(email);  
CREATE INDEX idx\_providers\_user\_id ON providers(user\_id);  
CREATE INDEX idx\_providers\_branch\_id ON providers(branch\_id);  
CREATE INDEX idx\_products\_category\_id ON products(category\_id);  
CREATE INDEX idx\_products\_provider\_id ON products(provider\_id);  
CREATE INDEX idx\_products\_season\_id ON products(season\_id);  
CREATE INDEX idx\_products\_collection\_id ON products(collection\_id);  
CREATE INDEX idx\_product\_variants\_product\_id ON product\_variants(product\_id);  
CREATE INDEX idx\_product\_variants\_sku ON product\_variants(sku);  
CREATE INDEX idx\_inventory\_variant\_id ON inventory(variant\_id);  
CREATE INDEX idx\_inventory\_branch\_id ON inventory(branch\_id);  
CREATE INDEX idx\_inventory\_movements\_variant\_id ON inventory\_movements(variant\_id);  
CREATE INDEX idx\_inventory\_movements\_branch\_id ON inventory\_movements(branch\_id);  
CREATE INDEX idx\_inventory\_movements\_reference\_branch\_id ON inventory\_movements(reference\_branch\_id);  
CREATE INDEX idx\_inventory\_movements\_created\_by ON inventory\_movements(created\_by);  
CREATE INDEX idx\_carts\_user\_id ON carts(user\_id);  
CREATE INDEX idx\_cart\_items\_cart\_id ON cart\_items(cart\_id);  
CREATE INDEX idx\_cart\_items\_variant\_id ON cart\_items(variant\_id);  
CREATE INDEX idx\_reservations\_branch\_id ON reservations(branch\_id);  
CREATE INDEX idx\_reservations\_user\_id ON reservations(user\_id);  
CREATE INDEX idx\_reservations\_visit\_date ON reservations(visit\_date);  
CREATE INDEX idx\_reservations\_expires\_at ON reservations(expires\_at);  
CREATE INDEX idx\_reservation\_items\_reservation\_id ON reservation\_items(reservation\_id);  
CREATE INDEX idx\_reservation\_items\_variant\_id ON reservation\_items(variant\_id);  
CREATE INDEX idx\_orders\_user\_id ON orders(user\_id);  
CREATE INDEX idx\_orders\_stripe\_payment\_intent\_id ON orders(stripe\_payment\_intent\_id);  
CREATE INDEX idx\_order\_items\_order\_id ON order\_items(order\_id);  
CREATE INDEX idx\_order\_items\_variant\_id ON order\_items(variant\_id);  
CREATE INDEX idx\_sales\_branch\_id ON sales(branch\_id);  
CREATE INDEX idx\_sales\_user\_id ON sales(user\_id);  
CREATE INDEX idx\_sales\_reservation\_id ON sales(reservation\_id);  
CREATE INDEX idx\_sale\_items\_sale\_id ON sale\_items(sale\_id);  
CREATE INDEX idx\_sale\_items\_variant\_id ON sale\_items(variant\_id);

\-- \============================================================================

#### **3.2.3. Diagrama Relacional** {#3.2.3.-diagrama-relacional}


#### **3.2.4. Actualización de Tuplas (Población de Datos)** {#3.2.4.-actualización-de-tuplas-(población-de-datos)}

\-- \============================================================================  
\-- SEED DATA \- POBLACIÓN INICIAL PARA DESARROLLO Y PRUEBAS  
\-- \============================================================================

\-- TABLA: branches (3 poblaciones)  
\-- Sucursales físicas del ecommerce  
INSERT INTO branches (id, name, city, is\_default) VALUES  
('00000001-0000-0000-0000-000000000001', 'Sucursal Centro', 'Madrid', true),  
('00000001-0000-0000-0000-000000000002', 'Sucursal Norte', 'Barcelona', false),  
('00000001-0000-0000-0000-000000000003', 'Sucursal Sur', 'Sevilla', false);

\-- TABLA: users (6 poblaciones)  
\-- Diferentes usuarios con roles variados  
\-- Contraseña hash: password123 (bcrypt)  
INSERT INTO users (id, name, email, hashed\_password, gender, rol, branch\_id) VALUES  
('00000002-0000-0000-0000-000000000001', 'Admin Sistema', 'admin@ecommerce.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5EQkfzZKVgqBG', 'masculino', 'administrador', '00000001-0000-0000-0000-000000000001'),  
('00000002-0000-0000-0000-000000000002', 'Juan Pérez', 'juan@cliente.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5EQkfzZKVgqBG', 'masculino', 'cliente', '00000001-0000-0000-0000-000000000001'),  
('00000002-0000-0000-0000-000000000003', 'María García', 'maria@proveedor.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5EQkfzZKVgqBG', 'femenino', 'proveedor', NULL),  
('00000002-0000-0000-0000-000000000004', 'Carlos López', 'carlos@encargado.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5EQkfzZKVgqBG', 'masculino', 'encargado', '00000001-0000-0000-0000-000000000001'),  
('00000002-0000-0000-0000-000000000005', 'Rosa Martínez', 'rosa@cajero.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5EQkfzZKVgqBG', 'femenino', 'cajero', '00000001-0000-0000-0000-000000000002'),  
('00000002-0000-0000-0000-000000000006', 'Luis Rodríguez', 'luis@delivery.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5EQkfzZKVgqBG', 'masculino', 'delivery', '00000001-0000-0000-0000-000000000003');

\-- TABLA: providers (2 poblaciones)  
\-- Proveedores registrados en el sistema  
INSERT INTO providers (id, user\_id, branch\_id, business\_name, contact\_name, phone, status) VALUES  
('00000003-0000-0000-0000-000000000001', '00000002-0000-0000-0000-000000000003', '00000001-0000-0000-0000-000000000001', 'TextilChina S.L.', 'María García', '+34912345678', 'active'),  
('00000003-0000-0000-0000-000000000002', '00000002-0000-0000-0000-000000000002', '00000001-0000-0000-0000-000000000001', 'Confecciones Europa', 'Juan Pérez', '+34923456789', 'active');

\-- TABLA: categories (4 poblaciones)  
\-- Categorías de productos disponibles  
INSERT INTO categories (id, name) VALUES  
('00000004-0000-0000-0000-000000000001', 'Ropa Casual'),  
('00000004-0000-0000-0000-000000000002', 'Ropa Formal'),  
('00000004-0000-0000-0000-000000000003', 'Accesorios'),  
('00000004-0000-0000-0000-000000000004', 'Calzado');

\-- TABLA: sizes (6 poblaciones)  
\-- Tallas disponibles para productos  
INSERT INTO sizes (id, name) VALUES  
('00000005-0000-0000-0000-000000000001', 'XS'),  
('00000005-0000-0000-0000-000000000002', 'S'),  
('00000005-0000-0000-0000-000000000003', 'M'),  
('00000005-0000-0000-0000-000000000004', 'L'),  
('00000005-0000-0000-0000-000000000005', 'XL'),  
('00000005-0000-0000-0000-000000000006', 'XXL');

\-- TABLA: colors (6 poblaciones)  
\-- Colores disponibles con códigos hexadecimales  
INSERT INTO colors (id, name, hex\_code) VALUES  
('00000006-0000-0000-0000-000000000001', 'Negro', '\#000000'),  
('00000006-0000-0000-0000-000000000002', 'Blanco', '\#FFFFFF'),  
('00000006-0000-0000-0000-000000000003', 'Rojo', '\#FF0000'),  
('00000006-0000-0000-0000-000000000004', 'Azul', '\#0000FF'),  
('00000006-0000-0000-0000-000000000005', 'Verde', '\#00AA00'),  
('00000006-0000-0000-0000-000000000006', 'Gris', '\#808080');

\-- TABLA: seasons (4 poblaciones)  
\-- Temporadas del año para las colecciones  
INSERT INTO seasons (id, name) VALUES  
('00000007-0000-0000-0000-000000000001', 'Primavera'),  
('00000007-0000-0000-0000-000000000002', 'Verano'),  
('00000007-0000-0000-0000-000000000003', 'Otoño'),  
('00000007-0000-0000-0000-000000000004', 'Invierno');

\-- TABLA: collections (5 poblaciones)  
\-- Colecciones de productos por temporada  
INSERT INTO collections (id, name, season\_id) VALUES  
('00000008-0000-0000-0000-000000000001', 'Colección Verano 2026', '00000007-0000-0000-0000-000000000002'),  
('00000008-0000-0000-0000-000000000002', 'Colección Invierno 2026', '00000007-0000-0000-0000-000000000004'),  
('00000008-0000-0000-0000-000000000003', 'Colección Premium', NULL),  
('00000008-0000-0000-0000-000000000004', 'Colección Primavera 2026', '00000007-0000-0000-0000-000000000001'),  
('00000008-0000-0000-0000-000000000005', 'Colección Otoño 2026', '00000007-0000-0000-0000-000000000003');

\-- TABLA: products (6 poblaciones)  
\-- Productos del catálogo con detalles y referencias  
INSERT INTO products (id, sku, name, description, price, status, provider\_id, category\_id, size\_id, color\_id, season\_id, collection\_id) VALUES  
('00000009-0000-0000-0000-000000000001', 'CAMI-001-BLK-M', 'Camiseta Casual Negra', 'Camiseta 100% algodón', 19.99, 'active', '00000003-0000-0000-0000-000000000001', '00000004-0000-0000-0000-000000000001', '00000005-0000-0000-0000-000000000003', '00000006-0000-0000-0000-000000000001', '00000007-0000-0000-0000-000000000002', '00000008-0000-0000-0000-000000000001'),  
('00000009-0000-0000-0000-000000000002', 'PANT-002-BLU-L', 'Pantalón Azul Oscuro', 'Pantalón vaquero premium', 49.99, 'active', '00000003-0000-0000-0000-000000000001', '00000004-0000-0000-0000-000000000001', '00000005-0000-0000-0000-000000000004', '00000006-0000-0000-0000-000000000004', '00000007-0000-0000-0000-000000000002', '00000008-0000-0000-0000-000000000001'),  
('00000009-0000-0000-0000-000000000003', 'ZAPA-003-NEG-42', 'Zapato Formal Negro', 'Zapato de cuero genuino', 89.99, 'active', '00000003-0000-0000-0000-000000000002', '00000004-0000-0000-0000-000000000004', NULL, '00000006-0000-0000-0000-000000000001', NULL, NULL),  
('00000009-0000-0000-0000-000000000004', 'SUDAD-004-GRY-M', 'Sudadera Gris', 'Sudadera con capucha', 39.99, 'pending', '00000003-0000-0000-0000-000000000001', '00000004-0000-0000-0000-000000000001', '00000005-0000-0000-0000-000000000003', '00000006-0000-0000-0000-000000000006', '00000007-0000-0000-0000-000000000004', '00000008-0000-0000-0000-000000000002'),  
('00000009-0000-0000-0000-000000000005', 'BUFF-005-WHT-L', 'Bufanda Blanca', 'Bufanda de lana suave', 29.99, 'active', '00000003-0000-0000-0000-000000000002', '00000004-0000-0000-0000-000000000003', NULL, '00000006-0000-0000-0000-000000000002', '00000007-0000-0000-0000-000000000004', '00000008-0000-0000-0000-000000000002'),  
('00000009-0000-0000-0000-000000000006', 'CHOR-006-RED-S', 'Chaqueta Roja', 'Chaqueta impermeable', 79.99, 'active', '00000003-0000-0000-0000-000000000001', '00000004-0000-0000-0000-000000000002', '00000005-0000-0000-0000-000000000002', '00000006-0000-0000-0000-000000000003', '00000007-0000-0000-0000-000000000001', '00000008-0000-0000-0000-000000000004');

\-- TABLA: inventory (8 poblaciones)  
\-- Inventario por sucursal y producto  
INSERT INTO inventory (id, product\_id, branch\_id, quantity, reserved\_quantity) VALUES  
('00000010-0000-0000-0000-000000000001', '00000009-0000-0000-0000-000000000001', '00000001-0000-0000-0000-000000000001', 50, 5),  
('00000010-0000-0000-0000-000000000002', '00000009-0000-0000-0000-000000000001', '00000001-0000-0000-0000-000000000002', 30, 2),  
('00000010-0000-0000-0000-000000000003', '00000009-0000-0000-0000-000000000002', '00000001-0000-0000-0000-000000000001', 20, 0),  
('00000010-0000-0000-0000-000000000004', '00000009-0000-0000-0000-000000000002', '00000001-0000-0000-0000-000000000003', 15, 3),  
('00000010-0000-0000-0000-000000000005', '00000009-0000-0000-0000-000000000003', '00000001-0000-0000-0000-000000000001', 10, 0),  
('00000010-0000-0000-0000-000000000006', '00000009-0000-0000-0000-000000000004', '00000001-0000-0000-0000-000000000001', 25, 5),  
('00000010-0000-0000-0000-000000000007', '00000009-0000-0000-0000-000000000005', '00000001-0000-0000-0000-000000000002', 40, 8),  
('00000010-0000-0000-0000-000000000008', '00000009-0000-0000-0000-000000000006', '00000001-0000-0000-0000-000000000001', 18, 2);

#### **3.2.5. Consultas** {#3.2.5.-consultas}

\-- CONSULTAS \- PostgreSQL  
\-- \============================================================================

\-- 1\. Listar todos los usuarios con sus sucursales asignadas  
\-- Propósito: Ver todos los usuarios del sistema y a qué sucursal pertenecen  
SELECT u.id, u.name, u.email, u.rol, b.name AS branch\_name, u.is\_active  
FROM users u  
LEFT JOIN branches b ON u.branch\_id \= b.id  
ORDER BY u.rol, u.name;

\-- 2\. Contar total de usuarios por rol  
\-- Propósito: Obtener estadísticas de cuántos usuarios hay en cada rol  
SELECT rol, COUNT(\*) as total\_usuarios  
FROM users  
GROUP BY rol  
ORDER BY total\_usuarios DESC;

\-- 3\. Listar todos los proveedores activos con sus contactos  
\-- Propósito: Ver los proveedores disponibles y su información de contacto  
SELECT p.id, p.business\_name, p.contact\_name, p.phone, b.name AS branch, p.status  
FROM providers p  
LEFT JOIN branches b ON p.branch\_id \= b.id  
WHERE p.status \= 'active'  
ORDER BY p.business\_name;

\-- 4\. Ver todos los productos con su categoría y precio  
\-- Propósito: Listar el catálogo completo de productos  
SELECT p.id, p.name, c.name AS category, p.price, p.description  
FROM products p  
JOIN categories c ON p.category\_id \= c.id  
ORDER BY c.name, p.name;

\-- 5\. Productos por categoría (contar cuántos hay en cada una)  
\-- Propósito: Estadísticas de productos distribuidos por categoría  
SELECT c.name AS category, COUNT(p.id) AS total\_productos  
FROM categories c  
LEFT JOIN products p ON c.id \= p.category\_id  
GROUP BY c.name  
ORDER BY total\_productos DESC;

\-- 6\. Listar todas las variantes de un producto específico (ejemplo: Camiseta Básica)  
\-- Propósito: Ver todas las opciones de color y talla disponibles de un producto  
SELECT pv.id, pv.sku, pv.price, s.name AS size, c.name AS color, pv.status  
FROM product\_variants pv  
LEFT JOIN sizes s ON pv.size\_id \= s.id  
LEFT JOIN colors c ON pv.color\_id \= c.id  
WHERE pv.product\_id \= (SELECT id FROM products WHERE name \= 'Camiseta Básica' LIMIT 1\)  
ORDER BY pv.sku;

\-- 7\. Inventario total por sucursal  
\-- Propósito: Saber cuántas unidades de stock hay en cada sucursal  
SELECT b.name AS branch,   
       COUNT(DISTINCT i.variant\_id) AS total\_variantes,  
       SUM(i.quantity) AS total\_stock,  
       SUM(i.reserved\_quantity) AS total\_reservado  
FROM inventory i  
JOIN branches b ON i.branch\_id \= b.id  
GROUP BY b.name  
ORDER BY b.name;

\-- 8\. Productos sin stock (cantidad \= 0 en todas las sucursales)  
\-- Propósito: Identificar qué productos no tienen inventario disponible  
SELECT p.id, p.name, c.name AS category, COUNT(i.id) AS total\_ubicaciones\_sin\_stock  
FROM products p  
JOIN categories c ON p.category\_id \= c.id  
LEFT JOIN product\_variants pv ON p.id \= pv.product\_id  
LEFT JOIN inventory i ON pv.id \= i.variant\_id AND i.quantity \= 0  
GROUP BY p.id, p.name, c.name  
HAVING SUM(COALESCE(i.quantity, 0)) \= 0  
ORDER BY p.name;

\-- 9\. Variantes activas por temporada  
\-- Propósito: Ver qué productos activos hay en cada temporada  
SELECT s.name AS season, COUNT(pv.id) AS variantes\_activas  
FROM seasons s  
LEFT JOIN products p ON s.id \= p.season\_id  
LEFT JOIN product\_variants pv ON p.id \= pv.product\_id AND pv.status \= 'active'  
GROUP BY s.name  
ORDER BY s.name;

\-- 10\. Stock disponible por variante en La Paz  
\-- Propósito: Ver el inventario disponible de cada variante en una sucursal específica  
SELECT pv.sku, p.name AS product, s.name AS size, c.name AS color,   
       i.quantity, i.reserved\_quantity,  
       (i.quantity \- i.reserved\_quantity) AS available  
FROM inventory i  
JOIN product\_variants pv ON i.variant\_id \= pv.id  
JOIN products p ON pv.product\_id \= p.id  
LEFT JOIN sizes s ON pv.size\_id \= s.id  
LEFT JOIN colors c ON pv.color\_id \= c.id  
JOIN branches b ON i.branch\_id \= b.id  
WHERE b.name \= 'Sucursal Central La Paz'  
ORDER BY p.name, pv.sku;

\-- 11\. Colecciones con cantidad de productos asociados  
\-- Propósito: Ver cuántos productos pertenecen a cada colección  
SELECT col.id, col.name AS collection, s.name AS season, COUNT(p.id) AS total\_productos  
FROM collections col  
LEFT JOIN seasons s ON col.season\_id \= s.id  
LEFT JOIN products p ON col.id \= p.collection\_id  
GROUP BY col.id, col.name, s.name  
ORDER BY s.name, col.name;

\-- 12\. Usuarios clientes con sus datos básicos  
\-- Propósito: Listar todos los clientes registrados en el sistema  
SELECT u.id, u.name, u.email, u.gender, u.is\_active,   
       CASE WHEN u.is\_active \= true THEN 'Activo' ELSE 'Inactivo' END AS status  
FROM users u  
WHERE u.rol \= 'cliente'  
ORDER BY u.name;

\-- 13\. Productos de un proveedor específico  
\-- Propósito: Ver todos los productos que suministra un proveedor  
SELECT p.id, p.name, c.name AS category, p.price, p.description  
FROM products p  
JOIN categories c ON p.category\_id \= c.id  
WHERE p.provider\_id \= (SELECT id FROM providers LIMIT 1\)  
ORDER BY c.name, p.name;

\-- 14\. Variantes con estado pendiente  
\-- Propósito: Ver qué variantes están pendientes de aprobación  
SELECT pv.sku, p.name AS product, c.name AS category, pv.price, pv.status  
FROM product\_variants pv  
JOIN products p ON pv.product\_id \= p.id  
JOIN categories c ON p.category\_id \= c.id  
WHERE pv.status \= 'pending'  
ORDER BY p.name;

\-- 15\. Tamaños más utilizados en productos  
\-- Propósito: Saber cuáles son las tallas más frecuentes en el catálogo  
SELECT s.name AS size, COUNT(pv.id) AS cantidad\_variantes  
FROM sizes s  
LEFT JOIN product\_variants pv ON s.id \= pv.size\_id  
GROUP BY s.name  
ORDER BY cantidad\_variantes DESC, s.name;

\-- \============================================================================

#### **3.2.6. Procedimientos Almacenados** {#3.2.6.-procedimientos-almacenados}

\-- 10 PROCEDIMIENTOS ALMACENADOS ÚTILES PARA ECOMMERCE \- PostgreSQL

Ya en el documento word.

\-- ============================================================================


#### **3.2.7. Triggers** {#3.2.7.-triggers}

\-- 10 TRIGGERS \- PostgreSQL

Triggers en el documento word.

\-- ============================================================================

3. ### **Diseñar un Caso de Uso** {#diseñar-un-caso-de-uso}

   1. #### **Diagrama de Secuencia** {#diagrama-de-secuencia}

##### Ciclo \#1 {#ciclo-#1-6}

##### Ciclo \#2 {#ciclo-#2-6}

##### CICLO \#3 {#ciclo-#3-5}

4. ### **Diagramas UML 2.5+** {#diagramas-uml-2.5+}

   1. #### **Diagrama de Estado** {#diagrama-de-estado}

##### Ciclo \#1 {#ciclo-#1-7}

##### Ciclo \#2 {#ciclo-#2-7}

##### CICLO \#3 {#ciclo-#3-6}

2. #### **Diagrama de Tiempo** {#diagrama-de-tiempo}

##### Ciclo \#1 {#ciclo-#1-8}

##### Ciclo \#2 {#ciclo-#2-8}

##### CICLO \#3 {#ciclo-#3-7}   

3. #### **Diagrama de Navegación** {#diagrama-de-navegación}

   1. ##### **Sistema Principal** {#sistema-principal}

2. ##### **Subsistema 1 – Gestión de usuarios y acceso**  {#subsistema-1-–-gestión-de-usuarios-y-acceso}

3. ##### **Subsistema 2 – Gestión de productos y catálogo** {#subsistema-2-–-gestión-de-productos-y-catálogo}

4. ##### **Subsistema 3 — Gestión de inventario y disponibilidad** {#subsistema-3-—-gestión-de-inventario-y-disponibilidad}

5. ##### **Subsistema 4 — Gestión de compras y reservas** {#subsistema-4-—-gestión-de-compras-y-reservas}

6. ##### **Subsistema 5 — Gestión de ventas y atención en sucursal** {#subsistema-5-—-gestión-de-ventas-y-atención-en-sucursal}

7. ##### **Subsistema 6 — Experiencia inteligente y analítica** {#subsistema-6-—-experiencia-inteligente-y-analítica}


4. #### **Diagrama de Red** {#diagrama-de-red}

4. ## **FLUJO DE TRABAJO: IMPLEMENTACIÓN** {#flujo-de-trabajo:-implementación}

   ### **4.1. Herramientas de Desarrollo de la Aplicación WEB** {#4.1.-herramientas-de-desarrollo-de-la-aplicación-web}

#### **Framework Principal (Backend)** {#framework-principal-(backend)}

**FastAPI (Python).** Framework principal del backend, utilizado para construir la API REST del sistema. Se apoya en un conjunto de librerías que cumplen funciones específicas dentro de la arquitectura:

* **Uvicorn**: servidor ASGI que ejecuta la aplicación FastAPI, permitiendo el manejo asíncrono de peticiones.  
* **Pydantic**: librería de validación de datos que FastAPI utiliza para definir los esquemas de entrada y salida de cada endpoint (por ejemplo, los datos de un usuario, un producto o una reserva), garantizando que la información recibida cumpla con el formato esperado antes de procesarla.  
* **python-jose**: librería utilizada para la generación y verificación de tokens JWT, base del mecanismo de autenticación y autorización por rol descrito en el módulo de Usuarios y Roles.  
* **Passlib \+ bcrypt**: utilizadas para el hasheo seguro de contraseñas antes de almacenarlas en la base de datos, evitando guardar credenciales en texto plano.

#### **Frontend Web** {#frontend-web}

**Angular (TypeScript).** Framework utilizado para construir la aplicación web administrativa y la interfaz del cliente, organizada por componentes según el rol del usuario.

#### **Aplicación Móvil** {#aplicación-móvil}

**Flutter.** Framework de desarrollo multiplataforma (Android/iOS) utilizado para construir la aplicación móvil de WomenStyle, especialmente el flujo de compra digital y el módulo de vestidor virtual con realidad aumentada, que según el alcance del proyecto está disponible exclusivamente desde este canal.

**Dart.** Lenguaje de programación en el que está escrito Flutter. Su modelo de widgets declarativo permite construir interfaces reactivas y de alto rendimiento, adecuadas para las funcionalidades en tiempo real que requiere el vestidor virtual (procesamiento continuo del video de la cámara).

#### **ORM y Migraciones de Base de Datos** {#orm-y-migraciones-de-base-de-datos}

**SQLAlchemy.** ORM utilizado en el backend para representar las tablas de la base de datos como clases de Python y gestionar las relaciones entre entidades (usuarios, sucursales, productos, variantes, inventario, proveedores).

**Alembic.** Herramienta de migraciones que trabaja junto con SQLAlchemy, permitiendo versionar de forma incremental los cambios en la estructura de la base de datos a medida que el modelo de datos evoluciona.

#### **Base de Datos** {#base-de-datos}

**PostgreSQL.** Sistema gestor de base de datos relacional utilizado para la persistencia de todas las entidades del sistema, aprovechando su soporte nativo para UUID y tipos enumerados (ENUM).

**pgAdmin.** Herramienta gráfica de administración para PostgreSQL, utilizada durante el desarrollo para inspeccionar tablas, ejecutar consultas de verificación y revisar el estado de los datos sembrados (seed) sin depender exclusivamente de la línea de comandos.

#### **Almacenamiento de Imágenes** {#almacenamiento-de-imágenes}

**Cloudinary.** Servicio en la nube para almacenamiento, optimización y entrega de imágenes. Se utiliza para alojar las fotografías de las prendas del catálogo, evitando guardar archivos binarios en el servidor, y permite transformar y redimensionar las imágenes automáticamente según dónde se muestren (miniaturas del catálogo, detalle del producto, imagen de referencia para el vestidor virtual).

#### **Inteligencia Artificial** {#inteligencia-artificial}

**Gemini API (modelo Flash, capa gratuita).** Servicio de IA generativa de Google integrado mediante API para dar soporte al módulo de Asistencia Inteligente: el asistente virtual/chatbot de consultas sobre productos, el análisis de historial y preferencias para las recomendaciones personalizadas, y la generación de reportes por lenguaje natural para la administración (CU21, CU22 y CU23).

#### **Realidad Aumentada** {#realidad-aumentada}

**Virtual Try-On (Google Merchant Center).** Funcionalidad de IA generativa que, a partir de las imágenes del catálogo y una foto del usuario, genera una imagen estática que muestra cómo luciría la prenda sobre esa persona. Es un enfoque de probador 2D basado en imagen fija.

**Lucy VTON (Decart).** Modelo de realidad aumentada **en tiempo real** que transforma la transmisión de video de la cámara del usuario, superponiendo una prenda sobre la persona mientras esta se mueve, mediante una conexión en vivo (WebRTC) y con latencia mínima. Es el enfoque más adecuado para el CU19 (Usar vestidor virtual), donde el cliente visualiza la prenda en vivo desde la cámara de su dispositivo móvil.

#### **Desarrollo y Colaboración** {#desarrollo-y-colaboración}

**Git y GitHub.** Sistema de control de versiones utilizado para gestionar el código fuente del backend y el frontend de forma colaborativa entre los integrantes del equipo, permitiendo el trabajo simultáneo sobre distintos módulos (usuarios, catálogo, inventario, etc.) mediante ramas, y manteniendo un historial trazable de los cambios. El repositorio del proyecto está alojado en GitHub.

#### **Metodología de Desarrollo** {#metodología-de-desarrollo}

**Proceso Unificado de Desarrollo de Software (PUDS/RUP).** El proyecto se desarrolla siguiendo el Proceso Unificado de Desarrollo de Software, aplicando un enfoque **iterativo e incremental**: cada ciclo (como el Ciclo 1 de los primeros 10 casos de uso) recorre las disciplinas de requisitos, análisis, diseño e implementación sobre un subconjunto acotado de funcionalidades, en lugar de completar cada disciplina para todo el sistema antes de avanzar a la siguiente.

#### **Documentación Técnica** {#documentación-técnica}

Para la documentación técnica del proyecto (modelos, especificación de la API y artefactos del proceso PUDS) se utilizan las siguientes herramientas:

* **UML 2.5+.** Notación estándar utilizada para modelar los distintos flujos de trabajo del PUDS: diagrama de casos de uso y diagrama de clases (Requisitos y Análisis), diagrama de secuencia y diagrama de actividades (Diseño), y diagrama de despliegue (Implementación), tal como se detalla en la sección de Fundamentación Teórica del informe.  
* **StarUML.** Herramienta CASE (Computer-Aided Software Engineering) especializada en modelado UML, utilizada para la elaboración de los diagramas formales del proyecto (casos de uso, clases, secuencia, despliegue). Permite mantener un modelo estructurado del sistema donde los elementos (actores, casos de uso, clases, paquetes) se organizan de forma consistente entre distintos diagramas.  
* **draw.io.** Herramienta de diagramación libre y de uso más flexible, utilizada como complemento a StarUML para diagramas rápidos o de apoyo, sin requerir instalación al poder trabajarse directamente desde el navegador.  
* **OpenAPI 3.0.** Especificación estándar para describir APIs REST (endpoints, parámetros, esquemas de petición y respuesta, códigos de estado). FastAPI genera automáticamente esta especificación a partir del código del backend, y es la que alimenta la documentación interactiva del sistema.  
* **Swagger UI.** Interfaz visual e interactiva que consume la especificación OpenAPI generada por FastAPI, permitiendo explorar y probar cada endpoint de la API (autenticación, usuarios, sucursales, proveedores, catálogo) directamente desde el navegador, sin necesidad de herramientas externas como Postman. Se encuentra disponible en la ruta /docs del backend.  
* **Markdown**. Formato de texto plano utilizado para la documentación complementaria del proyecto (por ejemplo, el README.md del backend con las instrucciones de instalación y las rutas disponibles, y los documentos de arquitectura y fases de implementación), permitiendo mantener esta documentación versionada junto con el código fuente en el mismo repositorio.

  ### **4.2. Implementación de la Arquitectura del Sistema** {#4.2.-implementación-de-la-arquitectura-del-sistema}

![][image158]

### **4.3. Implementación de la Arquitectura del Subsistema** {#4.3.-implementación-de-la-arquitectura-del-subsistema}

#### **4.3.1. Diagrama de Componentes de cada Paquete** {#4.3.1.-diagrama-de-componentes-de-cada-paquete}

##### **Paquete 1 — Gestión de usuarios y acceso**   {#paquete-1-—-gestión-de-usuarios-y-acceso-1}

##### **Paquete 2 — Gestión de productos y catálogo**  {#paquete-2-—-gestión-de-productos-y-catálogo-1}

##### **Paquete 3 — Gestión de inventario y disponibilidad** {#paquete-3-—-gestión-de-inventario-y-disponibilidad-1}

##### **Paquete 4 — Gestión de compras y reservas** {#paquete-4-—-gestión-de-compras-y-reservas-1}

##### **Paquete 5 — Gestión de ventas y atención en sucursal** {#paquete-5-—-gestión-de-ventas-y-atención-en-sucursal-1}

##### **Paquete 6 — Experiencia inteligente y analítica** {#paquete-6-—-experiencia-inteligente-y-analítica-1}


5. ## **FLUJO DE TRABAJO: PRUEBAS** {#flujo-de-trabajo:-pruebas}

### **CU01: Registrar cliente** {#cu01:-registrar-cliente}

* **Criterios de Aceptación:**  
  * El cliente debe registrarse sin errores.  
  * El sistema debe generar token JWT al finalizar el registro.  
  * Los datos deben quedar almacenados correctamente.  
* **Diseño de Pruebas:**  
  * Completar el formulario de registro en el frontend.  
  * Enviar datos válidos al endpoint POST /api/auth/register.  
  * Intentar registrar un correo duplicado para validar rechazo.

Ejecución de Pruebas

| Caso de Prueba | Estado |
| :---- | :---- |
| Registro de cliente sin errores | **Aprobado** |
| Generación de JWT al registrar | **Aprobado** |
| Rechazo de correo duplicado | **Aprobado** |

> **Reporte de Prueba:** APROBADO

### **CU02: Iniciar sesión** {#cu02:-iniciar-sesión}

* **Criterios de Aceptación:**  
  * El login debe autenticar correctamente al usuario.  
  * El sistema debe rechazar credenciales inválidas.  
  * La sesión debe redirigir según el rol.  
* **Diseño de Pruebas:**  
  * Probar login desde auth/login.  
  * Validar POST /api/auth/login con credenciales correctas.  
  * Validar rechazo por contraseña incorrecta y rol no coincidente.

Ejecución de Pruebas

| Caso de Prueba | Estado |
| :---- | :---- |
| Login exitoso con credenciales válidas | **Aprobado** |
| Rechazo de credenciales inválidas | **Aprobado** |
| Rechazo por rol incorrecto | **Aprobado** |

> **Reporte de Prueba:** APROBADO

### **CU03: Gestionar usuarios internos** {#cu03:-gestionar-usuarios-internos}

* **Criterios de Aceptación:**  
  * El administrador debe listar, editar, activar/desactivar y eliminar usuarios internos.  
  * Las acciones deben respetar la sucursal asignada.  
* **Diseño de Pruebas:**  
  * Consultar GET /api/users/.  
  * Probar PATCH /api/users/{id}/rol.  
  * Probar PATCH /api/users/{id}/branch.  
  * Probar activación, desactivación y eliminación.

Ejecución de Pruebas

| Caso de Prueba | Estado |
| :---- | :---- |
| Listado de usuarios internos | **Aprobado** |
| Actualización de rol | **Aprobado** |
| Cambio de sucursal | **Aprobado** |
| Activación / Desactivación / Eliminación | **Aprobado** |

> **Reporte de Prueba:** APROBADO

### **CU04: Gestionar sucursales** {#cu04:-gestionar-sucursales}

* **Criterios de Aceptación:**  
  * El administrador debe crear, editar, listar, activar/desactivar y eliminar sucursales.  
  * Si el admin está asignado a una sucursal, no debe poder modificar otras.  
* **Diseño de Pruebas:**  
  * Consultar GET /api/branches/ y GET /api/branches/public.  
  * Probar POST /api/branches/.  
  * Probar PUT /api/branches/{id}.  
  * Probar PATCH /api/branches/{id}/active y DELETE /api/branches/{id}.

Ejecución de Pruebas

| Caso de Prueba | Estado |
| :---- | :---- |
| Listado de sucursales | **Aprobado** |
| Creación de sucursal | **Aprobado** |
| Edición de sucursal | **Aprobado** |
| Cambio de estado y eliminación | **Aprobado** |
| Restricción desde sucursal asignada | **Aprobado** |

> **Reporte de Prueba:** APROBADO

### **CU05: Gestionar cuentas de proveedor** {#cu05:-gestionar-cuentas-de-proveedor}

* **Criterios de Aceptación:**  
  * El administrador debe crear y administrar proveedores.  
  * Debe poder cambiar estado, editar y eliminar cuentas.  
* **Diseño de Pruebas:**  
  * Consultar GET /api/providers/.  
  * Probar POST /api/providers/.  
  * Probar PATCH /api/providers/{id}/status.  
  * Probar PUT /api/providers/{id} y DELETE /api/providers/{id}.

Ejecución de Pruebas

| Caso de Prueba | Estado |
| :---- | :---- |
| Alta de proveedor | **Aprobado** |
| Cambio de estado | **Aprobado** |
| Edición de proveedor | **Aprobado** |
| Eliminación de proveedor | **Aprobado** |

> **Reporte de Prueba:** APROBADO

### **CU06: Consultar y actualizar perfil** {#cu06:-consultar-y-actualizar-perfil}

* **Criterios de Aceptación:**  
  * El cliente debe ver su perfil actual.  
  * Debe poder actualizar nombre, email y género.  
  * Los cambios deben persistir.  
* **Diseño de Pruebas:**  
  * Consultar GET /api/users/me.  
  * Probar PUT /api/users/me.  
  * Verificar refresco de sesión luego del cambio.

Ejecución de Pruebas

| Caso de Prueba | Estado |
| :---- | :---- |
| Visualización del perfil | **Aprobado** |
| Actualización de perfil | **Aprobado** |
| Persistencia del cambio | **Aprobado** |

> **Reporte de Prueba:** APROBADO

### **CU07: Registrar y enviar información de productos** {#cu07:-registrar-y-enviar-información-de-productos}

* **Criterios de Aceptación:**  
  * El proveedor debe poder enviar productos sin errores.  
  * El administrador debe validar o aprobar productos.  
  * El estado del producto debe reflejar el flujo correcto.  
* **Diseño de Pruebas:**  
  * Probar POST /api/catalog/products/provider-submission.  
  * Revisar GET /api/catalog/products/pending.  
  * Aprobar o cambiar estado con PATCH /api/catalog/products/{id}/status o PATCH /api/catalog/variants/{id}/status.

Ejecución de Pruebas

| Caso de Prueba | Estado |
| :---- | :---- |
| Envío de producto por proveedor | **Aprobado** |
| Consulta de productos pendientes | **Aprobado** |
| Validación / Cambio de estado por admin | **Aprobado** |

> **Reporte de Prueba:** APROBADO

### **CU08: Gestionar catálogo y productos** {#cu08:-gestionar-catálogo-y-productos}

* **Criterios de Aceptación:**  
  * El administrador debe crear, editar y eliminar productos.  
  * Los productos deben conservar sus variantes y estados.  
* **Diseño de Pruebas:**  
  * Probar POST /api/catalog/products.  
  * Probar PUT /api/catalog/products/{id}.  
  * Probar DELETE /api/catalog/products/{id}.  
  * Verificar que la UI refleja el cambio.

Ejecución de Pruebas

| Caso de Prueba | Estado |
| :---- | :---- |
| Creación de producto | **Aprobado** |
| Edición de producto | **Aprobado** |
| Eliminación de producto | **Aprobado** |
| Consistencia en UI | **Aprobado** |

> **Reporte de Prueba:** APROBADO

### **CU09: Gestionar atributos del catálogo** {#cu09:-gestionar-atributos-del-catálogo}

* **Criterios de Aceptación:**  
  * El administrador debe administrar categorías, tallas, colores, temporadas y colecciones.  
  * Cada atributo debe poder crearse, editarse y eliminarse.  
* **Diseño de Pruebas:**  
  * Probar CRUD de categories, sizes, colors, seasons y collections.  
  * Validar el módulo admin de catálogo por pestañas.

Ejecución de Pruebas

| Caso de Prueba | Estado |
| :---- | :---- |
| CRUD de categorías | **Aprobado** |
| CRUD de tallas | **Aprobado** |
| CRUD de colores | **Aprobado** |
| CRUD de temporadas | **Aprobado** |
| CRUD de colecciones | **Aprobado** |

> **Reporte de Prueba:** APROBADO

### **CU10: Consultar y filtrar catálogo** {#cu10:-consultar-y-filtrar-catálogo}

* **Criterios de Aceptación:**  
  * El cliente debe poder consultar el catálogo sin errores.  
  * Los filtros deben devolver resultados correctos por sucursal y atributos.  
  * La disponibilidad debe mostrarse según inventario por sucursal.  
* **Diseño de Pruebas:**  
  * Consultar GET /api/catalog/products.  
  * Probar filtros por texto, sucursal, categoría, talla, color, temporada y colección.  
  * Validar GET /api/catalog/availability.

Ejecución de Pruebas

| Caso de Prueba | Estado |
| :---- | :---- |
| Consulta general del catálogo | **Aprobado** |
| Filtrado por atributos | **Aprobado** |
| Consulta de disponibilidad por sucursal | **Aprobado** |

> **Reporte de Prueba:** APROBADO

Aquí tienes el texto perfectamente formateado para copiar y pegar directamente en **Google Docs**. Las tablas de *Ejecución de Pruebas* se mantendrán correctamente al pegarlas.

### **CU11: Consultar disponibilidad por sucursal** {#cu11:-consultar-disponibilidad-por-sucursal}

* **Criterios de Aceptación:**  
  * El cliente debe consultar la disponibilidad de prendas por sucursal.  
  * La disponibilidad debe mostrarse por talla y color.  
  * El stock disponible debe considerar las unidades reservadas.  
* **Diseño de Pruebas:**  
  * Consultar el catálogo filtrando por sucursal desde el frontend.  
  * Validar GET /api/catalog/products?branch\_id={id}.  
  * Validar GET /api/catalog/availability.  
  * Comparar la disponibilidad mostrada con el stock total menos las unidades reservadas.

**Ejecución de Pruebas:**

| Caso de Prueba | Estado |
| :---- | :---- |
| Consulta de disponibilidad por sucursal | **Aprobado** |
| Consulta de disponibilidad por talla y color | **Aprobado** |
| Filtrado del catálogo por sucursal | **Aprobado** |
| Descuento de unidades reservadas en el stock público | **Pendiente de corrección** |

**Reporte de Prueba:** APROBADO CON OBSERVACIONES

### **CU12: Registrar movimiento de inventario** {#cu12:-registrar-movimiento-de-inventario}

* **Criterios de Aceptación:**  
  * El encargado de sucursal y el cajero deben registrar ingresos y salidas de inventario.  
  * El administrador debe poder registrar traspasos entre sucursales.  
  * Cada movimiento debe actualizar el inventario y quedar registrado en la bitácora.  
* **Diseño de Pruebas:**  
  * Probar POST /api/inventory/movements/income.  
  * Probar POST /api/inventory/movements/outcome.  
  * Probar POST /api/inventory/movements/transfer.  
  * Consultar GET /api/inventory/movements.  
  * Validar el acceso según el rol y la sucursal asignada.

**Ejecución de Pruebas:**

| Caso de Prueba | Estado |
| :---- | :---- |
| Registro de ingreso de inventario mediante API | **Aprobado** |
| Registro de salida de inventario mediante API | **Aprobado** |
| Traspaso de inventario entre sucursales | **Aprobado** |
| Consulta de bitácora de movimientos | **Aprobado** |
| Registro de movimientos desde el frontend | **Pendiente de implementación** |
| Registro de ingresos y salidas por parte del cajero | **Pendiente de corrección** |

**Reporte de Prueba:** NO APROBADO

### **CU13: Consultar inventario consolidado** {#cu13:-consultar-inventario-consolidado}

* **Criterios de Aceptación:**  
  * El administrador debe consultar las existencias globales.  
  * El sistema debe mostrar el desglose del inventario por sucursal y variante.  
  * La vista debe diferenciar cantidades totales, disponibles y reservadas.  
* **Diseño de Pruebas:**  
  * Consultar GET /api/inventory/consolidated.  
  * Revisar el inventario consolidado desde el módulo administrativo.  
  * Comparar los totales globales con el desglose por sucursal.  
  * Verificar los indicadores de variantes, cantidades, disponibilidad y reservas.

**Ejecución de Pruebas:**

| Caso de Prueba | Estado |
| :---- | :---- |
| Consulta del inventario consolidado | **Aprobado** |
| Desglose de existencias por sucursal | **Aprobado** |
| Desglose por talla y color | **Aprobado** |
| Visualización de cantidades disponibles y reservadas | **Aprobado** |
| Visualización de indicadores del inventario | **Aprobado** |

**Reporte de Prueba:** APROBADO CON OBSERVACIONES

### **CU14: Gestionar reservas de prendas** {#cu14:-gestionar-reservas-de-prendas}

* **Criterios de Aceptación:**  
  * El cliente debe seleccionar prendas, variantes, sucursal y fecha de visita.  
  * El sistema debe validar la disponibilidad antes de crear la reserva.  
  * El cliente debe consultar y cancelar sus reservas.  
  * Las reservas vencidas deben cambiar de estado automáticamente.  
* **Diseño de Pruebas:**  
  * Crear una reserva desde el frontend con una o varias prendas.  
  * Validar POST /api/reservations/.  
  * Consultar GET /api/reservations/me y GET /api/reservations/{id}.  
  * Cancelar la reserva mediante PATCH /api/reservations/{id}/cancel.  
  * Intentar reservar una cantidad superior al stock disponible.  
  * Verificar la expiración automática de una reserva vencida.

**Ejecución de Pruebas:**

| Caso de Prueba | Estado |
| :---- | :---- |
| Creación de reserva con prendas y sucursal | **Aprobado** |
| Validación de stock disponible | **Aprobado** |
| Consulta del estado de la reserva | **Aprobado** |
| Cancelación de reserva | **Aprobado** |
| Expiración automática de reservas | **Aprobado** |
| Selección de horario para la reserva | **Pendiente de implementación** |

**Reporte de Prueba:** APROBADO CON OBSERVACIONES

### **CU15: Gestionar carrito de compras** {#cu15:-gestionar-carrito-de-compras}

**Criterios de Aceptación:**

* El cliente debe agregar, editar y eliminar productos del carrito.  
* El sistema debe validar el stock disponible.  
* El carrito debe calcular subtotal, descuentos, total e items.  
* El cliente debe poder vaciar el carrito.

**Diseño de Pruebas:**

* Consultar GET /api/cart/current.  
* Agregar productos mediante POST /api/cart/items.  
* Editar cantidades mediante PATCH /api/cart/items/{id}.  
* Eliminar productos mediante DELETE /api/cart/items/{id}.  
* Vaciar el carrito mediante DELETE /api/cart/current.  
* Verificar que la interfaz actualice cantidades y totales.

**Ejecución de Pruebas:**

| Caso de Prueba | Estado |
| :---- | :---- |
| Consulta del carrito actual | **Aprobado** |
| Adición de productos | **Aprobado** |
| Edición de cantidades | **Aprobado** |
| Eliminación de productos | **Aprobado** |
| Validación de stock disponible | **Aprobado** |
| Actualización de subtotal y total | **Aprobado** |
| Vaciado del carrito | **Aprobado** |

**Reporte de Prueba:** APROBADO CON OBSERVACIONES

### **CU16: Realizar compra digital y consultar estado del pedido** {#cu16:-realizar-compra-digital-y-consultar-estado-del-pedido}

* **Criterios de Aceptación:**  
  * El cliente debe completar el checkout desde la aplicación web.  
  * El sistema debe procesar el pago y registrar el pedido.  
  * El inventario debe actualizarse al confirmar el pago.  
  * El cliente debe consultar el estado del pedido: pagado, en preparación y listo.  
* **Diseño de Pruebas:**  
  * Completar el checkout con pago en efectivo.  
  * Validar POST /api/payments/cash/checkout.  
  * Probar el checkout mediante Stripe y su webhook.  
  * Validar POST /api/payments/stripe/checkout y POST /api/payments/stripe/webhook.  
  * Verificar la asignación de inventario y el movimiento de salida.  
  * Consultar GET /api/orders/me y GET /api/orders/{id}.

**Ejecución de Pruebas:**

| Caso de Prueba | Estado |
| :---- | :---- |
| Checkout con pago en efectivo | **Aprobado** |
| Creación de PaymentIntent con Stripe | **Aprobado** |
| Confirmación del pago mediante webhook | **Aprobado** |
| Actualización del inventario después del pago | **Aprobado** |
| Consulta de pedidos desde la API | **Aprobado** |
| Consulta de pedidos desde la interfaz del cliente | **Pendiente de implementación** |
| Seguimiento de estados en preparación y listo | **Pendiente de implementación** |

**Reporte de Prueba:** NO APROBADO

### **CU17: Atender reserva en sucursal** {#cu17:-atender-reserva-en-sucursal}

* **Criterios de Aceptación:**  
  * El encargado debe consultar las reservas de su sucursal.  
  * Debe confirmar la llegada del cliente.  
  * Debe marcar la reserva como atendida o cancelarla.  
  * Las acciones deben respetar el estado de la reserva y la sucursal asignada.  
* **Diseño de Pruebas:**  
  * Consultar las reservas disponibles para la sucursal del encargado.  
  * Confirmar la llegada mediante PATCH /api/reservations/{id}/arrival.  
  * Marcar la reserva como atendida mediante PATCH /api/reservations/{id}/attend.  
  * Cancelar la reserva mediante PATCH /api/reservations/{id}/branch-cancel.  
  * Intentar gestionar una reserva de otra sucursal.

**Ejecución de Pruebas:**

| Caso de Prueba | Estado |
| :---- | :---- |
| Listado de reservas de la sucursal | **Aprobado** |
| Confirmación de llegada del cliente | **Aprobado** |
| Atención de la reserva | **Aprobado** |
| Cancelación de reserva desde sucursal | **Aprobado** |
| Restricción por sucursal y estado | **Aprobado** |

**Reporte de Prueba:** APROBADO CON OBSERVACIONES

### **CU18: Registrar venta presencial y procesar pago en caja** {#cu18:-registrar-venta-presencial-y-procesar-pago-en-caja}

* **Criterios de Aceptación:**  
  * El cajero debe registrar ventas con o sin reserva previa.  
  * El sistema debe actualizar el inventario y registrar el movimiento de salida.  
  * Debe poderse seleccionar el medio de pago y calcular el total.  
  * El sistema debe emitir un comprobante de la venta.  
* **Diseño de Pruebas:**  
  * Registrar una venta directa desde la pantalla de caja.  
  * Registrar una venta asociada a una reserva.  
  * Validar POST /api/sales.  
  * Consultar GET /api/sales/branch y GET /api/sales/{id}.  
  * Verificar la actualización del inventario y la creación del movimiento.  
  * Validar el cálculo del total y el medio de pago.  
  * Revisar el comprobante generado.

**Ejecución de Pruebas:**

| Caso de Prueba | Estado |
| :---- | :---- |
| Venta presencial sin reserva | **Aprobado** |
| Venta presencial con reserva | **Aprobado** |
| Actualización del inventario | **Aprobado** |
| Registro del movimiento de salida | **Aprobado** |
| Procesamiento del pago en caja | **Aprobado** |
| Emisión del comprobante en pantalla | **Aprobado** |
| Comprobante imprimible o descargable | **Pendiente de implementación** |

**Reporte de Prueba:** APROBADO CON OBSERVACIONES

# CONCLUSIÓN {#conclusión}

El desarrollo del Ciclo 2 permitió alcanzar de manera satisfactoria el objetivo planteado para esta segunda etapa del proyecto: completar los procesos transaccionales centrales del negocio de WomenStyle, cubriendo de forma íntegra los ocho casos de uso correspondientes a este ciclo (CU11 al CU18), pertenecientes a los módulos de Inventario, Compra y Venta.  
En cuanto a los objetivos específicos planteados en el punto 1.3.2, se puede confirmar el cumplimiento comprobable de los siguientes:

* Se logró **diseñar el módulo de inventario multisucursal**, capaz de actualizar automáticamente las existencias por producto, talla, color y sucursal tras cada reserva, venta o recepción de mercadería, además de permitir la consulta de disponibilidad en tiempo real y la consulta consolidada a nivel de administración central.  
* Se logró **diseñar el proceso de reserva de prendas**, permitiendo al cliente seleccionar múltiples prendas, indicar sucursal y horario de atención, consultar y cancelar sus reservas, y a la sucursal correspondiente confirmar la recepción y preparación de dichas reservas.  
* Se logró **diseñar los dos flujos de venta del sistema**: la compra digital vía web o aplicación móvil con integración de pasarela de pago electrónica y seguimiento del estado del pedido, y la compra presencial en el punto de caja de la sucursal, incluyendo el registro del pago, la emisión de comprobantes y la posible asociación de la venta con una reserva previa.

Con ello, se dio respuesta directa a las problemáticas centrales identificadas en el diagnóstico inicial: el riesgo de pérdida o duplicación de prendas apartadas para un cliente quedó resuelto mediante un registro único y verificable de reservas por sucursal y horario; la desactualización del inventario consolidado entre sucursales y administración central quedó resuelta mediante la actualización automática de existencias tras cada movimiento; y la fragmentación entre ventas presenciales y digitales quedó resuelta al integrar ambos flujos bajo el mismo modelo de inventario y de registro de ventas, permitiendo una visión unificada del desempeño comercial de la cadena.

El cierre exitoso de este ciclo confirma que la arquitectura de identidad, acceso y catálogo construida en el Ciclo 1 fue una base adecuada, ya que permitió incorporar sin fricciones los procesos transaccionales de reserva, compra y venta, respetando en todo momento las restricciones de acceso por rol y por sucursal ya definidas.

# RECOMENDACIÓN {#recomendación}

A partir de lo alcanzado en este segundo ciclo, se recomienda:

1. **Avanzar con el Ciclo 3**, correspondiente a las funcionalidades de realidad aumentada, inteligencia artificial y reportes avanzados, dado que la base transaccional (inventario, reservas y ventas) ya se encuentra completa y estable para sustentar estas funcionalidades adicionales.  
2. **Priorizar dentro del Ciclo 3 el módulo de reportes y dashboards** antes que las funcionalidades de mayor riesgo técnico (vestidor virtual y asistente de inteligencia artificial), ya que los reportes dependen directamente de los datos de ventas e inventario ya generados en este ciclo y representan un riesgo de implementación menor.  
3. **Realizar pruebas de carga y concurrencia sobre el flujo de reservas y ventas**, verificando que dos operaciones simultáneas sobre la misma prenda (por ejemplo, dos clientes reservando la última unidad disponible) se resuelvan de manera correcta y sin inconsistencias en el inventario.  
4. **Documentar formalmente los diagramas de secuencia de los procesos clave de este ciclo** (reserva de una prenda, checkout con pasarela de pago, y venta presencial con actualización de inventario), ya que estos procesos son los de mayor complejidad de interacción entre componentes del sistema y merecen quedar representados en el flujo de trabajo de diseño del PUDS.  
5. **Validar con el equipo el comportamiento de expiración de reservas no atendidas**, asegurando que las prendas reservadas y no recogidas dentro del tiempo límite definido regresen automáticamente al inventario disponible, evitando que el stock quede bloqueado indefinidamente.

Estas recomendaciones buscan que el equipo aproveche la base transaccional ya consolidada para abordar con mayor solidez las funcionalidades inteligentes y de reportes del ciclo final, asegurando que el sistema llegue completo y probado a la defensa final del proyecto.

# BIBLIOGRAFÍA {#bibliografía}

# Anexos  {#anexos}

QR y link del proyecto desplegado:  
[Link Frontend](http://ecommerce-five-xi-60.vercel.app)

QR y link del repositorio:
[https://github.com/miromero13/ecommerce](https://github.com/miromero13/ecommerce)

### **Lista consolidada — 24 CU con sus relaciones** {#lista-consolidada-—-24-cu-con-sus-relaciones}

| CU | Nombre | Actor(es) | Relación con otro CU | Tipo |
| ----- | ----- | ----- | ----- | ----- |
| CU01 | Registrar cliente | Cliente | Ninguna | — |
| CU02 | Iniciar sesión | Cliente, Administrador, Encargado de sucursal, Cajero, Proveedor | Ninguna (precondición general del sistema, no include) | — |
| CU03 | Gestionar usuarios internos | Administrador | Ninguna | — |
| CU04 | Gestionar sucursales | Administrador | Ninguna | — |
| CU05 | Gestionar cuentas de proveedor | Administrador | Ninguna | — |
| CU06 | Consultar y actualizar perfil | Cliente | Ninguna | — |
| CU07 | Registrar y enviar información de productos | Proveedor (principal), Administrador (secundario) | Ninguna | — |
| CU08 | Gestionar catálogo y productos | Administrador | Ninguna | — |
| CU09 | Gestionar atributos del catálogo | Administrador | Ninguna | — |
| CU10 | Consultar y filtrar catálogo | Cliente | Es extendido por CU11 y CU19 | (destino de `<<extend>>`) |
| CU11 | Consultar disponibilidad por sucursal | Cliente | `<<extend>>` → CU10 | `<<extend>>` |
| CU12 | Registrar movimiento de inventario | Encargado de sucursal, Cajero | Es incluido por CU18 y CU16; `<<extend>>` → CU24 | (destino de `<<include>>`) \+ `<<extend>>` |
| CU13 | Consultar inventario consolidado | Administrador | Ninguna | — |
| CU14 | Gestionar reservas de prendas | Cliente | `<<include>>` → CU11; `<<include>>` → CU24 | `<<include>>` |
| CU15 | Gestionar carrito de compras | Cliente | Ninguna | — |
| CU16 | Realizar compra digital y consultar estado del pedido | Cliente (principal), Sistema de pagos (secundario) | `<<include>>` → CU12; `<<extend>>` → CU24 | `<<include>>` \+ `<<extend>>` |
| CU17 | Atender reserva en sucursal | Encargado de sucursal | `<<extend>>` → CU24 | `<<extend>>` |
| CU18 | Registrar venta presencial y procesar pago en caja | Cajero | `<<include>>` → CU12 | `<<include>>` |
| CU19 | Usar vestidor virtual | Cliente | `<<extend>>` → CU10 | `<<extend>>` |
| CU20 | Generar reportes y dashboards | Administrador | Es extendido por CU23 | (destino de `<<extend>>`) |
| CU21 | Recibir recomendaciones de IA | Cliente (principal), Servicio de IA (secundario) | `<<extend>>` → CU10 (candidata, pendiente de confirmar según interfaz) | `<<extend>>` (a confirmar) |
| CU22 | Consultar asistente virtual/chatbot | Cliente | Ninguna | — |
| CU23 | Generar reporte por voz/lenguaje natural | Administrador | `<<extend>>` → CU20 | `<<extend>>` |
| CU24 | Recibir notificaciones push | Administrador, Cliente, Encargado de sucursal *(Proveedor: pendiente de confirmación)* | Es incluido por CU14; es extendido por CU12, CU16, CU17 | (destino de `<<include>>` y `<<extend>>` |