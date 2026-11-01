"""Escribe en el codigo, sobre la funcion (o la linea) que lo implementa, cada mensaje de los diagramas de secuencia:

    # [CU01 - Secuencia: Paso 1.1] TenantManagementPageComponent llama a list_tenants_route(...) de tenant_routes (GET /api/tenants)

Los retornos (flechas punteadas) se escriben junto a la misma funcion que atiende la llamada, con el texto del diagrama:

    # [CU10 - Secuencia: Paso 1.3] TrabajoImportacionRPA retorna create_job(...): RpaIngestJob a rpa_ingest_routes

Uso (desde la raiz del repo):  python docs/ea/secuencia/anotar_codigo.py [--only CU8]
  --only CUn: solo borra y reescribe las anotaciones de ese caso de uso ([CU08 - ...] o [CU8 - ...]) y solo comprueba
              ese diagrama; las anotaciones de los demas casos de uso quedan como estan.

- Antes de anotar borra todas las anotaciones anteriores ("- Secuencia: Paso"), asi se puede volver a ejecutar
  cada vez que se regeneran los diagramas y las anotaciones nunca quedan desfasadas.
- Cada mensaje se ubica con el MISMO rastreo que genera el diagrama (generar_secuencia.py): metodo del componente
  Angular, ruta FastAPI, funcion de servicio, consulta ORM directa o llamada a IndexedDB. Se comprueba que el
  rastreo reproduce exactamente los mensajes de secuencia.json.
- Los comentarios no usan comillas ni llaves ni "this.", para no alterar el rastreo de los generadores.
"""
import ast
import contextlib
import io
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
APP = ROOT / "backend" / "app"
FRONT = ROOT / "frontend" / "src" / "app"
MARCA = "- Secuencia: Paso"
# --only CU8: solo borra y vuelve a escribir las anotaciones de ese caso de uso (CU08 / CU8); las demas no se tocan
ONLY = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
CU_RX = rf"CU0*{int(ONLY[2:])}" if ONLY else r"CU\d+"

# ----------------------------------------------------------------------------- 1. quitar anotaciones anteriores
for path in list(APP.rglob("*.py")) + list(FRONT.rglob("*.ts")) + list(FRONT.rglob("*.html")):
    raw = path.read_bytes().decode("utf-8")
    if "- Secuencia:" not in raw:
        continue
    lines = raw.splitlines(keepends=True)
    # toda anotacion [CUxx - Secuencia: ...] anterior (tambien las escritas a mano, que pueden estar desfasadas)
    keep = [ln for ln in lines if not (re.match(rf"\s*(#|//|<!--)\s*\[{CU_RX} - Secuencia:", ln))]
    if len(keep) != len(lines):
        path.write_bytes("".join(keep).encode("utf-8"))

# ----------------------------------------------------------------------------- 2. rastreo (mismo que el diagrama)
sys.path.insert(0, str(HERE))
with contextlib.redirect_stdout(io.StringIO()):
    import generar_secuencia as S  # noqa: E402
G, T, AC, NOMBRE = S.G, S.T, S.AC, S.NOMBRE
SEQ = {d["cu"]: d for d in json.loads((HERE / "secuencia.json").read_text(encoding="utf-8"))["diagrams"]
       if not ONLY or d["cu"] == ONLY}
ROUTE = {r["key"]: r for r in T.ROUTES}

# mensajes control -> entidad de cada ruta, con la funcion (o la linea ORM) que los produce
ORIGEN = {}   # (ruta, entidad, etiqueta) -> (archivo, linea, es_definicion)
_original = S.mensajes_control


def py_file(module):
    return APP / (module.replace(".", "/") + ".py")


def mensajes_con_origen(handler_key, solo=None):
    """Copia de generar_secuencia.mensajes_control que ademas recuerda donde esta cada mensaje."""
    route = AC.FUNCS[handler_key]
    res = []

    def emitir(k, ctx):
        f = AC.FUNCS[k]
        if solo and k.split(".")[1] not in solo:
            return
        for m in T.destino(f):
            item = (NOMBRE[AC.CLASS_TABLE[m]], T.label(f), S.retorno(f), ctx)
            if not any(r[:2] == item[:2] and [c[0] for c in r[3]] == [c[0] for c in ctx] for r in res):
                res.append(item)
                ORIGEN.setdefault((handler_key, item[0], item[1]), (py_file(f.module), f.node, True))

    if solo:
        def walk(fn, ctx, d, seen):
            for k, c, _ in S.sitios(fn):
                if k in seen or d > 4:
                    continue
                seen.add(k)
                emitir(k, ctx + c)
                walk(AC.FUNCS[k], ctx + c, d + 1, seen)
        walk(route, (), 0, set())
        return res
    for i, (k, c1, _) in enumerate(S.sitios(route)):
        emitir(k, c1)
        for k2, c2, _ in S.sitios(AC.FUNCS[k]):
            emitir(k2, c1 + S.pref(c2, i))
    if not res:
        res = S.orm_sitios(route)
        # cada consulta / constructor ORM de la ruta: su linea exacta
        for _, ctx, node in S.sitios(route, resolve=lambda f, name: ["*"]):
            name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", None)
            lab = None
            if name in ("query", "select", "get") and node.args:
                a0 = node.args[0]
                base = a0.value if isinstance(a0, ast.Attribute) else a0
                if isinstance(base, ast.Name) and base.id in AC.CLASS_TABLE:
                    ent, lab = NOMBRE[AC.CLASS_TABLE[base.id]], ast.unparse(node)
            if isinstance(node.func, ast.Name) and node.func.id in AC.CLASS_TABLE:
                kws = ", ".join(x.arg for x in node.keywords if x.arg)
                ent, lab = NOMBRE[AC.CLASS_TABLE[node.func.id]], f"{node.func.id}({kws})"
            if lab:
                ORIGEN.setdefault((handler_key, ent, lab), (py_file(route.module), node, False))
    assert [r[:3] for r in res] == [r[:3] for r in _original(handler_key, solo)], handler_key
    return res


