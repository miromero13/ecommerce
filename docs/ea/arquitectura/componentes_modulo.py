"""Componentes por módulo (paquete de casos de uso) en el estilo Vista / Control / Modelo / Conexión.

Se toman de los diagramas de secuencia (docs/ea/secuencia/secuencia.json), que ya están trazados del código:
  Vista   : objetos frontera (componentes Angular) que llaman a un control.
  Control : rutas FastAPI y servicios del frontend (offline / PWA) que reciben esas llamadas.
  Modelo  : entidades con las que un control interactúa (nombres del modelo de dominio).
  Conexión: PostgreSQL para las entidades del backend; IndexedDB para las entidades locales del navegador
            (las que se leen y escriben con STORES.* en los servicios offline).
Las líneas son las mismas llamadas de los diagramas de secuencia:
  control -> vista (la vista llama al control), control -> control, control -> modelo, modelo -> conexión.

Para el diagrama general también se calcula, desde el código:
  qué módulos usa la app móvil (rutas que llama mobile/lib) y qué servicios externos usa cada módulo
  (funciones del backend alcanzables desde las rutas de sus casos de uso que llaman a Stripe, Gemini, etc.).
Nada se escribe a mano: si algo no existe en el código, el script falla.
"""
import ast
import contextlib
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "comunicacion"))
with contextlib.redirect_stdout(io.StringIO()):
    import trazar as T  # noqa: E402
AC = T.AC
SEQ = {d["cu"]: d for d in json.loads((HERE.parent / "secuencia" / "secuencia.json").read_text(encoding="utf-8"))["diagrams"]}

# Servicio externo -> lo que lo identifica dentro de una función del backend.
EXTERNOS = {
    "Stripe": r"\bstripe\.(PaymentIntent|Webhook|Refund|checkout)\b",
    "Google Gemini": r"\bgenai\.Client\(",
    "Hugging Face Space": r"\bgradio_client\b",
    "Firebase Cloud Messaging": r"\bmessaging\.send\(",
    "Mailtrap": r"\bemail_service\.send_\w+|\bmailer\.send_\w+",
    "Cloudinary": r"\buploader\.(upload|destroy)\(",
}


def modulos():
    out = {}
    for code in sorted(AC.MODULOS):
        nombre, cus = AC.MODULOS[code]
        vistas, controles, modelos, locales, handlers = [], [], [], set(), set()
        cv, cc, cm = set(), set(), set()

        def agregar(lista, x):
            if x not in lista:
                lista.append(x)

        for cu in cus:
            d = SEQ[cu]
            objs = d["objs"]
            for m in d["msgs"]:
                if m["ret"]:
                    continue
                a, b = m["from"], m["to"]
                an, bn = objs[a]["name"], objs[b]["name"]
                if a.startswith("bnd:") and b.startswith("ctl:"):
                    agregar(vistas, an); agregar(controles, bn); cv.add((bn, an))
                if a.startswith("ctl:") and b.startswith("ctl:") and a != b:
                    agregar(controles, an); agregar(controles, bn); cc.add((an, bn))
                if a.startswith("ctl:") and b.startswith("ent:"):
                    agregar(controles, an); agregar(modelos, bn); cm.add((an, bn))
                    if "STORES." in m["label"]:
                        locales.add(bn)
                if b.startswith("ctl:") and a != b and bn not in T.TS:     # llamada HTTP a una ruta FastAPI
                    clave = f"routes.{bn}.{m['label'].split('(')[0]}"
                    assert clave in AC.FUNCS, f"{cu}: no existe {clave}"
                    handlers.add(clave)
        out[code] = {"nombre": nombre, "cus": cus, "vistas": vistas, "controles": controles, "modelos": modelos,
                     "locales": locales, "handlers": handlers, "edges": {"cv": cv, "cc": cc, "cm": cm}}
    return out


def _referencias(f):
    """Funciones del backend que f llama o pasa como argumento: asyncio.to_thread(_generar, ...) o
    background_tasks.add_task(service.send_gift_card_email, ...)."""
    refs = {c for c in f.calls if c in AC.FUNCS}
    for n in ast.walk(f.node):
        if isinstance(n, ast.Name) and f"{f.module}.{n.id}" in AC.FUNCS:
            refs.add(f"{f.module}.{n.id}")
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
            cands = [k for k in AC.FUNCS if k.startswith("services.") and k.endswith("." + n.attr)]
            if len(cands) == 1:          # solo si el nombre identifica una única función de servicio
                refs.add(cands[0])
    return refs


def externos_de(handlers, profundidad=6):
    """Servicios externos que usan las funciones alcanzables desde estas rutas."""
    vistos, frente, usados = set(), set(handlers), set()
    for _ in range(profundidad + 1):
        nuevo = set()
        for k in frente - vistos:
            vistos.add(k)
            texto = ast.unparse(AC.FUNCS[k].node)
            for ext, patron in EXTERNOS.items():
                if re.search(patron, texto):
                    usados.add(ext)
            nuevo |= _referencias(AC.FUNCS[k])
        frente = nuevo
    return usados


def rutas_movil():
    """Módulos de rutas FastAPI que llama la app móvil (llamadas del cliente Dio en mobile/lib)."""
    rx = re.compile(r"\.(get|post|put|patch|delete)\s*(?:<[^>]*>)?\s*\(\s*['\"]([^'\"]+)['\"]", re.S)
    modulos_r = set()
    for f in (ROOT / "mobile" / "lib").rglob("*.dart"):
        for verbo, ruta in rx.findall(f.read_text(encoding="utf-8")):
            ruta = "/" + re.sub(r"\$\{[^}]*\}|\$\w+", "{}", ruta).lstrip("/")
            r = T.match_route(verbo, ruta)
            assert r, f"{f.name}: {verbo.upper()} {ruta} no coincide con ninguna ruta del backend"
            modulos_r.add(r["module"])
    return modulos_r


if __name__ == "__main__":
    movil = rutas_movil()
    for code, m in modulos().items():
        print(code, m["nombre"], "| vistas", len(m["vistas"]), "controles", len(m["controles"]),
              "modelos", len(m["modelos"]), "locales", sorted(m["locales"]),
              "| lineas", {k: len(v) for k, v in m["edges"].items()},
              "| externos", sorted(externos_de(m["handlers"])),
              "| movil", sorted(set(m["controles"]) & movil))
