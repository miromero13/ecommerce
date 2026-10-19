# Contexto del Proyecto – Segundo Parcial

**Materia:** Sistemas de Información II (S2-2026) – MSc. Ing. Angélica Garzón Cuéllar  
**Plataforma:** FashionStore SaaS (Evolución de E-Commerce a Plataforma B2B Multi-Tenant)  
**Metodología:** ICONIX con notación UML 2.5+  

---

## 1. Perfil del Proyecto

### 1.1. Introducción
Durante el primer examen parcial se construyó el prototipo funcional de FashionStore, una plataforma de comercio electrónico omnicanal para una cadena de tiendas de ropa con sucursales físicas, catálogo web, app móvil, realidad aumentada y probadores virtuales.

Para este segundo examen parcial, la solución evoluciona hacia un **modelo de negocio SaaS (Software as a Service) Multi-Tenant**. La plataforma deja de ser de uso exclusivo para una sola marca y pasa a comercializarse a terceros: múltiples empresas de moda pueden suscribirse mediante planes comerciales, disponiendo cada una de su propio entorno lógico aislado para administrar sucursales, empleados, catálogos, inventarios, clientes, reservas y ventas, sin interferencia entre organizaciones.

Asimismo, ante problemas recurrentes de conectividad en tiendas físicas, FashionStore adopta una arquitectura **Offline-First**:
* En **Web**: evolución a **Progressive Web App (PWA)** con Service Workers y almacenamiento local en **IndexedDB**.
* En **Móvil**: persistencia local estructurada con **SQLite** en la app Flutter.
* Ambas plataformas permiten registrar ventas de contado y reservas sin conexión, encolando operaciones para su sincronización diferida e idempotente con resolución de conflictos de inventario al recuperar conectividad.

Finalmente, la plataforma potencia sus capacidades de analítica e Inteligencia Artificial incorporando **reportes generativos por voz y texto en lenguaje natural** contra datos reales de la base de datos, junto con un módulo de **Machine Learning** (modelos supervisados y no supervisados entrenados con datos sintéticos y reales).

### 1.2. Fundamentación y Sistemas de Referencia
* **Arquitectura SaaS Multi-Tenant (Row-Level Security / Shared DB):** Similar a plataformas B2B como *Shopify Plus* o *Tiendanube*, donde múltiples marcas conviven sobre una misma infraestructura física y base de datos relacional (PostgreSQL), garantizando aislamiento estricto mediante identificador de organización (`tenant_id`) en cada consulta, tabla y transacción.
* **PWA y Operación Offline (Offline-First POS):** Siguiendo el estándar de sistemas POS modernos (*Square POS*, *Shopify POS*), las terminales de caja continúan facturando en efectivo aun cuando la red colapsa, almacenando transacciones localmente con identificadores universales (UUID/operation_id) y despachándolas atómicamente cuando el socket o la red se restablecen.
* **Reportes Generativos e Inteligencia Artificial:** Integración de modelos de lenguaje (LLMs vía API) para interpretar peticiones en lenguaje natural y traducirlas a filtros estructurados de negocio (*Text-to-Query*), evitando consultas SQL abiertas que comprometan la seguridad.

---

## 2. Objetivos del Proyecto

### 2.1. Objetivo General
Evolucionar la plataforma FashionStore hacia una solución de comercio electrónico SaaS multitenant funcional, incorporando planes de suscripción, aplicaciones web progresivas (PWA), operación offline en web y móvil con sincronización diferida, y reportes generativos mediante inteligencia artificial, aplicando la metodología ICONIX y garantizando la coherencia entre los modelos UML 2.5+ y la implementación en producción.

### 2.2. Objetivos Específicos
1. Aplicar la metodología **ICONIX** en el análisis, diseño y evolución del software.
2. Transformar FashionStore en una plataforma **SaaS Multi-Tenant** que aísle lógicamente la información entre múltiples empresas independientes.
3. Implementar **planes de suscripción** (Básico y Profesional) que regulen los límites operativos y funcionalidades habilitadas.
4. Evolucionar la aplicación web Angular hacia una **Progressive Web App (PWA)** instalable con Service Workers.
5. Implementar almacenamiento local con **IndexedDB** para navegación de catálogo y registro de transacciones offline en web.
6. Integrar **SQLite** en la aplicación móvil Flutter para persistencia local de catálogo, clientes, ventas y reservas.
7. Habilitar el registro de **ventas de contado y reservas sin conexión** a Internet en ambas plataformas cliente.
8. Desarrollar mecanismos de **sincronización diferida e idempotente** de operaciones pendientes hacia el backend.
9. Diseñar algoritmos para la **detección y tratamiento de conflictos de inventario** derivados de operaciones offline.
10. Incorporar **reportes generativos con IA** que respondan a lenguaje natural escrito y por voz con datos reales.
11. Implementar un módulo de **analítica inteligente con Machine Learning** (datos sintéticos, aprendizaje supervisado y no supervisado).
12. Desarrollar **pruebas automatizadas** funcionales, de integración y de reglas críticas de negocio.
13. Mantener la **coherencia documental** entre el código fuente y los modelos UML 2.5+.