S.mensajes_control = mensajes_con_origen
modelos = {cu: S.build(cu) for cu in SEQ}
for cu, mdl in modelos.items():   # el rastreo debe dar exactamente los mensajes del diagrama
    a = [(m["from"], m["to"], m["label"], m["num"]) for m in mdl["msgs"] if not m["ret"]]
    b = [(m["from"], m["to"], m["label"], m["num"]) for m in SEQ[cu]["msgs"] if not m["ret"]]
    assert a == b, f"{cu}: secuencia.json no coincide con el codigo; regenera los diagramas primero"

# ----------------------------------------------------------------------------- 3. ubicar cada mensaje en el codigo
NOTAS = OrderedDict()   # (archivo, linea_1) -> {(cu, texto): [pasos]}
UBICACION = {}          # (cu, paso de la llamada) -> [(archivo, linea_1)]: ahi mismo va el comentario de su retorno


def anotar(path, line, cu, num, texto):
    NOTAS.setdefault((Path(path), line), OrderedDict()).setdefault((cu, texto), []).append(num)
    UBICACION.setdefault((cu, num), []).append((Path(path), line))


def ts_linea_metodo(cls, meth):
    text = cls.text
    pos = text.index(meth, cls.methods[meth]["pos"])
    return text.count("\n", 0, pos) + 1


def ts_metodos_alcanzables(cls, meth, seen=None):
    seen = seen if seen is not None else set()
    if meth in seen or meth not in cls.methods:
        return seen
    seen.add(meth)
    for x in re.finditer(r"this\.(\w+)\s*\(", cls.methods[meth]["body"]):
        if x.group(1) in cls.methods:
            ts_metodos_alcanzables(cls, x.group(1), seen)
    return seen


def ts_buscar(cls, metodos, patron):
    """Lineas (1-based) donde aparece patron dentro de los cuerpos de los metodos dados."""
    out = []
    for m in metodos:
        body = cls.methods[m]["body"]
        start = cls.text.index(body, cls.methods[m]["pos"])
        for x in re.finditer(patron, body):
            ln = cls.text.count("\n", 0, start + x.start()) + 1
            if ln not in out:
                out.append(ln)
    return out


def py_linea_def(node):
    return min([node.lineno] + [d.lineno for d in node.decorator_list])


