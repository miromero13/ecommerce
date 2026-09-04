# Arquitectura del sistema

## Objetivo

Definir una arquitectura base para FashionStore que soporte el ciclo 1 de los 10 casos de uso, con control por rol y por sucursal.

## Principios

- El backend es la fuente de verdad.
- El frontend solo controla la experiencia de usuario.
- La autorizacion depende de `rol` y `sucursal_id` dentro del JWT.
- Un usuario solo pertenece a una sucursal.
- El administrador global puede ver todo.
- Los usuarios operativos solo ven datos de su sucursal.

## Estructura general

### Frontend

Organizar `src/app/features/` con una carpeta por rol:

- `shared/`: auth, guards, interceptors, modelos comunes, servicios compartidos.
- `admin/`: gestion global, usuarios internos, sucursales, proveedores, reportes.
- `cliente/`: perfil, catalogo, reservas, carrito, compras, recomendaciones.
- `proveedor/`: alta y envio de productos.
- `encargado/`: reservas y operacion de sucursal.
- `cajero/`: ventas presenciales y cobro.
- `delivery/`: entregas y seguimiento asignado.

### Backend

Organizar la API por dominios:

- `auth/`: login, registro, refresh si aplica.
- `users/`: perfiles, roles y usuarios internos.
- `branches/`: sucursales.
- `providers/`: cuentas y operaciones de proveedor.
- `catalog/`: productos, categorias, tallas, colores, temporadas y colecciones.
- `inventory/`: stock por sucursal y movimientos.
- `reservations/`: reserva y atencion en tienda.
- `sales/`: ventas presenciales y digitales.
- `reports/`: dashboards y reportes.

## Modelo de acceso

### JWT

El token debe incluir:

- `sub`: `user_id`
- `rol`: rol del usuario
- `sucursal_id`: sucursal asignada o `null` para admin global

### Reglas de autorizacion

- `admin global`: acceso total a todos los recursos.
- `admin de sucursal`: acceso limitado a su sucursal.
- `encargado`: operaciones de su sucursal.
- `cajero`: ventas y movimientos de su sucursal.
- `proveedor`: productos propios y su informacion.
- `cliente`: perfil, catalogo publico, reservas y compras propias.
- `delivery`: entregas asignadas.

### Regla de filtrado

Cada endpoint debe aplicar una de estas dos validaciones:

1. Validacion por rol.
2. Validacion por rol + sucursal.

## Modelo de datos minimo

### Tablas base

- `users`
- `branches`
- `providers`
- `products`
- `product_attributes`
- `inventory`
- `inventory_movements`
- `reservations`
- `reservation_items`
- `sales`
- `sale_items`

### Relaciones clave

- `users.sucursal_id -> branches.id`
- `inventory.sucursal_id -> branches.id`
- `inventory.product_id -> products.id`
- `reservations.sucursal_id -> branches.id`
- `sales.sucursal_id -> branches.id`

## Vista por rol en frontend

### Admin

- dashboard global
- usuarios internos
- sucursales
- proveedores
- catalogo y atributos
- inventario consolidado
- reportes

### Cliente

- perfil
- catalogo
- reservas
- carrito
- compras

### Proveedor

- productos enviados
- estado de validacion

### Encargado

- reservas de su sucursal
- preparacion de prendas
- stock local

### Cajero

- ventas presenciales
- cobro en caja
- comprobantes

## Estado actual del proyecto

### Ya existe

- login y registro
- JWT
- perfil de usuario
- listado de usuarios internos
- cambio de rol
- guardas basicos por autenticacion y rol

### Falta construir

- sucursales
- enlace usuario-sucursal
- administracion de proveedores
- catalogo y atributos
- inventario
- reservas
- ventas
- reportes
- estructura real por rol en `features/`

## Recomendacion tecnica

Implementar primero la capa de identidad y alcance:

1. sucursales
2. usuarios con `sucursal_id`
3. JWT con `rol` y `sucursal_id`
4. policies de acceso en backend
5. frontend por rol
