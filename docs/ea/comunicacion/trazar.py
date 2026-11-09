"""Traza desde el codigo los mensajes de cada caso de uso para los diagramas de comunicacion (ICONIX).

Cadena (todo leido del codigo, nada escrito a mano salvo que pantalla y que endpoints pertenecen a cada CU):
  actor -> interfaz      : metodo del componente Angular que dispara el usuario (template / ngOnInit)
  interfaz -> control    : funcion de la ruta FastAPI que atiende la llamada HTTP de ese metodo
  control -> entidad     : funciones de servicio que llama la ruta (y las que estas llaman, 1 nivel), dirigidas a la
                           entidad que crean o consultan: la misma asignacion de operaciones del modelo de dominio.
Regla ICONIX: una entidad nunca llama a otra; solo los controles hablan con las entidades.
"""
import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FRONT = ROOT / "frontend" / "src" / "app"
BACK = ROOT / "backend" / "app"
sys.path.insert(0, str(HERE.parent / "modelo_dominio"))
import io, contextlib  # noqa: E402
with contextlib.redirect_stdout(io.StringIO()):
    import analizar_codigo as AC  # noqa: E402  (FUNCS, CLASS_TABLE, ENTRADAS)
from generar_dominio import NOMBRE  # noqa: E402

# ----------------------------------------------------------------------------- backend: rutas HTTP
ROUTES = []   # {verb, path, module, handler, params}
SKIP_PARAMS = {"db", "request", "response", "background_tasks", "current_user", "tenant_id_dep", "_"}
for path in sorted((BACK / "routes").glob("*.py")):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    prefix = ""
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "APIRouter":
            for kw in n.keywords:
                if kw.arg == "prefix":
                    prefix = kw.value.value
    for n in tree.body:
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in n.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr in (
                    "get", "post", "put", "patch", "delete"):
                sub = dec.args[0].value if dec.args else ""
                args = n.args.args
                defaults = [None] * (len(args) - len(n.args.defaults)) + list(n.args.defaults)
                params = []
                for a, dft in zip(args, defaults):
                    if a.arg in SKIP_PARAMS:
                        continue
                    if isinstance(dft, ast.Call) and getattr(dft.func, "id", "") == "Depends":
                        continue
                    params.append(a.arg)
                ROUTES.append({"verb": dec.func.attr, "path": prefix + sub, "module": path.stem,
                               "handler": n.name, "params": params, "key": f"routes.{path.stem}.{n.name}"})


def _segs(p):
    p = p.split("?")[0].rstrip("/")
    segs = [s for s in p.split("/") if s != ""]
    if segs and segs[0] == "{}":            # ${apiUrl}/... : la URL base al inicio
        segs = segs[1:]
    if segs and segs[-1].endswith("{}") and segs[-1] != "{}":   # /dashboard${query}: parametros de consulta
        segs[-1] = segs[-1][:-2]
    return segs


def match_route(verb, fpath):
    fs = _segs(fpath)
    best = None
    for r in ROUTES:
        if r["verb"] != verb:
            continue
        bs = _segs(r["path"])
        if len(bs) != len(fs):
            continue
        score, ok = 0, True
        for b, f in zip(bs, fs):
            if b.startswith("{"):
                continue
            if f == "{}":
                continue
            if b != f:
                ok = False
                break
            score += 1
        if ok and (best is None or score > best[0]):
            best = (score, r)
    return best[1] if best else None


# ----------------------------------------------------------------------------- frontend: clases TS
METHOD_RX = re.compile(r"^\s*(?:(?:public|protected|private|static|readonly|override)\s+)*(?:async\s+)?"
                       r"(\w+)\s*(?:<[^>]*>)?\(([^)]*)\)[^\n=]*\{[ \t]*$", re.M)


