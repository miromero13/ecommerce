/* =====================================================================================================
 * FashionStore SaaS - Diagrama general de casos de uso (CU1-CU30) para Enterprise Architect 15
 *
 * Generado por docs/ea/casos_de_uso/generar.py (no editar a mano: cambie el .py y vuelva a generar).
 *
 * USO: en el Project Browser seleccione el paquete donde quiere el diagrama; Specialize > Tools > Scripting;
 *      clic derecho en un grupo > New JScript; pegue TODO este archivo; guarde y ejecute (Run).
 *
 * Crea el paquete "Casos de uso - FashionStore SaaS" con los 7 actores oficiales, los 30 casos de uso, sus
 * asociaciones, las relaciones include / extend, el diagrama general con el limite del sistema y un diagrama
 * por caso de uso (UML 2.5: <<include>> va del caso base al incluido; <<extend>> va de la extension al caso
 * que extiende). Cada subcaso es una operacion real del codigo; su endpoint o funcion queda en las notas.
 * Actores, casos de uso y diagrama viven en el MISMO paquete: asi EA no escribe "(from Paquete...)" debajo
 * de cada figura. Si el paquete ya existe (de una ejecucion anterior) lo borra y lo crea de nuevo.
 * ===================================================================================================== */

var MODEL = {"actors": {"SA": "Superadministrador", "AD": "Administrador del tenant", "EN": "Encargado de sucursal", "PR": "Proveedor", "CL": "Cliente", "CA": "Cajero", "RE": "Repartidor"}, "cases": [{"id": "CU1", "name": "Gestionar organizaciones (Tenants) de la plataforma", "actors": ["SA"], "notes": "Alta, edicion, suspension y reactivacion de empresas inquilinas; registro de su administrador."}, {"id": "CU2", "name": "Gestionar planes de suscripci\u00f3n SaaS", "actors": ["SA"], "notes": "Crear y actualizar planes (tarifas mensual/anual, max_branches, max_garments y modulos habilitados)."}, {"id": "CU3", "name": "Gestionar roles y permisos de usuario (RBAC)", "actors": ["SA", "AD"], "notes": "Crear roles a medida y asignarles permisos granulares por modulo y verbo."}, {"id": "CU4", "name": "Consultar p\u00e1gina comercial y planes de suscripci\u00f3n", "actors": ["AD"], "notes": "Portal publico con diferenciales del producto, comparativa de planes y prueba gratuita."}, {"id": "CU5", "name": "Probar prendas en el vestidor virtual", "actors": ["CL"], "notes": "Proyeccion en vivo de prendas sobre la silueta del cliente con la camara."}, {"id": "CU6", "name": "Recibir recomendaciones personalizadas de prendas", "actors": ["CL"], "notes": "Sugerencias por interacciones del cliente, con respaldo por popularidad (cold start)."}, {"id": "CU7", "name": "Consultar al asistente virtual (Chatbot)", "actors": ["CL"], "notes": "Asistente conversacional con clasificacion de intenciones y stock real."}, {"id": "CU8", "name": "Generar reportes inteligentes con IA", "actors": ["AD"], "notes": "Reportes por lenguaje natural (texto o voz), predictivos y de patrones con Machine Learning."}, {"id": "CU9", "name": "Reabastecer stock autom\u00e1ticamente entre sucursales", "actors": ["AD"], "notes": "Sistema experto que evalua reglas de inventario y propone traspasos entre sucursales."}, {"id": "CU10", "name": "Registrar ingreso de mercader\u00eda con RPA e IA", "actors": ["PR", "AD", "EN"], "notes": "Bot que lee remitos y facturas (OCR) y crea borradores de ingreso de mercaderia."}, {"id": "CU11", "name": "Transferir inventario entre sucursales", "actors": ["AD", "EN"], "notes": "Traspaso atomico de prendas entre dos sucursales (transfer_out / transfer_in)."}, {"id": "CU12", "name": "Recibir notificaciones push en el m\u00f3vil", "actors": ["CL", "AD", "EN"], "notes": "Push (FCM movil y web) con bandeja: al cliente por pedidos y reservas; al administrador y encargado por stock bajo, reabastecimiento y pedidos de sucursal (notification_delivery.py)."}, {"id": "CU13", "name": "Consultar dashboard de m\u00e9tricas comerciales", "actors": ["AD"], "notes": "Tablero con KPIs de facturacion, prendas vendidas, ranking e inventario por sucursal."}, {"id": "CU14", "name": "Generar y exportar reportes operativos", "actors": ["AD", "EN"], "notes": "Reportes de ventas, existencias y movimientos con filtros y exportacion."}, {"id": "CU15", "name": "Gestionar y aplicar cupones de descuento", "actors": ["AD", "EN", "CL", "CA"], "notes": "Emision de cupones (porcentaje o monto fijo, vigencia, tope de usos) y aplicacion en el checkout."}, {"id": "CU16", "name": "Gestionar lista de deseos (Wishlist)", "actors": ["CL"], "notes": "Guardar prendas favoritas y moverlas al carrito."}, {"id": "CU17", "name": "Acumular y canjear puntos de fidelizaci\u00f3n (Loyalty)", "actors": ["CL", "CA"], "notes": "Billetera de puntos por empresa: acumula al pagar y se canjea como descuento en web, movil o caja."}, {"id": "CU18", "name": "Comprar y emitir tarjetas de regalo (Gift Cards)", "actors": ["CL"], "notes": "Compra de vouchers prepagados con dedicatoria y codigo QR unico."}, {"id": "CU19", "name": "Gestionar billetera digital (Store Wallet)", "actors": ["CL"], "notes": "Saldo del cliente: canje de Gift Cards, conversion de puntos, pagos y reembolsos de devoluciones."}, {"id": "CU20", "name": "Gestionar env\u00edo a domicilio con validaci\u00f3n por PIN", "actors": ["CL", "RE", "SA"], "notes": "Cotizacion de flete, hoja de ruta del repartidor y confirmacion de entrega con PIN; alta de repartidores."}, {"id": "CU21", "name": "Solicitar y procesar cambios y devoluciones (RMA)", "actors": ["CL", "EN", "AD"], "notes": "Solicitud de cambio o devolucion dentro de 30 dias y dictamen por prenda."}, {"id": "CU22", "name": "Instalar la aplicaci\u00f3n web progresiva (PWA)", "actors": ["CL", "CA", "EN", "AD"], "notes": "Instalacion de la aplicacion web en el dispositivo y aviso de nuevas versiones."}, {"id": "CU23", "name": "Consultar cat\u00e1logo sin conexi\u00f3n (Offline)", "actors": ["CA"], "notes": "Catalogo guardado localmente (IndexedDB) para buscar prendas en caja sin internet."}, {"id": "CU24", "name": "Reintegrar inventario por devoluciones y registrar mermas", "actors": ["EN", "AD"], "notes": "Inspeccion de prendas devueltas: reingreso al stock o envio a merma / cuarentena."}, {"id": "CU25", "name": "Registrar ventas y reservas sin conexi\u00f3n (POS Offline)", "actors": ["CA"], "notes": "Ventas de contado y reservas en contingencia con comprobante provisional."}, {"id": "CU26", "name": "Personalizar la marca de la tienda (Branding)", "actors": ["AD", "SA"], "notes": "Logo, colores e identidad visual de la empresa en web y movil."}, {"id": "CU27", "name": "Contratar suscripci\u00f3n B2B (Onboarding)", "actors": ["AD"], "notes": "Seleccion de plan, ciclo de facturacion, datos de la empresa y pago simulado."}, {"id": "CU28", "name": "Monitorear consumo y cambiar plan de suscripci\u00f3n", "actors": ["AD"], "notes": "Consumo de sucursales y prendas frente al plan, historial y upgrade / downgrade."}, {"id": "CU29", "name": "Gestionar cola de operaciones pendientes (Offline Queue)", "actors": ["CA", "CL"], "notes": "Consulta y auditoria de las operaciones retenidas localmente sin conexion."}, {"id": "CU30", "name": "Sincronizar operaciones offline y resolver conflictos de inventario", "actors": ["CA", "AD", "EN"], "notes": "Envio en lote de la cola, deteccion de colisiones de stock y compensacion al cliente."}], "relations": [{"from": "CU1", "to": "CU2", "kind": "include"}, {"from": "CU4", "to": "CU2", "kind": "include"}, {"from": "CU12", "to": "CU11", "kind": "extend"}], "layout": {"CU1": [310, 80], "CU2": [660, 160], "CU3": [310, 400], "CU4": [660, 320], "CU5": [1010, 240], "CU6": [1010, 80], "CU7": [1360, 320], "CU8": [660, 640], "CU9": [660, 1280], "CU10": [310, 1200], "CU11": [660, 800], "CU12": [1010, 400], "CU13": [660, 1120], "CU14": [310, 1040], "CU15": [1010, 1040], "CU16": [1360, 160], "CU17": [1360, 1120], "CU18": [1010, 1200], "CU19": [1010, 1360], "CU20": [1010, 720], "CU21": [660, 480], "CU22": [1010, 880], "CU23": [1360, 1440], "CU24": [310, 560], "CU25": [1360, 1280], "CU26": [310, 240], "CU27": [310, 1360], "CU28": [660, 1440], "CU29": [1010, 560], "CU30": [660, 960], "SA": [70, 140], "AD": [70, 540], "EN": [70, 860], "PR": [70, 1180], "CL": [1740, 540], "CA": [1740, 1020], "RE": [1740, 1260]}, "boundary": [240, 40, 1380, 1560], "uc": [190, 76], "act": [50, 90], "routes": [{"from": "AD", "to": "CU4", "path": [[580, 450]]}, {"from": "CL", "to": "CU6", "path": [[1280, 370]]}, {"from": "AD", "to": "CU8", "path": [[580, 690]]}, {"from": "AD", "to": "CU10", "path": [[275, 1090]]}, {"from": "AD", "to": "CU12", "path": [[930, 370]]}, {"from": "AD", "to": "CU15", "path": [[275, 690]]}, {"from": "EN", "to": "CU15", "path": [[930, 930]]}, {"from": "SA", "to": "CU20", "path": [[275, 690]]}, {"from": "AD", "to": "CU21", "path": [[275, 530]]}, {"from": "AD", "to": "CU22", "path": [[580, 930]]}, {"from": "AD", "to": "CU27", "path": [[275, 1170], [275, 1250]]}, {"from": "AD", "to": "CU28", "path": [[580, 1090], [580, 1250]]}], "subs": [{"key": "S:Registrar organizaci\u00f3n", "name": "Registrar organizaci\u00f3n", "notes": "Fuente en el codigo: POST /subscriptions/tenants/with-subscription (create_tenant_with_subscription_route)", "cu": "CU1"}, {"key": "S:Suspender o reactivar organizaci\u00f3n", "name": "Suspender o reactivar organizaci\u00f3n", "notes": "Fuente en el codigo: PATCH /tenants/{id}/status (update_tenant_status_route)", "cu": "CU1"}, {"key": "S:Registrar administrador de la organizaci\u00f3n", "name": "Registrar administrador de la organizaci\u00f3n", "notes": "Fuente en el codigo: POST /tenants/{id}/admin (register_tenant_admin_route)", "cu": "CU1"}, {"key": "S:Ingresar al panel de la organizaci\u00f3n", "name": "Ingresar al panel de la organizaci\u00f3n", "notes": "Fuente en el codigo: POST /tenants/{id}/panel-session (open_tenant_panel_route)", "cu": "CU1"}, {"key": "S:Crear plan de suscripci\u00f3n", "name": "Crear plan de suscripci\u00f3n", "notes": "Fuente en el codigo: POST /subscriptions/plans (create_plan_route)", "cu": "CU2"}, {"key": "S:Editar plan de suscripci\u00f3n", "name": "Editar plan de suscripci\u00f3n", "notes": "Fuente en el codigo: PATCH /subscriptions/plans/{id} (update_plan_route)", "cu": "CU2"}, {"key": "S:Crear rol personalizado", "name": "Crear rol personalizado", "notes": "Fuente en el codigo: POST /rbac/roles (post_role)", "cu": "CU3"}, {"key": "S:Editar permisos del rol", "name": "Editar permisos del rol", "notes": "Fuente en el codigo: PUT /rbac/roles/{id} (put_role)", "cu": "CU3"}, {"key": "S:Asignar roles a un usuario", "name": "Asignar roles a un usuario", "notes": "Fuente en el codigo: role_id en POST/PUT /users desde admin-user-page", "cu": "CU3"}, {"key": "S:Consultar cat\u00e1logo de permisos", "name": "Consultar cat\u00e1logo de permisos", "notes": "Fuente en el codigo: GET /rbac/permissions (get_permissions)", "cu": "CU3"}, {"key": "S:Consultar historial de conversaci\u00f3n", "name": "Consultar historial de conversaci\u00f3n", "notes": "Fuente en el codigo: GET /chatbot/messages (chatbot_messages_route)", "cu": "CU7"}, {"key": "S:Reiniciar conversaci\u00f3n", "name": "Reiniciar conversaci\u00f3n", "notes": "Fuente en el codigo: DELETE /chatbot/conversation (chatbot_reset_route)", "cu": "CU7"}, {"key": "S:Predecir demanda de prendas", "name": "Predecir demanda de prendas", "notes": "Fuente en el codigo: POST /reports/ml/predict-demand (predict_demand_route)", "cu": "CU8"}, {"key": "S:Segmentar clientes por comportamiento", "name": "Segmentar clientes por comportamiento", "notes": "Fuente en el codigo: POST /reports/ml/customer-clusters (customer_clusters_route)", "cu": "CU8"}, {"key": "S:Exportar reporte inteligente", "name": "Exportar reporte inteligente", "notes": "Fuente en el codigo: GET /reports/export/excel y /reports/export/pdf", "cu": "CU8"}, {"key": "S:Aplicar traspasos sugeridos", "name": "Aplicar traspasos sugeridos", "notes": "Fuente en el codigo: expert_replenishment_routes.apply_replenishment_transfers", "cu": "CU9"}, {"key": "S:Descartar traspasos sugeridos", "name": "Descartar traspasos sugeridos", "notes": "Fuente en el codigo: discard_replenishment_transfers, desde notification-page", "cu": "CU9"}, {"key": "S:Configurar reglas de reabastecimiento", "name": "Configurar reglas de reabastecimiento", "notes": "Fuente en el codigo: expert_replenishment_routes.update_replenishment_rules", "cu": "CU9"}, {"key": "S:Corregir \u00edtems extra\u00eddos", "name": "Corregir \u00edtems extra\u00eddos", "notes": "Fuente en el codigo: PATCH /rpa/jobs/{id}/items (correct_items_route)", "cu": "CU10"}, {"key": "S:Confirmar ingreso de mercader\u00eda", "name": "Confirmar ingreso de mercader\u00eda", "notes": "Fuente en el codigo: POST /rpa/jobs/{id}/commit (commit_job_route)", "cu": "CU10"}, {"key": "S:Registrar dispositivo para notificaciones", "name": "Registrar dispositivo para notificaciones", "notes": "Fuente en el codigo: POST /notifications/tokens (register_token_route)", "cu": "CU12"}, {"key": "S:Marcar notificaciones como le\u00eddas", "name": "Marcar notificaciones como le\u00eddas", "notes": "Fuente en el codigo: PATCH /notifications/{id}/read y /notifications/read-all", "cu": "CU12"}, {"key": "S:Exportar reporte operativo", "name": "Exportar reporte operativo", "notes": "Fuente en el codigo: PDF, HTML o CSV desde sales-history-page y admin-inventory-page", "cu": "CU14"}, {"key": "S:Crear cup\u00f3n de descuento", "name": "Crear cup\u00f3n de descuento", "notes": "Fuente en el codigo: POST /promotions (create_promotion_code)", "cu": "CU15"}, {"key": "S:Aplicar cup\u00f3n en el carrito", "name": "Aplicar cup\u00f3n en el carrito", "notes": "Fuente en el codigo: POST /cart/coupon (apply_coupon_route)", "cu": "CU15"}, {"key": "S:Quitar cup\u00f3n del carrito", "name": "Quitar cup\u00f3n del carrito", "notes": "Fuente en el codigo: DELETE /cart/coupon (remove_coupon_route)", "cu": "CU15"}, {"key": "S:Aplicar cup\u00f3n en la venta de caja", "name": "Aplicar cup\u00f3n en la venta de caja", "notes": "Fuente en el codigo: sales_service._apply_cashier_coupon (caja-page)", "cu": "CU15"}, {"key": "S:Agregar prenda a la lista de deseos", "name": "Agregar prenda a la lista de deseos", "notes": "Fuente en el codigo: POST /wishlist/items (add_route)", "cu": "CU16"}, {"key": "S:Quitar prenda de la lista de deseos", "name": "Quitar prenda de la lista de deseos", "notes": "Fuente en el codigo: DELETE /wishlist/items/{id} (remove_route)", "cu": "CU16"}, {"key": "S:Mover prendas al carrito", "name": "Mover prendas al carrito", "notes": "Fuente en el codigo: POST /wishlist/items/{id}/move-to-cart y /move-all-to-cart", "cu": "CU16"}, {"key": "S:Consultar movimientos de puntos", "name": "Consultar movimientos de puntos", "notes": "Fuente en el codigo: GET /loyalty/transactions (transactions_route)", "cu": "CU17"}, {"key": "S:Canjear puntos en la compra", "name": "Canjear puntos en la compra", "notes": "Fuente en el codigo: points_to_redeem en payment_schema y sales_schema", "cu": "CU17"}, {"key": "S:Consultar puntos del cliente en caja", "name": "Consultar puntos del cliente en caja", "notes": "Fuente en el codigo: GET /loyalty/customer (customer_balance_route)", "cu": "CU17"}, {"key": "S:Consultar tarjetas de regalo compradas", "name": "Consultar tarjetas de regalo compradas", "notes": "Fuente en el codigo: GET /gift-cards/my-purchases (my_purchases_route)", "cu": "CU18"}, {"key": "S:Canjear tarjeta de regalo en la billetera", "name": "Canjear tarjeta de regalo en la billetera", "notes": "Fuente en el codigo: POST /wallet/redeem-gift-card", "cu": "CU19"}, {"key": "S:Convertir puntos en saldo", "name": "Convertir puntos en saldo", "notes": "Fuente en el codigo: POST /wallet/convert-points", "cu": "CU19"}, {"key": "S:Pagar con saldo de la billetera", "name": "Pagar con saldo de la billetera", "notes": "Fuente en el codigo: POST /wallet/pay y /wallet/checkout", "cu": "CU19"}, {"key": "S:Consultar movimientos de la billetera", "name": "Consultar movimientos de la billetera", "notes": "Fuente en el codigo: GET /wallet/transactions", "cu": "CU19"}, {"key": "S:Cotizar env\u00edo a domicilio", "name": "Cotizar env\u00edo a domicilio", "notes": "Fuente en el codigo: POST /delivery/quotes (quote_route)", "cu": "CU20"}, {"key": "S:Consultar mis env\u00edos", "name": "Consultar mis env\u00edos", "notes": "Fuente en el codigo: GET /delivery/my-orders (my_orders_route)", "cu": "CU20"}, {"key": "S:Tomar pedido disponible", "name": "Tomar pedido disponible", "notes": "Fuente en el codigo: GET /delivery/available y POST /delivery/orders/{id}/claim", "cu": "CU20"}, {"key": "S:Consultar hoja de ruta", "name": "Consultar hoja de ruta", "notes": "Fuente en el codigo: GET /delivery/routes (routes_route)", "cu": "CU20"}, {"key": "S:Confirmar entrega con PIN", "name": "Confirmar entrega con PIN", "notes": "Fuente en el codigo: POST /delivery/confirm-delivery (confirm_route)", "cu": "CU20"}, {"key": "S:Registrar repartidor", "name": "Registrar repartidor", "notes": "Fuente en el codigo: POST /delivery/drivers (create_driver_route)", "cu": "CU20"}, {"key": "S:Registrar solicitud de cambio o devoluci\u00f3n", "name": "Registrar solicitud de cambio o devoluci\u00f3n", "notes": "Fuente en el codigo: POST /rma/requests (create_rma_request_endpoint)", "cu": "CU21"}, {"key": "S:Consultar pedidos elegibles", "name": "Consultar pedidos elegibles", "notes": "Fuente en el codigo: GET /rma/eligible-orders (plazo de 30 dias)", "cu": "CU21"}, {"key": "S:Descargar comprobante de la solicitud", "name": "Descargar comprobante de la solicitud", "notes": "Fuente en el codigo: GET /rma/requests/{id}/pdf", "cu": "CU21"}, {"key": "S:Dictaminar prenda devuelta", "name": "Dictaminar prenda devuelta", "notes": "Fuente en el codigo: PATCH /rma/requests/{id}/items/{item}/review", "cu": "CU21"}, {"key": "S:Liquidar reembolsos en billetera", "name": "Liquidar reembolsos en billetera", "notes": "Fuente en el codigo: POST /rma/settle-monthly-wallets", "cu": "CU21"}, {"key": "S:Cargar manifiesto de la empresa", "name": "Cargar manifiesto de la empresa", "notes": "Fuente en el codigo: GET /pwa/manifest y PwaService.loadDynamicManifest", "cu": "CU22"}, {"key": "S:Actualizar a la nueva versi\u00f3n", "name": "Actualizar a la nueva versi\u00f3n", "notes": "Fuente en el codigo: PwaService.applyUpdate (SwUpdate)", "cu": "CU22"}, {"key": "S:Sincronizar cat\u00e1logo local", "name": "Sincronizar cat\u00e1logo local", "notes": "Fuente en el codigo: GET /offline/catalog-sync y OfflineCatalogService.syncCatalog", "cu": "CU23"}, {"key": "S:Encolar operaci\u00f3n pendiente", "name": "Encolar operaci\u00f3n pendiente", "notes": "Fuente en el codigo: OfflineQueueService.enqueueOperation", "cu": "CU25"}, {"key": "S:Emitir comprobante provisional", "name": "Emitir comprobante provisional", "notes": "Fuente en el codigo: OfflineProvisionalReceiptDialogComponent", "cu": "CU25"}, {"key": "S:Subir logo de la empresa", "name": "Subir logo de la empresa", "notes": "Fuente en el codigo: POST /tenants/me/logo y /tenants/{id}/logo", "cu": "CU26"}, {"key": "S:Eliminar logo de la empresa", "name": "Eliminar logo de la empresa", "notes": "Fuente en el codigo: DELETE /tenants/me/logo y /tenants/{id}/logo", "cu": "CU26"}, {"key": "S:Cambiar plan de suscripci\u00f3n", "name": "Cambiar plan de suscripci\u00f3n", "notes": "Fuente en el codigo: POST /subscriptions/change-plan (change_plan_route)", "cu": "CU28"}, {"key": "S:Consultar historial de facturaci\u00f3n", "name": "Consultar historial de facturaci\u00f3n", "notes": "Fuente en el codigo: GET /subscriptions/history", "cu": "CU28"}, {"key": "S:Resolver conflicto de inventario", "name": "Resolver conflicto de inventario", "notes": "Fuente en el codigo: POST /offline/conflicts/{id}/resolve", "cu": "CU30"}], "subLinks": [{"from": "S:Registrar organizaci\u00f3n", "to": "CU1", "kind": "extend"}, {"from": "S:Suspender o reactivar organizaci\u00f3n", "to": "CU1", "kind": "extend"}, {"from": "S:Registrar administrador de la organizaci\u00f3n", "to": "CU1", "kind": "extend"}, {"from": "S:Ingresar al panel de la organizaci\u00f3n", "to": "CU1", "kind": "extend"}, {"from": "S:Crear plan de suscripci\u00f3n", "to": "CU2", "kind": "extend"}, {"from": "S:Editar plan de suscripci\u00f3n", "to": "CU2", "kind": "extend"}, {"from": "S:Crear rol personalizado", "to": "CU3", "kind": "extend"}, {"from": "S:Editar permisos del rol", "to": "CU3", "kind": "extend"}, {"from": "S:Asignar roles a un usuario", "to": "CU3", "kind": "extend"}, {"from": "S:Crear rol personalizado", "to": "S:Consultar cat\u00e1logo de permisos", "kind": "include"}, {"from": "S:Consultar historial de conversaci\u00f3n", "to": "CU7", "kind": "extend"}, {"from": "S:Reiniciar conversaci\u00f3n", "to": "CU7", "kind": "extend"}, {"from": "S:Predecir demanda de prendas", "to": "CU8", "kind": "extend"}, {"from": "S:Segmentar clientes por comportamiento", "to": "CU8", "kind": "extend"}, {"from": "S:Exportar reporte inteligente", "to": "CU8", "kind": "extend"}, {"from": "S:Aplicar traspasos sugeridos", "to": "CU9", "kind": "extend"}, {"from": "S:Descartar traspasos sugeridos", "to": "CU9", "kind": "extend"}, {"from": "S:Configurar reglas de reabastecimiento", "to": "CU9", "kind": "extend"}, {"from": "S:Corregir \u00edtems extra\u00eddos", "to": "CU10", "kind": "extend"}, {"from": "S:Confirmar ingreso de mercader\u00eda", "to": "CU10", "kind": "extend"}, {"from": "CU12", "to": "S:Registrar dispositivo para notificaciones", "kind": "include"}, {"from": "S:Marcar notificaciones como le\u00eddas", "to": "CU12", "kind": "extend"}, {"from": "S:Exportar reporte operativo", "to": "CU14", "kind": "extend"}, {"from": "S:Crear cup\u00f3n de descuento", "to": "CU15", "kind": "extend"}, {"from": "S:Aplicar cup\u00f3n en el carrito", "to": "CU15", "kind": "extend"}, {"from": "S:Quitar cup\u00f3n del carrito", "to": "S:Aplicar cup\u00f3n en el carrito", "kind": "extend"}, {"from": "S:Aplicar cup\u00f3n en la venta de caja", "to": "CU15", "kind": "extend"}, {"from": "S:Agregar prenda a la lista de deseos", "to": "CU16", "kind": "extend"}, {"from": "S:Quitar prenda de la lista de deseos", "to": "CU16", "kind": "extend"}, {"from": "S:Mover prendas al carrito", "to": "CU16", "kind": "extend"}, {"from": "S:Consultar movimientos de puntos", "to": "CU17", "kind": "extend"}, {"from": "S:Canjear puntos en la compra", "to": "CU17", "kind": "extend"}, {"from": "S:Consultar puntos del cliente en caja", "to": "CU17", "kind": "extend"}, {"from": "S:Consultar tarjetas de regalo compradas", "to": "CU18", "kind": "extend"}, {"from": "S:Canjear tarjeta de regalo en la billetera", "to": "CU19", "kind": "extend"}, {"from": "S:Convertir puntos en saldo", "to": "CU19", "kind": "extend"}, {"from": "S:Pagar con saldo de la billetera", "to": "CU19", "kind": "extend"}, {"from": "S:Consultar movimientos de la billetera", "to": "CU19", "kind": "extend"}, {"from": "S:Cotizar env\u00edo a domicilio", "to": "CU20", "kind": "extend"}, {"from": "S:Consultar mis env\u00edos", "to": "CU20", "kind": "extend"}, {"from": "S:Tomar pedido disponible", "to": "CU20", "kind": "extend"}, {"from": "S:Consultar hoja de ruta", "to": "CU20", "kind": "extend"}, {"from": "S:Confirmar entrega con PIN", "to": "CU20", "kind": "extend"}, {"from": "S:Registrar repartidor", "to": "CU20", "kind": "extend"}, {"from": "S:Registrar solicitud de cambio o devoluci\u00f3n", "to": "CU21", "kind": "extend"}, {"from": "S:Registrar solicitud de cambio o devoluci\u00f3n", "to": "S:Consultar pedidos elegibles", "kind": "include"}, {"from": "S:Descargar comprobante de la solicitud", "to": "CU21", "kind": "extend"}, {"from": "S:Dictaminar prenda devuelta", "to": "CU21", "kind": "extend"}, {"from": "S:Liquidar reembolsos en billetera", "to": "CU21", "kind": "extend"}, {"from": "CU22", "to": "S:Cargar manifiesto de la empresa", "kind": "include"}, {"from": "S:Actualizar a la nueva versi\u00f3n", "to": "CU22", "kind": "extend"}, {"from": "CU23", "to": "S:Sincronizar cat\u00e1logo local", "kind": "include"}, {"from": "CU25", "to": "S:Encolar operaci\u00f3n pendiente", "kind": "include"}, {"from": "CU25", "to": "S:Emitir comprobante provisional", "kind": "include"}, {"from": "S:Subir logo de la empresa", "to": "CU26", "kind": "extend"}, {"from": "S:Eliminar logo de la empresa", "to": "CU26", "kind": "extend"}, {"from": "S:Cambiar plan de suscripci\u00f3n", "to": "CU28", "kind": "extend"}, {"from": "S:Consultar historial de facturaci\u00f3n", "to": "CU28", "kind": "extend"}, {"from": "S:Resolver conflicto de inventario", "to": "CU30", "kind": "extend"}], "diagrams": [{"cu": "CU1", "layout": {"S:Registrar organizaci\u00f3n": [590, 40], "S:Suspender o reactivar organizaci\u00f3n": [590, 150], "S:Registrar administrador de la organizaci\u00f3n": [590, 260], "S:Ingresar al panel de la organizaci\u00f3n": [590, 370], "CU2": [590, 480], "CU1": [210, 260], "SA": [40, 260]}, "hide": ["SA|CU2"]}, {"cu": "CU2", "layout": {"S:Crear plan de suscripci\u00f3n": [590, 40], "S:Editar plan de suscripci\u00f3n": [590, 290], "CU1": [590, 540], "CU4": [590, 790], "CU2": [210, 415], "SA": [40, 415]}, "hide": ["SA|CU1"]}, {"cu": "CU3", "layout": {"S:Crear rol personalizado": [590, 40], "S:Editar permisos del rol": [590, 150], "S:Asignar roles a un usuario": [590, 260], "S:Consultar cat\u00e1logo de permisos": [940, 40], "CU3": [210, 150], "SA": [40, 65], "AD": [40, 235]}, "hide": []}, {"cu": "CU4", "layout": {"CU2": [590, 40], "CU4": [210, 40], "AD": [40, 40]}, "hide": []}, {"cu": "CU5", "layout": {"CU5": [210, 40], "CL": [40, 40]}, "hide": []}, {"cu": "CU6", "layout": {"CU6": [210, 40], "CL": [40, 40]}, "hide": []}, {"cu": "CU7", "layout": {"S:Consultar historial de conversaci\u00f3n": [590, 40], "S:Reiniciar conversaci\u00f3n": [590, 150], "CU7": [210, 95], "CL": [40, 95]}, "hide": []}, {"cu": "CU8", "layout": {"S:Predecir demanda de prendas": [590, 40], "S:Segmentar clientes por comportamiento": [590, 150], "S:Exportar reporte inteligente": [590, 260], "CU8": [210, 150], "AD": [40, 150]}, "hide": []}, {"cu": "CU9", "layout": {"S:Aplicar traspasos sugeridos": [590, 40], "S:Descartar traspasos sugeridos": [590, 150], "S:Configurar reglas de reabastecimiento": [590, 260], "CU9": [210, 150], "AD": [40, 150]}, "hide": []}, {"cu": "CU10", "layout": {"S:Corregir \u00edtems extra\u00eddos": [590, 155], "S:Confirmar ingreso de mercader\u00eda": [590, 265], "CU10": [210, 210], "PR": [40, 40], "AD": [40, 210], "EN": [40, 380]}, "hide": []}, {"cu": "CU11", "layout": {"CU12": [630, 125], "CU11": [210, 125], "AD": [40, 40], "EN": [40, 210]}, "hide": ["AD|CU12", "EN|CU12"]}, {"cu": "CU12", "layout": {"S:Registrar dispositivo para notificaciones": [590, 80], "S:Marcar notificaciones como le\u00eddas": [590, 210], "CU11": [590, 340], "CU12": [210, 210], "CL": [40, 40], "AD": [40, 210], "EN": [40, 380]}, "hide": ["AD|CU11", "EN|CU11"]}, {"cu": "CU13", "layout": {"CU13": [210, 40], "AD": [40, 40]}, "hide": []}, {"cu": "CU14", "layout": {"S:Exportar reporte operativo": [590, 125], "CU14": [210, 125], "AD": [40, 40], "EN": [40, 210]}, "hide": []}, {"cu": "CU15", "layout": {"S:Crear cup\u00f3n de descuento": [590, 185], "S:Aplicar cup\u00f3n en el carrito": [590, 295], "S:Aplicar cup\u00f3n en la venta de caja": [590, 405], "S:Quitar cup\u00f3n del carrito": [940, 295], "CU15": [210, 295], "AD": [40, 40], "EN": [40, 210], "CL": [40, 380], "CA": [40, 550]}, "hide": []}, {"cu": "CU16", "layout": {"S:Agregar prenda a la lista de deseos": [590, 40], "S:Quitar prenda de la lista de deseos": [590, 150], "S:Mover prendas al carrito": [590, 260], "CU16": [210, 150], "CL": [40, 150]}, "hide": []}, {"cu": "CU17", "layout": {"S:Consultar movimientos de puntos": [590, 40], "S:Canjear puntos en la compra": [590, 150], "S:Consultar puntos del cliente en caja": [590, 260], "CU17": [210, 150], "CL": [40, 65], "CA": [40, 235]}, "hide": []}, {"cu": "CU18", "layout": {"S:Consultar tarjetas de regalo compradas": [590, 40], "CU18": [210, 40], "CL": [40, 40]}, "hide": []}, {"cu": "CU19", "layout": {"S:Canjear tarjeta de regalo en la billetera": [590, 40], "S:Convertir puntos en saldo": [590, 150], "S:Pagar con saldo de la billetera": [590, 260], "S:Consultar movimientos de la billetera": [590, 370], "CU19": [210, 205], "CL": [40, 205]}, "hide": []}, {"cu": "CU20", "layout": {"S:Cotizar env\u00edo a domicilio": [590, 40], "S:Consultar mis env\u00edos": [590, 150], "S:Tomar pedido disponible": [590, 260], "S:Consultar hoja de ruta": [590, 370], "S:Confirmar entrega con PIN": [590, 480], "S:Registrar repartidor": [590, 590], "CU20": [210, 315], "CL": [40, 145], "RE": [40, 315], "SA": [40, 485]}, "hide": []}, {"cu": "CU21", "layout": {"S:Registrar solicitud de cambio o devoluci\u00f3n": [590, 45], "S:Descargar comprobante de la solicitud": [590, 155], "S:Dictaminar prenda devuelta": [590, 265], "S:Liquidar reembolsos en billetera": [590, 375], "S:Consultar pedidos elegibles": [940, 45], "CU21": [210, 210], "CL": [40, 40], "EN": [40, 210], "AD": [40, 380]}, "hide": []}, {"cu": "CU22", "layout": {"S:Cargar manifiesto de la empresa": [590, 240], "S:Actualizar a la nueva versi\u00f3n": [590, 350], "CU22": [210, 295], "CL": [40, 40], "CA": [40, 210], "EN": [40, 380], "AD": [40, 550]}, "hide": []}, {"cu": "CU23", "layout": {"S:Sincronizar cat\u00e1logo local": [590, 40], "CU23": [210, 40], "CA": [40, 40]}, "hide": []}, {"cu": "CU24", "layout": {"CU24": [210, 125], "EN": [40, 40], "AD": [40, 210]}, "hide": []}, {"cu": "CU25", "layout": {"S:Encolar operaci\u00f3n pendiente": [590, 40], "S:Emitir comprobante provisional": [590, 150], "CU25": [210, 95], "CA": [40, 95]}, "hide": []}, {"cu": "CU26", "layout": {"S:Subir logo de la empresa": [590, 70], "S:Eliminar logo de la empresa": [590, 180], "CU26": [210, 125], "AD": [40, 40], "SA": [40, 210]}, "hide": []}, {"cu": "CU27", "layout": {"CU27": [210, 40], "AD": [40, 40]}, "hide": []}, {"cu": "CU28", "layout": {"S:Cambiar plan de suscripci\u00f3n": [590, 40], "S:Consultar historial de facturaci\u00f3n": [590, 150], "CU28": [210, 95], "AD": [40, 95]}, "hide": []}, {"cu": "CU29", "layout": {"CU29": [210, 125], "CA": [40, 40], "CL": [40, 210]}, "hide": []}, {"cu": "CU30", "layout": {"S:Resolver conflicto de inventario": [590, 210], "CU30": [210, 210], "CA": [40, 40], "AD": [40, 210], "EN": [40, 380]}, "hide": []}]};
var ROOT_NAME = "Casos de uso - FashionStore SaaS";
var MARKER = "[generado: FashionStore_casos_de_uso.js]";
var STEP = "inicio";

