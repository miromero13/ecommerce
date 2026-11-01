"""Genera FashionStore_comunicacion.js: un diagrama de comunicacion (ICONIX / UML 2.5) por caso de uso.

Uso (desde la raiz del repo):  python docs/ea/comunicacion/generar_comunicacion.py [--only CU8]
  --only CUn: regenera solo ese caso de uso y lo une a comunicacion.json (los demas diagramas no cambian); el .js se
              vuelve a escribir desde el JSON unido.
Lo unico escrito a mano es QUE pantallas y acciones (metodos del componente) forman cada caso de uso, en el
orden de su ficha. Todo lo demas se traza del codigo con trazar.py: la llamada HTTP de cada metodo, la ruta FastAPI
que la atiende, sus parametros, las funciones de servicio que llama y la entidad a la que van (la misma asignacion
de operaciones del modelo de dominio). El script falla si un metodo no existe, en vez de inventarlo.
"""
import ast
from collections import Counter
import io
import contextlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
with contextlib.redirect_stdout(io.StringIO()):
    import trazar as T  # noqa: E402
AC = T.AC
NOMBRE = T.NOMBRE

ACTORES = {"SA": "Superadministrador", "AD": "Administrador del tenant", "EN": "Encargado de sucursal",
           "PR": "Proveedor", "CL": "Cliente", "CA": "Cajero", "RE": "Repartidor"}
# servicios del frontend que hacen trabajo propio (no solo HTTP): se dibujan como control
FRONT_CONTROLS = {"OfflineQueueService", "OfflineCatalogService", "PwaService", "OfflineSyncService", "OfflineCartService"}
LOCAL_CUS = {"CU22", "CU23", "CU25", "CU29", "CU30"}   # casos que trabajan con servicios / datos locales
LOCAL_ENTITY = {"PENDING_OPERATIONS_QUEUE": "OfflineOperation", "CACHED_CATALOG": "OfflineCatalogProduct",
                "PENDING_CART_ITEMS": "PendingCartItem"}

