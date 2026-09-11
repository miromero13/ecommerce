# 1\. PERFIL 

## **1.1. INTRODUCCIÓN** 

Actualmente el comercio de indumentaria es uno de los sectores más dinámicos del retail a nivel mundial, y en las últimas dos décadas ha experimentado una transformación profunda impulsada por la digitalización. Las tiendas de ropa físicas tradicionales han evolucionado hacia modelos omnicanal, en los que el cliente puede investigar, comparar y comprar prendas tanto en establecimientos físicos como en plataformas digitales, integrando catálogos en línea, aplicaciones móviles, pasarelas de pago electrónicas y sistemas de gestión de inventario en tiempo real. 

Grandes cadenas internacionales de moda han incorporado tecnologías como la realidad aumentada para permitir a sus clientes visualizar prendas antes de probárselas físicamente, así como sistemas de inteligencia artificial para ofrecer recomendaciones personalizadas según el historial de compra y las preferencias de cada usuario. Estas innovaciones, además de modernizar la experiencia de compra, también han optimizado la gestión logística e interna de las empresas del rubro, permitiendo administrar de manera centralizada múltiples sucursales, proveedores y temporadas de colección. 

En Bolivia, el sector de venta de ropa mantiene una fuerte presencia de comercio presencial, aunque en los últimos años se ha observado un crecimiento sostenido de tiendas que incorporan canales digitales complementarios, como catálogos web, redes sociales y aplicaciones de venta, especialmente en las principales ciudades del eje troncal. Las cadenas de tiendas de ropa que operan con varias sucursales enfrentan el reto particular de coordinar de manera integrada el inventario, la disponibilidad de tallas y colores, y los procesos de venta entre sus distintos puntos físicos, a la par de ofrecer canales digitales que complementen —y no reemplacen— la experiencia de prueba física de las prendas, que continúa siendo un factor determinante en la decisión de compra del cliente. 

En este contexto se enmarca WomenStyle, una cadena de tiendas de ropa que opera con múltiples sucursales distribuidas en distintas ciudades de Bolivia. WomenStyle ha construido su presencia comercial ofreciendo prendas de vestir organizadas por categorías, temporadas y colecciones, trabajando con diversos proveedores que abastecen de manera periódica su catálogo de acuerdo a las tendencias de cada temporada comercial (primavera-verano, otoño-invierno, entre otras). Actualmente, la empresa gestiona sus operaciones de manera independiente en cada sucursal: el cliente puede acudir físicamente a cualquiera de sus tiendas para conocer el catálogo disponible, seleccionar prendas de las tallas y colores que desea, probárselas en los vestidores físicos y realizar la compra directamente en el punto de caja de la sucursal correspondiente. La actualización del inventario y el registro de las ventas se realizan a nivel de cada sucursal, y la comunicación entre estas y la administración central se da de forma periódica para consolidar la información de existencias, movimientos de mercadería y desempeño comercial de la cadena. 

Frente al crecimiento de la demanda de experiencias de compra más ágiles y flexibles, FashionStore ha identificado la oportunidad de complementar su operación presencial con una plataforma digital que integre sus canales web y móvil, permitiendo a sus clientes explorar el catálogo completo de la cadena, verificar la disponibilidad de prendas por sucursal y reservar productos antes de acudir a probárselos físicamente, incorporando además tecnologías emergentes como la realidad aumentada y la inteligencia artificial para enriquecer la experiencia de compra tanto presencial como digital. 

## **1.2. ANTECEDENTES**

2.1. Fundamentación teórica 

El desarrollo de plataformas de comercio electrónico inteligentes para el rubro de la moda responde a una transformación real y medible del sector, no a una tendencia pasajera. La incorporación de tecnologías como la inteligencia artificial y la realidad aumentada en la experiencia de compra tiene relevancia porque ataca dos de los mayores desafíos históricos del e-commerce de ropa: la incertidumbre sobre cómo lucirá una prenda antes de comprarla, y la dificultad de ofrecer al cliente una experiencia de descubrimiento de productos verdaderamente personalizada. Un sistema de este tipo es relevante en la medida en que logra articular, bajo una misma plataforma, la operación física de una cadena de tiendas (sucursales, inventario, punto de venta) con sus canales digitales (catálogo web, aplicación móvil, pasarela de pago), evitando que ambos mundos funcionen como sistemas aislados.

Lo que este proyecto se propone hacer es diseñar y modelar (siguiendo el Proceso Unificado de Desarrollo de Software (PUDS) y la notación UML) una plataforma que permita a WomenStyle centralizar la gestión de su catálogo, sus reservas de prendas, su inventario multisucursal y sus ventas (tanto presenciales como digitales), incorporando además un módulo de vestidores virtuales mediante realidad aumentada y funcionalidades de inteligencia artificial orientadas a la recomendación de productos.

El aporte de este documento consiste en traducir ese conjunto de necesidades de negocio en una especificación técnica completa y trazable: captura y análisis de requisitos, modelado de casos de uso y de la arquitectura del sistema, diseño de la base de datos y de los flujos de trabajo entre sucursales, y una propuesta tecnológica concreta (FastAPI, Angular, Flutter/Dart y PostgreSQL) que sirva de base para la implementación de un MVP funcional dentro del plazo académico establecido.