function log(msg) { Session.Output(msg); }
function has(obj, key) { return Object.prototype.hasOwnProperty.call(obj, key); }

function newElement(pkg, name, type, notes, alias) {
    STEP = "elemento " + name;
    var e = pkg.Elements.AddNew(name, type);
    if (notes) { e.Notes = notes; }
    if (alias) { e.Alias = alias; }
    if (!e.Update()) { throw new Error("No se pudo crear " + name + ": " + e.GetLastError()); }
    return e;
}

function place(d, el, left, top, width, height) {
    var o = d.DiagramObjects.AddNew("l=" + left + ";r=" + (left + width) + ";t=" + top + ";b=" + (top + height) + ";", "");
    o.ElementID = el.ElementID;
    o.Style = "NSL=0;";
    o.Sequence = 1 + Math.floor((width * height) / 100);  /* lo mas grande (limite del sistema) queda detras */
    o.Update();
    return o;
}

function associate(actor, uc) {
    STEP = "asociacion " + actor.Name + " - " + uc.Name;
    var c = actor.Connectors.AddNew("", "Association");
    c.SupplierID = uc.ElementID;
    if (!c.Update()) { throw new Error("No se pudo crear " + STEP + ": " + c.GetLastError()); }
    return c;
}

function relate(from, to, kind) {
    STEP = kind + " " + from.Name + " -> " + to.Name;
    var c = from.Connectors.AddNew("", "UseCase");
    c.SupplierID = to.ElementID;
    c.Subtype = kind === "include" ? "Includes" : "Extends";
    c.Stereotype = kind;
    c.Direction = "Source -> Destination";
    if (!c.Update()) { throw new Error("No se pudo crear " + STEP + ": " + c.GetLastError()); }
    return c;
}