# (actor | None, componente, metodo, opciones)   opciones: {"solo": [modulos de servicio a mostrar]}
SPEC = {
    "CU1": ["SA", [("TenantManagementPageComponent", "loadTenants"), ("TenantManagementPageComponent", "loadPlans"),
                   ("TenantManagementPageComponent", "saveTenant"), ("TenantManagementPageComponent", "toggleTenantStatus"),
                   ("TenantManagementPageComponent", "enterPanel"), ("TenantManagementPageComponent", "registerAdmin")]],
    "CU2": ["SA", [("PlanManagementPageComponent", "loadPlans"), ("PlanManagementPageComponent", "save"),
                   ("PlanManagementPageComponent", "toggleActive")]],
    "CU3": ["AD", [("RbacRolesPageComponent", "loadData"), ("RbacRolesPageComponent", "saveRole"),
                   ("AdminUserPageComponent", "submitUser")]],
    "CU4": ["AD", [("PricingTableComponent", "loadPlans"), ("LandingPageComponent", "onPlanSelected")]],
    "CU5": ["CL", [("PhotoTryOnComponent", "onFile"), ("PhotoTryOnComponent", "generate")]],
    "CU6": ["CL", [("CatalogPageComponent", "selectBranch"), ("CatalogPageComponent", "recordProductView")]],
    "CU7": ["CL", [("ChatbotComponent", "openChat"), ("ChatbotComponent", "sendMessage"), ("ChatbotComponent", "confirmDelete")]],
    # ask() interpreta la consulta (POST /reports/query) y luego ejecuta run() (POST /reports/analytics)
    "CU8": ["AD", [("AdminReportsPageComponent", "ask", None, {"rutas": ["routes.report_routes.natural_report_route",
                                                                         "routes.report_routes.analytics_route"]}),
                   ("AdminReportsPageComponent", "exportAnalytics", None, {"rutas": ["routes.report_routes.analytics_export_route"]}),
                   ("AdminReportsPageComponent", "predictDemand"), ("AdminReportsPageComponent", "segmentCustomers")]],
    "CU9": ["AD", [("AdminExpertReplenishmentPageComponent", "loadRules"), ("AdminExpertReplenishmentPageComponent", "loadSuggestions"),
                   ("AdminExpertReplenishmentPageComponent", "evaluateReplenishment"),
                   ("AdminExpertReplenishmentPageComponent", "applySelectedTransfers"),
                   ("AdminExpertReplenishmentPageComponent", "saveRules"),
                   ("NotificationPageComponent", "applyReplenishment"), ("NotificationPageComponent", "discardReplenishment")]],
    "CU10": ["PR", [("ProviderRpaIngestPageComponent", "onPick"), ("ProviderRpaIngestPageComponent", "open"),
                    ("ProviderRpaIngestPageComponent", "saveCorrections"), ("ProviderRpaIngestPageComponent", "commit")]],
    "CU11": ["AD", [("AdminInventoryPageComponent", "refresh"), ("AdminInventoryPageComponent", "registerTransfer")]],
    "CU12": ["CL", [("NotificationPageComponent", "enablePush"), ("NotificationPageComponent", "open"),
                    ("NotificationPageComponent", "markAllRead"), ("AppShellComponent", "logout")]],
    "CU13": ["AD", [("AdminHomePageComponent", "refresh"), ("AdminHomePageComponent", "applyFilters")]],
    "CU14": ["AD", [("SalesHistoryPageComponent", "generateReport"), ("AdminInventoryPageComponent", "generateReport")]],
    "CU15": ["AD", [("PromotionsPageComponent", "load"), ("PromotionsPageComponent", "create"),
                    ("CartPageComponent", "applyCoupon", "CL"), ("CartPageComponent", "removeCoupon", "CL"),
                    ("CajaPageComponent", "submitSale", "CA", {"rutas": ["routes.sales_routes.create_sale_route"],
                                                              "solo": ["promotion_service"]})]],
    "CU16": ["CL", [("WishlistPageComponent", "load"), ("WishlistToggleButtonComponent", "toggle"),
                    ("WishlistPageComponent", "move"), ("WishlistPageComponent", "moveAll"), ("WishlistPageComponent", "remove")]],
    "CU17": ["CL", [("LoyaltyPageComponent", "load"), ("CajaPageComponent", "lookupPoints", "CA")]],
    "CU18": ["CL", [("GiftCardsPageComponent", "loadPurchases"), ("GiftCardsPageComponent", "purchase"),
                    ("GiftCardsPageComponent", "onGiftCardPaid")]],
    "CU19": ["CL", [("WalletPageComponent", "loadAll"), ("WalletPageComponent", "redeemCard"),
                    ("WalletPageComponent", "convertPoints"), ("CartPageComponent", "checkout")]],
    "CU20": ["CL", [("CartPageComponent", "quoteDelivery"), ("MyDeliveriesPageComponent", "load"),
                    ("DeliveryHomePageComponent", "load", "RE"), ("DeliveryHomePageComponent", "claim", "RE"),
                    ("DeliveryHomePageComponent", "confirm", "RE"), ("DriversPageComponent", "create", "SA")]],
    "CU21": ["CL", [("RmaHistoryPageComponent", "openWizard"), ("RmaHistoryPageComponent", "submitRequest"),
                    ("RmaReviewPageComponent", "loadRequests", "EN"), ("RmaReviewPageComponent", "submitReview", "EN"),
                    ("RmaReviewPageComponent", "triggerSettlement", "AD")]],
    "CU22": ["CL", [("PwaService", "loadDynamicManifest", "-"), ("PwaInstallPromptComponent", "install"),
                    ("PwaUpdatePromptComponent", "update")]],
    "CU23": ["CA", [("CajaPageComponent", "syncOfflineCatalog"), ("CajaPageComponent", "searchProducts")]],
    "CU24": ["EN", [("RmaReviewPageComponent", "submitReview")]],
    "CU25": ["CA", [("CajaPageComponent", "submitSale", None, {"local": True}),
                    ("ProductDetailPageComponent", "addToCart", "CL", {"local": True})]],
    "CU26": ["AD", [("TenantBrandingEditorComponent", "saveColor"), ("TenantBrandingEditorComponent", "uploadLogo"),
                    ("TenantBrandingEditorComponent", "removeLogo"), ("TenantBrandingEditorComponent", "resetColor")]],
    "CU27": ["AD", [("OnboardingPageComponent", "loadPlans", None, {"rutas": ["routes.subscription_routes.get_plans_route"]}), ("OnboardingPageComponent", "submitOrder")]],
    "CU28": ["AD", [("SubscriptionPageComponent", "loadSubscription"), ("SubscriptionPageComponent", "confirmChange")]],
    # el monitor no tiene metodo propio: se abre desde la plantilla de la caja y lee la senal del servicio
    # 1) el servicio carga la cola en su constructor (offline-queue.service.ts: constructor -> loadQueue);
    # 2) el cajero abre el monitor desde la caja (caja-page.component.html: showQueueModal.set(true));
    # 3) la plantilla del monitor lee la senal del servicio (offline-queue-modal.component.ts: offlineQueue.operations()).
    "CU29": ["CA", [("MANUAL", [("ctl:OfflineQueueService", "ctl:OfflineQueueService", "loadQueue()", "1"),
                                ("ctl:OfflineQueueService", "ent:OfflineOperation",
                                 "getAll<OfflineOperation>(STORES.PENDING_OPERATIONS_QUEUE)", "1.1"),
                                ("act:CA", "bnd:CajaPageComponent", "showQueueModal.set(true)", "2"),
                                ("act:CA", "bnd:OfflineQueueModalComponent", None, None),
                                ("bnd:OfflineQueueModalComponent", "ctl:OfflineQueueService", "operations()", "2.1")])]],
    "CU30": ["CA", [("OfflineSyncService", "triggerAutoSync", "-"), ("CajaPageComponent", "syncOfflineQueue"),
                    ("OfflineCartService", "syncPending", "-"),
                    # la pagina de conflictos lee los conflictos del servidor y resuelve uno (entregado / reembolso /
                    # billetera / cambio); resolve() vuelve a cargar la lista
                    ("OfflineConflictsPageComponent", "setTab", None, {"rutas": ["routes.offline_routes.list_offline_conflicts"]}),
                    ("OfflineConflictsPageComponent", "resolve", None, {"rutas": ["routes.offline_routes.resolve_offline_conflict",
                                                                                 "routes.offline_routes.list_offline_conflicts"]})]],
}