2.2. Sistemas similares 

Para fundamentar el diseño de FashionStore se revisaron casos de sistemas reales que ya implementan, de forma independiente, algunas de las funcionalidades que la plataforma busca integrar:

**Probador virtual con inteligencia artificial (Zara).** En años recientes Zara incorporó a su aplicación móvil una herramienta de prueba virtual basada en IA generativa: el cliente sube una fotografía de su rostro y una de cuerpo completo, con las cuales el sistema genera un avatar personalizado que se viste con la prenda elegida y gira 360° para mostrar el ajuste desde distintos ángulos. Este caso es relevante porque el beneficio reportado por la marca ha sido una reducción de dos dígitos en las devoluciones asociadas a errores de talla, lo que confirma que un vestidor virtual no es solo una mejora estética de la experiencia, sino una herramienta que reduce costos logísticos concretos. FashionStore retoma esta idea, aunque orientada a realidad aumentada sobre la cámara del dispositivo en lugar de un avatar generado por IA.

**Recomendaciones personalizadas basadas en IA (Amazon).** Amazon construyó desde hace más de una década un sistema de recomendaciones que analiza el historial de navegación y compra de cada usuario mediante técnicas como el filtrado colaborativo, comparando patrones de comportamiento entre usuarios similares para sugerir productos. Este enfoque tiene un peso comercial considerable: la propia empresa ha reportado que cerca del 35% de sus ventas provienen de estas recomendaciones personalizadas. Este caso sirve de referencia para el módulo de recomendación de prendas de FashionStore, que buscará sugerir productos considerando preferencias, historial y disponibilidad del cliente. 

**Reserva y recogida en tienda — Click & Collect (Decathlon, Zara, H\&M).** Distintas cadenas de retail han consolidado un modelo en el que el cliente reserva o compra en línea y recoge (o se prueba) el producto físicamente en la sucursal de su preferencia. En el caso de Decathlon, los clientes pueden reservar productos en la tienda más cercana y recogerlos en pocas horas, un esquema especialmente útil para artículos de alta demanda. Este modelo es el antecedente directo del proceso de reserva de prendas que FashionStore plantea: el cliente selecciona varias prendas desde la app, indica sucursal y horario, y acude posteriormente a probárselas antes de decidir la compra.

Estos tres casos (vestidor virtual, motor de recomendación e integración de reserva digital con atención físicaI) constituyen la base conceptual sobre la cual se diseñará la plataforma de FashionStore, adaptando cada una de estas ideas a la escala y al contexto de una cadena de tiendas de ropa que opera en Bolivia.

## **1.3. OBJETIVOS** 

### **1.3.1. Objetivo General** 

Desarrollar una plataforma inteligente e-commerce con gestión de venta, reservas, inventario y probadores virtuales vía realidad aumentada para la cadena de tiendas Fashion Store.

### **1.3.2. Objetivo Específicos**

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

## **1.4. DESCRIPCIÓN DEL PROBLEMA** 

Trabajando dentro de la operación diaria de FashionStore, se identifican las siguientes situaciones en la cadena:

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

## **1.5. ALCANCE** 

El alcance del proyecto comprende el diseño, modelado y posterior implementación del MVP de una plataforma inteligente de comercio electrónico para FashionStore. A continuación, se detallan los requisitos funcionales organizados por módulos:

### **1\. MÓDULO DE USUARIOS Y ROLES**

Este módulo permitirá administrar el acceso a la plataforma y la estructura organizacional de la cadena, controlando qué puede hacer cada tipo de usuario según su rol.

Funcionalidades:

* Registro e inicio de sesión de clientes.  
* Autenticación y autorización mediante roles (JWT).  
* Gestión de usuarios internos: administradores, encargados de sucursal y cajeros.  
* Registro y administración de sucursales por ciudad.  
* Registro y gestión de proveedores.  
* Control de acceso a funcionalidades según el rol del usuario.  
* Consulta y actualización de datos de perfil del cliente.

  ### **2\. MÓDULO DE INVENTARIO**

Este módulo permitirá administrar el catálogo de prendas de la cadena y mantener actualizadas y sincronizadas las existencias de cada sucursal.

Funcionalidades:

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

  ### **3\. MÓDULO DE COMPRA**

Este módulo permitirá al cliente reservar prendas para probárselas en tienda y/o completar una compra digital desde la plataforma web o móvil.

Funcionalidades:

* Selección de múltiples prendas para reservar, indicando sucursal y horario aproximado de atención.  
* Notificación de la reserva a la sucursal correspondiente y consulta de su estado (pendiente, confirmada, atendida, cancelada).  
* Cancelación de reservas y definición de un tiempo límite de validez.  
* Adición y edición de productos en el carrito de compras.  
* Cálculo automático de totales, considerando promociones vigentes.  
* Compra digital desde plataforma web o aplicación móvil.  
* Integración con pasarela de pago electrónica.  
* Confirmación y comprobante de compra digital.  
* Seguimiento del estado del pedido (pagado, en preparación, listo para entrega o recogida).

  ### **4\. MÓDULO DE VENTA**

