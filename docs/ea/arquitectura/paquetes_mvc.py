"""Diagramas de componentes de los paquetes Backend, Frontend web y App móvil en el estilo Vista / Control / Modelo /
Conexión (el mismo de la referencia y de los diagramas general y por módulo).

Para que se lean (unas 15 líneas, sin cruces) cada diagrama muestra solo los flujos principales de la aplicación,
uno por columna: Vista -> Control -> Modelo -> Conexión. Los flujos se eligen aquí, pero cada línea se comprueba en el
código; si una dependencia ya no existe, el script falla en vez de dibujar algo falso.

App móvil (mobile/lib)
  Vista: pantalla *_page.dart · Control: controlador o servicio que la pantalla importa · Modelo: *_models.dart que
  importa el control · Conexión: API REST /api (modelos que llegan por la API) o flutter_secure_storage (modelos que
  se guardan en el dispositivo).
Frontend web (frontend/src/app)
  Vista: componente Angular · Control: servicio que el componente inyecta · Modelo: *.model.ts que importa el servicio ·
  Conexión: API REST /api o IndexedDB (servicios offline).
Backend FastAPI (backend/app)
  Vista: esquema Pydantic que importa la ruta (el JSON que responde) · Control: ruta FastAPI · Modelo: entidad con la
  que trabaja la ruta en los diagramas de secuencia · Conexión: PostgreSQL y las APIs externas que usa la ruta.
"""
import re

import componentes_modulo as CM

ST_V, ST_C, ST_M, ST_X = "Componente:Vista", "Componente:Control", "Componente:Model", "conexion"
ROOT = CM.ROOT
MOB, BACK = ROOT / "mobile" / "lib", ROOT / "backend" / "app"
T = CM.T

# ---------------------------------------------------------------- flujos principales (uno por columna)
MOVIL = [   # pantalla, archivo del control, archivo de modelos, conexión
    ("login_page.dart", "auth_controller.dart", "auth_models.dart", "rest"),
    ("catalog_page.dart", "catalog_controller.dart", "catalog_models.dart", "rest"),
    ("cart_page.dart", "cart_controller.dart", "cart_models.dart", "rest"),
    ("checkout_page.dart", "order_controller.dart", "order_models.dart", "rest"),
    ("offline_queue_page.dart", "offline_queue_service.dart", "offline_queue_models.dart", "sec"),
]
FRONTEND = [   # componente, servicio, modelo (None: el servicio no tiene modelo propio), conexiones
    ("TenantManagementPageComponent", "TenantApiService", "tenant.model", ["rest"]),
    ("CatalogPageComponent", "CatalogApiService", "catalog.model", ["rest"]),
    ("CartPageComponent", "CartApiService", "cart.model", ["rest"]),
    ("AdminReportsPageComponent", "ReportsApiService", "report.model", ["rest"]),
    ("CajaPageComponent", "OfflineQueueService", None, ["idb", "rest"]),
]
BACKEND = [   # esquema, ruta, entidad, módulo
    ("rbac_schema", "rbac_routes", "Rol", "M1"),
    ("catalog_schema", "catalog_routes", "Producto", "M2"),
    ("report_schema", "report_routes", "Venta", "M2"),
    ("cart_schema", "cart_routes", "Carrito", "M5"),
    ("gift_card_schema", "gift_card_routes", "TarjetaRegalo", "M5"),
]


def _clase(path):
    """Clase principal de un archivo Dart: la que se llama como el archivo; si no, la primera clase pública widget."""
    nombre = "".join(p.capitalize() for p in path.stem.split("_"))
    texto = path.read_text(encoding="utf-8")
    if re.search(rf"^class {nombre}\b", texto, re.M):
        return nombre
    m = re.search(r"^class ([A-Z]\w*) extends (?:StatelessWidget|StatefulWidget)\b", texto, re.M)
    assert m, f"sin clase principal en {path}"
    return m.group(1)


def _imports_dart(path):
    return {re.sub(r".*/", "", m) for m in re.findall(r"^import '([^']+)'", path.read_text(encoding="utf-8"), re.M)}


def _dart(nombre):
    hits = list(MOB.rglob(nombre))
    assert len(hits) == 1, nombre
    return hits[0]


def _conexiones(usadas, nombres):
    return [(f"x_{k}", nombres[k], ST_X, True) for k in nombres if k in usadas]