---

## 3. Planteamiento del Problema

El desarrollo del segundo parcial atiende a cuatro problemáticas operativas y de negocio:
1. **Monolito de Marca Única vs. Escalabilidad SaaS:** La arquitectura inicial estaba acoplada a una sola empresa. Para comercializar el software, se requiere migrar toda la base de datos y la capa de servicios hacia multi-tenancy, impidiendo cualquier fuga de información (*Data Leakage*) entre marcas competidoras.
2. **Vulnerabilidad ante Cortes de Conectividad:** Las sucursales físicas sufren interrupciones de internet. Si el sistema exige conexión permanente, la tienda se paraliza, perdiendo ventas presenciales y dejando de atender reservas.
3. **Inconsistencia de Inventario en Operaciones Desconectadas:** Vender sin internet implica el riesgo de sobrevender stock si dos sucursales venden la misma prenda en paralelo. Se necesita un protocolo transaccional de sincronización con reglas claras de conciliación de inventario.
4. **Rigidez en la Consulta Analítica:** Los reportes estáticos predefinidos no satisfacen la velocidad de decisión de un administrador de tienda. Se requiere una interfaz conversacional inteligente que interprete intenciones y grafique métricas al instante sin exponer la base de datos a inyecciones o consultas inseguras.

---

## 4. Alcance Técnico y Desafíos del Examen

### Desafío I: Metodología ICONIX y Trazabilidad UML
* Proceso ágil dirigido por casos de uso que une análisis y diseño mediante cuatro hitos:
  1. **Requisitos:** Modelo de Dominio inicial y redacción concisa de casos de uso.
  2. **Análisis y Diseño Preliminar:** Diagramas de Robustez con objetos *Boundary* (interfaz), *Control* (lógica/controlador) y *Entity* (datos).
  3. **Diseño Detallado:** Diagramas de Secuencia (asignación de mensajes a métodos) y Diagrama de Clases estático actualizado.
  4. **Implementación y Pruebas:** Codificación y pruebas unitarias/integración trazables a los diagramas.

### Desafío II: Progressive Web App (PWA) e Instalabilidad (Angular)
* Archivo `manifest.webmanifest` con iconos adaptativos y configuración de pantalla completa (`standalone`).
* Service Worker para caché de assets estáticos y páginas shell (`ngsw-config.json`).
* Interceptor de instalación (`beforeinstallprompt`) con banner personalizado.
* Soporte de actualización en segundo plano (`SwUpdate`).

### Desafío III y IV: Operaciones Offline, Persistencia y Sincronización
* **Almacenamiento Local:**
  * Web: **IndexedDB** para catálogo cacheado y cola `pending_operations_queue`.
  * Móvil: **SQLite** en Flutter para tablas locales de productos, variantes, sucursales, clientes, ventas y reservas.
* **Operaciones Offline Obligatorias:**
  * Consulta de catálogo, precios, tallas, colores y existencias conocidas.
  * Registro de **reservas** sin conexión.
  * Registro de **ventas de contado** (efectivo) sin conexión.
  * Consulta de operaciones pendientes y conservación de datos tras reiniciar la app.
* **Protocolo de Sincronización e Idempotencia:**
  * Identificador universal único (`operation_id` UUID) generado en el cliente.
  * Estados de sincronización: `local_pending`, `synced_confirmed`, `conflict_rejected`.
  * Endpoint backend `/api/offline/queue-sync` con procesamiento en lote transaccional.
  * Las operaciones nunca se borran del cliente ante fallos de red; permanecen hasta confirmación explícita del servidor.
  * Conciliación de inventario: si no hay stock al sincronizar, se marca conflicto y se genera alerta de ajuste.

### Desafío V: Reportes Generativos con IA y Módulo de Machine Learning
* **Reportes Generativos:**
  * Entrada: solicitudes escritas o dictadas por voz (Web Speech API).
  * Backend: servicio NLP que interpreta entidades (sucursal, fechas, categorías) y mapea a consultas dinámicas parametrizadas seguras.
  * Salida: visualización en tablas, gráficos interactivos y exportación (CSV/Excel).
  * Seguridad: validación estricta de filtros y forzado de scope por `tenant_id` en el backend.