Este módulo permitirá registrar las ventas realizadas directamente en el punto de caja de la sucursal, incluyendo aquellas derivadas de una reserva previa.

Funcionalidades:

* Preparación y confirmación de recepción de prendas reservadas por parte del encargado de sucursal.  
* Registro de ventas presenciales por parte del cajero.  
* Asociación de la venta presencial con una reserva previa, si corresponde.  
* Procesamiento de pagos en punto de caja.  
* Emisión de comprobantes de venta.  
* Actualización automática del inventario tras cada venta presencial.

  ### **5\. MÓDULO DE REALIDAD AUMENTADA**

Este módulo permitirá al cliente visualizar de manera virtual cómo luciría una prenda, utilizando la cámara de su dispositivo móvil, sin necesidad de probársela físicamente.

Funcionalidades:

* Visualización de la prenda seleccionada sobre la imagen del cliente mediante realidad aumentada.  
* Integración con el catálogo de productos y sus características (color, talla, modelo).  
* Disponibilidad exclusiva desde la aplicación móvil.  
* Opción de guardar o compartir la visualización generada.

  ### **6\. MÓDULO DE REPORTES Y DASHBOARD**

Este módulo permitirá a la administración de FashionStore visualizar de manera consolidada el desempeño comercial y operativo de la cadena.

Funcionalidades:

* Reportes de ventas y compras por sucursal, producto y periodo.  
* Reportes de inventario y movimientos de mercadería.  
* Indicadores de reservas atendidas, canceladas y expiradas.  
* Dashboards visuales para apoyo a la toma de decisiones.  
* Exportación de reportes.

  ### **7\. MÓDULO DE ASISTENCIA INTELIGENTE**

Este módulo permitirá ofrecer sugerencias personalizadas de productos y asistencia mediante inteligencia artificial, tanto al cliente como a la administración.

Funcionalidades:

* Recomendación de prendas según historial de navegación o compra.  
* Recomendación considerando temporada, categoría, talla y disponibilidad.  
* Asistente virtual/chatbot para consultas del cliente sobre productos.  
* Generación de reportes bajo demanda para la administración, mediante comando de voz o lenguaje natural.

# PARTE I. FUNDAMENTACIÓN TEÓRICA

## **1\. E-commerce**

El comercio electrónico (e-commerce) se define como la práctica de comprar y vender bienes o servicios a través de Internet, abarcando todas las transacciones en línea, desde que un cliente navega por un sitio web hasta la entrega final de su compra. Detrás de toda plataforma de este tipo existen componentes técnicos comunes: escaparates en línea donde las empresas muestran sus productos, carritos de compra que permiten seleccionar artículos y proceder al pago, pasarelas de pago que procesan las transacciones de forma segura, y sistemas de gestión de inventario que actualizan la disponibilidad en tiempo real.

Existen distintas formas de clasificar el e-commerce según el tipo de actores que participan en la transacción: 

* el modelo B2B (business to business) involucra transacciones entre empresas conectadas mediante la red;   
* el modelo B2C (business to consumer) involucra transacciones entre una empresa y su clientela, usualmente a través de portales de venta oficiales;   
* el modelo C2B (consumer to business), donde la transacción se origina en el interés del propio cliente. 

A esta clasificación se suman modelos más recientes como el C2C (venta directa entre consumidores) y el social commerce, que traslada la venta a redes sociales como Instagram o TikTok sin que el usuario deba salir de la aplicación. 

Este marco conceptual es la base sobre la cual se analizan a continuación seis plataformas reales, tanto desde la perspectiva de quien compra como de quien desarrolla una tienda online.

