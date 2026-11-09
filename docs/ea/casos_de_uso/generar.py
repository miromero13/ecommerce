"""Genera FashionStore_casos_de_uso.js: diagrama general de casos de uso (CU1-CU30) para Enterprise Architect.

Uso:  python -I docs/ea/casos_de_uso/generar.py      (escribe el .js y preview.png al lado de este archivo)

Los actores de cada caso de uso salen de los guardas de rol del codigo (require_roles / require_permission en
backend/app/routes, roleGuard en frontend/src/app/app.routes.ts). Las posiciones se buscan con recocido simulado
y se comprueba que ninguna linea toque un caso de uso o actor que no sea el suyo.
"""
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from subcasos import SUB  # noqa: E402

HERE = Path(__file__).resolve().parent

ACTORS = {
    "SA": "Superadministrador",
    "AD": "Administrador del tenant",
    "EN": "Encargado de sucursal",
    "PR": "Proveedor",
    "CL": "Cliente",
    "CA": "Cajero",
    "RE": "Repartidor",
}
LEFT, RIGHT = ["SA", "AD", "EN", "PR"], ["CL", "CA", "RE"]

# id, nombre, actores, descripcion (notas del elemento en EA)
CASES = [
    ("CU1", "Gestionar organizaciones (Tenants) de la plataforma", ["SA"],
     "Alta, edicion, suspension y reactivacion de empresas inquilinas; registro de su administrador."),
    ("CU2", "Gestionar planes de suscripción SaaS", ["SA"],
     "Crear y actualizar planes (tarifas mensual/anual, max_branches, max_garments y modulos habilitados)."),
    ("CU3", "Gestionar roles y permisos de usuario (RBAC)", ["SA", "AD"],
     "Crear roles a medida y asignarles permisos granulares por modulo y verbo."),
    ("CU4", "Consultar página comercial y planes de suscripción", ["AD"],
     "Portal publico con diferenciales del producto, comparativa de planes y prueba gratuita."),
    ("CU5", "Probar prendas en el vestidor virtual", ["CL"],
     "Proyeccion en vivo de prendas sobre la silueta del cliente con la camara."),
    ("CU6", "Recibir recomendaciones personalizadas de prendas", ["CL"],
     "Sugerencias por interacciones del cliente, con respaldo por popularidad (cold start)."),
    ("CU7", "Consultar al asistente virtual (Chatbot)", ["CL"],
     "Asistente conversacional con clasificacion de intenciones y stock real."),
    ("CU8", "Generar reportes inteligentes con IA", ["AD"],
     "Reportes por lenguaje natural (texto o voz), predictivos y de patrones con Machine Learning."),
    ("CU9", "Reabastecer stock automáticamente entre sucursales", ["AD"],
     "Sistema experto que evalua reglas de inventario y propone traspasos entre sucursales."),
    ("CU10", "Registrar ingreso de mercadería con RPA e IA", ["PR", "AD", "EN"],
     "Bot que lee remitos y facturas (OCR) y crea borradores de ingreso de mercaderia."),
    ("CU11", "Transferir inventario entre sucursales", ["AD", "EN"],
     "Traspaso atomico de prendas entre dos sucursales (transfer_out / transfer_in)."),
    ("CU12", "Recibir notificaciones push en el móvil", ["CL", "AD", "EN"],
     "Push (FCM movil y web) con bandeja: al cliente por pedidos y reservas; al administrador y encargado por stock "
     "bajo, reabastecimiento y pedidos de sucursal (notification_delivery.py)."),
    ("CU13", "Consultar dashboard de métricas comerciales", ["AD"],
     "Tablero con KPIs de facturacion, prendas vendidas, ranking e inventario por sucursal."),
    ("CU14", "Generar y exportar reportes operativos", ["AD", "EN"],
     "Reportes de ventas, existencias y movimientos con filtros y exportacion."),
    ("CU15", "Gestionar y aplicar cupones de descuento", ["AD", "EN", "CL", "CA"],
     "Emision de cupones (porcentaje o monto fijo, vigencia, tope de usos) y aplicacion en el checkout."),
    ("CU16", "Gestionar lista de deseos (Wishlist)", ["CL"],
     "Guardar prendas favoritas y moverlas al carrito."),
    ("CU17", "Acumular y canjear puntos de fidelización (Loyalty)", ["CL", "CA"],
     "Billetera de puntos por empresa: acumula al pagar y se canjea como descuento en web, movil o caja."),
    ("CU18", "Comprar y emitir tarjetas de regalo (Gift Cards)", ["CL"],
     "Compra de vouchers prepagados con dedicatoria y codigo QR unico."),
    ("CU19", "Gestionar billetera digital (Store Wallet)", ["CL"],
     "Saldo del cliente: canje de Gift Cards, conversion de puntos, pagos y reembolsos de devoluciones."),
    ("CU20", "Gestionar envío a domicilio con validación por PIN", ["CL", "RE", "SA"],
     "Cotizacion de flete, hoja de ruta del repartidor y confirmacion de entrega con PIN; alta de repartidores."),
    ("CU21", "Solicitar y procesar cambios y devoluciones (RMA)", ["CL", "EN", "AD"],
     "Solicitud de cambio o devolucion dentro de 30 dias y dictamen por prenda."),
    ("CU22", "Instalar la aplicación web progresiva (PWA)", ["CL", "CA", "EN", "AD"],
     "Instalacion de la aplicacion web en el dispositivo y aviso de nuevas versiones."),
    ("CU23", "Consultar catálogo sin conexión (Offline)", ["CA"],
     "Catalogo guardado localmente (IndexedDB) para buscar prendas en caja sin internet."),
    ("CU24", "Reintegrar inventario por devoluciones y registrar mermas", ["EN", "AD"],
     "Inspeccion de prendas devueltas: reingreso al stock o envio a merma / cuarentena."),
    ("CU25", "Registrar ventas y reservas sin conexión (POS Offline)", ["CA"],
     "Ventas de contado y reservas en contingencia con comprobante provisional."),
    ("CU26", "Personalizar la marca de la tienda (Branding)", ["AD", "SA"],
     "Logo, colores e identidad visual de la empresa en web y movil."),
    ("CU27", "Contratar suscripción B2B (Onboarding)", ["AD"],
     "Seleccion de plan, ciclo de facturacion, datos de la empresa y pago simulado."),
    ("CU28", "Monitorear consumo y cambiar plan de suscripción", ["AD"],
     "Consumo de sucursales y prendas frente al plan, historial y upgrade / downgrade."),
    ("CU29", "Gestionar cola de operaciones pendientes (Offline Queue)", ["CA", "CL"],
     "Consulta y auditoria de las operaciones retenidas localmente sin conexion."),
    ("CU30", "Sincronizar operaciones offline y resolver conflictos de inventario", ["CA", "AD", "EN"],
     "Envio en lote de la cola, deteccion de colisiones de stock y compensacion al cliente."),
]

