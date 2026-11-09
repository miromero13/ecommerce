"""Analiza backend/app (rutas y servicios) con AST para obtener, sin escribir nada a mano:
  - por funcion: modelos que usa (constructor Model(...), query(Model), select(Model), db.get(Model, ...),
    filtros Model.columna) y funciones que llama;
  - por caso de uso: las tablas alcanzadas desde sus puntos de entrada (endpoints) siguiendo las llamadas;
  - por tabla: sus operaciones = funciones publicas de servicio que crean o consultan esa tabla.
Guarda analisis.json junto a este archivo.
"""
import ast
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP = HERE.parents[2] / "backend" / "app"
MODELOS = json.loads((HERE / "modelos.json").read_text(encoding="utf-8"))
CLASS_TABLE = {v["class"]: t for t, v in MODELOS.items() if v["class"]}

# Puntos de entrada por caso de uso: modulo.funcion (endpoints y funciones de servicio invocadas por el CU).
ENTRADAS = {
    "CU1": ["routes.tenant_routes.list_tenants_route", "routes.tenant_routes.get_tenant_route",
            "routes.tenant_routes.register_tenant_admin_route", "routes.tenant_routes.open_tenant_panel_route",
            "routes.tenant_routes.update_tenant_status_route", "routes.subscription_routes.create_tenant_with_subscription_route",
            "routes.subscription_routes.get_plans_route"],
    "CU2": ["routes.subscription_routes.list_all_plans_route", "routes.subscription_routes.create_plan_route",
            "routes.subscription_routes.update_plan_route"],
    "CU3": ["routes.rbac_routes.get_permissions", "routes.rbac_routes.get_roles", "routes.rbac_routes.post_role",
            "routes.rbac_routes.put_role", "routes.user_routes.create_admin_user_route", "routes.user_routes.update_user_full_route"],
    "CU4": ["routes.subscription_routes.get_plans_route"],
    "CU5": ["routes.garment_routes.catalog_garment_route", "routes.garment_routes.virtual_try_on_route"],
    "CU6": ["routes.recommendation_routes.collaborative_recommendations_route", "routes.catalog_routes.record_product_view_route"],
    "CU7": ["routes.chatbot_routes.chatbot_message_route", "routes.chatbot_routes.chatbot_messages_route",
            "routes.chatbot_routes.chatbot_reset_route"],
    "CU8": ["routes.report_routes.natural_report_route", "routes.report_routes.predict_demand_route",
            "routes.report_routes.customer_clusters_route", "routes.report_routes.top_products_route",
            "routes.report_routes.branch_comparison_route", "routes.report_routes.critical_inventory_route",
            "routes.report_routes.excel_export_route", "routes.report_routes.pdf_export_route"],
    "CU9": ["routes.expert_replenishment_routes.evaluate_replenishment", "routes.expert_replenishment_routes.apply_replenishment_transfers",
            "routes.expert_replenishment_routes.discard_replenishment_transfers", "routes.expert_replenishment_routes.get_rules",
            "routes.expert_replenishment_routes.update_replenishment_rules", "routes.expert_replenishment_routes.get_suggestions"],
    "CU10": ["routes.rpa_ingest_routes.upload_document_route", "routes.rpa_ingest_routes.list_jobs_route",
             "routes.rpa_ingest_routes.get_job_route", "routes.rpa_ingest_routes.correct_items_route",
             "routes.rpa_ingest_routes.commit_job_route"],
    "CU11": ["routes.inventory_routes.transfer_route", "routes.inventory_routes.branch_stock_route",
             "routes.inventory_routes.movements_route"],
    "CU12": ["routes.notification_routes.list_notifications_route", "routes.notification_routes.unread_count_route",
             "routes.notification_routes.mark_all_read_route", "routes.notification_routes.mark_read_route",
             "routes.notification_routes.register_token_route", "routes.notification_routes.unregister_token_route",
             "services.notification_delivery.notify_reservation_event", "services.notification_delivery.notify_order_event",
             "services.notification_delivery.notify_low_stock"],
    "CU13": ["routes.dashboard_routes.dashboard_route"],
    "CU14": ["routes.report_routes.sales_report_route", "routes.report_routes.inventory_report_route",
             "routes.report_routes.movements_report_route"],
    "CU15": ["routes.promotion_routes.get_promotion_codes", "routes.promotion_routes.create_promotion_code",
             "routes.cart_routes.apply_coupon_route", "routes.cart_routes.remove_coupon_route",
             "services.sales_service._apply_cashier_coupon"],
    "CU16": ["routes.wishlist_routes.list_route", "routes.wishlist_routes.add_route", "routes.wishlist_routes.remove_route",
             "routes.wishlist_routes.move_route", "routes.wishlist_routes.move_all_route"],
    "CU17": ["routes.loyalty_routes.balance_route", "routes.loyalty_routes.transactions_route",
             "routes.loyalty_routes.customer_balance_route", "services.loyalty_service.earn", "services.loyalty_service.redeem"],
    "CU18": ["routes.gift_card_routes.purchase_route", "routes.gift_card_routes.confirm_payment_route",
             "routes.gift_card_routes.my_purchases_route"],
    "CU19": ["routes.wallet_routes.balance_route", "routes.wallet_routes.redeem_gift_card_route",
             "routes.wallet_routes.convert_points_route", "routes.wallet_routes.pay_route",
             "routes.wallet_routes.checkout_route", "routes.wallet_routes.transactions_route"],
    "CU20": ["routes.delivery_routes.quote_route", "routes.delivery_routes.my_orders_route",
             "routes.delivery_routes.available_route", "routes.delivery_routes.claim_route",
             "routes.delivery_routes.routes_route", "routes.delivery_routes.confirm_route",
             "routes.delivery_routes.drivers_route", "routes.delivery_routes.create_driver_route"],
    "CU21": ["routes.rma_routes.get_eligible_orders_endpoint", "routes.rma_routes.create_rma_request_endpoint",
             "routes.rma_routes.list_rma_requests_endpoint", "routes.rma_routes.get_rma_request_endpoint",
             "routes.rma_routes.download_rma_pdf_endpoint", "routes.rma_routes.review_rma_item_endpoint",
             "routes.rma_routes.settle_monthly_wallets_endpoint"],
    "CU22": ["routes.pwa_routes.get_pwa_manifest"],
    "CU23": ["routes.offline_routes.get_offline_catalog_sync"],
    "CU24": ["routes.rma_routes.review_rma_item_endpoint"],
    "CU25": ["routes.cart_routes.add_cart_item_route"],  # la venta se guarda en IndexedDB; el cliente agrega al carrito (o lo guarda sin conexion)
    "CU26": ["routes.tenant_routes.get_branding_route", "routes.tenant_routes.update_my_branding_route",
             "routes.tenant_routes.upload_my_logo_route", "routes.tenant_routes.upload_tenant_logo_route",
             "routes.tenant_routes.delete_my_logo_route", "routes.tenant_routes.delete_tenant_logo_route",
             "routes.tenant_routes.update_tenant_route"],
    "CU27": ["routes.subscription_routes.purchase_simulated_subscription_route"],
    "CU28": ["routes.subscription_routes.get_current_subscription_route", "routes.subscription_routes.get_subscription_history_route",
             "routes.subscription_routes.change_plan_route"],
    "CU29": [],  # solo frontend / movil: lee la cola local
    "CU30": ["routes.offline_routes.sync_offline_queue", "routes.offline_routes.resolve_offline_conflict",
             "routes.cart_routes.add_cart_item_route"],
}
MODULOS = {
    "M1": ("SaaS y Seguridad", ["CU1", "CU2", "CU3", "CU4", "CU26", "CU27", "CU28"]),
    "M2": ("Inteligencia Artificial", ["CU5", "CU6", "CU7", "CU8", "CU9", "CU10"]),
    "M3": ("Inventario y Operaciones", ["CU11", "CU12"]),
    "M4": ("Business Intelligence", ["CU13", "CU14"]),
    "M5": ("Promociones y Fidelización", ["CU15", "CU16", "CU17", "CU18", "CU19"]),
    "M6": ("Logística y Posventa", ["CU20", "CU21", "CU22", "CU23", "CU24", "CU25", "CU29", "CU30"]),
}
PROFUNDIDAD = 3  # niveles de llamadas seguidos desde cada endpoint