1. ### **Como usuario**

   1. #### **Amazon.**

   Es mucho más que una tienda online: es un ecosistema de servicios que conecta compradores, vendedores, marcas, empresas, desarrolladores y usuarios que consumen contenido digital o servicios en la nube. Desde la perspectiva del comprador es importante distinguir entre Amazon Retail y Amazon Marketplace: cuando el cliente compra directamente a Amazon.com, la empresa se queda con todo el beneficio de la venta; cuando compra a un vendedor externo dentro del Marketplace, Amazon retiene una comisión fija y el resto va al vendedor. 

   Para el usuario final, esta diferencia se traduce en variedad y precio: el Marketplace le da acceso a una selección más amplia de productos, incluyendo artículos de nicho, con precios más competitivos gracias a la competencia entre vendedores, todo bajo la garantía y el sistema de pagos de Amazon. Como usuario final, la experiencia gira en torno a la búsqueda, la comparación de precios, las reseñas de otros compradores y el seguimiento del pedido hasta la entrega. 

      2. #### **Alibaba.**

   A diferencia de Amazon, Alibaba opera principalmente bajo un modelo B2B (empresa a empresa): proporciona un espacio en línea donde las empresas pueden comprar y vender productos al por mayor, ofreciendo herramientas para la búsqueda de productos, la negociación de precios y el pago. Su escala es considerable: la plataforma conecta a fabricantes, proveedores y distribuidores, principalmente de China, con compradores de todo el mundo, reuniendo más de 200 millones de productos en cientos de categorías. 

   Como usuario/comprador, la experiencia difiere bastante de Amazon: en Alibaba los proveedores publican catálogos de productos, establecen una cantidad mínima de pedido (MOQ) y ofrecen precios bajo condiciones comerciales internacionales (FOB/CIF), por lo que el proceso de compra suele incluir negociación directa con el proveedor antes de cerrar el pedido, algo poco común en plataformas orientadas al consumidor final.

      3. #### **Shopify.**

   Desde la óptica del usuario/comprador, Shopify no es una tienda en sí misma sino la infraestructura sobre la que operan miles de tiendas independientes: es una plataforma de comercio que ayuda a emprendedores, minoristas y marcas internacionales a vender online y en persona, gestionar su tienda y hacer crecer sus negocios. 

   Al comprar en una tienda construida sobre Shopify, el usuario normalmente encuentra un proceso de compra estandarizado (catálogo, carrito, checkout, confirmación) independientemente de la marca, ya que Shopify centraliza en una sola herramienta todo lo necesario para vender por internet: diseño de la tienda, gestión de productos, pagos y pedidos. Además, muchas tiendas Shopify integran su catálogo con redes sociales y marketplaces externos, lo que amplía los puntos de contacto para el comprador.

   2. ### **Como desarrollador**

      1. #### **Magento (Adobe Commerce).**

   Es una de las plataformas más utilizadas por equipos de desarrollo para construir tiendas complejas y a gran escala. Al ser una plataforma de código abierto, ofrece una infraestructura completa que las empresas pueden usar para construir, gestionar y hacer crecer sus tiendas online, permitiendo a los desarrolladores modificar y expandir sus funcionalidades libremente. Actualmente coexisten dos versiones: Magento Open Source, gratuita y de código abierto, pensada para equipos que buscan control total sobre su tienda; y Adobe Commerce, la versión comercial en la nube con funciones empresariales adicionales. 

   Para un desarrollador, el beneficio principal de Magento es que permite crear experiencias de compra multicanal tanto para clientes B2B como B2C en una sola plataforma, aunque su configuración exige conocimientos técnicos más avanzados que otras alternativas.

      2. #### **PrestaShop.**

   Es un sistema de gestión de contenidos (CMS) especializado en comercio electrónico, popular especialmente en Europa y América Latina. Está desarrollado completamente en PHP, MySQL y Smarty, y desde su versión 1.7 incorpora el framework Symfony para mejorar el rendimiento de la plataforma. 

   Su arquitectura está pensada para que el desarrollador construya la tienda de forma incremental: permite crear comercios electrónicos modulares, es decir, se puede empezar con una tienda simple e ir añadiendo módulos según se necesiten, como métodos de pago adicionales, mejoras de SEO o sistemas de promoción. A nivel técnico, utiliza el patrón Modelo-Vista-Controlador (MVC) como arquitectura de software, además de tecnologías como JavaScript, HTML, CSS y jQuery, lo que la hace una opción intermedia entre la simplicidad de Shopify y la complejidad de Magento.

      3. #### **WooCommerce.**

   Es la opción más ligada al ecosistema WordPress: se trata específicamente de un plugin de WordPress que convierte un blog o sitio web en una tienda online. Su principal ventaja para un desarrollador es la rapidez de implementación sobre un sitio ya existente en WordPress, sin necesidad de migrar a una plataforma completamente distinta. Su adopción es muy amplia: cuenta con más de 5 millones de usuarios activos e impulsa alrededor del 40% del total de tiendas online del mundo. 

   A diferencia de Shopify (que es un servicio SaaS con costo mensual fijo), WooCommerce es gratuito, pero requiere que el desarrollador contrate por separado el hosting, los plugins adicionales y otros servicios necesarios para mantener la tienda, lo que le da más flexibilidad de personalización a cambio de asumir la responsabilidad del mantenimiento técnico.

## **2\. Pasarelas de pago**

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

## **3\. Deliverys**

1. ### **¿Cómo funcionan los servicios de delivery?**

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

   Yummy es una superapp de delivery de origen venezolano que, en Bolivia, absorbió a la plataforma local YAIGO (fundada como un emprendimiento boliviano que llegó a ser la app más descargada del país antes de la adquisición). Bajo su modelo actual, Yummy no se limita a comida: dentro de la misma aplicación integra supermercados, farmacias, entradas a eventos y, en algunos mercados de la región, incluso venta de ropa. Su funcionamiento se apoya en una flota de repartidores ("Yummers") activa los siete días de la semana, y ofrece múltiples métodos de pago tanto en moneda local como internacional dentro de la misma app. Este ejemplo es relevante para el proyecto porque ilustra cómo una plataforma de delivery puede evolucionar de una app enfocada en comida hacia un marketplace más amplio que incluye retail, algo conceptualmente cercano a lo que FashionStore necesitaría si en el futuro decidiera tercerizar la entrega a domicilio de sus compras digitales en lugar de operarla internamente.

      6. **PedidosYa**

   PedidosYa es una de las plataformas de delivery más consolidadas en Bolivia y en general en América Latina. Además de su servicio tradicional de comida, opera un servicio específico de "Envíos" para mensajería de paquetes y documentos, disponible en varias ciudades bolivianas (Santa Cruz, Cochabamba, La Paz, El Alto, entre otras). Es particularmente útil como referencia porque su mecánica de cálculo de tarifa es explícita y basada en distancia: el sistema cobra una tarifa fija por los primeros kilómetros de recorrido, y a partir de ahí aplica un recargo adicional por cada kilómetro extra que deba recorrer el repartidor entre el punto de recojo y el de entrega, calculado automáticamente por la app según la ruta real. Además, el servicio impone restricciones de tamaño y peso al paquete (máximo 5 kg y dimensiones límite), lo cual es un patrón común entre los servicios de última milla: la tarifa y la elegibilidad del envío dependen tanto de la distancia recorrida como del tamaño/peso de la carga.

