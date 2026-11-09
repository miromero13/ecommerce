"""Genera FashionStore_modelo_dominio.js: un diagrama de modelo de dominio por modulo (M1-M6) para EA 15.

Uso (desde la raiz del repo):
  1) cd backend && PYTHONPATH=. .venv/Scripts/python.exe ../docs/ea/modelo_dominio/extraer_modelos.py
  2) python docs/ea/modelo_dominio/analizar_codigo.py
  3) python docs/ea/modelo_dominio/generar_dominio.py      (escribe el .js y vista_Mx.png)

Todo sale de modelos.json (columnas, FK, cascadas de los modelos SQLAlchemy) y analisis.json (tablas que alcanza
cada caso de uso y operaciones reales de los servicios). Aqui solo se traducen los nombres al espanol.
"""
import json
import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODELOS = json.loads((HERE / "modelos.json").read_text(encoding="utf-8"))
ANALISIS = json.loads((HERE / "analisis.json").read_text(encoding="utf-8"))

# ---------------------------------------------------------------- nombres en espanol (los del documento)
NOMBRE = {
    "branches": "Sucursal", "carts": "Carrito", "cart_items": "DetalleCarrito", "cash_movements": "MovimientoCaja",
    "cash_sessions": "SesionCaja", "categories": "Categoria", "collaborative_embeddings": "RepresentacionColaborativa",
    "collections": "Coleccion", "colors": "ColorPrenda", "conversations": "Conversacion",
    "conversation_messages": "MensajeConversacion", "device_tokens": "TokenDispositivo",
    "expert_replenishment_rules": "ReglaReposicionExperta", "expert_transfer_suggestions": "SugerenciaTrasladoExperto",
    "inventory": "Inventario", "inventory_movements": "MovimientoInventario", "loyalty_accounts": "CuentaFidelizacion",
    "loyalty_ledger": "MovimientoPuntos", "notifications": "Notificacion", "orders": "Pedido", "order_items": "DetallePedido",
    "payment_attempts": "IntentoPago", "payment_receipts": "ComprobantePago", "payment_transactions": "TransaccionPago",
    "permissions": "Permiso", "products": "Producto", "product_variants": "VarianteProducto",
    "promotion_codes": "CodigoPromocional", "promotion_code_usages": "UsoCodigoPromocional", "providers": "Proveedor",
    "provider_variant_availability": "DisponibilidadVarianteProveedor", "qr_payments": "PagoQR",
    "replenishment_requests": "SolicitudReposicion", "replenishment_request_items": "DetalleSolicitudReposicion",
    "reservations": "Reserva", "reservation_items": "DetalleReserva", "roles": "Rol",
    "rpa_ingest_jobs": "TrabajoImportacionRPA", "sales": "Venta", "sale_items": "DetalleVenta", "seasons": "Temporada",
    "settlements": "Liquidacion", "sizes": "Talla", "stripe_events": "EventoStripe", "saas_plans": "PlanSuscripcion",
    "tenants": "Empresa", "tenant_subscriptions": "SuscripcionEmpresa", "users": "Usuario",
    "user_body_profiles": "PerfilCorporal", "user_product_interactions": "InteraccionProducto",
    "wishlist_items": "ProductoFavorito", "role_permissions": "PermisosRoles", "user_roles": "AsignacionRolesUsuarios",
    # tablas nuevas (segundo parcial), con el mismo patron de nombres
    "gift_cards": "TarjetaRegalo", "rma_requests": "SolicitudDevolucion", "rma_request_items": "DetalleSolicitudDevolucion",
    "user_wallets": "BilleteraUsuario", "wallet_transactions": "MovimientoBilletera",
}
_prev = json.loads((HERE / "traducciones_columnas.json").read_text(encoding="utf-8"))
COLUMNA = dict(_prev)
COLUMNA.update({
    "product_id": "id_producto", "size_id": "id_talla", "color_id": "id_color",
    "action": "accion", "balance": "saldo", "balance_after": "saldo_posterior", "buyer_id": "id_comprador",
    "concept": "concepto", "custom_message": "mensaje_personalizado", "customer_notes": "notas_cliente",
    "dispatch_movement_id": "id_movimiento_despacho", "inspected_at": "fecha_inspeccion",
    "inspected_by": "inspeccionado_por", "inspection_notes": "notas_inspeccion", "item_condition": "condicion_prenda",
    "order_item_id": "id_detalle_pedido", "preferred_resolution": "resolucion_preferida", "qr_code_url": "url_codigo_qr",
    "quarantine_record": "registro_cuarentena", "recipient_email": "correo_destinatario",
    "recipient_name": "nombre_destinatario", "redeemed_at": "fecha_canje", "redeemed_by_id": "id_canjeado_por",
    "refund_amount": "importe_reembolso", "replacement_variant_id": "id_variante_reemplazo",
    "requested_variant_id": "id_variante_solicitada", "restock_movement_id": "id_movimiento_reingreso",
    "rma_id": "id_solicitud_devolucion", "rma_number": "numero_solicitud", "settlement_status": "estado_liquidacion",
    "wallet_id": "id_billetera", "wallet_settlement_date": "fecha_liquidacion_billetera",
})
faltan = sorted({c["column"] for t in MODELOS.values() for c in t["columns"]} - set(COLUMNA))
assert not faltan, f"columnas sin traduccion: {faltan}"
assert set(MODELOS) <= set(NOMBRE), set(MODELOS) - set(NOMBRE)