class Func:
    def __init__(self, module, node, imports):
        self.module, self.node, self.name = module, node, node.name
        self.models, self.calls = set(), set()
        self.writes = set()
        self.queried = []  # (linea, columna, Modelo) del primer argumento de query/select/get, en orden de codigo
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                f = sub.func
                fname = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
                if fname in CLASS_TABLE:
                    self.models.add(fname)
                    self.writes.add(fname)  # constructor: crea la fila
                if fname in ("query", "select", "get", "delete", "update") and sub.args:
                    a0 = sub.args[0]
                    base = a0.value if isinstance(a0, ast.Attribute) else a0
                    if isinstance(base, ast.Name) and base.id in CLASS_TABLE:
                        self.models.add(base.id)
                        self.queried.append((sub.lineno, sub.col_offset, base.id))
                if isinstance(f, ast.Name):
                    self.calls.add(imports.get(f.id, f"{module}.{f.id}"))
                elif isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id in imports:
                    self.calls.add(f"{imports[f.value.id]}.{f.attr}")
            elif isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name) and sub.value.id in CLASS_TABLE:
                if isinstance(sub.ctx, ast.Load):
                    self.models.add(sub.value.id)  # Model.columna en filtros / ordenamientos

    def _models_in(self, ann):
        import re as _re
        return [n for n in _re.findall(r"\b([A-Z]\w+)\b", ann or "") if n in CLASS_TABLE]

    def evidence(self):
        """(modifica, retorna, recibe): entidades segun asignaciones a parametros tipados, retorno y parametros."""
        typed = {}
        for a in self.node.args.args + self.node.args.kwonlyargs:
            ms = self._models_in(ast.unparse(a.annotation)) if a.annotation else []
            if ms:
                typed[a.arg] = ms[0]
        mod = []
        for sub in ast.walk(self.node):
            if isinstance(sub, (ast.Assign, ast.AugAssign)):
                targets = sub.targets if isinstance(sub, ast.Assign) else [sub.target]
                for t in targets:
                    if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id in typed:
                        if typed[t.value.id] not in mod:
                            mod.append(typed[t.value.id])
        ret = self._models_in(ast.unparse(self.node.returns)) if self.node.returns else []
        return mod, ret, list(typed.values())

    def params(self):
        args = [a for a in self.node.args.args + self.node.args.kwonlyargs
                if a.arg not in ("db", "self", "session", "background_tasks")]
        return [a.arg for a in args], [ast.unparse(a.annotation) if a.annotation else "" for a in args]

    def signature(self):
        names, types = self.params()
        return f"{self.name}({', '.join(n + (': ' + t if t else '') for n, t in zip(names, types))})"