2. ### **Cómo calculan las plataformas el costo de una entrega**

   De los casos revisados se pueden extraer los factores que, en general, determinan el costo de una entrega en este tipo de plataformas:

* **Distancia recorrida**: es el factor más determinante; normalmente se cobra una tarifa base por un primer tramo (por ejemplo, los primeros kilómetros) y luego un costo incremental por cada unidad de distancia adicional.  
* **Peso y tamaño del paquete**: los servicios de mensajería suelen limitar el peso y volumen máximo aceptado, y algunos aplican recargos si el paquete excede ciertas dimensiones estándar.  
* **Tiempo/demanda**: en varias plataformas de este tipo, la tarifa puede variar según la hora del día o la disponibilidad de repartidores en la zona (mecanismos de precio dinámico), aunque este componente varía según cada empresa y no siempre es visible para el usuario final.  
* **Frecuencia y volumen para negocios**: cuando el servicio se contrata a nivel empresarial (como es el caso de las cuentas B2B de Yango o PedidosYa), suele existir facturación consolidada periódica y, en algunos casos, tarifas preferenciales por volumen de envíos.

## **4\. PUDS**

1. ### **Concepto general**

El Proceso Unificado de Desarrollo de Software (PUDS), también conocido como Proceso Unificado (UP) o, en su implementación más difundida y documentada, como Proceso Unificado de Rational (RUP), es un marco de trabajo para el desarrollo de software que se caracteriza por tres rasgos definitorios: está **dirigido por casos de uso**, está **centrado en la arquitectura**, y es **iterativo e incremental**. En esencia, es un conjunto de actividades necesarias para transformar los requisitos de un usuario en un sistema de software funcional.

Que el proceso esté "dirigido por casos de uso" significa que cada iteración del desarrollo se organiza alrededor de un conjunto de casos de uso o escenarios que se llevan de principio a fin a través de todas las disciplinas del proyecto (requisitos, análisis, diseño, implementación y pruebas), en lugar de completar cada disciplina para todo el sistema antes de pasar a la siguiente, como ocurriría en un modelo en cascada tradicional. Que sea "iterativo e incremental" implica que el sistema no se entrega de una sola vez al final del proyecto, sino que se construye en ciclos sucesivos, cada uno de los cuales añade o mejora funcionalidades sobre la versión anterior, permitiendo detectar riesgos y ajustar el rumbo tempranamente en lugar de descubrir problemas graves al final del desarrollo.

2. ### **Fases del PUDS**

El PUDS organiza el trabajo de desarrollo en cuatro fases secuenciales, cada una de las cuales puede subdividirse a su vez en una o más iteraciones:

1) **Inicio.** Se define el alcance y los objetivos del negocio, se evalúa la factibilidad del proyecto, se identifican los riesgos críticos y se esboza una arquitectura candidata inicial. El énfasis está en comprender qué se va a construir y por qué.  
2) **Elaboración.** Se profundiza en el análisis del dominio del problema, se establece una arquitectura base sólida para la construcción posterior, y se planifican las actividades necesarias para completar el proyecto, mientras se sigue monitoreando activamente los riesgos identificados.  
3) **Construcción.** Es la fase donde se desarrolla la mayor parte del sistema: se implementan los casos de uso restantes en iteraciones sucesivas hasta obtener un producto funcional con todos los requisitos acordados con el cliente, típicamente entregando una versión beta hacia el final de la fase.  
4) **Transición.** El sistema se entrega formalmente a los usuarios finales: se corrigen errores detectados durante las pruebas, se ajusta el software al entorno real de producción (hardware, sistemas operativos), se elaboran los manuales correspondientes y se genera la versión formal del sistema.

3. ### **Disciplinas (flujos de trabajo)**

De forma transversal a las cuatro fases, el PUDS organiza el trabajo técnico en un conjunto de disciplinas (también llamadas flujos de trabajo), que en cada iteración desarrollan un modelo específico: 

* **Requisitos** (produce el modelo de casos de uso),   
* **Análisis y Diseño** (produce el modelo de diseño y el modelo de despliegue),   
* **Implementación** (produce el modelo de implementación, es decir, el código),  
* **Pruebas** (produce el modelo de pruebas). 