JUNCTION = {t for t, v in MODELOS.items() if v["columns"] and all(c["fk"] and c["pk"] for c in v["columns"])}


def rol(col):
    """Nombre de la asociacion: el rol de la FK en espanol (id_empresa -> empresa)."""
    n = COLUMNA[col]
    return n[3:] if n.startswith("id_") else n


def duenio(t):
    """Unico todo compuesto de la tabla t (UML 2.5: una parte tiene a lo sumo un todo), o None.
    Candidatos: FK obligatoria, sin RESTRICT, y borrada con el padre (ON DELETE CASCADE o delete-orphan).
    1) si un padre declara cascade='all, delete-orphan' sobre t, ese es el todo (propiedad explicita del ORM);
    2) si no, y hay una sola FK candidata, esa; 3) si hay varias sin dueno declarado, ninguna (asociaciones)."""
    cand = [c for c in MODELOS[t]["columns"] if c["fk"] and not c["nullable"] and c["ondelete"] != "RESTRICT"
            and (c["ondelete"] == "CASCADE" or c["fk"] in MODELOS[t]["cascade_from"])]
    orphan = [c for c in cand if c["fk"] in MODELOS[t]["cascade_from"]]
    if len(orphan) == 1:
        return orphan[0]["column"]
    if not orphan and len(cand) == 1:
        return cand[0]["column"]
    return None


def relaciones(tablas):
    """FK entre tablas del diagrama: multiplicidades, composicion y M:N de tablas puente."""
    rels = []
    for t in sorted(tablas):
        own = duenio(t)
        for c in MODELOS[t]["columns"]:
            p = c["fk"]
            if not p or p not in tablas or t in JUNCTION:
                continue
            compuesta = c["column"] == own
            rels.append({"hijo": t, "padre": p, "nombre": rol(c["column"]), "columna": c["column"],
                         "mult_hijo": "0..1" if c["unique"] else "0..*", "mult_padre": "0..1" if c["nullable"] else "1",
                         "composicion": compuesta})
    for j in sorted(JUNCTION):
        a, b = [c["fk"] for c in MODELOS[j]["columns"]][:2]
        if a in tablas and b in tablas:
            rels.append({"hijo": a, "padre": b, "nombre": NOMBRE[j], "columna": j, "mult_hijo": "0..*",
                         "mult_padre": "0..*", "composicion": False})
    return rels


def atributos(t):
    return [{"nombre": COLUMNA[c["column"]], "tipo": c["type"], "columna": c["column"]} for c in MODELOS[t]["columns"]]


def operaciones(t):
    return ANALISIS["operaciones"][t]