FUNCS = {}
for folder in ("routes", "services"):
    for path in sorted((APP / folder).rglob("*.py")):
        rel = path.relative_to(APP).with_suffix("")
        module = ".".join(rel.parts)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {}
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("app."):
                for alias in n.names:
                    target = n.module[4:]
                    imports[alias.asname or alias.name] = (
                        f"{target}.{alias.name}" if not target.endswith(("services", "routes")) else f"{target}.{alias.name}")
        for n in tree.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                FUNCS[f"{module}.{n.name}"] = Func(module, n, imports)


def reach(entry):
    seen, frontier, models = set(), [entry], set()
    for _ in range(PROFUNDIDAD + 1):
        nxt = []
        for key in frontier:
            if key in seen or key not in FUNCS:
                continue
            seen.add(key)
            models |= FUNCS[key].models
            nxt.extend(FUNCS[key].calls)
        frontier = nxt
    return models


faltan = [e for es in ENTRADAS.values() for e in es if e not in FUNCS]
assert not faltan, f"Puntos de entrada inexistentes: {faltan}"

cu_tablas = {}
for cu, entries in ENTRADAS.items():
    ms = set()
    for e in entries:
        ms |= reach(e)
    cu_tablas[cu] = sorted(CLASS_TABLE[m] for m in ms)