A estas se suman disciplinas de apoyo como la gestión de proyecto y la gestión de configuración y cambios. Es importante notar que todas las disciplinas participan en todas las fases, pero con distinto nivel de esfuerzo: por ejemplo, la disciplina de Requisitos tiene mucho peso en la fase de Inicio y va disminuyendo hacia la fase de Construcción, mientras que Implementación ocurre lo contrario.

Este esquema de fases y disciplinas es el que se seguirá para organizar el desarrollo de la plataforma FashionStore, documentando en cada flujo de trabajo (captura de requisitos, análisis, diseño e implementación) los artefactos y diagramas correspondientes.

## **5\. UML**

1. ### **Concepto general**

UML (Lenguaje Unificado de Modelado) es un lenguaje de modelado visual estandarizado que permite a los equipos de desarrollo visualizar, especificar, construir y documentar los artefactos de un sistema de software. Fue desarrollado en la década de 1990 por tres ingenieros de software —Grady Booch, Ivar Jacobson y James Rumbaugh, trabajando en Rational Software— con el objetivo de unificar en una sola notación los distintos métodos de modelado orientado a objetos que existían hasta entonces (cada uno de ellos había desarrollado previamente su propio método por separado). Hoy UML es mantenido como estándar por el OMG (Object Management Group) y está reconocido como estándar ISO/IEC 19505\.

La relación entre PUDS y UML es estrecha y complementaria: mientras que el PUDS define las actividades, fases y criterios para construir un sistema —desde la idea inicial hasta el software terminado—, UML aporta la notación gráfica con la que se representan y documentan los distintos modelos que se producen en cada iteración del proceso. Es decir, PUDS dice "qué hacer y cuándo", y UML aporta "cómo dibujarlo".

2. ### **Categorías de diagramas**

La especificación UML 2.5 define un total de 14 tipos de diagramas, agrupados en dos grandes categorías:

- **Diagramas estructurales**, que representan la vista estática del sistema (qué elementos lo componen y cómo se relacionan entre sí, independientemente del tiempo). Incluyen, entre otros: diagrama de clases (el más utilizado, muestra las clases del sistema, sus atributos, operaciones y las relaciones entre ellas), diagrama de objetos, diagrama de componentes, diagrama de despliegue, diagrama de paquetes, diagrama de estructura compuesta y diagrama de perfiles.  
- **Diagramas de comportamiento**, que capturan la vista dinámica del sistema (cómo interactúan sus elementos a lo largo del tiempo). Incluyen: diagrama de casos de uso (representa las funcionalidades del sistema desde la perspectiva de los actores que interactúan con él), diagrama de actividades (modela flujos de trabajo y procesos), diagrama de máquina de estados, y los diagramas de interacción (un subgrupo dentro de los de comportamiento) que comprenden el diagrama de secuencia, el diagrama de comunicación, el diagrama de temporización y el diagrama de vista de interacción.

3. ### **Diagramas relevantes para este proyecto**

Para el desarrollo de WomenStyle, siguiendo el flujo de trabajo del PUDS, se emplearán principalmente:

* **Diagrama de casos de uso**, en la disciplina de Requisitos, para representar las funcionalidades del sistema por cada actor identificado (cliente, administrador, encargado de sucursal, cajero, proveedor, sistema de pagos, servicio de IA).  
* **Diagrama de clases**, en la disciplina de Análisis y Diseño, para modelar las entidades del sistema (usuarios, prendas, sucursales, reservas, inventario, ventas) y sus relaciones.  
* **Diagrama de secuencia**, para representar la interacción entre los componentes del sistema en procesos clave como la reserva de una prenda, el flujo de compra digital con pasarela de pago, o la actualización de inventario tras una venta.  
* **Diagrama de actividades**, para modelar procesos de negocio más amplios, como el flujo completo de atención de una reserva desde que el cliente la solicita hasta que retira o compra la prenda en sucursal.  
* **Diagrama de despliegue**, en la disciplina de Implementación, para representar cómo se distribuyen los componentes del sistema (backend FastAPI, frontend Angular, app Flutter, base de datos PostgreSQL) sobre la infraestructura en la nube.

# PARTE II. PROCESO DE DESARROLLO

1. ## **FLUJO DE TRABAJO: CAPTURA DE REQUISITOS**

   1. ### **Identificar actores y casos de uso**

      1. #### **Actores**

* Cliente: Usuario que compra en la plataforma web o móvil. Consulta el catálogo, reserva y compra prendas, usa el vestidor virtual con realidad aumentada y recibe recomendaciones mediante IA.  
* Administrador: Supervisa el funcionamiento de la plataforma. Gestiona usuarios, sucursales, cuentas de proveedor y catálogo, valida la información enviada por proveedores, consulta el inventario consolidado y genera reportes.  
* Encargado de sucursal: Gestiona la operación diaria de su sucursal. Prepara las reservas, confirma la llegada del cliente y registra los movimientos de inventario locales.  
* Cajero: Atiende el punto de venta físico. Registra ventas presenciales, procesa pagos en caja y emite comprobantes.  
* Proveedor: Suministra prendas a la cadena. Registra y envía información de sus productos, indica disponibilidad y los asocia a temporadas o colecciones, sujeto a validación del administrador.

  2. #### **Casos de Uso**

  2. ### **Priorizar los Casos de Uso**

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


  3. ### **Detalle de Casos de Uso**

     #### **Ciclo \#1**