def _body(text, start):
    depth, i = 0, start
    while i < len(text):
        c = text[i]
        if text.startswith("//", i):          # comentario de linea: un apostrofo en el texto no abre cadena
            i = text.find("\n", i)
            i = len(text) if i < 0 else i
            continue
        if text.startswith("/*", i):
            i = text.find("*/", i + 2)
            i = len(text) if i < 0 else i + 2
            continue
        if c in "'\"`":
            q = c
            i += 1
            while i < len(text) and text[i] != q:
                i += 2 if text[i] == "\\" else 1
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    return text[start:]


class TsClass:
    def __init__(self, path):
        self.path = path
        self.text = path.read_text(encoding="utf-8")
        m = re.search(r"export class (\w+)", self.text)
        self.name = m.group(1) if m else path.stem
        self.fields = {}
        for fm in re.finditer(r"(?:private|protected|public|readonly)\s+(?:readonly\s+)?(\w+)\s*=\s*inject\((\w+)\)", self.text):
            self.fields[fm.group(1)] = fm.group(2)
        for fm in re.finditer(r"(?:private|protected|public)\s+(?:readonly\s+)?(\w+)\s*:\s*(\w+)", self.text):
            self.fields.setdefault(fm.group(1), fm.group(2))
        self.methods = {}
        for mm in METHOD_RX.finditer(self.text):
            name = mm.group(1)
            if name in ("if", "for", "while", "switch", "catch", "function", "return"):
                continue
            params = [p.split(":")[0].split("=")[0].strip().lstrip(".").rstrip("?") for p in mm.group(2).split(",") if p.strip()]
            # el cuerpo empieza en la ULTIMA llave de la firma (el tipo de retorno puede tener llaves)
            body = _body(self.text, self.text.rfind("{", mm.start(), mm.end()))
            self.methods.setdefault(name, {"params": params, "body": body, "pos": mm.start()})
        self.endpoint = None
        em = re.search(r"endpoint\s*=\s*'([^']+)'", self.text)
        if em:
            self.endpoint = em.group(1)
        html = path.with_suffix(".html")
        self.template = html.read_text(encoding="utf-8") if html.exists() else self.text


TS = {}
for p in FRONT.rglob("*.ts"):
    if p.name.endswith(".spec.ts"):
        continue
    c = TsClass(p)
    TS[c.name] = c

API_RX = re.compile(r"this\.(?:api|http)\.(get|post|put|patch|delete)\s*(?:<[^(]*?>)?\(\s*([`'])(.*?)\2", re.S)


def api_calls_of(cls, method, seen=None, depth=0):
    """Llamadas HTTP (verb, path) que hace un metodo, siguiendo metodos propios y de servicios inyectados."""
    seen = seen or set()
    key = (cls.name, method)
    if key in seen or method not in cls.methods or depth > 4:
        return []
    seen.add(key)
    body = cls.methods[method]["body"]
    out = []
    events = []
    for m in API_RX.finditer(body):
        path = m.group(3).replace("${this.endpoint}", cls.endpoint or "")
        path = re.sub(r"\$\{[^}]*\}", "{}", path)
        events.append((m.start(), ("http", m.group(1), path)))
    for m in re.finditer(r"this\.(\w+)\.(\w+)\s*\(", body):
        f, meth = m.group(1), m.group(2)
        if f in cls.fields and cls.fields[f] in TS:
            events.append((m.start(), ("svc", TS[cls.fields[f]], meth)))
    for m in re.finditer(r"this\.(\w+)\s*\(", body):
        if m.group(1) in cls.methods and m.group(1) != method:
            events.append((m.start(), ("own", cls, m.group(1))))
    for _, ev in sorted(events, key=lambda e: e[0]):
        if ev[0] == "http":
            out.append((ev[1], ev[2]))
        else:
            out.extend(api_calls_of(ev[1], ev[2], seen, depth + 1))
    return out


# ----------------------------------------------------------------------------- backend: ruta -> servicios -> entidad
def destino(fn):
    return AC.destino(fn)   # la misma regla que las operaciones del modelo de dominio