# ---------------------------------------------------------------- tamanos (mismo calculo validado en EA 15)
def tamano(t):
    lines = [NOMBRE[t]] + [f"- {a['nombre']}: {a['tipo']}" for a in atributos(t)] + \
            [f"+ {o['firma']}" for o in operaciones(t)]
    w = max(170, max(len(s) for s in lines) * 6.4 + 40)
    h = 60 + (len(atributos(t)) + len(operaciones(t))) * 14.5 + 16
    return round(w), round(h)


# ---------------------------------------------------------------- ubicacion en grilla
def ubicar(tablas, rels, seed=3, iters=40000):
    n = len(tablas)
    C = max(2, math.ceil(math.sqrt(n * 1.3)))
    R = math.ceil(n / C)
    rnd = random.Random(seed)
    cells = [(r, c) for r in range(R) for c in range(C)]
    order = sorted(tablas, key=lambda t: -sum(1 for x in rels if t in (x["hijo"], x["padre"])))
    pos = {t: cells[i] for i, t in enumerate(order)}
    free = cells[n:]

    def cost(p):
        s = 0
        for x in rels:
            (r1, c1), (r2, c2) = p[x["hijo"]], p[x["padre"]]
            s += abs(r1 - r2) * 1.3 + abs(c1 - c2)
        return s

    cur = cost(pos)
    best = (cur, dict(pos))
    for it in range(iters):
        temp = 3 * (1 - it / iters) + 0.01
        p2, f2 = dict(pos), list(free)
        a = rnd.choice(tablas)
        if f2 and rnd.random() < 0.3:
            j = rnd.randrange(len(f2))
            p2[a], f2[j] = f2[j], p2[a]
        else:
            b = rnd.choice(tablas)
            p2[a], p2[b] = p2[b], p2[a]
        c2 = cost(p2)
        if c2 <= cur or rnd.random() < math.exp((cur - c2) / temp):
            pos, free, cur = p2, f2, c2
            if cur < best[0]:
                best = (cur, dict(pos))
    return best[1], R, C


# ---------------------------------------------------------------- ruteo ortogonal por pasillos con carriles
LANE, H_BASE, V_BASE = 12, 46, 34


