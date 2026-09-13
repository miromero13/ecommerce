# Revisión de implementación — Ciclo 2 (CU11 – CU18)

Fecha: 2026-09-13
Alcance: verificación de que los casos de uso del ciclo 2 (`Casos_de_Uso_WomenStyle.md`, sección 2, tabla Ciclo 2) están implementados de forma completa (backend API + frontend web) y de acuerdo a su definición.

---

## 1. Resumen global

| CU | Caso de uso | % implementado | Backend | Frontend | Estado |
|---|-------------|:--------------:|:-------:|:--------:|--------|
| CU11 | Consultar disponibilidad por sucursal | **85 %** | ✔ | ✔ | Funcional, con salvedad de cálculo |
| CU12 | Registrar movimiento de inventario | **35 %** | ✔ | ✘ | Solo API; sin pantalla |
| CU13 | Consultar inventario consolidado | **95 %** | ✔ | ✔ | Casi completo |
| CU14 | Gestionar reservas de prendas | **80 %** | ✔ | ✔ | Funcional, sin "horario" |
| CU15 | Gestionar carrito de compras | **90 %** | ✔ | ✔ | Funcional (web) |
| CU16 | Compra digital y estado del pedido | **50 %** | ✔ | ✘ (parcial) | Falta seguimiento del pedido |
| CU17 | Atender reserva en sucursal | **85 %** | ✔ | ✔ | Funcional |
| CU18 | Venta presencial y pago en caja | **85 %** | ✔ | ✔ | Funcional |

**Promedio ponderado estimado del ciclo 2: ~70 %**

Buenas noticias: la mayoría de los CU tienen **backend completo, coherente y con control por rol/sucursal**, y los flujos transaccionales están bien encadenados (reserva → venta → movimiento de inventario). Las dos brechas grandes son **CU12 sin interfaz** y **CU16 sin pantalla de seguimiento del pedido**.

---

## 2. Detalle por caso de uso

### CU11 – Consultar disponibilidad por sucursal — 85 %

**Implementado:**
- Catálogo público filtrable por sucursal, con cantidad por variante (talla/color): `frontend/src/app/features/cliente/pages/catalog-page.component.html` (línea 134-138) → `GET /catalog/products?branch_id=...` (`backend/app/routes/catalog_routes.py:240`).
- Endpoint de disponibilidad: `GET /catalog/availability` (`catalog_routes.py:397`).
- Stock por sucursal (rol admin/encargado/cajero): `GET /inventory/branches/{branch_id}` (`inventory_routes.py:42`).

**Falta / a corregir:**
1. **El stock visible al cliente no descuenta lo reservado.** En `backend/app/services/catalog_service.py:409-415` (y `get_branch_quantity`, línea 446-448) se devuelve `inventory.quantity` completo; y en `inventory_routes.py:404/412` el `/catalog/availability` también suma `quantity` sin restar `reserved_quantity`. Una prenda 100 % reservada sigue apareciendo disponible. Debería exponer `available = quantity - reserved_quantity` (ya se calcula así en `inventory_service.py`).
2. **Plataforma móvil (Flutter) no existe** en el repo (CU declarado "Ambas"). Solo web.

---

### CU12 – Registrar movimiento de inventario — 35 %

**Implementado (solo API):**
- Ingreso: `POST /inventory/movements/income` (`inventory_routes.py:69`).
- Salida: `POST /inventory/movements/outcome` (`inventory_routes.py:88`).
- Traspaso entre sucursales: `POST /inventory/movements/transfer` (`inventory_routes.py:107`).
- Bitácora: `GET /inventory/movements` (`inventory_routes.py:53`). Lógica en `services/inventory_service.py`.

**Falta:**
1. **No hay ninguna pantalla ni servicio frontend para registrar movimientos.** `frontend/src/app/features/shared/services/inventory-api.service.ts` solo expone GET (consolidado, por sucursal, movimientos). La página `admin-inventory-page.component.html` es **solo lectura** (consolidado / sucursal / movimientos). El rol **encargado no tiene ninguna página de inventario** (su inicio es un placeholder: `encargado-home-page.component.html`). El cajero tampoco.
2. **Backend no permite al cajero registrar ingresos/salidas**: `inventory_routes.py:73,92` restringen a `administrador` y `encargado`, aunque el CU12 declara como actores "Encargado de sucursal, Cajero". (El traspaso es solo admin, razonable por seguridad.)
3. Alerta de stock bajo (módulo de inventario del alcance) no implementada.