def cls_of(name):
    assert name in T.TS, f"clase inexistente: {name}"
    return T.TS[name]


def params_of(c, m):
    assert m in c.methods, f"metodo inexistente: {c.name}.{m}"
    return c.methods[m]["params"]


def events(c, m, seen=None, depth=0):
    """Eventos en orden de codigo: ('http', verb, path) | ('fctl', clase, metodo, [eventos]) | ('idb', store, texto)."""
    seen = seen or set()
    if (c.name, m) in seen or m not in c.methods or depth > 4:
        return []
    seen.add((c.name, m))
    body = c.methods[m]["body"]
    found = []
    for x in T.API_RX.finditer(body):
        path = re.sub(r"\$\{[^}]*\}", "{}", x.group(3).replace("${this.endpoint}", c.endpoint or ""))
        found.append((x.start(), ("http", x.group(1), path)))
    for x in re.finditer(r"this\.idb\.(\w+)(?:<[^>]*>)?\((\s*STORES\.(\w+))", body):
        # argumentos literales: desde el parentesis hasta su cierre
        i, depth = x.start(2), 1
        while i < len(body) and depth:
            depth += {"(": 1, ")": -1}.get(body[i], 0)
            i += 1
        args = " ".join(body[x.start(2):i - 1].split())
        found.append((x.start(), ("idb", x.group(3), f"{x.group(1)}({args})")))
    for x in re.finditer(r"this\.(\w+)\.(\w+)\s*\(", body):
        f, meth = x.group(1), x.group(2)
        tcls = c.fields.get(f)
        if tcls in T.TS and tcls not in ("ApiService",):
            sub = T.TS[tcls]
            if tcls in FRONT_CONTROLS:
                if meth not in sub.methods:      # senales / propiedades (p. ej. isOffline()) no son mensajes
                    continue
                found.append((x.start(), ("fctl", tcls, meth, events(sub, meth, seen, depth + 1))))
            else:
                found.extend((x.start() + i / 1000, e) for i, e in enumerate(events(sub, meth, seen, depth + 1)))
    for x in re.finditer(r"this\.(\w+)\s*\(", body):
        if x.group(1) in c.methods and x.group(1) != m:
            found.extend((x.start() + i / 1000, e) for i, e in enumerate(events(c, x.group(1), seen, depth + 1)))
    return [e for _, e in sorted(found, key=lambda t: t[0])]