* **Módulo de Analítica con Machine Learning:**
  * Generación y procesamiento de **datos sintéticos** para entrenamiento.
  * **Modelo Supervisado:** predicción de demanda de ventas o probabilidad de cancelación de reservas.
  * **Modelo No Supervisado:** clustering/segmentación de clientes según patrones de compra (ej. K-Means / RFM).
  * Dashboard analítico con métricas de rendimiento del modelo e indicadores clave.

### Desafío VI: Plataforma SaaS Multi-Tenant y Planes de Suscripción
* **Modelo Multi-Tenant:** Base de datos PostgreSQL compartida con discriminador `tenant_id` en cada entidad de negocio.
* **Planes de Suscripción:**
  * **Plan Básico:** hasta 2 sucursales activas, ventas, reservas, catálogo, reportes convencionales.
  * **Plan Profesional:** hasta 10 sucursales activas, reportes generativos con IA, vestidor virtual y soporte avanzado.
* **Resolución de Tenant:** Detección automática por subdominio (`{tenant}.plataforma.com`) o encabezado HTTP `X-Tenant-ID`.
* **Seguridad:** Enmascaramiento y validación forzosa en la capa de servicios del backend; ningún usuario puede consultar o mutar datos de otra empresa.

---

## 5. Requisitos No Funcionales Obligatorios (RNF)

| **Código** | **Nombre** | **Criterio de Aceptación** |
| :--- | :--- | :--- |
| **RNF01** | **Seguridad** | Autenticación JWT con claim `tenant_id` y roles RBAC granulares. |
| **RNF02** | **Aislamiento de Datos** | Filtro obligatorio por `tenant_id` en todas las consultas SQL del backend. |
| **RNF03** | **Persistencia Offline** | Datos locales en IndexedDB y SQLite persisten tras cierre o reinicio de la app. |
| **RNF04** | **Integridad Transaccional** | Ventas y movimientos de stock ejecutados atómicamente en transacciones ACID. |
| **RNF05** | **Idempotencia** | Reenvío de transacciones con el mismo `operation_id` no duplica ventas ni stock. |
| **RNF06** | **Recuperación ante Fallos** | Operaciones pendientes se conservan intactas ante caídas de red o HTTP 5xx. |
| **RNF07** | **Mantenibilidad** | Separación limpia de responsabilidades (Presentación, Negocio, Persistencia, Sync). |
| **RNF08** | **Compatibilidad** | PWA compatible con navegadores Chromium/Safari; Flutter móvil con soporte Android/iOS. |
| **RNF09** | **Rendimiento** | Consultas optimizadas con índices relacionales en PostgreSQL y carga diferida en frontends. |
| **RNF10** | **Observabilidad** | Trazabilidad y logs de sincronización para diagnóstico de errores sin fugar datos sensibles. |
| **RNF11** | **Calidad** | Cobertura de pruebas unitarias y de integración sobre reglas críticas del negocio. |
| **RNF12** | **Coherencia Documental** | Trazabilidad estricta y correspondencia total entre los diagramas UML y el código fuente. |

---

## 6. Stack Tecnológico Obligatorio

| **Capa** | **Tecnología Principal** | **Librerías / Herramientas Clave** |
| :--- | :--- | :--- |
| **Backend** | Python 3.11+ / FastAPI | SQLAlchemy, Alembic, Pydantic v2, Uvicorn, Jose JWT |
| **Base de Datos** | PostgreSQL 16+ | Migraciones con Alembic, Row-Level isolation |
| **Frontend Web** | Angular 17+ (Standalone) | RxJS, TailwindCSS, `@angular/pwa`, Service Workers |
| **Persistencia Web** | IndexedDB | Almacenamiento local estructurado para catálogo y cola offline |
| **Aplicación Móvil** | Flutter 3.x / Dart | `sqflite` (SQLite), `provider`/`bloc`, `dio`, `camera` |
| **Persistencia Móvil** | SQLite | Tablas relacionales locales para operación sin conexión |
| **Inteligencia Artificial** | Gemini API / Scikit-Learn | Text-to-Report (NLP), Modelos de ML Supervisado/No Supervisado |
| **Metodología & Diseño** | ICONIX / UML 2.5+ | Diagramas de Casos de Uso, Dominio, Robustez, Secuencia y Clases |

---

## 7. Actores y Mapa Consolidado de Casos de Uso (CU1 al CU23)

### Actores del Sistema
* **Superadministrador:** Administra la plataforma SaaS, crea planes y gestiona tenants.
* **Administrador de Tenant:** Administra su empresa, sucursales, usuarios, catálogo, suscripción y reportes con IA.
* **Encargado de Sucursal:** Prepara reservas, recepciona mercadería y gestiona transferencias de stock.
* **Cajero:** Atiende la caja física, emite ventas presenciales (online y offline de contado) y cobra pedidos.
* **Cliente:** Navega el catálogo, usa el vestidor virtual, compra digitalmente, reserva prendas y usa su billetera.
* **Proveedor:** Carga remitos y catálogos de mercadería mediante RPA con IA.
* **Repartidor / Delivery:** Consulta hojas de ruta y valida entregas a domicilio mediante código PIN de seguridad.