# relaciones respaldadas por el codigo: (desde, hacia, tipo)
RELATIONS = [
    ("CU1", "CU2", "include"),   # crear tenant asigna un plan de suscripcion
    ("CU4", "CU2", "include"),   # la pagina comercial lista los planes publicos
    ("CU12", "CU11", "extend"),  # transfer_route -> notify_low_stock si el stock queda bajo el minimo
]

# ---------------------------------------------------------------- geometria
UC_W, UC_H = 190, 76          # elipse de caso de uso
ACT_W, ACT_H = 50, 90         # figura de actor (+ etiqueta debajo)
BX0, BY0 = 240, 40            # limite del sistema
COLS, ROWS = 4, 9
COL_X = [BX0 + 70 + i * 350 for i in range(COLS)]
ROW_H = 160
BX1 = COL_X[-1] + UC_W + 70
BY1 = BY0 + 40 + ROWS * ROW_H + ROW_H // 2
LEFT_X, RIGHT_X = BX0 - 170, BX1 + 120
MARGIN = 10
BEND_PENALTY = 120
# puntos de quiebre: huecos entre columnas y pasillos entre filas, dentro del limite del sistema
GAP_X = [BX0 + 35] + [x + UC_W + 80 for x in COL_X[:-1]] + [BX1 - 35]
GAP_Y = [BY0 + 40 + r * ROW_H // 2 - 30 for r in range(2 * ROWS + 2)]
GAPS = [(x, y) for x in GAP_X for y in GAP_Y]

ids = [c[0] for c in CASES]


def _allowed(actors):
    """Columnas permitidas: personal a la izquierda, cliente/cajero/repartidor a la derecha, mixtos al centro."""
    left = any(a in LEFT for a in actors)
    right = any(a in RIGHT for a in actors)
    return {1, 2} if left and right else ({0, 1} if left else {2, 3})


ALLOWED = {c[0]: _allowed(c[2]) for c in CASES}
lines = [(a, c[0]) for c in CASES for a in c[2]] + [(f, t) for f, t, _ in RELATIONS]


def center(pos, key):
    x, y = pos[key]
    return (x + ACT_W / 2, y + ACT_H / 2) if key in ACTORS else (x + UC_W / 2, y + UC_H / 2)


def hits(p, q, pos, key):
    """True si el segmento p-q pasa por la figura `key` (inflada MARGIN px)."""
    cx, cy = center(pos, key)
    if key in ACTORS:
        hw, hh = ACT_W / 2 + 40 + MARGIN, ACT_H / 2 + 20 + MARGIN  # incluye la etiqueta del nombre
    else:
        hw, hh = UC_W / 2 + MARGIN, UC_H / 2 + MARGIN
    if max(p[0], q[0]) < cx - hw or min(p[0], q[0]) > cx + hw or max(p[1], q[1]) < cy - hh or min(p[1], q[1]) > cy + hh:
        return False
    # escalar a figura unitaria centrada en el origen
    ax, ay = (p[0] - cx) / hw, (p[1] - cy) / hh
    bx, by = (q[0] - cx) / hw, (q[1] - cy) / hh
    dx, dy = bx - ax, by - ay
    if key in ACTORS:  # segmento vs cuadrado [-1,1]^2 (Liang-Barsky)
        t0, t1 = 0.0, 1.0
        for pp, qq in ((-dx, ax + 1), (dx, 1 - ax), (-dy, ay + 1), (dy, 1 - ay)):
            if pp == 0:
                if qq < 0:
                    return False
            else:
                r = qq / pp
                if pp < 0:
                    t0 = max(t0, r)
                else:
                    t1 = min(t1, r)
        return t0 < t1
    ll = dx * dx + dy * dy  # distancia del origen al segmento < 1
    t = 0.0 if ll == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / ll))
    x, y = ax + dx * t, ay + dy * t
    return x * x + y * y < 1