def direct_orm(handler_key):
    fn = AC.FUNCS[handler_key]
    out = []
    for sub in ast.walk(fn.node):
        if isinstance(sub, ast.Call) and sub.args:
            name = sub.func.id if isinstance(sub.func, ast.Name) else getattr(sub.func, "attr", None)
            a0 = sub.args[0]
            base = a0.value if isinstance(a0, ast.Attribute) else a0
            if name in ("query", "select", "get") and isinstance(base, ast.Name) and base.id in AC.CLASS_TABLE:
                out.append((sub.lineno, NOMBRE[AC.CLASS_TABLE[base.id]], ast.unparse(sub)))
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id in AC.CLASS_TABLE:
            kws = ", ".join(k.arg for k in sub.keywords if k.arg)   # constructor: nombres reales de sus argumentos
            out.append((sub.lineno, NOMBRE[AC.CLASS_TABLE[sub.func.id]], f"{sub.func.id}({kws})"))
    seen, res = set(), []
    for _, ent, lab in sorted(out):
        if (ent, lab) not in seen:
            seen.add((ent, lab))
            res.append((ent, lab))
    return res


def entity_msgs(handler_key, solo=None):
    fn = AC.FUNCS[handler_key]
    msgs = []

    def add(k):
        if solo and k.split(".")[1] not in solo:
            return
        f = AC.FUNCS[k]
        for m in T.destino(f):
            msg = (NOMBRE[AC.CLASS_TABLE[m]], T.label(f))
            if msg not in msgs:
                msgs.append(msg)

    if solo:   # solo ciertos servicios: se siguen las llamadas en profundidad hasta encontrarlos
        def walk(k, d, seen):
            for k2 in T.call_order(AC.FUNCS[k]):
                if k2 in seen or d > 4:
                    continue
                seen.add(k2)
                add(k2)
                walk(k2, d + 1, seen)
        walk(handler_key, 0, set())
        return msgs
    for k in T.call_order(fn):
        add(k)
        for k2 in T.call_order(AC.FUNCS[k]):
            add(k2)
    if not msgs and not solo:
        msgs = direct_orm(handler_key)
    return msgs


