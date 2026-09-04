# Fases de implementacion

## Objetivo

Ordenar el desarrollo del ciclo 1 en tareas pequeñas, dependientes y verificables.

## Fase 0. Ajuste de base

### Tareas

- [x] Confirmar roles del sistema.
- [x] Definir el contenido del JWT: `user_id`, `rol`, `branch_id`.
- [x] Alinear nombres de carpetas por rol en frontend.
- [x] Alinear enum de roles en backend.
- [x] Confirmar que el cliente no pertenece a una sucursal.

### Entregable

- Documento tecnico aprobado y estructura acordada.

## Fase 1. Identidad y acceso

### Tareas

- [x] Ajustar el modelo `users` para incluir `branch_id`.
- [x] Crear tabla `branches`.
- [x] Emitir JWT con `sub`, `rol` y `branch_id`.
- [x] Actualizar el login y el registro.
- [x] Mantener `/users/me` como base del perfil.

### Casos de uso

- CU01 Registrar cliente
- CU02 Iniciar sesion
- CU06 Consultar y actualizar perfil

### Entregable

- Usuarios autenticados con contexto completo de rol y sucursal.

## Fase 2. Administracion global

### Tareas

- [x] Gestionar usuarios internos.
- [x] Listar y editar roles.
- [x] Crear y listar sucursales.
- [x] Asignar usuarios internos a sucursal.

### Casos de uso

- CU03 Gestionar usuarios internos
- CU04 Gestionar sucursales

### Entregable

- Admin global puede administrar estructura organizacional.

## Fase 3. Proveedores

### Tareas

- [x] Crear cuentas de proveedor.
- [x] Aprobar o suspender proveedores.
- [x] Guardar la sucursal o alcance del proveedor si aplica.

### Casos de uso

- CU05 Gestionar cuentas de proveedor

### Entregable

- Flujo inicial para proveedores listo.

## Fase 4. Catalogo e inventario base

### Tareas

- [x] Crear categorias, tallas, colores, temporadas y colecciones.
- [x] Crear productos.
- [x] Permitir envio de productos por proveedor.
- [x] Validar productos por admin.
- [x] Consultar y filtrar catalogo.
- [x] Consultar disponibilidad por sucursal.

### Casos de uso

- CU07 Registrar y enviar informacion de productos
- CU08 Gestionar catalogo y productos
- CU09 Gestionar atributos del catalogo
- CU10 Consultar y filtrar catalogo

### Entregable

- Catalogo operativo con filtros y control por sucursal.

## Fase 5. Inventario multisucursal

### Tareas

- [ ] Registrar stock por sucursal.
- [ ] Registrar movimientos de inventario.
- [ ] Consultar inventario consolidado.
- [ ] Aplicar reglas de stock bajo.

### Casos de uso

- CU11 Consultar disponibilidad por sucursal
- CU12 Registrar movimiento de inventario
- CU13 Consultar inventario consolidado

### Entregable

- Inventario visible por sucursal y consolidado por admin.

## Fase 6. Compra y reservas

### Tareas

- [ ] Crear reservas de prendas.
- [ ] Gestionar carrito.
- [ ] Crear compra digital.
- [ ] Consultar estado del pedido.
- [ ] Atender reserva en sucursal.

### Casos de uso

- CU14 Gestionar reservas de prendas
- CU15 Gestionar carrito de compras
- CU16 Realizar compra digital y consultar estado del pedido
- CU17 Atender reserva en sucursal

### Entregable

- Flujo de compra y atencion en tienda funcionando.

## Fase 7. Venta presencial

### Tareas

- [ ] Registrar ventas en caja.
- [ ] Procesar pago presencial.
- [ ] Emitir comprobantes.
- [ ] Vincular venta con reserva si corresponde.

### Casos de uso

- CU18 Registrar venta presencial y procesar pago en caja

### Entregable

- Venta fisica integrada al inventario.

## Fase 8. Reportes y extras

### Tareas

- [ ] Construir reportes y dashboards.
- [ ] Preparar base para recomendaciones IA.
- [ ] Preparar base para vestidor virtual.
- [ ] Preparar asistente virtual si entra en alcance.

### Casos de uso

- CU19 Usar vestidor virtual
- CU20 Generar reportes y dashboards
- CU21 Recibir recomendaciones de IA
- CU22 Consultar asistente virtual/chatbot
- CU23 Generar reporte por voz/lenguaje natural

### Entregable

- Cierre del ciclo funcional y extensiones futuras.

## Regla de programacion

Cada tarea debe cerrarse con estos pasos:

1. modelo de datos
2. servicio o logica
3. endpoint
4. validacion por rol/sucursal
5. pantalla o vista
6. prueba del flujo

## Orden recomendado de ejecucion

1. Identidad y acceso.
2. Sucursales.
3. Usuarios internos.
4. Proveedores.
5. Catalogo.
6. Inventario.
7. Reservas.
8. Venta presencial.
9. Reportes.
10. Extras de IA y realidad aumentada.