def call_order(fn):
    """Funciones de servicio que llama fn, en orden de aparicion en el codigo."""
    calls = []
    for sub in ast.walk(fn.node):
        if isinstance(sub, ast.Call):
            f = sub.func
            name = None
            imports = {}
            if isinstance(f, ast.Name):
                name = f.id
            elif isinstance(f, ast.Attribute):
                name = f.attr
            if name:
                calls.append((sub.lineno, sub.col_offset, name, sub))
    resolved = []
    for line, col, name, node in sorted(calls, key=lambda c: (c[0], c[1])):
        for k in fn.calls:
            if k.endswith("." + name) and k.startswith("services.") and k in AC.FUNCS:
                if k not in [r[0] for r in resolved]:
                    resolved.append((k, line))
    return [k for k, _ in resolved]


def label(fn):
    names, _ = fn.params()
    return f"{fn.name}({', '.join(names)})"


def entity_msgs(handler_key):
    """Mensajes control -> entidad de una ruta: servicios que llama (y 1 nivel debajo), en orden de codigo."""
    fn = AC.FUNCS[handler_key]
    msgs = []

    def add(k):
        f = AC.FUNCS[k]
        for m in destino(f):
            msg = (NOMBRE[AC.CLASS_TABLE[m]], label(f))
            if msg not in msgs:
                msgs.append(msg)

    for k in call_order(fn):
        add(k)
        for k2 in call_order(AC.FUNCS[k]):
            add(k2)
    direct = destino(fn)   # la ruta consulta un modelo directamente (sin servicio)
    return msgs, [NOMBRE[AC.CLASS_TABLE[m]] for m in direct]


if __name__ == "__main__":
    unmatched = []
    for cname, c in TS.items():
        if cname == "ApiService":
            continue
        for mname in c.methods:
            for verb, p in api_calls_of(c, mname):
                if not match_route(verb, p):
                    unmatched.append((cname, mname, verb, p))
    print("rutas backend:", len(ROUTES), "| llamadas sin ruta:", len(set((u[2], u[3]) for u in unmatched)))
    for u in sorted(set((u[2], u[3]) for u in unmatched))[:40]:
        print("  ", u)


# ----------------------------------------------------------------------------- casos de uso
EVENT_RX = re.compile(r"\((?:click|ngSubmit|change|submit|keydown\.enter|keyup\.enter|selectPlan|toggleActive|enter|view|syncNow|confirm)\)\s*=\s*\"([^\"]*)\"")


def triggers(cls):
    """Metodos que dispara el usuario (eventos de la plantilla) o la carga de la pantalla (ngOnInit)."""
    found = []
    for m in EVENT_RX.finditer(cls.template):
        for name in re.findall(r"(\w+)\s*\(", m.group(1)):
            if name in cls.methods and name not in [f[0] for f in found]:
                found.append((name, m.start() + 100000))
    init = cls.methods.get("ngOnInit") or cls.methods.get("constructor")
    if init:
        for m in re.finditer(r"this\.(\w+)\s*\(", init["body"]):
            if m.group(1) in cls.methods and m.group(1) not in [f[0] for f in found]:
                found.append((m.group(1), m.start()))
    return [f[0] for f in sorted(found, key=lambda f: f[1])]


COMPONENTS = {n: c for n, c in TS.items() if "@Component" in c.text}


def build_cu(cu):
    routes = {k for k in AC.ENTRADAS[cu] if k.startswith("routes.")}
    actions = []   # (componente, metodo, [rutas])
    for cname, c in COMPONENTS.items():
        for meth in triggers(c):
            hits = []
            for verb, p in api_calls_of(c, meth):
                r = match_route(verb, p)
                if r and r["key"] in routes and r not in hits:
                    hits.append(r)
            if hits:
                actions.append((cname, meth, hits))
    return actions


if __name__ == "__main__":
    for cu in [f"CU{i}" for i in range(1, 31)]:
        acts = build_cu(cu)
        print(f"{cu}: " + ("; ".join(f"{c}.{m} -> {','.join(r['handler'] for r in rs)}" for c, m, rs in acts) or "SIN ACCIONES"))