def build(cu):
    default_actor, steps = SPEC[cu]
    cu_routes = {k for k in AC.ENTRADAS[cu] if k.startswith("routes.")}
    objs = {}          # id -> {name, kind}
    links, msgs = [], []

    def obj(oid, name, kind):
        objs.setdefault(oid, {"name": name, "kind": kind})
        return oid

    def link(a, b):
        if (a, b) not in links and (b, a) not in links:
            links.append((a, b))

    n = 0
    for step in steps:
        if step[0] == "MANUAL":                # mensajes escritos con expresiones reales del codigo
            for fa, fb, lab, num in step[1]:
                for oid in (fa, fb):
                    kind = {"act": "actor", "bnd": "boundary", "ctl": "control", "ent": "entity"}[oid[:3]]
                    obj(oid, ACTORES[oid[4:]] if kind == "actor" else oid[4:], kind)
                if fa != fb:
                    link(fa, fb)
                if lab:                        # sin etiqueta: solo el enlace (el actor ve el monitor)
                    msgs.append({"from": fa, "to": fb, "num": num, "label": lab})
                    n = max(n, int(num.split(".")[0]))
            continue
        comp, meth = step[0], step[1]
        actor = step[2] if len(step) > 2 and step[2] else default_actor
        opts = step[3] if len(step) > 3 else {}
        c = cls_of(comp)
        ps = params_of(c, meth)
        n += 1
        k = 0
        if actor == "-":                       # disparado por el sistema (evento del navegador), sin actor
            src = obj("ctl:" + comp, comp, "control")
            start = src
        else:
            a = obj("act:" + actor, ACTORES[actor], "actor")
            b = obj("bnd:" + comp, comp, "boundary")
            link(a, b)
            msgs.append({"from": a, "to": b, "num": str(n), "label": f"{meth}({', '.join(ps)})"})
            start = b
        allowed = set(opts.get("rutas", [])) or cu_routes
        if actor == "-":
            ev = [("self", None)] + events(c, meth)
        else:
            ev = events(c, meth)

        def emit(sender, evs):
            nonlocal k
            for e in evs:
                if e[0] == "http":
                    r = T.match_route(e[1], e[2])
                    if not r or r["key"] not in allowed:
                        continue
                    ctl = obj("ctl:" + r["module"], r["module"], "control")
                    link(sender, ctl)
                    k += 1
                    msgs.append({"from": sender, "to": ctl, "num": f"{n}.{k}", "label": f"{r['handler']}({', '.join(r['params'])})"})
                    for ent, lab in entity_msgs(r["key"], opts.get("solo")):
                        eo = obj("ent:" + ent, ent, "entity")
                        link(ctl, eo)
                        k += 1
                        msgs.append({"from": ctl, "to": eo, "num": f"{n}.{k}", "label": lab})
                elif e[0] == "fctl" and cu not in LOCAL_CUS:
                    continue
                elif e[0] == "idb" and cu not in LOCAL_CUS:
                    continue
                elif e[0] == "fctl":
                    fc = obj("ctl:" + e[1], e[1], "control")
                    sub_ps = params_of(T.TS[e[1]], e[2])
                    link(sender, fc)
                    k += 1
                    msgs.append({"from": sender, "to": fc, "num": f"{n}.{k}", "label": f"{e[2]}({', '.join(sub_ps)})"})
                    emit(fc, e[3])
                elif e[0] == "idb":
                    eo = obj("ent:" + LOCAL_ENTITY.get(e[1], e[1]), LOCAL_ENTITY.get(e[1], e[1]), "entity")
                    link(sender, eo)
                    k += 1
                    msgs.append({"from": sender, "to": eo, "num": f"{n}.{k}", "label": e[2]})

        if actor == "-":
            k = 0
            # disparado por el sistema (evento del navegador / inicio de la aplicacion): mensaje a si mismo
            msgs.append({"from": start, "to": start, "num": str(n), "label": f"{meth}({', '.join(ps)})"})
            emit(start, events(c, meth))
        else:
            emit(start, ev)
        if opts.get("local") is None and actor != "-" and not any(m["num"].startswith(f"{n}.") for m in msgs):
            pass
    # sin repetir el mismo mensaje dos veces seguidas en el mismo paso; se renumera
    clean = []
    for m in msgs:
        head = m["num"].split(".")[0]
        if "." in m["num"] and any(c["from"] == m["from"] and c["to"] == m["to"] and c["label"] == m["label"]
                                   and c["num"].split(".")[0] == head for c in clean):
            continue   # el mismo llamado dos veces en un paso (ramas alternativas del codigo): se dibuja una vez
        clean.append(m)
    step_k = {}
    for m in clean:
        head = m["num"].split(".")[0]
        if "." in m["num"]:
            step_k[head] = step_k.get(head, 0) + 1
            m["num"] = f"{head}.{step_k[head]}"
    return {"objs": objs, "links": links, "msgs": clean}