---

### CU13 – Consultar inventario consolidado — 95 %

**Implementado:**
- `GET /inventory/consolidated` (`inventory_routes.py:33`) con totales por variante y desglose por sucursal (`services/inventory_service.py:111`).
- Vista de administrador completa: `admin-inventory-page.component.html` (tab "Consolidado" con total, disponible, reservado y badges por sucursal).
- Incluye KPIs (variantes, cantidades, disponible, reservado, sucursales, movimientos).

**Falta (menor):**
- Filtros de búsqueda (producto/talla/color) en la vista consolidada; no es obligatorio según el CU. Nada bloqueante.

---

### CU14 – Gestionar reservas de prendas — 80 %

**Implementado:**
- Creación con múltiples prendas, sucursal, fecha de visita y expiración automática (`expires_at = visit_date + 1 día`): `POST /reservations/` (`reservation_routes.py:87`), lógica en `services/reservation_service.py:170`.
- Vista cliente: selección de producto/variante/cantidad, borrador, listado con estados y cancelación (`cliente/pages/reservations-page.component.*`).
- Cancelación cliente y por sucursal: `PATCH /reservations/{id}/cancel` y `/branch-cancel`.
- Expiración automática evaluada en cada consulta (`expire_due_reservations`, `reservation_service.py:115`).
- Consulta de estado: `GET /reservations/me` y `GET /reservations/{id}`.
- Validación de stock real (quita `reserved_quantity`) y variante `active`.

**Falta:**
1. **"Horario" de la reserva no se modela.** El CU define "selección de prendas, sucursal y **horario**"; el payload solo tiene `visit_date` (date) (`schemas/reservation_schema.py:23`). No hay franja horaria.
2. La fecha no se valida contra `visita >= hoy` (podría crearse una reserva en el pasado; no es crítico pero conviene).
3. La "notificación a la sucursal" es pasiva (listado de sucursal en la pantalla del encargado) — aceptable para el MVP, no hay push/correo.
4. Tiempo límite de validez fijo a +1 día (no configurable). Aceptable.

---

### CU15 – Gestionar carrito de compras — 90 %

**Implementado:**
- CRUD completo: `GET /cart/current`, `POST /cart/items`, `PATCH /cart/items/{id}`, `DELETE /cart/items/{id}`, `DELETE /cart/current` (`cart_routes.py`).
- Validación de stock global (suma de disponibles entre sucursales) al agregar/editar (`services/cart_service.py:16`).
- Totales automáticos (subtotal, descuento, total, item_count).
- Vista cliente completa: ajuste de cantidades (+/−), eliminar, vaciar, resumen (`cliente/pages/cart-page.component.*`).

**Falta / nota:**
1. `discount_amount` siempre es 0 y no existe lógica de promociones (en el modelo, `models/cart.py:19`). Según `Casos_de_Uso_WomenStyle.md` sección 6, las promociones se gestionan dentro de **CU08** (ciclo 1), por lo que no es un bloqueante de CU15; pero el alcance del proyecto pide "cálculo de totales considerando promociones vigentes".
2. Plataforma móvil no implementada (CU "Ambas").

---

### CU16 – Realizar compra digital y consultar estado del pedido — 50 %

**Implementado:**
- Checkout efectivo: `POST /payments/cash/checkout` (`payment_routes.py:18`).
- Checkout Stripe (PaymentIntent + webhook): `POST /payments/stripe/checkout` y `/payments/stripe/webhook` (`payment_routes.py:31-80`).
- Asignación de inventario automática y movimientos de salida al pagar (`services/order_service.py:_allocate_inventory`).
- API de pedidos del cliente: `GET /orders/me` y `GET /orders/{id}` (`order_routes.py`).
- En el carrito se muestra el último pedido tras checkout (`cart-page.component.ts:30,98`).

**Falta (bloqueante para el CU):**
1. **No hay ninguna pantalla de "mis pedidos" / seguimiento del estado.** No existe servicio Angular de pedidos (no hay `OrderApiService`), no hay ruta (`app.routes.ts` no define `cliente/orders`) ni componente. La API `GET /orders/me` existe pero nadie la consume. El CU pide "consulta del estado del pedido" — falta la UI.
2. **Ciclo de estados incompleto.** El requisito pide seguimiento: **pagado → en preparación → listo para entrega/recogida**. `OrderStatusEnum` solo tiene `pending / paid / failed / cancelled` (`schemas/order_schema.py:9`). Faltan `preparing` y `ready`, y el pedido no guarda sucursal/punto de recogida.
3. Frontend Stripe solo muestra el `client_secret` en un recuadro (`cart-page.component.html:120-122`); no hay elemento de pago ni confirmación real en el navegador (en el MVP se confirma vía webhook).