**CU01 – Registrar cliente**

![][image1]

**CU02 – Iniciar sesión**

![][image2]

**CU03 – Gestionar usuarios internos**

**CU04 – Gestionar sucursales**

**CU06 – Consultar y actualizar perfil**

**CU07 – Registrar y enviar información de productos**

**CU10 – Gestionar catálogo de prendas**

**CU11 – Gestionar atributos del catálogo**

**CU12 – Consultar y filtrar catálogo**

**CU13 – Consultar disponibilidad por sucursal**

**CU16 – Reservar prendas**

**CU17 – Consultar y cancelar reserva**

**CU18 – Gestionar carrito de compras**

 


4. ### **Prototipo de Interfaz de Usuario**

   5. ### **Estructurar el Modelo de Caso de Uso**

2. ## **FLUJO DE TRABAJO: ANÁLISIS**

   ### **2.1. Análisis de Arquitectura**

   #### **2.1.1. Identificar Paquetes**

   #### **2.1.2. Relacionar Paquete y Caso de Uso**

   ### **2.2. Análisis de Caso de Uso**

   ### **2.3. Análisis de una Clase**

   ### **2.4. Análisis de Paquete**

3. ## **FLUJO DE TRABAJO: DISEÑO**

   1. ### **Diseño de Arquitectura**

      #### **3.1.1. Diseño Físico(Diagrama de Despliegue)**

      #### **3.1.2. Diseño Lógico(Diagrama de Paquete)**

   2. ### **Diseño de Datos**

      #### **3.2.1. Diseño de Datos Lógico**

      ##### 3.2.1.1. Diagrama de Clase

      ##### 3.2.1.2. Mapeo

      ##### 3.2.1.3. Normalización

#### **3.2.2. Diseño de Datos Físico**

##### 3.2.2.1. Tabla de Volumen

##### 3.2.2.2. Script

#### **3.2.3. Diagrama Relacional**

#### **3.2.4. Actualización de Tuplas(Población de Datos)**

#### **3.2.5. Consultas**

#### **3.2.6. Procedimientos Almacenados**

#### **3.2.7. Triggers**

3. ### **Diseñar un Caso de Uso**

   4. ### **Diagrama de Secuencia**

   5. ### **Diagramas UML 2.5+**

      1. #### **Diagrama de Estado**

      2. #### **Diagrama de Tiempo**

      3. #### **Diagrama de Navegación**

      4. #### **Diagrama de Red**

4. ## **FLUJO DE TRABAJO: IMPLEMENTACIÓN**

5. ## **FLUJO DE TRABAJO: PRUEBAS**

# CONCLUSIÓN

# RECOMENDACIÓN

# BIBLIOGRAFÍA

Jacobson, I., Booch, G., & Rumbaugh, J. (1999). *El proceso unificado de desarrollo de software.* Addison-Wesley.

Booch, G., Rumbaugh, J., & Jacobson, I. (2000). *El lenguaje unificado de modelado. Guía de usuario.* (2a ed.). Addison-Wesley.

Rumbaugh, J., Jacobson, I., & Booch, G. (2005). *El lenguaje unificado de modelado: Manual de referencia*. Addison-Wesley.