def layout(model):
    # separacion de columnas segun la etiqueta mas larga que debe caber entre ellas (6.2 px por caracter)
    def col_de(oid):
        o = model["objs"][oid]
        if o["kind"] == "control" and o["name"] in FRONT_CONTROLS:
            return "fctl"
        return o["kind"]
    ancho = {}
    for m in model["msgs"]:
        if m["from"] == m["to"]:
            continue
        par = tuple(sorted((col_de(m["from"]), col_de(m["to"])), key=["actor", "boundary", "fctl", "control", "entity"].index))
        ancho[par] = max(ancho.get(par, 0), (len(m["num"]) + 2 + len(m["label"])) * 6.2 + 10)
    hay_fctl = any(col_de(o) == "fctl" for o in model["objs"])
    cols = {"actor": 40}
    cols["boundary"] = cols["actor"] + 50 + max(260, ancho.get(("actor", "boundary"), 0) + 90)
    cols["fctl"] = cols["boundary"] + 90 + max(260, ancho.get(("boundary", "fctl"), 0) + 90)
    previo = "fctl" if hay_fctl else "boundary"
    cols["control"] = cols[previo] + 90 + max(260, max(ancho.get(("boundary", "control"), 0),
                                                         ancho.get(("fctl", "control"), 0)) + 90)
    cols["entity"] = cols["control"] + 90 + max(520, ancho.get(("control", "entity"), 0) + 160)
    # margen superior: las etiquetas de un enlace se apilan hacia arriba (16 px cada una en EA)
    count = {}
    for m in model["msgs"]:
        key = tuple(sorted((m["from"], m["to"])))
        count[key] = count.get(key, 0) + 1
    top = max(60, 40 + 17 * max(count.values() or [1]))
    rows = {}
    pos = {}
    order = list(model["objs"])
    local = set(LOCAL_ENTITY.values())
    for oid in order:
        o = model["objs"][oid]
        kind = o["kind"]
        if kind == "control" and o["name"] in FRONT_CONTROLS:
            col = "fctl"
        elif kind == "entity" and o["name"] in local:
            col = "fctl"            # datos locales (IndexedDB): debajo del servicio del frontend que los usa
        else:
            col = kind
        rows.setdefault(col, []).append(oid)
    for col, ids in rows.items():
        if col in ("entity", "fctl", "boundary"):
            continue
        for i, oid in enumerate(ids):
            pos[oid] = (cols[col], top + i * 190)
    # servicios del frontend: los que guardan datos locales van al final, cada uno con su entidad local justo debajo
    # (asi el enlace vertical servicio -> dato local no atraviesa otro objeto)
    fcol = rows.get("fctl", [])
    servicios = [o for o in fcol if model["objs"][o]["kind"] == "control"]
    propios = {sv: [m["to"] for m in model["msgs"] if m["from"] == sv and m["to"] in fcol
                    and model["objs"][m["to"]]["kind"] == "entity"] for sv in servicios}
    y = top
    for sv in sorted(servicios, key=lambda o: (bool(propios[o]), servicios.index(o))):
        pos[sv] = (cols["fctl"], y)
        y += 190
        for loc in dict.fromkeys(propios[sv]):
            n_msgs = sum(1 for m in model["msgs"] if m["from"] == sv and m["to"] == loc)
            y += max(40, 16 * n_msgs - 60)
            pos[loc] = (cols["fctl"], y)
            y += 230
    # interfaces: ordenadas por la altura media de los objetos a los que envian mensajes (sin cruces de lineas)
    bnds = rows.get("boundary", [])
    def media(b):
        ys = [pos[m["to"]][1] for m in model["msgs"] if m["from"] == b and m["to"] in pos]
        return sum(ys) / len(ys) if ys else 0
    for i, b in enumerate(sorted(bnds, key=lambda b: (media(b), bnds.index(b)))):
        pos[b] = (cols["boundary"], top + i * 190)
    # entidades: cada una a la altura promedio de los controles que le envian mensajes (menos cruces de lineas),
    # ordenadas por esa altura y separadas lo suficiente para que las etiquetas no se encimen
    ents = rows.get("entity", [])
    # altura objetivo = promedio de la altura de los controles que le envian mensajes, ponderado por cuantos envia;
    # a igual altura va primero la entidad que mas mensajes recibe (queda en linea recta con su control)
    callers = {e: [m["from"] for m in model["msgs"] if m["to"] == e and m["from"] in pos] for e in ents}
    bary = {e: (sum(pos[c][1] for c in callers[e]) / len(callers[e]) if callers[e] else 0) for e in ents}
    y = top
    principal = {e: (Counter(callers[e]).most_common(1)[0][0] if callers[e] else None) for e in ents}
    clave = lambda e: (pos[principal[e]][1] if principal[e] else 0, -len(callers[e]), ents.index(e))
    for e in sorted(ents, key=clave):
        y = max(y, bary[e])
        pos[e] = (cols["entity"], round(y))
        y += 200
    return pos


