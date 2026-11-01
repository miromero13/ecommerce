"""Genera FashionStore_arquitectura.js: diagramas de arquitectura para EA 15.

Uso (desde la raiz del repo):  python docs/ea/arquitectura/generar_arquitectura.py

Diagramas:
  1) Paquetes en tres capas (Vista / Controlador / Modelo / Persistencia) con los 6 paquetes de casos de uso.
  2) Diagrama de componentes general del sistema, por filas: Vista (aplicaciones cliente), Control (un componente
     por modulo), Modelo (las entidades de cada modulo) y Conexion (PostgreSQL, almacenamientos locales y APIs
     externas que usa el codigo de cada modulo).
  3) Backend FastAPI, 4) Frontend web Angular PWA y 5) App móvil Flutter, con el mismo estilo por filas
     (paquetes_mvc.py): esquemas / componentes / pantallas, sus controles, sus modelos y sus conexiones.
  6..11) Diagrama de componentes de cada modulo M1-M6 con el mismo estilo: vistas, controles y entidades de sus
     diagramas de secuencia, y la conexion donde persisten (componentes_modulo.py; dibujo en capas.py).
Cada elemento y cada linea corresponde a algo verificado en el codigo (carpetas, imports, inject(), dependencias de
FastAPI y librerias externas); las cifras (rutas, servicios, paginas...) se cuentan del repositorio al generar.
Cada linea lleva su recorrido ortogonal; el script falla si una linea pasa sobre una caja o se encima con otra.
En los diagramas por filas el orden de las cajas se elige para tener la menor cantidad de cruces (se informa al generar).
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BACK = ROOT / "backend"
sys.path.insert(0, str(HERE.parent / "modelo_dominio"))
import io, contextlib  # noqa: E402
with contextlib.redirect_stdout(io.StringIO()):
    import analizar_codigo as AC  # noqa: E402

# ---------------------------------------------------------------- comprobación: todas las rutas están registradas
main_py = (BACK / "main.py").read_text(encoding="utf-8")
n_rutas = len([p for p in (BACK / "app/routes").glob("*.py") if p.stem != "__init__"])
assert n_rutas == len(re.findall(r"api_router\.include_router\(", main_py)), "rutas sin registrar en main.py"

MODULOS = [AC.MODULOS[k][0] for k in sorted(AC.MODULOS)]          # los 6 paquetes de casos de uso


# ---------------------------------------------------------------- utilidades de dibujo
class Diagrama:
    def __init__(self, nombre, tipo, nota=""):
        self.nombre, self.tipo, self.nota = nombre, tipo, nota
        self.el, self.ln = {}, []

    def caja(self, id_, kind, name, x, y, w, h, st="", contenedor=False):
        self.el[id_] = {"id": id_, "kind": kind, "name": name, "st": st, "b": [x, y, w, h], "cont": contenedor}
        return id_

    def borde(self, id_, lado, f=0.5):
        x, y, w, h = self.el[id_]["b"]
        return {"L": (x, y + h * f), "R": (x + w, y + h * f), "T": (x + w * f, y), "B": (x + w * f, y + h)}[lado]

    def linea(self, a, b, tipo, label, pts):
        """pts: puntos del recorrido (inicio en el borde de a, fin en el borde de b), solo tramos rectos."""
        pts = [tuple(map(round, p)) for p in pts]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            assert x1 == x2 or y1 == y2, (a, b, pts)
        self.ln.append({"a": a, "b": b, "type": tipo, "label": label, "pts": pts})

    def recta(self, a, la, b, lb, tipo, label, fa=0.5, fb=None):
        """Linea recta entre dos lados enfrentados (se alinea al punto del primero)."""
        p = self.borde(a, la, fa)
        q = self.borde(b, lb, 0.5)
        q = (p[0], q[1]) if la in "TB" else (q[0], p[1])
        self.linea(a, b, tipo, label, [p, q])

    def validar(self):
        cajas = {k: v["b"] for k, v in self.el.items() if v["kind"] not in ("frame",) and not v["cont"]}
        segs = []
        for i, l in enumerate(self.ln):
            for (x1, y1), (x2, y2) in zip(l["pts"], l["pts"][1:]):
                for k, (bx, by, bw, bh) in cajas.items():
                    if k in (l["a"], l["b"]):
                        continue
                    if min(x1, x2) < bx + bw and max(x1, x2) > bx and min(y1, y2) < by + bh and max(y1, y2) > by:
                        raise SystemExit(f"{self.nombre}: la linea {l['a']}->{l['b']} pasa sobre {k}")
                segs.append((i, (x1, y1), (x2, y2)))
        for s in segs:                        # dos lineas distintas no comparten un mismo tramo
            for t in segs:
                if s[0] >= t[0]:
                    continue
                (a1, b1), (a2, b2) = (s[1], s[2]), (t[1], t[2])
                if a1[0] == b1[0] == a2[0] == b2[0]:
                    lo, hi = max(min(a1[1], b1[1]), min(a2[1], b2[1])), min(max(a1[1], b1[1]), max(a2[1], b2[1]))
                    if hi - lo > 2:
                        raise SystemExit(f"{self.nombre}: tramos verticales encimados {self.ln[s[0]]['a']}->{self.ln[s[0]]['b']} y {self.ln[t[0]]['a']}->{self.ln[t[0]]['b']}")
                if a1[1] == b1[1] == a2[1] == b2[1]:
                    lo, hi = max(min(a1[0], b1[0]), min(a2[0], b2[0])), min(max(a1[0], b1[0]), max(a2[0], b2[0]))
                    if hi - lo > 2:
                        raise SystemExit(f"{self.nombre}: tramos horizontales encimados {self.ln[s[0]]['a']}->{self.ln[s[0]]['b']} y {self.ln[t[0]]['a']}->{self.ln[t[0]]['b']}")

    def etiquetas(self):
        """Lugar de la etiqueta de cada linea: EA la ancla en el centro del tramo central del recorrido y la mueve
        con OX/OY. Se prueban puntos de todos los tramos de la linea, al costado del trazo, y se elige el que no tapa
        cajas, no cruza otras lineas y no choca con etiquetas ya colocadas (a igualdad, el tramo mas largo)."""
        cajas = [v["b"] for v in self.el.values() if v["kind"] != "frame" and not v["cont"]]
        todos = [((x1, y1), (x2, y2), i) for i, l in enumerate(self.ln) for (x1, y1), (x2, y2) in zip(l["pts"], l["pts"][1:])]
        puestas = []

        def choca(r, q):
            return not (r[2] <= q[0] or r[0] >= q[2] or r[3] <= q[1] or r[1] >= q[3])

        for i, l in enumerate(self.ln):
            segs = list(zip(l["pts"], l["pts"][1:]))
            (dx1, dy1), (dx2, dy2) = segs[len(segs) // 2]
            defecto = ((dx1 + dx2) / 2, (dy1 + dy2) / 2)
            w, h = len(l["label"]) * 6.4 + 10, 16
            cands = []
            for (x1, y1), (x2, y2) in segs:
                largo = abs(x2 - x1) + abs(y2 - y1)
                for t in (0.5, 0.3, 0.7):
                    cx, cy = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
                    if y1 == y2:
                        lados = [(cx, cy - 11), (cx, cy + 11)]
                    else:
                        lados = [(cx + w / 2 + 6, cy), (cx - w / 2 - 6, cy)]
                    for px, py in lados:
                        r = (px - w / 2, py - h / 2, px + w / 2, py + h / 2)
                        c = sum(10 for b in cajas if choca(r, (b[0], b[1], b[0] + b[2], b[1] + b[3])))
                        c += sum(4 for (a1, a2, j) in todos if j != i and choca(r, (min(a1[0], a2[0]) - 1, min(a1[1], a2[1]) - 1,
                                                                                    max(a1[0], a2[0]) + 1, max(a1[1], a2[1]) + 1)))
                        c += sum(10 for q in puestas if choca(r, q))
                        c += 0 if largo >= w + 20 else 2
                        c += abs(t - 0.5)
                        cands.append((c, -largo, px, py, r))
            c, _, px, py, r = min(cands)
            puestas.append(r)
            l["lmt"] = ("$LLB=;LLT=;LMT=CX=%d:CY=13:OX=%d:OY=%d:HDN=0:BLD=0:ITA=0:UND=0:CLR=-1:ALN=0:DIR=0:ROT=0;"
                        "LMB=;LRT=;LRB=;IRHS=;ILHS=;" % (round(w), round(px - defecto[0]), round(py - defecto[1])))

    def modelo(self):
        self.validar()
        self.etiquetas()
        links = []
        for l in self.ln:
            (ax, ay, aw, ah), (bx, by, bw, bh) = self.el[l["a"]]["b"], self.el[l["b"]]["b"]
            s, e = l["pts"][0], l["pts"][-1]
            lado = 1 if s[1] == ay else 3 if s[1] == ay + ah else 4 if s[0] == ax else 2
            geom = "SX=%d;SY=%d;EX=%d;EY=%d;EDGE=%d;" % (round(s[0] - (ax + aw / 2)), round((ay + ah / 2) - s[1]),
                                                       round(e[0] - (bx + bw / 2)), round((by + bh / 2) - e[1]), lado)
            links.append({**l, "geom": geom + l["lmt"], "path": [list(p) for p in l["pts"][1:-1]]})
        return {"name": self.nombre, "type": self.tipo, "note": self.nota, "elements": list(self.el.values()),
                "links": links}


# ================================================================ 1) paquetes en tres capas
d1 = Diagrama("Diseño lógico - Diagrama de paquetes en tres capas", "Package")
PW, PG, X0 = 300, 40, 70
PITCH = PW + PG
xs = [X0 + i * PITCH for i in range(6)]
FR_R = xs[-1] + PW + 30
capas = [("c1", "Capa 1: Vista (Presentación / Interfaz de Usuario: Angular PWA y Flutter)", "Vistas", 40),
         ("c2", "Capa 2: Controlador (Lógica de Aplicación: rutas y servicios FastAPI)", "Controladores", 400),
         ("c3", "Capa 3: Modelo (Dominio: entidades SQLAlchemy)", "Modelos", 760)]
for cid, titulo, pref, y in capas:
    d1.caja(cid, "frame", titulo, 40, y, FR_R - 40, 270)
    for i, m in enumerate(MODULOS):
        d1.caja(f"{cid}_{i}", "package", f"Paquete {pref} {m}", xs[i], y + 60, PW, 170)
LOC_X = FR_R + 60
d1.caja("cp", "frame", "Capa de Persistencia / Base de Datos", 40, 1120, LOC_X + 320 - 40, 230)
d1.caja("pg", "package", "Base de Datos Central PostgreSQL", X0, 1190, xs[-1] + PW - X0, 120)
d1.caja("loc", "package", "Almacenamiento local offline (IndexedDB / flutter_secure_storage)", LOC_X, 1190, 300, 120)
for i in range(6):
    d1.recta(f"c1_{i}", "B", f"c2_{i}", "T", "dep", "invoca (HTTPS REST/JSON + JWT)")
    d1.recta(f"c2_{i}", "B", f"c3_{i}", "T", "dep", "usa (SQLAlchemy ORM)")
    d1.recta(f"c3_{i}", "B", "pg", "T", "dep", "persiste (psycopg2)")
p = d1.borde("c1_5", "R", 0.5)
d1.linea("c1_5", "loc", "dep", "guarda la cola y el catálogo offline", [p, (LOC_X + 150, p[1]), (LOC_X + 150, 1190)])

# ================================================================ 2) diagrama de componentes general (Vista / Control / Modelo / Conexión)
import componentes_modulo as CM  # noqa: E402
from capas import distribuir  # noqa: E402

ST_V, ST_C, ST_M, ST_X = "Componente:Vista", "Componente:Control", "Componente:Model", "conexion"
MODS = CM.modulos()
RUTAS_MOVIL = CM.rutas_movil()
CRUCES = {}


def general():
    vistas = [("vw", "V.Frontend web (Angular 21 PWA)", ST_V, False), ("vm", "V.App móvil (Flutter)", ST_V, False)]
    controles = [(f"c{c}", f"Control {c}: {m['nombre']}", ST_C, False) for c, m in MODS.items()]
    modelos = [(f"m{c}", f"M.Modelo {c}: {m['nombre']}", ST_M, False) for c, m in MODS.items()]
    externos = {c: CM.externos_de(m["handlers"]) for c, m in MODS.items()}
    usados = sorted(set().union(*externos.values()))
    # conexiones en dos filas: APIs externas y, al fondo, la base de datos y los almacenamientos locales
    almacenes = [("pg", "PostgreSQL", ST_X, True)]
    if any(m["locales"] for m in MODS.values()):
        almacenes.append(("idb", "IndexedDB (navegador)", ST_X, True))
    almacenes.append(("sec", "flutter_secure_storage (dispositivo móvil)", ST_X, False))
    ids_ext = {e: f"x{i}" for i, e in enumerate(usados)}
    apis = [(ids_ext[e], e, ST_X, False) for e in usados]
    aristas = []
    for c, m in MODS.items():
        aristas.append((f"c{c}", "vw"))                       # todas sus vistas son componentes Angular
        if set(m["controles"]) & RUTAS_MOVIL:                 # la app móvil llama a alguna de sus rutas
            aristas.append((f"c{c}", "vm"))
        aristas.append((f"c{c}", f"m{c}"))
        if set(m["modelos"]) - m["locales"]:
            aristas.append((f"m{c}", "pg"))
        if m["locales"]:
            aristas.append((f"m{c}", "idb"))
        for e in sorted(externos[c]):
            aristas.append((f"c{c}", ids_ext[e]))
    aristas.append(("vm", "sec"))                             # sesión y cola offline de la app (checks)
    capas = distribuir([vistas, controles, modelos, apis, almacenes], aristas)
    d = Diagrama("Diagrama de componentes general del sistema", "Component",
                 "Vista: aplicaciones cliente. Control: rutas FastAPI y servicios del frontend de cada módulo. "
                 "Modelo: entidades de cada módulo. Conexión: base de datos, almacenamientos locales y APIs externas "
                 "que usa el código de cada módulo.")
    CRUCES[d.nombre] = capas.dibujar(d)
    return d


d2 = general()

# ================================================================ 3..5) paquetes Backend, Frontend web y App móvil (Vista / Control / Modelo / Conexión)
import paquetes_mvc as PM  # noqa: E402


def diagrama_paquete(nombre, nota, datos):
    filas, aristas = datos
    capas = distribuir([f for f in filas if f], aristas)
    d = Diagrama(nombre, "Component", nota)
    CRUCES[d.nombre] = capas.dibujar(d)
    return d


d3 = diagrama_paquete("Componentes del backend (FastAPI)",
                      "Vista: esquemas Pydantic que responde cada ruta. Control: rutas FastAPI de los casos de uso. "
                      "Modelo: clases SQLAlchemy de cada módulo. Conexión: PostgreSQL y APIs externas.", PM.backend())
d4 = diagrama_paquete("Componentes del frontend web (Angular PWA)",
                      "Vista: componentes Angular de cada módulo. Control: servicios Angular que llaman a sus rutas y "
                      "servicios offline / PWA. Modelo: archivos *.model.ts. Conexión: API REST e IndexedDB.",
                      PM.frontend())
d5 = diagrama_paquete("Componentes de la app móvil (Flutter)",
                      "Vista: pantallas *_page.dart. Control: controladores, APIs y servicios del núcleo. "
                      "Modelo: archivos *_models.dart. Conexión: API REST y flutter_secure_storage.", PM.movil())

# ================================================================ 6..11) componentes por módulo (Vista / Control / Modelo / Conexión)
RANGOS = {"M1": "CU1–CU4, CU26–CU28", "M2": "CU5–CU10", "M3": "CU11–CU12", "M4": "CU13–CU14", "M5": "CU15–CU19",
          "M6": "CU20–CU25, CU29–CU30"}


def diagrama_modulo(code, m):
    """Mismos objetos y llamadas que los diagramas de secuencia de los casos de uso del módulo."""
    ident = {}

    def nid(pref, nombre):
        return ident.setdefault((pref, nombre), f"{pref}{len(ident)}")

    vistas = [(nid("v", v), f"V.{v}", ST_V, False) for v in m["vistas"]]
    # controles del frontend (servicios offline / PWA) en su propia fila, encima de las rutas FastAPI que llaman
    front = [(nid("c", c), c, ST_C, False) for c in m["controles"] if c in CM.T.TS]
    controles = [(nid("c", c), c, ST_C, False) for c in m["controles"] if c not in CM.T.TS]
    modelos = [(nid("m", e), f"M.{e}", ST_M, False) for e in m["modelos"]]
    conex = []
    if set(m["modelos"]) - m["locales"]:
        conex.append(("pg", "PostgreSQL", ST_X, True))
    if m["locales"]:
        conex.append(("idb", "IndexedDB (navegador)", ST_X, True))
    aristas = [(ident[("c", c)], ident[("v", v)]) for c, v in sorted(m["edges"]["cv"])]
    aristas += [(ident[("c", a)], ident[("c", b)]) for a, b in sorted(m["edges"]["cc"])]
    aristas += [(ident[("c", c)], ident[("m", e)]) for c, e in sorted(m["edges"]["cm"])]
    aristas += [(ident[("m", e)], "idb" if e in m["locales"] else "pg") for e in m["modelos"]]
    capas = distribuir([f for f in (vistas, front, controles, modelos, conex) if f], aristas)
    d = Diagrama(f"Diagrama de componentes del módulo {code}: {m['nombre']} ({RANGOS[code]})", "Component",
                 "Tomado de los diagramas de secuencia del módulo: cada vista llama a sus controles y cada control "
                 "trabaja con sus entidades; las entidades del backend persisten en PostgreSQL y las locales en IndexedDB.")
    CRUCES[d.nombre] = capas.dibujar(d)
    return d


MODULO_DIAGRAMAS = [diagrama_modulo(code, m) for code, m in MODS.items()]

if __name__ == "__main__":
    diagramas = [d.modelo() for d in (d1, d2, d3, d4, d5, *MODULO_DIAGRAMAS)]
    for d in diagramas:
        cruces = f", {CRUCES[d['name']]} cruces de lineas" if d["name"] in CRUCES else ""
        print(f"{d['name']}: {len(d['elements'])} elementos, {len(d['links'])} lineas{cruces}")
    model = {"diagrams": diagramas}
    tpl = (HERE / "plantilla_arquitectura.js").read_text(encoding="utf-8")
    js = "var MODEL = " + json.dumps(model, ensure_ascii=True) + ";\n"
    (HERE / "FashionStore_arquitectura.js").write_text(tpl.replace("/*MODEL*/\n", js), encoding="utf-8")
    print("OK: FashionStore_arquitectura.js generado")