# ---------------------------------------------------------------- app móvil
def movil():
    vistas, controles, modelos, aristas = [], [], [], []
    apis = list(MOB.glob("features/*/*_api.dart"))
    for pagina, control, modelo, conex in MOVIL:
        p, c, m = _dart(pagina), _dart(control), _dart(modelo)
        assert control in _imports_dart(p), f"{pagina} no usa {control}"
        assert modelo in _imports_dart(c), f"{control} no usa {modelo}"
        if conex == "rest":       # los modelos que llegan por la API: los importa un *_api.dart
            assert any(modelo in _imports_dart(a) for a in apis), f"{modelo} no llega por la API"
        else:                     # los que se guardan en el dispositivo
            assert "flutter_secure_storage.dart" in _imports_dart(c), f"{control} no usa flutter_secure_storage"
        vistas.append((f"v_{p.stem}", f"V.{_clase(p)}", ST_V, False))
        controles.append((f"c_{c.stem}", _clase(c), ST_C, False))
        modelos.append((f"m_{m.stem}", f"M.{modelo}", ST_M, False))
        aristas += [(f"c_{c.stem}", f"v_{p.stem}"), (f"c_{c.stem}", f"m_{m.stem}"), (f"m_{m.stem}", f"x_{conex}")]
    conex = _conexiones({b[2:] for _, b in aristas if b.startswith("x_")},
                        {"rest": "HTTPS / API REST /api (FastAPI)",
                         "sec": "flutter_secure_storage (almacenamiento seguro del dispositivo)"})
    return [vistas, controles, modelos, conex], aristas


# ---------------------------------------------------------------- frontend web
def _modelos_ts(cls):
    return set(re.findall(r"from '[^']*/models/([\w.-]+)'", cls.text))


def frontend():
    vistas, controles, modelos, aristas = [], [], [], []
    for comp, serv, modelo, conex in FRONTEND:
        c, s = T.TS[comp], T.TS[serv]
        assert serv in c.fields.values(), f"{comp} no inyecta {serv}"
        usa = set(s.fields.values())
        vistas.append((f"v_{comp}", f"V.{comp}", ST_V, False))
        controles.append((f"c_{serv}", serv, ST_C, False))
        aristas.append((f"c_{serv}", f"v_{comp}"))
        if modelo:
            assert modelo in _modelos_ts(s), f"{serv} no usa {modelo}"
            assert {"ApiService", "HttpClient"} & usa, f"{serv} no llama a la API"
            modelos.append((f"m_{modelo}", f"M.{modelo}", ST_M, False))
            aristas += [(f"c_{serv}", f"m_{modelo}")] + [(f"m_{modelo}", f"x_{k}") for k in conex]
        else:                     # servicio sin modelo propio: se une directo a lo que usa
            for k in conex:
                assert {"idb": "IndexedDbService", "rest": "HttpClient"}[k] in usa, f"{serv} no usa {k}"
                aristas.append((f"c_{serv}", f"x_{k}"))
    conex = _conexiones({b[2:] for _, b in aristas if b.startswith("x_")},
                        {"rest": "HTTPS / API REST /api (ApiService · HttpClient)", "idb": "IndexedDB (navegador)"})
    return [vistas, controles, modelos, conex], aristas


# ---------------------------------------------------------------- backend
def backend():
    mods = CM.modulos()
    vistas, controles, modelos, aristas, externos = [], [], [], [], []
    for esquema, ruta, entidad, code in BACKEND:
        src = (BACK / "routes" / f"{ruta}.py").read_text(encoding="utf-8")
        assert re.search(rf"from app\.schemas\.{esquema} import", src), f"{ruta} no usa {esquema}"
        assert (ruta, entidad) in mods[code]["edges"]["cm"], f"{ruta} no trabaja con {entidad} en {code}"
        vistas.append((f"v_{esquema}", f"V.{esquema}", ST_V, False))
        controles.append((f"c_{ruta}", ruta, ST_C, False))
        modelos.append((f"m_{entidad}", f"M.{entidad}", ST_M, False))
        aristas += [(f"c_{ruta}", f"v_{esquema}"), (f"c_{ruta}", f"m_{entidad}"), (f"m_{entidad}", "x_pg")]
        hs = {h for h in mods[code]["handlers"] if h.startswith(f"routes.{ruta}.")}
        for e in sorted(CM.externos_de(hs)):                     # APIs externas que usa el código de la ruta
            if e not in externos:
                externos.append(e)
            aristas.append((f"c_{ruta}", f"x_{externos.index(e)}"))
    conex = [("x_pg", "PostgreSQL", ST_X, True)] + [(f"x_{i}", e, ST_X, False) for i, e in enumerate(externos)]
    return [vistas, controles, modelos, conex], aristas


if __name__ == "__main__":
    for nombre, fn in (("movil", movil), ("frontend", frontend), ("backend", backend)):
        filas, aristas = fn()
        print(nombre, [len(f) for f in filas], "lineas", len(aristas))
        for f in filas:
            print("   ", [n for _, n, _, _ in f])
