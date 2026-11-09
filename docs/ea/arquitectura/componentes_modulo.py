"""Componentes por módulo (paquete de casos de uso), trazados del código.

Vista       : componentes Angular y servicios del frontend que el trazado de cada caso de uso usa
              (docs/ea/comunicacion/comunicacion.json, generado por generar_comunicacion.py desde el código).
Controlador : módulo de rutas FastAPI (app/routes) que atiende cada llamada HTTP de esa vista.
Servicio    : módulos de app/services que llaman esas funciones de ruta (análisis estático del código).
Modelo      : clases SQLAlchemy (app/models) que esas funciones de servicio consultan o modifican.
Almacén local: almacenes IndexedDB que usan los servicios offline del frontend.
Nada se escribe a mano: si una función no existe en el código, el script falla.
"""
import contextlib
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "comunicacion"))
with contextlib.redirect_stdout(io.StringIO()):
    import trazar as T  # noqa: E402
AC = T.AC
COM = json.loads((HERE.parent / "comunicacion" / "comunicacion.json").read_text(encoding="utf-8"))
POR_CU = {d["cu"]: d for d in COM["diagrams"]}
FRONT_CONTROLS = {"OfflineQueueService", "OfflineCatalogService", "PwaService", "OfflineSyncService", "OfflineCartService"}
LOCAL = {"OfflineOperation": "IndexedDB: pending_operations_queue", "OfflineCatalogProduct": "IndexedDB: cached_catalog",
         "PendingCartItem": "IndexedDB: pending_cart_items"}


def _nombres(f):
    out = set()
    for x in list(f.models) + list(f.writes) + list(f.queried):
        out.add(x[-1] if isinstance(x, tuple) else x)
    return {n for n in out if n in AC.CLASS_TABLE} if hasattr(AC, "CLASS_TABLE") else out


def modelos_de(clave):
    """Clases ORM que usa una función de servicio y las funciones de app/services que llama (un nivel)."""
    f = AC.FUNCS[clave]
    out = _nombres(f)
    for c in f.calls:
        if c.startswith("services.") and c in AC.FUNCS:
            out |= _nombres(AC.FUNCS[c])
    return out


def modulos():
    out = {}
    for code in sorted(AC.MODULOS):
        nombre, cus = AC.MODULOS[code]
        vistas, rutas, servicios, modelos, locales = set(), set(), set(), set(), set()
        e_vr, e_rs, e_sm, e_vl = set(), set(), set(), set()
        for cu in cus:
            d = POR_CU[cu]
            for m in d["msgs"]:
                a, b = m["from"], m["to"]
                an, bn = a.split(":", 1)[1], b.split(":", 1)[1]
                es_vista = a.startswith("bnd:") or (a.startswith("ctl:") and an in FRONT_CONTROLS)
                if a.startswith("bnd:"):
                    vistas.add(an)
                if es_vista and b.startswith("ctl:") and bn not in FRONT_CONTROLS:
                    vistas.add(an); rutas.add(bn); e_vr.add((an, bn))
                    handler = m["label"].split("(")[0]
                    clave = f"routes.{bn}.{handler}"
                    assert clave in AC.FUNCS, f"{cu}: no existe {clave}"
                    for c in AC.FUNCS[clave].calls:
                        if c.startswith("services.") and c in AC.FUNCS:
                            srv = c.rsplit(".", 1)[0][len("services."):]
                            servicios.add(srv); e_rs.add((bn, srv))
                            for mod in modelos_de(c):
                                modelos.add(mod); e_sm.add((srv, mod))
                if es_vista and b.startswith("ctl:") and bn in FRONT_CONTROLS:
                    vistas.add(an); vistas.add(bn); e_vr.add((an, bn)) if a.startswith("bnd:") else None
                if es_vista and b.startswith("ent:") and bn in LOCAL:
                    vistas.add(an); locales.add(LOCAL[bn]); e_vl.add((an, LOCAL[bn]))
        out[code] = {"nombre": nombre, "cus": cus, "vistas": vistas, "rutas": rutas, "servicios": servicios,
                     "modelos": modelos, "locales": locales,
                     "edges": {"vr": e_vr, "rs": e_rs, "sm": e_sm, "vl": e_vl}}
    return out


if __name__ == "__main__":
    for code, m in modulos().items():
        print(code, m["nombre"], "| vistas", len(m["vistas"]), "rutas", len(m["rutas"]), "servicios",
              len(m["servicios"]), "modelos", len(m["modelos"]), "locales", len(m["locales"]),
              "| lineas", {k: len(v) for k, v in m["edges"].items()})