ACTOR = G.ACTORES
for cu in sorted(SEQ, key=lambda c: int(c[2:])):
    objs = SEQ[cu]["objs"]
    nombre = lambda oid: objs[oid]["name"]
    llamado = {}   # objeto frontend -> metodos que se le pidieron en el paso actual
    ultima_ruta = {}
    for m in SEQ[cu]["msgs"]:
        if m["ret"] or not m["num"]:
            continue
        fr, to, lab, num = m["from"], m["to"], m["label"], m["num"]
        meth = lab.split("(")[0]
        kfr, kto = fr[:3], to[:3]
        if "." not in num:
            llamado = {}
        if kfr == "act":                                            # actor -> interfaz
            cls = T.TS[nombre(to)]
            texto = f"El {ACTOR[fr[4:]]} ejecuta {lab} en {nombre(to)}"
            if meth in cls.methods:
                anotar(cls.path, ts_linea_metodo(cls, meth), cu, num, texto)
                llamado[to] = ts_metodos_alcanzables(cls, meth)
            else:                                                   # expresion de la plantilla (CU29)
                html = cls.path.with_suffix(".html")
                src = html.read_text(encoding="utf-8")
                pos = src.index(lab)
                tag = src.rfind("<", 0, pos)                       # el comentario va antes del elemento
                anotar(html, src.count("\n", 0, tag) + 1, cu, num, texto + " (en la plantilla)")
        elif fr == to:                                              # disparado por el sistema
            cls = T.TS[nombre(to)]
            anotar(cls.path, ts_linea_metodo(cls, meth), cu, num,
                   f"El sistema dispara {lab} en {nombre(to)} (evento del navegador)")
            llamado[to] = ts_metodos_alcanzables(cls, meth)
        elif kto == "ctl" and nombre(to) in T.TS:                   # servicio del frontend
            cls = T.TS[nombre(to)]
            texto = f"{nombre(fr)} invoca {lab} en {nombre(to)}"
            if meth in cls.methods:
                anotar(cls.path, ts_linea_metodo(cls, meth), cu, num, texto)
                llamado.setdefault(to, set()).update(ts_metodos_alcanzables(cls, meth))
            else:                                                   # senal leida por la plantilla (CU29)
                ln = [i + 1 for i, s in enumerate(cls.text.splitlines()) if re.search(rf"\b{meth}\s*=\s*signal", s)]
                assert len(ln) == 1, (cu, num, lab)
                anotar(cls.path, ln[0], cu, num, texto + " (senal que lee la plantilla)")
        elif kto == "ctl":                                          # ruta FastAPI
            key = f"routes.{nombre(to)}.{meth}"
            fn, r = AC.FUNCS[key], ROUTE[key]
            ultima_ruta[to] = key
            anotar(py_file(fn.module), py_linea_def(fn.node), cu, num,
                   f"{nombre(fr)} llama a {lab} de {nombre(to)} ({r['verb'].upper()} /api{r['path']})")
        elif kto == "ent" and nombre(fr) in T.TS:                   # IndexedDB desde un servicio del frontend
            cls = T.TS[nombre(fr)]
            op, store = re.match(r"(\w+)(?:<[^>]*>)?\(\s*STORES\.(\w+)", lab).groups()
            lineas = ts_buscar(cls, sorted(llamado.get(fr, set())), rf"this\.idb\.{op}(?:<[^>]*>)?\(\s*STORES\.{store}\b")
            assert lineas, (cu, num, lab)
            for ln in lineas:
                anotar(cls.path, ln, cu, num, f"{nombre(fr)} ejecuta {lab} sobre la entidad local {nombre(to)} (IndexedDB)")
        elif kto == "ent":                                          # control backend -> entidad
            path, node, es_def = ORIGEN[(ultima_ruta[fr], nombre(to), lab)]
            verbo = "invoca" if es_def else "ejecuta"
            anotar(path, py_linea_def(node) if es_def else node.lineno, cu, num,
                   f"{nombre(fr)} {verbo} {lab} sobre la entidad {nombre(to)}")
        else:
            raise SystemExit(f"{cu} {num}: mensaje sin regla de ubicacion: {fr} -> {to}")

    # retornos (flechas punteadas): junto a la misma funcion que atiende la llamada que responden
    msgs = SEQ[cu]["msgs"]
    for i, m in enumerate(msgs):
        if not m["ret"] or not m["num"]:
            continue
        llamada = next(c for c in reversed(msgs[:i]) if not c["ret"] and c["num"] and c["from"] == m["to"]
                       and c["to"] == m["from"] and c["label"] == m["op"])
        for path, line in UBICACION[(cu, llamada["num"])]:
            NOTAS.setdefault((path, line), OrderedDict()).setdefault(
                (cu, f"{nombre(m['from'])} retorna {m['op']}: {m['label']} a {nombre(m['to'])}"), []).append(m["num"])

# ----------------------------------------------------------------------------- 4. escribir los comentarios
PROHIBIDO = re.compile(r"""['"`{}]|this\.|(?<![\w.])(if|for|while)\s*\(""")
por_archivo = OrderedDict()
for (path, line), grupos in NOTAS.items():
    por_archivo.setdefault(path, []).append((line, grupos))
total = 0
for path, items in por_archivo.items():
    raw = path.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.splitlines(keepends=True)
    if path.suffix == ".py":
        abre, cierra = "# ", ""
    elif path.suffix == ".ts":
        abre, cierra = "// ", ""
    else:
        abre, cierra = "<!-- ", " -->"
    for line, grupos in sorted(items, key=lambda x: -x[0]):
        objetivo = lines[line - 1]
        sangria = objetivo[:len(objetivo) - len(objetivo.lstrip())]
        nuevas = []
        for (cu, texto), pasos in sorted(grupos.items(), key=lambda g: (int(g[0][0][2:]), [int(p) for p in g[1][0].split(".")])):
            assert path.suffix == ".py" or not PROHIBIDO.search(texto), texto   # en Python no afecta al rastreo
            etiqueta = ("Paso " if len(pasos) == 1 else "Pasos ") + ", ".join(pasos)
            nuevas.append(f"{sangria}{abre}[CU{int(cu[2:]):02d} - Secuencia: {etiqueta}] {texto}{cierra}{nl}")
        lines[line - 1:line - 1] = nuevas
        total += len(nuevas)
    path.write_bytes("".join(lines).encode("utf-8"))
print(f"OK: {total} comentarios en {len(por_archivo)} archivos para {len(SEQ)} casos de uso")