def rutear(tablas, rels, cell, R, C):
    size = {t: tamano(t) for t in tablas}
    colw = [max([size[t][0] for t in tablas if cell[t][1] == c] or [170]) for c in range(C)]
    rowh = [max([size[t][1] for t in tablas if cell[t][0] == r] or [80]) for r in range(R)]

    # 1) ruta logica de cada relacion: lados de salida/entrada, pasillos horizontales y vertical
    plans = []
    for i, x in enumerate(rels):
        a, b = x["hijo"], x["padre"]
        (ra, ca), (rb, cb) = cell[a], cell[b]
        if rb < ra:
            sa, ha, sb, hb = "top", ra, "bottom", rb + 1
        elif rb > ra:
            sa, ha, sb, hb = "bottom", ra + 1, "top", rb
        else:
            sa, ha, sb, hb = "top", ra, "top", rb
        v = None if ha == hb else (ca + 1 if cb > ca else ca if cb < ca else ca + 1)
        plans.append({"i": i, "a": a, "b": b, "sa": sa, "ha": ha, "sb": sb, "hb": hb, "v": v})

    # 2) puntos de conexion repartidos en cada lado de cada clase, ordenados hacia su destino
    sides = {}
    for p in plans:
        sides.setdefault((p["a"], p["sa"]), []).append((p, "a"))
        sides.setdefault((p["b"], p["sb"]), []).append((p, "b"))

    def layout(hlanes, vlanes):
        X, x = [], 0
        vx0 = []
        for c in range(C):
            vx0.append(x)
            x += V_BASE + LANE * vlanes[c]
            X.append(x)
            x += colw[c]
        vx0.append(x)
        Y, y = [], 0
        hy0 = []
        for r in range(R):
            hy0.append(y)
            y += H_BASE + LANE * hlanes[r]
            Y.append(y)
            y += rowh[r]
        hy0.append(y)
        width = x + V_BASE + LANE * vlanes[C]
        height = y + H_BASE + LANE * hlanes[R]
        return X, Y, vx0, hy0, width, height

    def attach(X):
        pts = {}
        for (t, side), lst in sides.items():
            r, c = cell[t]
            w = size[t][0]

            def far(item):
                p, end = item
                other = p["b"] if end == "a" else p["a"]
                return cell[other][1] * 10000 + (cell[other][0] if side == "bottom" else -cell[other][0])
            lst = sorted(lst, key=far)
            for k, (p, end) in enumerate(lst):
                pts[(p["i"], end)] = X[c] + round((k + 1) * w / (len(lst) + 1))
        return pts

    hlanes, vlanes = [0] * (R + 1), [0] * (C + 1)
    for _ in range(3):  # 3 pasadas: los carriles cambian los anchos y estos los intervalos
        X, Y, vx0, hy0, W, Hh = layout(hlanes, vlanes)
        pts = attach(X)
        hseg, vseg = {}, {}
        for p in plans:
            xa, xb = pts[(p["i"], "a")], pts[(p["i"], "b")]
            if p["v"] is None:
                hseg.setdefault(p["ha"], []).append((min(xa, xb), max(xa, xb), p["i"], "h"))
            else:
                vxm = vx0[p["v"]] + V_BASE / 2
                hseg.setdefault(p["ha"], []).append((min(xa, vxm), max(xa, vxm), p["i"], "ha"))
                hseg.setdefault(p["hb"], []).append((min(xb, vxm), max(xb, vxm), p["i"], "hb"))
                y1, y2 = hy0[p["ha"]], hy0[p["hb"]]
                vseg.setdefault(p["v"], []).append((min(y1, y2), max(y1, y2), p["i"], "v"))
        lane_of = {}
        newh, newv = [0] * (R + 1), [0] * (C + 1)
        for store, newl in ((hseg, newh), (vseg, newv)):
            for k, segs in store.items():
                ends = []
                for s0, s1, i, tag in sorted(segs):
                    for li, e in enumerate(ends):
                        if e < s0 - 6:
                            ends[li] = s1
                            lane_of[(i, tag)] = li
                            break
                    else:
                        lane_of[(i, tag)] = len(ends)
                        ends.append(s1)
                newl[k] = max(newl[k], len(ends))
        if newh == hlanes and newv == vlanes:
            break
        hlanes, vlanes = newh, newv
    X, Y, vx0, hy0, W, Hh = layout(hlanes, vlanes)
    pts = attach(X)

    def hy(k, lane):
        return hy0[k] + 22 + lane * LANE

    def vx(k, lane):
        return vx0[k] + 17 + lane * LANE

    boxes = {t: (X[cell[t][1]], Y[cell[t][0]], size[t][0], size[t][1]) for t in tablas}
    paths = []
    for p in plans:
        xa, xb = pts[(p["i"], "a")], pts[(p["i"], "b")]
        if p["v"] is None:
            y = hy(p["ha"], lane_of[(p["i"], "h")])
            pth = [(xa, y), (xb, y)]
        else:
            ya = hy(p["ha"], lane_of[(p["i"], "ha")])
            yb = hy(p["hb"], lane_of[(p["i"], "hb")])
            v = vx(p["v"], lane_of[(p["i"], "v")])
            pth = [(xa, ya), (v, ya), (v, yb), (xb, yb)]
        ax, ay, aw, ah = boxes[p["a"]]
        bx, by, bw, bh = boxes[p["b"]]
        start = (xa, ay if p["sa"] == "top" else ay + ah)
        end = (xb, by if p["sb"] == "top" else by + bh)
        # Punto exacto de conexion en cada clase, relativo a su centro (EA: y hacia arriba). Sin esto EA elige
        # su propio punto y el ultimo tramo sale en diagonal. EDGE: lado de salida del origen (1 arriba, 3 abajo).
        geom = "SX=%d;SY=%d;EX=%d;EY=%d;EDGE=%d;" % (
            round(start[0] - (ax + aw / 2)), round((ay + ah / 2) - start[1]),
            round(end[0] - (bx + bw / 2)), round((by + bh / 2) - end[1]),
            1 if p["sa"] == "top" else 3)
        paths.append({"rel": p["i"], "path": pth, "start": start, "end": end, "geom": geom})
    return boxes, paths, (W, Hh)