def etiquetas(model, pos):
    """Desplazamiento (sx, sy) de las etiquetas de cada enlace (comprobado en EA 15):
    - linea casi horizontal: con SX=0 la etiqueta se centra en el punto medio; SY>0 la sube, SY<0 la baja;
    - linea casi vertical: con SX=0 la etiqueta TERMINA en la linea; SX>0 la corre a la derecha.
    Las etiquetas de un mismo enlace se apilan cada 16 px. Para cada enlace se prueban los lados posibles y se elige
    el que menos choca con otras lineas y objetos del diagrama."""
    def centro(oid):
        x, y = pos[oid]
        return (x + 25, y + 45) if model["objs"][oid]["kind"] == "actor" else (x + 45, y + 35)

    def cruza(seg, rect):
        (x1, y1), (x2, y2) = seg
        rx1, ry1, rx2, ry2 = rect
        for i in range(21):                       # muestreo del segmento
            t = i / 20
            x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
            if rx1 <= x <= rx2 and ry1 <= y <= ry2:
                return True
        return False

    enlaces = {}
    for m in model["msgs"]:
        if m["from"] == m["to"]:
            m["sx"], m["sy"] = 0, 70              # automensaje: por encima del objeto
            continue
        enlaces.setdefault(tuple(sorted((m["from"], m["to"]))), []).append(m)
    segmentos = {k: (centro(k[0]), centro(k[1])) for k in enlaces}
    # zonas ocupadas por cada objeto: su figura y el nombre escrito debajo (mas ancho que la figura)
    cajas = []
    for o, (x, y) in pos.items():
        actor = model["objs"][o]["kind"] == "actor"
        fw, fh = (50, 90) if actor else (90, 70)
        nombre = model["objs"][o]["name"] if actor else ":" + model["objs"][o]["name"]
        nw = len(nombre) * 6.8 + 10
        cx = x + fw / 2
        cajas.append((x - 8, y - 8, x + fw + 8, y + fh + 4))
        cajas.append((cx - nw / 2, y + fh, cx + nw / 2, y + fh + 22))

    colocadas = []                            # rectangulos de etiquetas ya ubicadas

    def solapa(a, b):
        return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])

    # primero los enlaces con mas mensajes (sus pilas son las mas grandes)
    for key, ms in sorted(enlaces.items(), key=lambda kv: -len(kv[1])):
        (x1, y1), (x2, y2) = segmentos[key]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = abs(x2 - x1), abs(y2 - y1)
        anchos = [(len(m["num"]) + 2 + len(m["label"])) * 6.2 + 10 for m in ms]
        w, n = max(anchos), len(ms)
        lados = []                            # (funcion lv,ancho -> (sx, sy) relativa al punto medio, rectangulo)
        if dx >= dy:
            pendiente = dy / dx if dx else 0
            corr = round(pendiente * w / 2) if pendiente >= 0.08 else 0
            lados.append((lambda lv, a, c=corr: (0, 18 + 16 * lv + c),
                          (mx - w / 2, my - 18 - corr - 16 * n, mx + w / 2, my - 8 - corr)))
            lados.append((lambda lv, a, c=corr: (0, -(14 + 16 * lv + c)),
                          (mx - w / 2, my + 8 + corr, mx + w / 2, my + 18 + corr + 16 * n)))
        else:
            inclin = dx / dy if dy else 0
            marg = round(12 + inclin * 8 * (n + 1))
            lados.append((lambda lv, a, mg=marg, nn=n: (round(a + mg), 16 * lv - 8 * (nn - 1)),
                          (mx + marg, my - 8 * n - 8, mx + marg + w, my + 8 * n + 8)))
            lados.append((lambda lv, a, mg=marg, nn=n: (-mg, 16 * lv - 8 * (nn - 1)),
                          (mx - marg - w, my - 8 * n - 8, mx - marg, my + 8 * n + 8)))
        opciones = []
        for t in (0.5, 0.35, 0.65, 0.25, 0.75):   # posicion a lo largo de la linea (0.5 = punto medio)
            ddx, ddy = (x2 - x1) * (t - 0.5), (y2 - y1) * (t - 0.5)
            for fn, r in lados:
                rect = (r[0] + ddx, r[1] + ddy, r[2] + ddx, r[3] + ddy)
                opciones.append((fn, ddx, ddy, rect))

        def costo(o):
            rect = o[3]
            c = sum(3 for k2, seg in segmentos.items() if k2 != key and cruza(seg, rect))
            c += sum(4 for b in cajas if solapa(rect, b))
            c += sum(6 for r in colocadas if solapa(rect, r))
            return c
        fn, ddx, ddy, rect = min(opciones, key=costo)   # empate: la primera (punto medio, lado natural)
        colocadas.append(rect)
        for lv, (m, a) in enumerate(zip(ms, anchos)):
            sx, sy = fn(lv, a)
            m["sx"], m["sy"] = round(sx + ddx), round(sy - ddy)   # en EA, SY positivo es hacia arriba