Banco Central de Bolivia. *Pagos QR BCB Bolivia.* [https://www.bcb.gob.bo/?q=pagos\_qr\_bcb\_bolivia](https://www.bcb.gob.bo/?q=pagos_qr_bcb_bolivia) 

Checkout.com. *Qué es y cómo funciona una pasarela de pago.* [https://www.checkout.com/es-es/blog/que-es-pasarela-pago](https://www.checkout.com/es-es/blog/que-es-pasarela-pago) 

Libélula. *Pasarela Multicanal.* [https://libelula.bo/pasarela-multi-canal/](https://libelula.bo/pasarela-multi-canal/) 

Stripe. *Guía de pasarelas de pagos globales.* [https://stripe.com/es/resources/more/global-payment-gateways-101-what-they-are-how-they-work-and-how-to-choose-one](https://stripe.com/es/resources/more/global-payment-gateways-101-what-they-are-how-they-work-and-how-to-choose-one) 

Lucidchart. *Tutorial de Lenguaje de Modelado Unificado (UML).* [https://lucid.co/es/diagrama/uml/tutorial](https://lucid.co/es/diagrama/uml/tutorial) 

Ciberaula. *UML: Lenguaje Unificado de Modelado.* [https://www.ciberaula.com/cursos/java/uml.php](https://www.ciberaula.com/cursos/java/uml.php) 

Yango Delivery. *Servicio de entrega en Bolivia.* [https://delivery.yango.com/bo-es/](https://delivery.yango.com/bo-es/) 

Forbes Centroamérica. *Yummy de YAIGO, la Superapp de delivery llega a Bolivia y Paraguay.* [https://forbescentroamerica.com/2021/10/29/yummy-de-yaigo-la-superapp-de-delivery-llega-a-bolivia-y-paraguay](https://forbescentroamerica.com/2021/10/29/yummy-de-yaigo-la-superapp-de-delivery-llega-a-bolivia-y-paraguay) 

Bolivia Emprende. *Pedidos Ya ofrece servicio de transporte de paquetes en tres ciudades.* [https://boliviaemprende.com/noticias/pedidos-ya-ofrece-servicio-de-transporte-de-paquetes-en-tres-ciudades](https://boliviaemprende.com/noticias/pedidos-ya-ofrece-servicio-de-transporte-de-paquetes-en-tres-ciudades) 

# Anexos 

QR y link del repositorio:

[https://github.com/miromero13/ecommerce](https://github.com/miromero13/ecommerce)

**22 de septiembre \- Examen y presentación final** 

Plataforma y aplicación web de e-commerce para tienda de ropa con vestidores virtuales y realidad aumentada 

Uso del método PUDS (Proceso unificado del desarrollo de software). Implementación de realidad aumentada para los clientes. Uso de inteligencia artificial si es posible.

**Lenguajes:**

* Para móvil: Flutter \- Dart  
* Para web: Backend con Fast API (Python) y Frontend Angular (Typescript)  
* base de datos: Postgre SQL 

**Funcionalidades:**

* Puede ser ropa solo para hombres, mujeres o niños.

* Se podrá organizar (uso de filtros) en prendas por temporadas, liquidaciones, nuevos modelos, por tipo, entre otros filtros.  
* Se contará con catálogo de todo el stock de ropa de la tienda  
* Tendrá un proceso de reserva de prendas que selecciona el cliente.  
* Se implementará un Carrito de compras para la ropa seleccionada.  
* Pasarela de pago (Stripe por ejemplo) para app móvil, investigar los diferentes métodos tanto para móvil como web.  
* Contará con un seguimiento del envío y despacho de la prenda a domicilio o trabajo del cliente.  
* Contará con inventario y actualización de mercancía.  
* Dos tipos de ventas:   
  * compra directa desde la tienda o la web  
  * reserva de la prenda hasta que el cliente llegue a tienda física para probarse la prenda.

[image1]: <data:image/png;base64,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>

[image2]: <data:image/png;base64,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h/z7778fDR8+PP/+9J49FV877bRTtNFGG3XoNbLvZauttsrn3n333ba8nid77rln/vu3vU7lop+bHE5VgqIEFVLKMbWzS/a/y27oK4oS1Co1xOW06667Rtddd51Nd+B6KEp0ymbSpElt215//fWCzxHlV6xYYdMd2KJEn1kNv4oC5XWqScKiZPPNN49222236KqrrsoXPrfeems+719HDb+W9RqXXXZZfvkXv/hF2z56rSuvvDK/HvrqV78aHXLIIdHVV18dffazn82viwoSPU8T2P30pz/t8Hn1vah48j/nz3/+cz7v9/E9Rj/5yU+iqVOn5pf1nYmKEn3W888/P9puu+26/B77Sq/rqkkJRckTLnnzBFFslOrLLnleV5cSl6yMRclOrvPnI4gBCzVU5bTppptGr776qk13oJ9rhUWJtmvd8wWApTkydNfantiiJHwtFTQqQCQsSuz4Fp/3z73tttui733ve23bjz/++Pxn9/uEPR0hXen0zDPP2HT+Z3/wwQdt6wsXLoxOO+206LXXXsu/XqEeF/9e9ttvv+iOO+5oy+tn+/evouShhx5q26bn9FTE9UZ6PFWPEooSoBSlHFM6daP9X41jmNnWJ2UsSoCqMmLECNu+9InuMGxPS1jxj+00QFW9AL4hVQM9YcKEtm0vvfRSh0JCjbfW77zzzrZcd7orSsQWJSqq9tprrw77eOFz9d1pXaHeCPXw2H0s/1586HSXhDkf/vWWLl3alltvvfXaCh7/c/T4xhtvJD8g5bepKFm5cmWHPEUJ0HvFHFP+0uEH7IZyoShBDbPtS5+89957nXoZRD/n4IMPzi/rdEg4BkO23XbbtkZYBUn4vvbee+9o++23zy8///zzBRvh7pRalIgfw+KNGjUq/+ifq14a3fvF02mrYoqSKVOmdFj3+2oAb9i78tZbb0XNzc35AunMM89syx9zzDEdepRE40VaW1vb9rE9JRQlQPl0d0ytFcfHLrn6ZmOzrawoSlDDbPvSZxqsqQZef+FrYOXuu++eP23he0fmzZuXb8Tmz58fLV++PJozZ05+3RcquppG62qYfa/I4sWL89u0rEGkep4Pf9rD72P1pijRPnr/ogGvGl/i86IeC5/zVwtpMG+4TyEqZvS5ZdmyZW373nTTTflt+o78GJHHH3+8bTyNPqfou/WDV/1z/XgUfxXSZptt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>