---

### CU17 – Atender reserva en sucursal — 85 %

**Implementado:**
- Confirmar llegada: `PATCH /reservations/{id}/arrival` (`reservation_routes.py:115`).
- Marcar atendida (liberando reservado y descontando stock): `PATCH /reservations/{id}/attend` (`reservation_service.py:276`).
- Cancelar desde sucursal: `PATCH /reservations/{id}/branch-cancel`.
- Vista de encargado completa: listado con KPIs, detalle de prendas y acciones por estado (`encargado/pages/reservations-page.component.*`).
- Control por sucursal (usa `branch_id` del JWT) y por estado válido.

**Falta / nota:**
1. La entrada del encargado muestra KPIs "inventario" y "reservas" como "-" (placeholder). No afecta al CU, pero el home del rol no refleja la fase final.
2. "Marcar atendida" no emite comprobante ni crea venta por sí misma (eso corresponde a CU18 vía cajero). Correcto para la separación de responsabilidades.

---

### CU18 – Registrar venta presencial y procesar pago en caja — 85 %

**Implementado:**
- `POST /sales` con items directos **o** reserva previa (`sales_routes.py:60`, `services/sales_service.py:239`).
- Actualización automática de inventario y registro de movimiento (cumple la relación `<<include>> CU18 → CU12`): `sales_service.py:169-224`.
- Transición de reserva → venta (pasa reserva a `attended`).
- `GET /sales/branch` y `GET /sales/{id}`.
- Pantalla de cajero completa: búsqueda de producto, carga de reserva por ID, edición de cantidades, medio de pago, total, comprobante en pantalla (`cajero/pages/sales-page.component.*`).
- Pago efectivo con referencia (cash) y opción Stripe como etiqueta de medio.

**Falta / nota:**
1. **Comprobante solo on-screen**, sin imprimir/PDF ni formato de recibo formal (la "emisión de comprobante" se cubre parcialmente).
2. La opción "Stripe" en caja solo registra el medio; no procesa un cobro real (en punto de venta es aceptable como MVP; el pago real de caja es efectivo).
3. No hay lista histórica de ventas visibles en el UI de caja (el servicio `listBranchSales` existe y no se usa).

---

## 3. Brechas transversales

1. **Plataforma móvil ausente.** CU11, CU14, CU15 y CU16 están definidos "Ambas" (web + móvil). No existe proyecto Flutter en el repo (no hay `pubspec.yaml`). Web nada más.
2. **Sin pruebas automatizadas.** No hay tests (pytest/unit) para ninguno de los flujos del ciclo 2, pese a que la "Regla de programación" de `docs/IMPLEMENTATION_PHASES.md` exige "prueba del flujo" en cada tarea.
3. **Fases de `IMPLEMENTATION_PHASES.md` del ciclo 2 sin marcar**: Fase 5 (inventario multisucursal), Fase 6 (compra y reservas) y Fase 7 (venta presencial) figuran con tareas `[ ]`, mientras que el código ya implementa gran parte. Hay desfase entre la planificación y el estado real.
4. **Promociones/descuentos**: el campo existe en carrito/pedido/venta pero siempre es 0; no hay gestión de promociones en ninguna pantalla.
5. **Sin alertas de stock bajo** (mencionada en alcance del módulo de inventario).

---

## 4. Prioridad de los trabajos pendientes

1. **CU16**: pantalla "Mis pedidos" + estados `preparing`/`ready` (máximo impacto, es un CU de prioridad/riesgo "Alto").
2. **CU12**: pantalla para registrar ingreso/salida/traspaso (encargado/admin) — el backend ya está listo.
3. **CU11**: corregir la disponibilidad para restar `reserved_quantity` al público.
4. **CU14**: agregar franja horaria y validar fecha futura.
5. **CU18**: comprobante imprimible (o al menos vista de historial de ventas).
6. Corrección menor: permitir cajero en `income/outcome` si se mantiene su rol como actor de CU12.