### Matriz de Casos de Uso del Segundo Parcial

| **ID** | **Caso de Uso** | **Módulo** | **Estado** | **Actor Principal** | **Plataforma** |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **CU1** | **Plataforma Multi-Tenant (Migración Integral)** | M1: SaaS y Seguridad | Pendiente | Superadministrador | Web |
| **CU2** | **Gestión de Planes y Suscripciones B2B** | M1: SaaS y Seguridad | Pendiente | Superadmin, Admin Tenant | Web |
| **CU3** | **Gestión Granular de Roles y Permisos (RBAC)** | M1: SaaS y Seguridad | Pendiente | Superadmin, Admin Tenant | Web |
| **CU4** | **Landing Page y Catálogo de Planes** | M1: SaaS y Seguridad | Pendiente | Prospecto B2B | Web |
| **CU5** | **Usar Vestidor Virtual en Tiempo Real** | M2: Inteligencia Artificial | **Hecho** | Cliente | Móvil / Web |
| **CU6** | **Recibir Recomendaciones de Catálogo** | M2: Inteligencia Artificial | **Hecho** | Cliente | Ambas |
| **CU7** | **Consultar Asistente Virtual / Chatbot** | M2: Inteligencia Artificial | **Hecho** | Cliente | Ambas |
| **CU8** | **Generar Reportes Inteligentes con IA y ML** | M2: Inteligencia Artificial | Pendiente | Admin Tenant | Web |
| **CU9** | **Reabastecimiento de Stock (Sistema Experto)** | M2: Inteligencia Artificial | Pendiente | Admin Tenant, Sistema | Web |
| **CU10** | **Ingesta de Mercadería con RPA e IA** | M2: Inteligencia Artificial | Pendiente | Proveedor, Sistema | Web |
| **CU11** | **Traspaso Manual de Inventario** | M3: Inventario y Operaciones | **Hecho** | Admin, Encargado | Web |
| **CU12** | **Notificaciones Push Móviles** | M3: Inventario y Operaciones | **Hecho** | Cliente, Sistema | Móvil |
| **CU13** | **Dashboard de Control y Métricas** | M4: Business Intelligence | **Hecho** | Admin Tenant | Web |
| **CU14** | **Generación y Exportación de Reportes** | M4: Business Intelligence | **Hecho** | Admin Tenant | Web |
| **CU15** | **Gestionar y Aplicar Cupones Promocionales** | M5: Promociones y Fidelidad | **Hecho** | Cliente, Admin, Cajero | Ambas |
| **CU16** | **Gestionar Lista de Deseos (Wishlist)** | M5: Promociones y Fidelidad | Pendiente | Cliente | Ambas |
| **CU17** | **Fidelización y Billetera de Puntos (Loyalty)** | M5: Promociones y Fidelidad | Pendiente | Cliente, Cajero | Ambas |
| **CU18** | **Emitir y Comprar Tarjetas de Regalo (Gift Cards)** | M5: Promociones y Fidelidad | Pendiente | Cliente | Ambas |
| **CU19** | **Gestionar Billetera Digital (Store Wallet)** | M5: Promociones y Fidelidad | Pendiente | Cliente, Cajero | Ambas |
| **CU20** | **Delivery y Despacho a Domicilio con PIN** | M6: Logística y Posventa | Pendiente | Cliente, Delivery | Ambas |
| **CU21** | **Solicitar y Procesar Cambios y Devoluciones (RMA)** | M6: Logística y Posventa | Pendiente | Cliente, Encargado | Ambas |
| **CU22** | **Progressive Web App (PWA) e Instalabilidad** | M6: Logística y Posventa | Pendiente | Cliente, Todos | Web |
| **CU23** | **Modo Offline y Sincronización Diferida (Offline-First)** | M6: Logística y Posventa | Pendiente | Cajero, Cliente, Delivery | Ambas |

* **Total de Casos de Uso:** 23 (8 Implementados en Base + 15 Pendientes de Evolución Segundo Parcial).

---

## 8. Cronograma de Hitos y Fechas de Evaluación

* **Presentación 1:** Domingo 25 de Octubre de 2026
* **Presentación 2:** Domingo 01 de Noviembre de 2026
* **Presentación 3:** Domingo 08 de Noviembre de 2026
* **Defensa Final del Examen:** **Martes 10 de Noviembre de 2026 – Hrs. 07:00**