def ccw(a, b, c):
    return (c[1] - a[1]) * (b[0] - a[0]) - (b[1] - a[1]) * (c[0] - a[0])


def crosses(a, b, c, d):
    if len({a, b, c, d}) < 4:
        return False
    return ccw(a, c, d) * ccw(b, c, d) < 0 and ccw(a, b, c) * ccw(a, b, d) < 0


def layout(slots, actor_rows):
    pos = {}
    for cid, (col, row) in slots.items():
        pos[cid] = (COL_X[col], BY0 + 40 + row * ROW_H + (col % 2) * ROW_H // 2)
    for k, r in actor_rows.items():
        pos[k] = (LEFT_X if k in LEFT else RIGHT_X, BY0 + 20 + r * (ROW_H / 2))
    return pos


def touching(pos):
    bad = []
    for a, b in lines:
        p, q = center(pos, a), center(pos, b)
        for k in list(ids) + list(ACTORS):
            if k not in (a, b) and hits(p, q, pos, k):
                bad.append((a, b, k))
    return bad


def cost(pos):
    segs = [(center(pos, a), center(pos, b)) for a, b in lines]
    c = 1000 * len(touching(pos))
    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            if crosses(*segs[i], *segs[j]):
                c += 12
    c += sum(math.dist(p, q) for p, q in segs) * 0.02
    return c


def solve(seed=7, iters=12000):
    rnd = random.Random(seed)
    free = [(c, r) for c in range(COLS) for r in range(ROWS)]
    rnd.shuffle(free)
    slots = {}
    for cid in sorted(ids, key=lambda c: len(ALLOWED[c])):
        k = next(i for i, f in enumerate(free) if f[0] in ALLOWED[cid])
        slots[cid] = free.pop(k)
    spare = free
    arows = {k: i * 3 for i, k in enumerate(LEFT)}
    arows.update({k: i * 3 + 2 for i, k in enumerate(RIGHT)})
    amax = ROWS * 2 - 2
    cur = cost(layout(slots, arows))
    best = (cur, dict(slots), dict(arows))
    for it in range(iters):
        temp = 200 * (1 - it / iters) + 0.5
        s2, a2, sp2 = dict(slots), dict(arows), list(spare)
        m = rnd.random()
        if m < 0.45:
            x, y = rnd.sample(ids, 2)
            if s2[y][0] not in ALLOWED[x] or s2[x][0] not in ALLOWED[y]:
                continue
            s2[x], s2[y] = s2[y], s2[x]
        elif m < 0.75 and sp2:
            x = rnd.choice(ids)
            j = rnd.randrange(len(sp2))
            if sp2[j][0] not in ALLOWED[x]:
                continue
            s2[x], sp2[j] = sp2[j], s2[x]
        else:
            k = rnd.choice(list(ACTORS))
            side = [q for q in ACTORS if (q in LEFT) == (k in LEFT) and q != k]
            v = max(0, min(amax, a2[k] + rnd.choice([-2, -1, 1, 2])))
            if all(abs(v - a2[q]) >= 3 for q in side):
                a2[k] = v
        c = cost(layout(s2, a2))
        if c < cur or rnd.random() < math.exp((cur - c) / temp):
            slots, arows, spare, cur = s2, a2, sp2, c
            if c < best[0]:
                best = (c, dict(s2), dict(a2))
    return best


def clear(pts, pos, a, b):
    for p, q in zip(pts, pts[1:]):
        for k in list(ids) + list(ACTORS):
            if k not in (a, b) and hits(p, q, pos, k):
                return False
    return True


def overlap(pts, drawn):
    """Penalizacion si algun tramo corre pegado y paralelo a una linea ya trazada."""
    pen = 0
    for p, q in zip(pts, pts[1:]):
        L = math.dist(p, q) or 1
        ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
        for r, t in drawn:
            d1 = abs((r[0] - p[0]) * uy - (r[1] - p[1]) * ux)
            d2 = abs((t[0] - p[0]) * uy - (t[1] - p[1]) * ux)
            if d1 < 8 and d2 < 8:
                s0 = (r[0] - p[0]) * ux + (r[1] - p[1]) * uy
                s1 = (t[0] - p[0]) * ux + (t[1] - p[1]) * uy
                if min(max(s0, s1), L) - max(min(s0, s1), 0) > 15:
                    pen += 2000
    return pen


DRAWN = []


def route(pos, a, b):
    """Camino sin tocar otras figuras: recto, con 1 quiebre o con 2; el mas corto. None si no hay."""
    p, q = center(pos, a), center(pos, b)
    if clear([p, q], pos, a, b):
        return []
    plen = lambda pts: sum(math.dist(u, v) for u, v in zip(pts, pts[1:])) + overlap(pts, DRAWN)
    best = None
    ok1 = [g for g in GAPS if clear([p, g], pos, a, b)]
    for g in ok1:
        if clear([g, q], pos, a, b):
            L = plen([p, g, q]) + BEND_PENALTY
            if best is None or L < best[0]:
                best = (L, [g])
    if best:
        return best[1]
    ok2 = [g for g in GAPS if clear([g, q], pos, a, b)]
    for g1 in ok1:
        for g2 in ok2:
            if g1 != g2 and clear([g1, g2], pos, a, b):
                L = plen([p, g1, g2, q]) + 2 * BEND_PENALTY
                if best is None or L < best[0]:
                    best = (L, [g1, g2])
    return best[1] if best else None


def preview(pos, path, routes):
    from PIL import Image, ImageDraw
    W, H = int(RIGHT_X + 200), int(BY1 + 60)
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    d.rectangle([BX0, BY0, BX1, BY1], outline="black")
    for a, b in lines:
        d.line([center(pos, a)] + (routes.get((a, b)) or []) + [center(pos, b)], fill="gray", width=1)
    for cid, name, *_ in CASES:
        x, y = pos[cid]
        d.ellipse([x, y, x + UC_W, y + UC_H], fill="#dbe8fb", outline="#3a5f9a")
        d.text((x + 20, y + 30), cid + " " + name[:26], fill="black")
    for k, nm in ACTORS.items():
        x, y = pos[k]
        d.rectangle([x, y, x + ACT_W, y + ACT_H], outline="black")
        d.text((x - 30, y + ACT_H + 2), nm, fill="black")
    im.save(path)


# ---------------------------------------------------------------- un diagrama por caso de uso
def skey(name):
    return "S:" + name


def sub_connectors():
    """(desde, hacia, tipo) de todos los subcasos, con la direccion de UML 2.5."""
    out = []
    for cid, items in SUB.items():
        for kind, name, _src, parent in items:
            par = cid if parent is None else skey(parent)
            out.append((skey(name), par, kind) if kind == "extend" else (par, skey(name), kind))
    return out


ALL_LINKS = [(a, c[0]) for c in CASES for a in c[2]] + [(f, t) for f, t, _ in RELATIONS] + [(a, b) for a, b, _ in sub_connectors()]


def cu_layout(cid):
    """Actores a la izquierda, caso base al centro, extensiones/inclusiones a la derecha (2.o nivel mas a la derecha).
    Agranda las distancias hasta que ninguna linea toque otra figura del diagrama."""
    case = next(c for c in CASES if c[0] == cid)
    items = SUB.get(cid, [])
    level1 = [skey(n) for k, n, s_, p in items if p is None]
    level1 += [t if f == cid else f for f, t, _ in RELATIONS if cid in (f, t)]
    level2 = {skey(p): [] for k, n, s_, p in items if p is not None}
    for k, n, s_, p in items:
        if p is not None:
            level2[skey(p)].append(skey(n))
    for gap in range(110, 400, 10):
        for dx in range(380, 900, 40):
            pos = {}
            rows = max(len(level1), 1)
            H = rows * gap
            for i, k in enumerate(level1):
                pos[k] = (40 + 170 + dx, 40 + i * gap)
            for par, kids in level2.items():
                for j, k in enumerate(kids):
                    pos[k] = (pos[par][0] + UC_W + 160, pos[par][1] + j * gap)
            pos[cid] = (210, 40 + (H - gap) / 2)
            na = len(case[2])
            for i, a in enumerate(case[2]):
                pos[a] = (40, 40 + (H - gap) / 2 + (i - (na - 1) / 2) * 170)
            top = min(v[1] for v in pos.values())
            if top < 40:
                pos = {k: (v[0], v[1] + 40 - top) for k, v in pos.items()}
            links = [(a, b) for a, b in ALL_LINKS if a in pos and b in pos]
            if not any(hits(center(pos, a), center(pos, b), pos, k)
                       for a, b in links for k in pos if k not in (a, b)):
                return pos
    raise SystemExit("No se encontro ubicacion libre para " + cid)


def js_layout(pos, routes):
    js = lambda v: json.dumps(v, ensure_ascii=True)
    model = {
        "actors": ACTORS,
        "cases": [{"id": c, "name": n, "actors": a, "notes": d} for c, n, a, d in CASES],
        "relations": [{"from": f, "to": t, "kind": k} for f, t, k in RELATIONS],
        "layout": {k: [round(v[0]), round(v[1])] for k, v in pos.items()},
        "boundary": [BX0, BY0, BX1 - BX0, BY1 - BY0],
        "uc": [UC_W, UC_H], "act": [ACT_W, ACT_H],
        "routes": [{"from": a, "to": b, "path": [[round(x), round(y)] for x, y in r]} for (a, b), r in routes.items() if r],
        "subs": [{"key": skey(n), "name": n, "notes": "Fuente en el codigo: " + src, "cu": cid}
                 for cid, items in SUB.items() for _k, n, src, _p in items],
        "subLinks": [{"from": a, "to": b, "kind": k} for a, b, k in sub_connectors()],
        "diagrams": [{"cu": c[0], "layout": {k: [round(v[0]), round(v[1])] for k, v in cu_layout(c[0]).items()},
                      # asociaciones de actores con OTROS casos visibles en este diagrama: se ocultan
                      "hide": [x + "|" + y for x, y in ALL_LINKS
                               if x in ACTORS and x in c[2] and y != c[0] and y in cu_layout(c[0])]}
                     for c in CASES],
    }
    return "var MODEL = " + js(model) + ";\n"


if __name__ == "__main__":
    best = None
    for seed in range(1, 5):
        r = solve(seed)
        print("seed", seed, "costo", round(r[0]), "toques en recto", len(touching(layout(r[1], r[2]))))
        if best is None or r[0] < best[0]:
            best = r
    pos = layout(best[1], best[2])
    routes, fail = {}, []
    for a, b in lines:  # primero las rectas, para que los quiebres las esquiven
        if not route(pos, a, b) and route(pos, a, b) is not None:
            DRAWN.append((center(pos, a), center(pos, b)))
    for a, b in lines:
        r = route(pos, a, b)
        if r is None:
            fail.append((a, b))
        elif r:
            pts = [center(pos, a)] + r + [center(pos, b)]
            DRAWN.extend(zip(pts, pts[1:]))
        routes[(a, b)] = r or []
    for a, b in fail:
        print("AVISO: sin camino libre para", a, "-", b)
    preview(pos, HERE / "preview.png", routes)
    tpl = (HERE / "plantilla.js").read_text(encoding="utf-8")
    (HERE / "FashionStore_casos_de_uso.js").write_text(tpl.replace("/*MODEL*/\n", js_layout(pos, routes)), encoding="utf-8")
    print("OK: generado;", sum(1 for r in routes.values() if r), "lineas con quiebre;", len(fail), "sin camino libre")