def unir(cu, diagrama, previo):
    """--only: reemplaza el diagrama de cu en el modelo previo; los clasificadores se recalculan de todos los diagramas."""
    diagrams = [diagrama if d["cu"] == cu else d for d in previo["diagrams"]]
    if diagrama not in diagrams:
        diagrams.append(diagrama)
    cls = sorted({(o["kind"], o["name"]) for d in diagrams for o in d["objs"].values() if o["kind"] != "actor"})
    return diagrams, [{"kind": k, "name": n} for k, n in cls]


if __name__ == "__main__":
    # --only CU8: regenera solo ese caso de uso y lo une al comunicacion.json existente (los demas quedan intactos)
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    diagrams = []
    classifiers = {}
    for cu in [only] if only else [f"CU{i}" for i in range(1, 31)]:
        m = build(cu)
        pos = layout(m)
        for oid, o in m["objs"].items():
            if o["kind"] != "actor":
                classifiers[(o["kind"], o["name"])] = True
        sin = [x for x in m["msgs"] if x["from"] and x["from"].startswith(("act:",)) and
               not any(y["num"].startswith(x["num"] + ".") for y in m["msgs"])]
        etiquetas(m, pos)
        diagrams.append({"cu": cu, "objs": m["objs"], "pos": {k: list(v) for k, v in pos.items()},
                         "links": m["links"], "msgs": m["msgs"]})
        print(f"{cu}: {len(m['objs'])} objetos, {len(m['msgs'])} mensajes"
              + (f" | acciones solo de interfaz: {[x['label'] for x in sin]}" if sin else ""))
        for x in m["msgs"]:
            if x["to"].startswith("ent:") and x["from"] and x["from"].startswith("ent:"):
                raise SystemExit(f"{cu}: entidad llama a entidad")
    model = {"actors": ACTORES, "classifiers": [{"kind": k, "name": n} for k, n in sorted(classifiers)],
             "diagrams": diagrams}
    if only:
        previo = json.loads((HERE / "comunicacion.json").read_text(encoding="utf-8"))
        model["diagrams"], model["classifiers"] = unir(only, diagrams[0], previo)
    (HERE / "comunicacion.json").write_text(json.dumps(model, ensure_ascii=False, indent=1), encoding="utf-8")
    tpl = (HERE / "plantilla_comunicacion.js").read_text(encoding="utf-8") if (HERE / "plantilla_comunicacion.js").exists() else None
    if tpl:
        js = "var MODEL = " + json.dumps(model, ensure_ascii=True) + ";\n"
        (HERE / "FashionStore_comunicacion.js").write_text(tpl.replace("/*MODEL*/\n", js), encoding="utf-8")
        print("OK: FashionStore_comunicacion.js generado")