def verificar(boxes, paths, rels):
    """Ninguna linea atraviesa una clase que no sea la suya."""
    malos = []
    for pa in paths:
        rel = rels[pa["rel"]]
        pts = [pa["start"]] + pa["path"] + [pa["end"]]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            for t, (bx, by, bw, bh) in boxes.items():
                if t in (rel["hijo"], rel["padre"]):
                    continue
                if min(x1, x2) < bx + bw - 1 and max(x1, x2) > bx + 1 and min(y1, y2) < by + bh - 1 and max(y1, y2) > by + 1:
                    malos.append((rel["hijo"], rel["padre"], t))
    return malos


def vista(code, boxes, paths, rels, size):
    from PIL import Image, ImageDraw
    k = 0.35
    im = Image.new("RGB", (int(size[0] * k) + 20, int(size[1] * k) + 20), "white")
    d = ImageDraw.Draw(im)
    for t, (x, y, w, h) in boxes.items():
        d.rectangle([x * k, y * k, (x + w) * k, (y + h) * k], outline="#7a4a1a", fill="#fbf1e6")
        d.text((x * k + 4, y * k + 3), NOMBRE[t], fill="black")
    for pa in paths:
        pts = [pa["start"]] + pa["path"] + [pa["end"]]
        comp = rels[pa["rel"]]["composicion"]
        d.line([(x * k, y * k) for x, y in pts], fill="#c0392b" if comp else "#555555", width=1)
    im.save(HERE / f"vista_{code}.png")


# ---------------------------------------------------------------- modelo para el script de EA
def construir():
    diagrams, used, all_rels = [], set(), {}
    for code, m in ANALISIS["modulos"].items():
        tablas = [t for t in m["tablas"] if t not in JUNCTION]
        rels = relaciones(set(tablas))
        cell, R, C = ubicar(tablas, rels)
        boxes, paths, size = rutear(tablas, rels, cell, R, C)
        malos = verificar(boxes, paths, rels)
        assert not malos, (code, malos[:5])
        vista(code, boxes, paths, rels, size)
        used |= set(tablas)
        for r in rels:
            all_rels[(r["hijo"], r["padre"], r["columna"])] = r
        diagrams.append({
            "code": code, "name": f"Modelo de dominio {code} - {m['titulo']} ({', '.join(m['casos'])})",
            "boxes": {t: list(map(round, b)) for t, b in boxes.items()},
            "links": [{"key": f"{rels[p['rel']]['hijo']}|{rels[p['rel']]['padre']}|{rels[p['rel']]['columna']}",
                       "path": [[round(x), round(y)] for x, y in p["path"]], "geom": p["geom"]} for p in paths],
        })
        print(f"{code}: {len(tablas)} clases, {len(rels)} relaciones "
              f"({sum(r['composicion'] for r in rels)} composiciones), lienzo {size[0]:.0f}x{size[1]:.0f}")
    clases = [{"t": t, "name": NOMBRE[t], "attrs": atributos(t), "ops": operaciones(t),
               "notes": f"Tabla {t} ({MODELOS[t]['class']}). Atributos y FK tomados del modelo SQLAlchemy; "
                        f"operaciones: funciones de servicio que crean o consultan la tabla."} for t in sorted(used)]
    rel_list = [{"key": f"{h}|{p}|{c}", **r} for (h, p, c), r in sorted(all_rels.items())]
    return {"classes": clases, "relations": rel_list, "diagrams": diagrams}


if __name__ == "__main__":
    model = construir()
    tpl = (HERE / "plantilla_dominio.js").read_text(encoding="utf-8")
    js = "var MODEL = " + json.dumps(model, ensure_ascii=True) + ";\n"
    (HERE / "FashionStore_modelo_dominio.js").write_text(tpl.replace("/*MODEL*/\n", js), encoding="utf-8")
    print("OK:", len(model["classes"]), "clases,", len(model["relations"]), "relaciones,", len(model["diagrams"]), "diagramas")