function run() {
    var parent = Repository.GetTreeSelectedPackage();
    if (parent === null || parent === undefined) {
        Session.Prompt("Seleccione en el Project Browser el paquete donde crear el diagrama y vuelva a ejecutar.", 1);
        return false;
    }
    var i, j, k;
    for (i = 0; i < parent.Packages.Count; i++) {
        var old = parent.Packages.GetAt(i);
        if (old.Name !== ROOT_NAME) { continue; }
        if (old.Notes.indexOf(MARKER) < 0) {
            throw new Error("Ya existe un paquete '" + ROOT_NAME + "' que NO creo este script: renombrelo y vuelva a ejecutar.");
        }
        parent.Packages.DeleteAt(i, false);
        parent.Packages.Refresh();
        log("Paquete anterior eliminado; se crea de nuevo.");
        break;
    }
    STEP = "paquete";
    var pkg = parent.Packages.AddNew(ROOT_NAME, "");
    pkg.Notes = "Actores oficiales y los 30 casos de uso de FashionStore SaaS. " + MARKER;
    pkg.Update();
    parent.Packages.Refresh();

    var EL = {};
    var CONN = {};  /* "desde|hacia" -> conector, para dibujar los quiebres */
    for (k in MODEL.actors) {
        if (has(MODEL.actors, k)) { EL[k] = newElement(pkg, MODEL.actors[k], "Actor", "", ""); }
    }
    for (i = 0; i < MODEL.cases.length; i++) {
        var c = MODEL.cases[i];
        EL[c.id] = newElement(pkg, c.id + " - " + c.name, "UseCase", c.notes, c.id);
        for (j = 0; j < c.actors.length; j++) { CONN[c.actors[j] + "|" + c.id] = associate(EL[c.actors[j]], EL[c.id]); }
    }
    for (i = 0; i < MODEL.relations.length; i++) {
        var r = MODEL.relations[i];
        CONN[r.from + "|" + r.to] = relate(EL[r.from], EL[r.to], r.kind);
    }

    STEP = "diagrama general";
    for (i = 0; i < MODEL.subs.length; i++) {
        var sb = MODEL.subs[i];
        EL[sb.key] = newElement(pkg, sb.name, "UseCase", sb.notes, "");
    }
    for (i = 0; i < MODEL.subLinks.length; i++) {
        var sl = MODEL.subLinks[i];
        relate(EL[sl.from], EL[sl.to], sl.kind);
    }

    var d = pkg.Diagrams.AddNew("Diagrama general de casos de uso - FashionStore SaaS", "Use Case");
    d.Notes = "Los 30 casos de uso con sus actores y relaciones include / extend. " + MARKER;
    if (!d.Update()) { throw new Error("No se pudo crear el diagrama: " + d.GetLastError()); }
    pkg.Diagrams.Refresh();
    var system = newElement(pkg, "FashionStore SaaS", "Boundary", "Limite del sistema", "");
    var B = MODEL.boundary;
    place(d, system, B[0], B[1], B[2], B[3]);
    for (k in MODEL.layout) {
        if (!has(MODEL.layout, k)) { continue; }
        var p = MODEL.layout[k];
        var size = has(MODEL.actors, k) ? MODEL.act : MODEL.uc;
        place(d, EL[k], p[0], p[1], size[0], size[1]);
    }
    d.Update();
    /* las lineas que chocarian con otro caso de uso pasan por el hueco libre entre dos figuras */
    for (i = 0; i < MODEL.routes.length; i++) {
        var rt = MODEL.routes[i];
        STEP = "quiebre " + rt.from + " - " + rt.to;
        var link = d.DiagramLinks.AddNew("", "");
        link.ConnectorID = CONN[rt.from + "|" + rt.to].ConnectorID;
        link.LineStyle = 3;
        var path = "";
        for (j = 0; j < rt.path.length; j++) { path += rt.path[j][0] + ":" + (-rt.path[j][1]) + ";"; }
        link.Path = path;
        if (!link.Update()) { throw new Error("No se pudo trazar " + STEP + ": " + link.GetLastError()); }
    }
    d.DiagramLinks.Refresh();
    d.Update();
    Repository.SaveDiagram(d.DiagramID);

    /* un diagrama por caso de uso: sus actores, el caso base y sus extensiones / inclusiones */
    for (i = 0; i < MODEL.diagrams.length; i++) {
        var dg = MODEL.diagrams[i];
        var base = EL[dg.cu];
        STEP = "diagrama " + base.Name;
        var cd = pkg.Diagrams.AddNew(base.Name, "Use Case");
        cd.Notes = base.Notes + " " + MARKER;
        if (!cd.Update()) { throw new Error("No se pudo crear el diagrama " + base.Name + ": " + cd.GetLastError()); }
        pkg.Diagrams.Refresh();
        for (k in dg.layout) {
            if (!has(dg.layout, k)) { continue; }
            var q = dg.layout[k];
            var sz = has(MODEL.actors, k) ? MODEL.act : MODEL.uc;
            place(cd, EL[k], q[0], q[1], sz[0], sz[1]);
        }
        for (j = 0; j < dg.hide.length; j++) {
            var hl = cd.DiagramLinks.AddNew("", "");
            hl.ConnectorID = CONN[dg.hide[j]].ConnectorID;
            hl.IsHidden = true;
            hl.Update();
        }
        cd.Update();
        Repository.SaveDiagram(cd.DiagramID);
    }
    Repository.RefreshModelView(parent.PackageID);
    Repository.OpenDiagram(d.DiagramID);
    return true;
}

function main() {
    Repository.EnsureOutputVisible("Script");
    Repository.ClearOutput("Script");
    if (typeof ScriptEngine === "undefined") {
        var msg = "Este script debe crearse como JScript, no como JavaScript: clic derecho en el grupo > New JScript.";
        log("[ERROR] " + msg);
        Session.Prompt(msg, 1);
        return;
    }
    log("FashionStore - generando el diagrama general de casos de uso...");
    Repository.EnableUIUpdates = false;
    var ok = false;
    try {
        ok = run();
    } catch (e) {
        log("[ERROR] " + (e.message || e.description || e) + " | paso: " + STEP);
    }
    Repository.EnableUIUpdates = true;
    if (ok) {
        log("[OK] Diagrama general y " + MODEL.diagrams.length + " diagramas por caso de uso creados en '" + ROOT_NAME + "'.");
        Session.Prompt("Diagramas de casos de uso generados correctamente.", 1);
    }
}

if (typeof Repository !== "undefined") { main(); }
