"""Genera FashionStore_arquitectura.js: diagramas de arquitectura para EA 15.

Uso (desde la raiz del repo):  python docs/ea/arquitectura/generar_arquitectura.py

Diagramas:
  1) Paquetes en tres capas (Vista / Controlador / Modelo / Persistencia) con los 6 paquetes de casos de uso.
  2) Integracion general de componentes (frontend web, app movil, backend, datos y servicios externos).
  3) Componentes del backend FastAPI.  4) Componentes del frontend Angular PWA.  5) Componentes de la app Flutter.
Cada elemento y cada linea corresponde a algo verificado en el codigo (carpetas, imports, inject(), dependencias de
FastAPI y librerias externas); las cifras (rutas, servicios, paginas...) se cuentan del repositorio al generar.
Cada linea lleva su recorrido ortogonal; el script falla si una linea pasa sobre una caja o se encima con otra.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BACK, FRONT, MOB = ROOT / "backend", ROOT / "frontend" / "src" / "app", ROOT / "mobile" / "lib"
sys.path.insert(0, str(HERE.parent / "modelo_dominio"))
import io, contextlib  # noqa: E402
with contextlib.redirect_stdout(io.StringIO()):
    import analizar_codigo as AC  # noqa: E402

# ---------------------------------------------------------------- cifras contadas del codigo
n_rutas = len([p for p in (BACK / "app/routes").glob("*.py") if p.stem != "__init__"])
n_serv = len([p for p in (BACK / "app/services").glob("*.py") if p.stem != "__init__"])
n_mig = len(list((BACK / "alembic/versions").glob("*.py")))
n_tablas = len(json.loads((HERE.parent / "base_datos/esquema.json").read_text(encoding="utf-8"))["tablas"])
main_py = (BACK / "main.py").read_text(encoding="utf-8")
n_ciclos = len(re.findall(r"asyncio\.create_task\(", main_py))
assert n_rutas == len(re.findall(r"api_router\.include_router\(", main_py)), "rutas sin registrar en main.py"
roles = ["superadmin", "admin", "encargado", "cajero", "cliente", "proveedor", "delivery", "shared"]
n_pag = sum(len(list((FRONT / "features" / r / "pages").glob("*.component.ts"))) for r in roles)
n_api_srv = len(list((FRONT / "features/shared/services").glob("*-api.service.ts"))) + \
    len(list((FRONT / "features/admin/services").glob("*.service.ts")))
m_pag = len(list(MOB.glob("features/*/*_page.dart")))
m_ctl = len(list(MOB.glob("features/*/*_controller.dart")))
m_api = len(list(MOB.glob("features/*/*_api.dart")))
m_feat = len([p for p in (MOB / "features").iterdir() if p.is_dir()])

# verificaciones de las dependencias que se dibujan (si el codigo cambia, el script avisa en vez de mentir)
def tiene(path, patron):
    return re.search(patron, path.read_text(encoding="utf-8")) is not None

checks = {
    "auth interceptor": tiene(FRONT / "app.config.ts", r"withInterceptors\(\[authInterceptor\]\)"),
    "service worker": tiene(FRONT / "app.config.ts", r"provideServiceWorker\('ngsw-worker\.js'"),
    "interceptor usa sesion": tiene(FRONT / "features/shared/interceptors/auth.interceptor.ts", r"inject\(SessionService\)"),
    "api usa HttpClient": tiene(FRONT / "core/services/api.service.ts", r"inject\(HttpClient\)"),
    "offline usa indexeddb": tiene(FRONT / "core/services/offline-queue.service.ts", r"inject\(IndexedDbService\)"),
    "offline usa http": tiene(FRONT / "core/services/offline-queue.service.ts", r"inject\(HttpClient\)"),
    "indexeddb": tiene(FRONT / "core/services/indexeddb.service.ts", r"indexedDB\.open"),
    "pwa swupdate": tiene(FRONT / "core/services/pwa.service.ts", r"SwUpdate"),
    "stripe web": tiene(FRONT / "features/shared/components/stripe-card-payment.component.ts", r"stripe"),
    "fcm web": tiene(FRONT / "features/shared/services/notification-push.service.ts", r"firebase/messaging"),
    "decart web": (ROOT / "frontend/public/decart-try-on.html").exists(),
    "guards": tiene(FRONT / "app.routes.ts", r"canActivate: \[authenticatedGuard\]"),
    "router middleware": tiene(BACK / "main.py", r"register_tenant_middleware\(app\)"),
    "get_db": tiene(BACK / "app/core/database.py", r"def get_db"),
    "alembic usa modelos": tiene(BACK / "alembic/env.py", r"from app\.models"),
    "ml en reportes": tiene(BACK / "app/routes/report_routes.py", r"services\.ml|services import ml|from app\.services\.ml"),
    "stripe back": tiene(BACK / "app/services/order_service.py", r"stripe\.PaymentIntent"),
    "gemini": tiene(BACK / "app/services/chatbot_service.py", r"(?i)gemini|genai"),
    "hugging face": tiene(BACK / "app/services/virtual_try_on_service.py", r"(?i)hugging|hf\.space|gradio"),
    "fcm back": tiene(BACK / "app/services/notification_delivery.py", r"(?i)firebase|fcm"),
    "mailtrap": tiene(BACK / "app/services/email_service.py", r"(?i)mailtrap|smtp"),
    "cloudinary": tiene(BACK / "app/services/cloudinary_service.py", r"cloudinary"),
    "dio": tiene(MOB / "core/network/api_client.dart", r"package:dio"),
    "bearer": tiene(MOB / "core/network/api_client.dart", r"Bearer"),
    "secure storage": tiene(MOB / "core/storage/session_storage.dart", r"flutter_secure_storage"),
    "offline movil storage": tiene(MOB / "core/offline/offline_queue_service.dart", r"flutter_secure_storage"),
    "offline movil api": tiene(MOB / "core/offline/offline_queue_service.dart", r"api_client\.dart"),
    "push movil": tiene(MOB / "features/notifications/notification_push_service.dart", r"firebase_messaging"),
    "push inicializada en app": tiene(MOB / "app/app.dart", r"NotificationPushService"),
    "stripe movil": tiene(MOB / "features/orders/checkout_page.dart", r"flutter_stripe"),
    "decart movil": tiene(MOB / "features/catalog/virtual_try_on_page.dart", r"decartTryOnUrl"),
    "auth controller sesion": tiene(MOB / "features/auth/auth_controller.dart", r"SessionStorage"),
    "offline queue page": tiene(MOB / "features/management/offline_queue_page.dart", r"OfflineQueueService"),
}
faltan = [k for k, v in checks.items() if not v]
assert not faltan, f"dependencias que ya no estan en el codigo: {faltan}"

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

# ================================================================ 2) integracion general
d2 = Diagrama("Integración general de componentes", "Component")
E0, C1, C2, C3, C4 = 40, 360, 780, 1180, 1600            # columnas
d2.caja("idb", "component", "IndexedDB (navegador)", E0, 240, 240, 90, "datastore")
d2.caja("web", "component", "Frontend web (Angular 21 PWA)", C1, 200, 300, 170, "subsystem")
d2.caja("mov", "component", "App móvil (Flutter)", C1, 640, 300, 170, "subsystem")
d2.caja("sec", "component", "Almacenamiento seguro del dispositivo (flutter_secure_storage)", E0, 680, 240, 90, "datastore")
d2.caja("api", "interface", "API REST /api", C2, 450, 260, 90)
d2.caja("bk", "component", "Backend (FastAPI)", C3, 420, 300, 150, "subsystem")
d2.caja("pgs", "component", "PostgreSQL", C3, 700, 300, 90, "database")
d2.caja("dec", "component", "Decart AI", C1, 40, 300, 70, "external")
d2.caja("str", "component", "Stripe", C2, 40, 260, 70, "external")
d2.caja("fcm", "component", "Firebase Cloud Messaging", C2, 700, 260, 70, "external")
for i, (k, n) in enumerate([("gem", "Google Gemini"), ("hf", "Hugging Face Space"), ("mail", "Mailtrap"),
                             ("cld", "Cloudinary")]):
    d2.caja(k, "component", n, C4, 300 + i * 110, 240, 70, "external")
web_r, mov_r = C1 + 300, C1 + 300
d2.linea("web", "api", "use", "HTTPS REST/JSON + JWT", [(web_r, 330), (720, 330), (720, 470), (C2, 470)])
d2.linea("mov", "api", "use", "HTTPS REST/JSON + JWT", [(mov_r, 680), (720, 680), (720, 520), (C2, 520)])
d2.recta("bk", "L", "api", "R", "real", "expone", fa=(495 - 420) / 150)
d2.recta("bk", "B", "pgs", "T", "use", "SQLAlchemy / psycopg2 (TCP 5432)")
d2.recta("web", "L", "idb", "R", "use", "cola y catálogo offline", fa=(285 - 200) / 170)
d2.recta("mov", "L", "sec", "R", "use", "sesión y cola offline", fa=(725 - 640) / 170)
d2.recta("web", "T", "dec", "B", "use", "@decartai/sdk (WebRTC)", fa=0.35)
d2.linea("mov", "dec", "use", "WebView (decart-try-on)", [(C1, 760), (320, 760), (320, 75), (C1, 75)])
d2.linea("web", "str", "use", "Stripe.js", [(web_r, 230), (750, 230), (750, 90), (C2, 90)])
d2.linea("mov", "str", "use", "flutter_stripe", [(mov_r, 780), (740, 780), (740, 60), (C2, 60)])
d2.linea("bk", "str", "use", "PaymentIntent + webhook", [(C3, 440), (1110, 440), (1110, 75), (C2 + 260, 75)])
d2.linea("bk", "fcm", "use", "envío push (firebase_admin)", [(C3, 550), (1130, 550), (1130, 735), (C2 + 260, 735)])
d2.linea("web", "fcm", "use", "firebase (web push)", [(web_r, 350), (760, 350), (760, 715), (C2, 715)])
d2.recta("mov", "R", "fcm", "L", "use", "firebase_messaging", fa=(755 - 640) / 170)
d2.linea("bk", "gem", "use", "chatbot, reportes, RPA, prendas", [(C3 + 280, 420), (C3 + 280, 335), (C4, 335)])
d2.recta("bk", "R", "hf", "L", "use", "probador por foto", fa=(445 - 420) / 150)
d2.recta("bk", "R", "mail", "L", "use", "correos", fa=(555 - 420) / 150)
d2.linea("bk", "cld", "use", "imágenes del catálogo y logos", [(C3 + 280, 570), (C3 + 280, 665), (C4, 665)])

# ================================================================ 3) backend FastAPI
d3 = Diagrama("Componentes del backend (FastAPI)", "Component")
L, C, R, X = 40, 440, 880, 1240
d3.caja("api", "interface", "API REST /api", C + 50, 30, 260, 70)
d3.caja("main", "component", "Aplicación FastAPI - main.py (APIRouter /api, CORS, middleware de empresa)", C, 160, 360, 90)
d3.caja("rut", "component", f"Rutas - app/routes ({n_rutas} APIRouter)", C, 320, 360, 110, "controller")
d3.caja("seg", "component", "Seguridad - app/auth (JWT, contraseñas, roles)", L, 290, 300, 90)
d3.caja("esq", "component", "Esquemas - app/schemas (Pydantic)", L, 420, 300, 90)
d3.caja("ml", "component", "Motor ML - app/services/ml (pronóstico de demanda, segmentación)", R, 320, 300, 110)
d3.caja("srv", "component", f"Servicios - app/services ({n_serv} servicios de negocio)", C, 560, 360, 380, "service")
d3.caja("tar", "component", f"Tareas en segundo plano - main.py ({n_ciclos} ciclos asíncronos)", L, 600, 300, 100, "worker")
d3.caja("ses", "component", "Sesión de BD - app/core/database.py (engine, SessionLocal, get_db)", L, 800, 300, 100)
d3.caja("mod", "component", f"Modelos - app/models (SQLAlchemy, {n_tablas} tablas)", C, 1020, 360, 90)
d3.caja("pg", "component", "PostgreSQL", C, 1200, 360, 90, "database")
d3.caja("mig", "component", f"Migraciones - alembic ({n_mig} versiones)", R, 1200, 300, 90)
ext = [("str", "Stripe", "PaymentIntent (pedidos y reservas)"), ("gem", "Google Gemini", "chatbot, reportes, RPA"),
       ("hf", "Hugging Face Space", "probador por foto"), ("fcm", "Firebase Cloud Messaging", "notificaciones push"),
       ("mail", "Mailtrap", "credenciales y comprobantes"), ("cld", "Cloudinary", "imágenes y logos")]
for i, (k, n, lab) in enumerate(ext):
    y = 575 + i * 58
    d3.caja(k, "component", n, X, y, 260, 44, "external")
    d3.linea("srv", k, "use", lab, [(C + 360, y + 22), (X, y + 22)])
d3.recta("main", "T", "api", "B", "real", "expone")
d3.recta("main", "B", "rut", "T", "use", f"include_router ({n_rutas})")
d3.recta("rut", "L", "seg", "R", "use", "Depends(get_current_user, require_roles)", fa=(335 - 320) / 110)
d3.recta("rut", "L", "esq", "R", "use", "valida entrada y salida", fa=(465 - 420) / 110 if False else (425 - 320) / 110)
d3.recta("rut", "B", "srv", "T", "use", "invoca", fa=0.5)
d3.recta("rut", "R", "ml", "L", "use", "report_routes: predicción y segmentación")
d3.recta("tar", "R", "srv", "L", "use", "ejecuta periódicamente")
d3.linea("rut", "ses", "use", "Depends(get_db)", [(C + 30, 430), (C + 30, 480), (390, 480), (390, 850), (L + 300, 850)])
d3.recta("srv", "B", "mod", "T", "use", "consulta y modifica")
d3.recta("mod", "B", "pg", "T", "use", "mapea las tablas")
d3.linea("ses", "pg", "use", "psycopg2 (TCP 5432)", [(190, 900), (190, 1245), (C, 1245)])
d3.recta("mig", "L", "pg", "R", "use", "crea y actualiza el esquema")
d3.linea("mig", "mod", "use", "Base.metadata", [(R + 150, 1200), (R + 150, 1065), (C + 360, 1065)])

# ================================================================ 4) frontend Angular PWA
d4 = Diagrama("Componentes del frontend web (Angular PWA)", "Component")
X0, X1, X2, X3, X4 = 40, 320, 720, 1160, 1560
d4.caja("rt", "component", "Enrutador - app.routes.ts (carga diferida)", X2, 40, 340, 80)
d4.caja("gd", "component", "Guards - auth.guards.ts (público, autenticado, por rol)", X1, 40, 320, 80, "guard")
d4.caja("sh", "component", "AppShell - core/layouts (menú por rol)", X3, 40, 300, 80)
d4.caja("pg", "component", f"Páginas por rol - features/*/pages ({n_pag} vistas)", X2, 200, 340, 110, "view")
d4.caja("sa", "component", f"Servicios API - features/*/services ({n_api_srv} servicios)", X2, 400, 340, 90, "service")
d4.caja("se", "component", "SessionService (token y usuario en localStorage)", X1, 400, 320, 90, "service")
d4.caja("as", "component", "ApiService - core/services/api.service.ts", X2, 570, 340, 80, "service")
d4.caja("hc", "component", "HttpClient + authInterceptor (app.config.ts)", X2, 730, 340, 80)
d4.caja("api", "interface", "API REST /api (backend)", X2 + 40, 890, 260, 70)
d4.caja("of", "component", "Servicios offline - cola, catálogo y sincronización (core/services)", X3, 400, 300, 90, "service")
d4.caja("ids", "component", "IndexedDbService", X3, 570, 300, 80, "service")
d4.caja("idb", "component", "IndexedDB (navegador)", X4, 570, 240, 80, "datastore")
d4.caja("pw", "component", "PwaService (instalar / actualizar)", X3, 200, 300, 80, "service")
d4.caja("sw", "component", "Service Worker (ngsw-worker.js)", X4, 200, 240, 80)
d4.caja("stc", "component", "Pago con tarjeta - stripe-card-payment.component", X1, 570, 320, 80)
d4.caja("psh", "component", "NotificationPushService", X1, 730, 320, 80, "service")
d4.caja("dcp", "component", "Vestidor en tiempo real - public/decart-try-on.html", X1, 890, 320, 80)
d4.caja("str", "component", "Stripe", X0, 570, 220, 80, "external")
d4.caja("fcm", "component", "Firebase Cloud Messaging", X0, 730, 220, 80, "external")
d4.caja("dec", "component", "Decart AI", X0, 890, 220, 80, "external")
d4.recta("rt", "L", "gd", "R", "use", "canActivate")
d4.recta("rt", "R", "sh", "L", "use", "layout de /app")
d4.recta("rt", "B", "pg", "T", "use", "loadComponent")
d4.recta("gd", "B", "se", "T", "use", "lee sesión y rol", fa=0.5)
d4.recta("pg", "B", "sa", "T", "use", "llaman a sus servicios")
d4.recta("sa", "B", "as", "T", "use", "inject(ApiService)")
d4.recta("as", "B", "hc", "T", "use", "HttpClient")
d4.recta("hc", "B", "api", "T", "use", "HTTPS REST/JSON + JWT")
d4.linea("hc", "se", "use", "authInterceptor: token", [(X2, 790), (690, 790), (690, 470), (X1 + 320, 470)])
for k, y, lane, lab in [("stc", 225, 650, "carrito"), ("psh", 255, 665, "notificaciones"), ("dcp", 285, 680, "probador")]:
    yt = d4.el[k]["b"][1] + 40
    d4.linea("pg", k, "use", lab, [(X2, y), (lane, y), (lane, yt), (X1 + 320, yt)])
d4.recta("stc", "L", "str", "R", "use", "Stripe.js")
d4.recta("psh", "L", "fcm", "R", "use", "firebase/messaging")
d4.recta("dcp", "L", "dec", "R", "use", "@decartai/sdk (WebRTC)")
d4.recta("pg", "R", "pw", "L", "use", "instalar / actualizar", fa=(240 - 200) / 110)
d4.recta("pw", "R", "sw", "L", "use", "SwUpdate")
d4.linea("pg", "of", "use", "caja del cajero", [(X2 + 340, 290), (1110, 290), (1110, 445), (X3, 445)])
d4.recta("of", "B", "ids", "T", "use", "guarda")
d4.recta("ids", "R", "idb", "L", "use", "indexedDB.open")
d4.linea("of", "hc", "use", "sincroniza (HttpClient)", [(X3, 475), (1130, 475), (1130, 770), (X2 + 340, 770)])

# ================================================================ 5) app movil Flutter
d5 = Diagrama("Componentes de la app móvil (Flutter)", "Component")
d5.caja("app", "component", "App - main.dart, app/app.dart, app/routes.dart", X2, 40, 340, 80)
d5.caja("pg", "component", f"Páginas - features/*/*_page.dart ({m_pag} vistas, {m_feat} funcionalidades)", X2, 200, 340, 110, "view")
d5.caja("wg", "component", "Widgets compartidos - shared/widgets", X1, 215, 320, 80)
d5.caja("ct", "component", f"Controladores - features/*/*_controller.dart ({m_ctl})", X2, 400, 340, 90, "controller")
d5.caja("ss", "component", "SessionStorage - core/storage", X1, 400, 320, 90, "service")
d5.caja("ap", "component", f"APIs por funcionalidad - features/*/*_api.dart ({m_api})", X2, 570, 340, 90, "service")
d5.caja("cl", "component", "ApiClient - core/network (Dio)", X2, 740, 340, 80, "service")
d5.caja("api", "interface", "API REST /api (backend)", X2 + 40, 900, 260, 70)
d5.caja("of", "component", "Servicios offline - core/offline (cola y catálogo)", X3, 400, 300, 90, "service")
d5.caja("ps", "component", "NotificationPushService", X3, 200, 300, 80, "service")
d5.caja("sec", "component", "flutter_secure_storage (Keystore del dispositivo)", X0, 1030, 300, 80, "datastore")
d5.caja("fcm", "component", "Firebase Cloud Messaging", X4, 200, 240, 80, "external")
d5.caja("str", "component", "Stripe", X4, 40, 240, 80, "external")
d5.caja("dec", "component", "Decart AI", X4, 400, 240, 90, "external")
d5.recta("app", "B", "pg", "T", "use", "rutas")
d5.linea("app", "ps", "use", "inicializa", [(X2 + 340, 100), (1310, 100), (1310, 200)])
d5.recta("ps", "R", "fcm", "L", "use", "firebase_messaging")
d5.recta("pg", "L", "wg", "R", "use", "usan")
d5.recta("pg", "B", "ct", "T", "use", "escuchan y llaman")
d5.recta("ct", "B", "ap", "T", "use", "llaman")
d5.linea("pg", "ap", "use", "algunas páginas llaman directo", [(X2, 300), (680, 300), (680, 615), (X2, 615)])
d5.recta("ap", "B", "cl", "T", "use", "ApiClient")
d5.recta("cl", "B", "api", "T", "use", "HTTPS REST/JSON + token Bearer")
d5.recta("ct", "L", "ss", "R", "use", "guarda la sesión (AuthController)")
d5.linea("ss", "sec", "use", "lee y escribe", [(X1 + 160, 490), (X1 + 160, 1070), (X0 + 300, 1070)])
d5.linea("pg", "of", "use", "cola offline", [(X2 + 340, 290), (1100, 290), (1100, 445), (X3, 445)])
d5.linea("of", "cl", "use", "sincroniza", [(X3, 475), (1120, 475), (1120, 780), (X2 + 340, 780)])
d5.linea("of", "sec", "use", "guarda la cola", [(X3 + 150, 490), (X3 + 150, 1090), (X0 + 300, 1090)])
d5.linea("pg", "str", "use", "flutter_stripe (checkout)", [(X2 + 340, 220), (1080, 220), (1080, 60), (X4, 60)])
d5.linea("pg", "dec", "use", "WebView (probador)", [(X2 + 340, 250), (1140, 250), (1140, 340), (1500, 340), (1500, 445), (X4, 445)])

# ================================================================ 6..11) componentes por módulo (trazados del código)
import componentes_modulo as CM  # noqa: E402

RANGOS = {"M1": "CU1–CU4, CU26–CU28", "M2": "CU5–CU10", "M3": "CU11–CU12", "M4": "CU13–CU14", "M5": "CU15–CU19",
          "M6": "CU20–CU25, CU29–CU30"}
BH, BGAP, TOP = 44, 16, 110          # alto de caja, separación y comienzo de las cajas
PASO_CARRIL = 9


def diagrama_modulo(code, m):
    d = Diagrama(f"Componentes del módulo {code}: {m['nombre']} ({RANGOS[code]})", "Component",
                 "Trazado del código: componentes Angular del trazado de cada caso de uso, rutas FastAPI que atienden sus "
                 "llamadas HTTP, servicios que esas rutas invocan y clases SQLAlchemy que esos servicios usan.")
    vistas = sorted(m["vistas"], key=lambda v: (v in CM.FRONT_CONTROLS, v))
    rutas = sorted(m["rutas"])
    servs = sorted(m["servicios"])
    mods = sorted(m["modelos"])
    locs = sorted(m["locales"])
    e = m["edges"]
    # líneas por hueco entre columnas (para dar ancho a los carriles)
    misma_col = [(a, b) for a, b in e["vr"] if b in CM.FRONT_CONTROLS]
    g0 = [(a, b) for a, b in e["vr"] if b not in CM.FRONT_CONTROLS] + sorted(e["vl"])
    g1, g2 = sorted(e["rs"]), []          # servicio -> modelo: una línea por servicio al bloque Modelo
    W = [310, 300, 300, 600]          # el bloque Modelo lleva las clases en dos columnas
    gaps = [60 + PASO_CARRIL * len(g) for g in (g0, g1, g2)]
    izq = 40 + 20 + PASO_CARRIL * len(misma_col)
    xs = [izq]
    for i in range(3):
        xs.append(xs[-1] + W[i] + gaps[i])
    cols = [(vistas, "v", "view"), (rutas + locs, "r", "controller"), (servs, "s", "service"), (mods, "m", "entity")]
    ident = {}
    alto = 0
    grado = {}
    for a, b in list(g0) + list(g1) + list(g2) + misma_col:
        grado[a] = grado.get(a, 0) + 1
        grado[b] = grado.get(b, 0) + 1
    for c, (items, pref, st) in enumerate(cols):
        y = TOP
        for k, it in enumerate(items):
            h = max(BH, 8 * grado.get(it, 0) + 14)
            if k:
                y = ultimo + BGAP
            ultimo = y + h
            if c == 0:
                nombre = it if it not in CM.FRONT_CONTROLS else f"{it} (frontend/core/services)"
                tipo = "service" if it in CM.FRONT_CONTROLS else "view"
            elif c == 1 and it in locs:
                nombre, tipo = it, "datastore"
            elif c == 1:
                nombre, tipo = f"app/routes/{it}.py", "controller"
            elif c == 2:
                nombre, tipo = f"app/services/{it.replace('.', '/')}.py", "service"
            else:
                nombre, tipo = f"{it} ({AC.CLASS_TABLE[it]})", "entity"
            if c == 3:      # sin líneas propias: grilla de dos columnas
                x_b, y, w_b, h = xs[3] + (k % 2) * 310, TOP + (k // 2) * (BH + BGAP), 290, BH
            else:
                x_b, w_b = xs[c], W[c]
            ident[(c, it)] = d.caja(f"{pref}{k}", "component", nombre, x_b, y, w_b, h, tipo)
            alto = max(alto, y + h)
    titulos = ["Vista - Angular (frontend/src/app)", "Controlador - rutas FastAPI (backend/app/routes)",
               "Servicio - lógica de negocio (backend/app/services)", "Modelo - clases SQLAlchemy (backend/app/models)"]
    if locs:
        titulos[1] = "Controlador - rutas FastAPI (backend/app/routes) y almacenes locales del navegador"
    for c in range(4):
        d.caja(f"f{c}", "frame", titulos[c], xs[c] - 15, 40, W[c] + 30, alto - 40 + 30)

    def col_de(nombre, cands):
        for c in cands:
            if (c, nombre) in ident:
                return c
        raise KeyError(nombre)

    # puertos: cada línea tiene su propio punto en el lado de la caja (ordenados por la altura del otro extremo)
    def y_caja(c, n):
        return d.el[ident[(c, n)]]["b"][1]

    lineas = [(0, a, col_de(b, (1,)), b) for a, b in g0] + [(1, a, 2, b) for a, b in g1] + [(2, a, 3, b) for a, b in g2]
    salida, entrada = {}, {}
    for ca, a, cb, b in lineas:
        salida.setdefault((ca, a), []).append((cb, b))
        entrada.setdefault((cb, b), []).append((ca, a))
    py = {}
    for (c, n), otros in salida.items():
        otros.sort(key=lambda o: y_caja(*o))
        bx, by, bw, bh = d.el[ident[(c, n)]]["b"]
        for i, o in enumerate(otros):
            py[("s", c, n, o)] = by + bh * (i + 1) / (len(otros) + 1)
    for (c, n), otros in entrada.items():
        otros.sort(key=lambda o: y_caja(*o))
        bx, by, bw, bh = d.el[ident[(c, n)]]["b"]
        for i, o in enumerate(otros):
            py[("e", c, n, o)] = by + bh * (i + 1) / (len(otros) + 1)
    carril = {0: 0, 1: 0, 2: 0}
    usadas = {0: set(), 1: set(), 2: set()}      # alturas de tramos horizontales ya usadas en cada hueco

    def libre(hueco, y, c, n):
        bx, by, bw, bh = d.el[ident[(c, n)]]["b"]
        for delta in (0, 3, -3, 6, -6, 9, -9, 12, -12, 15, -15):
            yy = round(y + delta)
            if by + 3 <= yy <= by + bh - 3 and all(abs(yy - u) > 2 for u in usadas[hueco]):
                usadas[hueco].add(yy)
                return yy
        raise SystemExit(f"{d.nombre}: sin altura libre para {n}")

    for ca, a, cb, b in sorted(lineas, key=lambda l: (l[0], py[("s", l[0], l[1], (l[2], l[3]))])):
        ys = libre(ca, py[("s", ca, a, (cb, b))], ca, a)
        ye = libre(ca, py[("e", cb, b, (ca, a))], cb, b) if abs(py[("e", cb, b, (ca, a))] - ys) > 0.5 else ys
        x0 = xs[ca] + W[ca]
        xl = x0 + 30 + PASO_CARRIL * carril[ca]
        carril[ca] += 1
        pts = [(x0, ys), (xs[cb], ys)] if ys == ye else [(x0, ys), (xl, ys), (xl, ye), (xs[cb], ye)]
        d.linea(ident[(ca, a)], ident[(cb, b)], "use", "", pts)
    # servicio -> bloque Modelo: una línea recta por servicio (el detalle de clases va en la tabla del documento)
    for k, sv in enumerate(servs):
        bx, by, bw, bh = d.el[ident[(2, sv)]]["b"]
        y = round(by + bh / 2)
        d.linea(ident[(2, sv)], "f3", "use", "", [(bx + bw, y), (xs[3] - 15, y)])
    # vista -> servicio del frontend (misma columna): por carriles a la izquierda de la columna
    for k, (a, b) in enumerate(sorted(misma_col)):
        ia, ib = ident[(0, a)], ident[(0, b)]
        ya = d.el[ia]["b"][1] + BH * (0.3 + 0.4 * (k % 2))
        yb = d.el[ib]["b"][1] + BH * (0.2 + 0.6 * k / max(1, len(misma_col)))
        xl = xs[0] - 15 - PASO_CARRIL * (k + 1)
        d.linea(ia, ib, "use", "", [(xs[0], round(ya)), (xl, round(ya)), (xl, round(yb)), (xs[0], round(yb))])
    return d


MODULO_DIAGRAMAS = [diagrama_modulo(code, m) for code, m in CM.modulos().items()]

if __name__ == "__main__":
    diagramas = [d.modelo() for d in (d1, d2, d3, d4, d5, *MODULO_DIAGRAMAS)]
    for d in diagramas:
        print(f"{d['name']}: {len(d['elements'])} elementos, {len(d['links'])} lineas")
    model = {"diagrams": diagramas}
    tpl = (HERE / "plantilla_arquitectura.js").read_text(encoding="utf-8")
    js = "var MODEL = " + json.dumps(model, ensure_ascii=True) + ";\n"
    (HERE / "FashionStore_arquitectura.js").write_text(tpl.replace("/*MODEL*/\n", js), encoding="utf-8")
    print("OK: FashionStore_arquitectura.js generado")