modulos = {}
for code, (title, cus) in MODULOS.items():
    tablas = sorted({t for cu in cus for t in cu_tablas[cu]})
    modulos[code] = {"titulo": title, "casos": cus, "tablas": tablas}

# Casos ambiguos revisados leyendo el codigo (reciben un objeto de una entidad y consultan otra): su tema es el
# objeto que reciben. Los demas ambiguos se dejan con la regla general (ver destino()).
REVISADOS = {
    "services.cart_service.validate_cart_company": "Cart",        # valida que el carrito sea de una sola empresa
    "services.delivery_service._summary": "Order",                # resume los datos de envio del pedido
    "services.notification_delivery.deliver_notification": "Notification",  # entrega por push esa notificacion
    "services.notification_delivery.notify_low_stock": "Inventory",         # evalua el stock de ese inventario
    "services.replenishment_service._read_request": "ReplenishmentRequest",  # arma la lectura de esa solicitud
}


def destino(fn):
    """Entidad(es) sobre la que trabaja la funcion, con evidencia del codigo, en este orden:
    1) las que CREA (constructor Model(...)); 2) la del parametro tipado cuyos atributos MODIFICA (obj.campo = ...);
    3) la de su tipo de RETORNO; 4) si es un serializador (_serialize*/serialize*), la del objeto que RECIBE;
    5) la PRIMERA que consulta (query/select/get); 6) la del primer parametro tipado."""
    if fn.writes:
        return sorted(fn.writes)
    key = f"{fn.module}.{fn.name}"
    if key in REVISADOS:
        return [REVISADOS[key]]
    mod, ret, recibe = fn.evidence()
    if mod:
        return mod[:1]
    if ret:
        return ret[:1]
    if "serialize" in fn.name and recibe:
        return recibe[:1]
    if fn.queried:
        return [min(fn.queried)[2]]
    return recibe[:1]


# operaciones: cada funcion de servicio se asigna a la entidad sobre la que trabaja (ver destino()).
ops = {t: [] for t in MODELOS}
for key, fn in FUNCS.items():
    if not key.startswith("services.") or fn.name.startswith("_"):
        continue
    for m in destino(fn):
        names, types = fn.params()
        ops[CLASS_TABLE[m]].append({"nombre": fn.name, "params": names, "tipos": types, "firma": fn.signature(),
                                    "archivo": "backend/app/" + key.rsplit(".", 1)[0].replace(".", "/") + ".py"})
# respaldo: una entidad sin operaciones publicas toma las funciones privadas de servicio que la crean o consultan
for key, fn in FUNCS.items():
    if not key.startswith("services.") or not fn.name.startswith("_"):
        continue
    for m in destino(fn):
        t = CLASS_TABLE[m]
        if any(not o["nombre"].startswith("_") for o in ops[t]):
            continue
        names, types = fn.params()
        ops[t].append({"nombre": fn.name, "params": names, "tipos": types, "firma": fn.signature(),
                       "archivo": "backend/app/" + key.rsplit(".", 1)[0].replace(".", "/") + ".py"})
for t in ops:
    ops[t].sort(key=lambda o: o["firma"])

(HERE / "analisis.json").write_text(json.dumps({"cu_tablas": cu_tablas, "modulos": modulos, "operaciones": ops},
                                               ensure_ascii=False, indent=1), encoding="utf-8")
for code, m in modulos.items():
    print(code, m["titulo"], len(m["tablas"]), "tablas:", ", ".join(m["tablas"]))
print("tablas sin operaciones:", [t for t, o in ops.items() if not o])
print("operaciones por tabla (max):", max((len(o), t) for t, o in ops.items()))
