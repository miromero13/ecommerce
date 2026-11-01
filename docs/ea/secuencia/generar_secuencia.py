"""Genera FashionStore_secuencia.js: un diagrama de secuencia (ICONIX / UML 2.5) por caso de uso (CU1-CU30).

Uso (desde la raiz del repo):  python docs/ea/secuencia/generar_secuencia.py [--only CU8]
  --only CUn: regenera solo ese caso de uso y lo une a secuencia.json (los demas diagramas no cambian); el .js se
              vuelve a escribir desde el JSON unido.

Mismas acciones (SPEC) y mismo rastreo del codigo que los diagramas de comunicacion:
  actor -> interfaz : metodo del componente Angular que dispara el actor
  interfaz -> control: funcion de la ruta FastAPI que atiende su llamada HTTP (o servicio del frontend)
  control -> entidad : funciones de servicio que llama la ruta, dirigidas a la entidad sobre la que trabajan
  retornos           : punteados, con su propio numero (unico y en orden de tiempo) + operacion que responden: valor
                       o, si no lo declara, lo que devuelve el codigo (respuesta de la ruta, valor del return o None)
Fragmentos, solo donde el codigo tiene la estructura, con la condicion literal del codigo como guarda:
  alt  = if / else (o elif) con llamadas en sus ramas;  opt = if sin else;  loop = for / while / comprension.
  alt y opt se dibujan desde la interfaz hasta la ultima entidad; loop desde el control hasta la ultima entidad.
Una entidad nunca envia mensajes a otra (el script falla si ocurriera).
"""
import ast
import contextlib
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "comunicacion"))
with contextlib.redirect_stdout(io.StringIO()):
    import generar_comunicacion as G  # noqa: E402
T, AC, NOMBRE = G.T, G.AC, G.NOMBRE


# ----------------------------------------------------------------------------- backend: llamadas con su contexto
def resolver(fn, name):
    return sorted(k for k in fn.calls if k.endswith("." + name) and k.startswith("services.") and k in AC.FUNCS)


def sitios(fn, resolve=None):
    """Llamadas a funciones de servicio dentro de fn, en orden de ejecucion, con los fragmentos que las rodean.
    ctx = ((id, tipo, operando, guarda), ...) de afuera hacia adentro."""
    resolve = resolve or resolver
    out = []
    fid = lambda n: f"{fn.module}.{fn.name}:{n.lineno}:{n.col_offset}"

    def visit(node, ctx):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node is not fn.node:
            return
        if isinstance(node, ast.If):
            ramas, cur = [], node
            while True:
                visit(cur.test, ctx)
                ramas.append((ast.unparse(cur.test), cur.body))
                if len(cur.orelse) == 1 and isinstance(cur.orelse[0], ast.If):
                    cur = cur.orelse[0]
                    continue
                if cur.orelse:
                    ramas.append((None, cur.orelse))
                break
            for i, (g, body) in enumerate(ramas):
                for st in body:
                    visit(st, ctx + ((fid(node), "if", i, g, "py", ramas[0][0]),))
            return
        if isinstance(node, ast.IfExp):
            visit(node.test, ctx)
            c0 = ast.unparse(node.test)
            visit(node.body, ctx + ((fid(node), "if", 0, c0, "py", c0),))
            visit(node.orelse, ctx + ((fid(node), "if", 1, None, "py", c0),))
            return
        if isinstance(node, (ast.For, ast.AsyncFor)):
            visit(node.iter, ctx)
            g = f"for {ast.unparse(node.target)} in {ast.unparse(node.iter)}"
            for st in node.body:
                visit(st, ctx + ((fid(node), "loop", 0, g, "py", g),))
            for st in node.orelse:
                visit(st, ctx)
            return
        if isinstance(node, ast.While):
            g = f"while {ast.unparse(node.test)}"
            for st in node.body:
                visit(st, ctx + ((fid(node), "loop", 0, g, "py", g),))
            return
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            for gen in node.generators:
                visit(gen.iter, ctx)
            g = " ".join(f"for {ast.unparse(x.target)} in {ast.unparse(x.iter)}" for x in node.generators)
            inner = ctx + ((fid(node), "loop", 0, g, "py", g),)
            for x in [node.key, node.value] if isinstance(node, ast.DictComp) else [node.elt]:
                visit(x, inner)
            return
        for ch in ast.iter_child_nodes(node):
            visit(ch, ctx)
        if isinstance(node, ast.Call):      # despues de sus argumentos: orden real de ejecucion
            f = node.func
            name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
            if name:
                for k in resolve(fn, name):
                    out.append((k, ctx, node))

    for st in fn.node.body:
        visit(st, ())
    return out


TERMINAL = {"first": "{} | None", "one_or_none": "{} | None", "scalar": "{} | None", "one": "{}", "all": "list[{}]",
            "count": "int"}


def retorno_consulta(fn, node, modelo):
    """Lo que devuelve la cadena db.query(Modelo)...: el metodo que la cierra (first, all, count...) en el codigo."""
    padres = {c: p for p in ast.walk(fn.node) for c in ast.iter_child_nodes(p)}
    cur, ultimo = node, None
    while isinstance(padres.get(cur), ast.Attribute) and isinstance(padres.get(padres[cur]), ast.Call) \
            and padres[padres[cur]].func is padres[cur]:
        ultimo = padres[cur].attr
        cur = padres[padres[cur]]
    if ultimo in TERMINAL:
        return TERMINAL[ultimo].format(modelo)
    if node.func.attr == "get" if isinstance(node.func, ast.Attribute) else False:
        return f"{modelo} | None"
    return f"Query[{modelo}]"


def orm_sitios(fn):
    """La ruta usa los modelos directamente (sin servicio): consultas y constructores, con su contexto y lo que
    devuelve cada uno (el modelo creado o el resultado de la consulta)."""
    res = []
    for _, ctx, node in sitios(fn, resolve=lambda f, name: ["*"]):
        name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", None)
        if name in ("query", "select", "get") and node.args:
            a0 = node.args[0]
            base = a0.value if isinstance(a0, ast.Attribute) else a0
            if isinstance(base, ast.Name) and base.id in AC.CLASS_TABLE:
                res.append((NOMBRE[AC.CLASS_TABLE[base.id]], ast.unparse(node), retorno_consulta(fn, node, base.id), ctx))
        if isinstance(node.func, ast.Name) and node.func.id in AC.CLASS_TABLE:
            kws = ", ".join(x.arg for x in node.keywords if x.arg)
            res.append((NOMBRE[AC.CLASS_TABLE[node.func.id]], f"{node.func.id}({kws})", node.func.id, ctx))
    return res


def pref(ctx, p):
    """Cada ejecucion de un if/for tiene su propio fragmento: el id lleva la llamada que lo ejecuta."""
    return tuple((f"{p}|{c[0]}",) + tuple(c[1:]) for c in ctx)


def _corto(texto, n=60):
    texto = " ".join(texto.split())
    return texto if len(texto) <= n else texto[:n - 3] + "..."


def _returns(fn):
    """Sentencias return con valor de la propia funcion (no de funciones anidadas), en orden de codigo."""
    out = []

    def visit(node):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                continue
            if isinstance(ch, ast.Return) and ch.value is not None:
                out.append(ch)
            visit(ch)
    visit(fn.node)
    return sorted(out, key=lambda r: r.lineno)


def retorno(fn):
    """Tipo de retorno declarado; si no lo declara, lo que devuelven sus return (None si no devuelve nada)."""
    r = fn.node.returns
    if r is not None:
        return ast.unparse(r)
    valores = list(dict.fromkeys(_texto_valor(x.value) for x in _returns(fn)))
    return _corto(" | ".join(valores)) if valores else "None"


def _texto_valor(v):
    """Un return: si es una consulta db.query(Modelo)... se muestra lo que devuelve; si no, su codigo."""
    cur, terminal = v, None
    while isinstance(cur, ast.Call) and isinstance(cur.func, ast.Attribute):
        terminal = terminal or cur.func.attr
        if cur.func.attr in ("query", "select") and len(cur.args) == 1 and isinstance(cur.args[0], ast.Name)                 and cur.args[0].id in AC.CLASS_TABLE:
            modelo = cur.args[0].id
            if cur is v:
                return f"Query[{modelo}]"
            return TERMINAL.get(terminal, "Query[{}]").format(modelo)
        cur = cur.func.value
    return ast.unparse(v)


def _texto_mensaje(msg):
    """message= de response(): literal tal cual; en un f-string, las partes variables se muestran como ..."""
    if isinstance(msg, ast.Constant):
        return str(msg.value)
    if isinstance(msg, ast.JoinedStr):
        return "".join(x.value if isinstance(x, ast.Constant) else "..." for x in msg.values)
    return ast.unparse(msg)


def retorno_ruta(key):
    """response_model o tipo declarado; si no, la respuesta que arma la ruta en su ultimo return:
    response(status_code, message) -> "200 Mensaje", u otra respuesta (archivo, PDF...) -> su constructor."""
    fn = AC.FUNCS[key]
    for dec in fn.node.decorator_list:
        if isinstance(dec, ast.Call):
            for kw in dec.keywords:
                if kw.arg == "response_model":
                    return ast.unparse(kw.value)
    if fn.node.returns is not None:
        return ast.unparse(fn.node.returns)
    rets = _returns(fn)
    if not rets:
        return "None"
    v = rets[-1].value
    if isinstance(v, ast.Call) and getattr(v.func, "id", "") == "response":
        kw = {k.arg: k.value for k in v.keywords}
        args = list(v.args) + [None, None]
        code = kw.get("status_code", args[0])
        msg = kw.get("message", args[1])
        code_txt = ast.unparse(code) if code is not None else ""
        m = re.search(r"HTTP_(\d{3})", code_txt)
        code_txt = m.group(1) if m else code_txt
        msg_txt = _texto_mensaje(msg) if msg is not None else ""
        return " ".join(f"{code_txt} {msg_txt}".split())      # el mensaje completo, sin recortar
    if isinstance(v, ast.Call):
        return ast.unparse(v.func)
    return _corto(ast.unparse(v))


def mensajes_control(handler_key, solo=None):
    """(entidad, etiqueta, retorno, ctx) que envia el control de una ruta, en orden de ejecucion."""
    route = AC.FUNCS[handler_key]
    res = []

    def emitir(k, ctx):
        f = AC.FUNCS[k]
        if solo and k.split(".")[1] not in solo:
            return
        for m in T.destino(f):
            item = (NOMBRE[AC.CLASS_TABLE[m]], T.label(f), retorno(f), ctx)
            if not any(r[:2] == item[:2] and [c[0] for c in r[3]] == [c[0] for c in ctx] for r in res):
                res.append(item)

    if solo:   # como en comunicacion: se siguen las llamadas en profundidad hasta los servicios pedidos
        def walk(fn, ctx, d, seen):
            for k, c, _ in sitios(fn):
                if k in seen or d > 4:
                    continue
                seen.add(k)
                emitir(k, ctx + c)
                walk(AC.FUNCS[k], ctx + c, d + 1, seen)   # cada servicio se recorre una sola vez
        walk(route, (), 0, set())
        return res
    for i, (k, c1, _) in enumerate(sitios(route)):
        emitir(k, c1)
        for k2, c2, _ in sitios(AC.FUNCS[k]):
            emitir(k2, c1 + pref(c2, i))
    if not res:
        res = orm_sitios(route)
    return res


# ----------------------------------------------------------------------------- frontend: if / for en TypeScript
def _parentesis(text, i):
    """text[i] == '(' -> indice del ')' que lo cierra."""
    depth = 0
    while i < len(text):
        c = text[i]
        if c in "'\"`":
            q = c
            i += 1
            while i < len(text) and text[i] != q:
                i += 2 if text[i] == "\\" else 1
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(text) - 1


def _bloque(text, i):
    """Desde i (tras la condicion): (inicio, fin) del bloque { } o de la sentencia simple hasta ';'."""
    while i < len(text) and text[i].isspace():
        i += 1
    if i < len(text) and text[i] == "{":
        b = T._body(text, i)
        return i, i + len(b)
    j, depth = i, 0
    while j < len(text):
        c = text[j]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c == ";" and depth <= 0:
            return i, j + 1
        j += 1
    return i, j


def regiones_ts(cls, meth):
    """Regiones (inicio, fin, id, tipo, operando, guarda) de if/else y for/while dentro del cuerpo de un metodo."""
    body = cls.methods[meth]["body"]
    regs = []
    for x in re.finditer(r"(?<![\w.])(if|for|while)\s*\(", body):
        if x.group(1) == "if" and re.search(r"else\s*$", body[:x.start()]):
            continue                       # 'else if': forma parte de la cadena del primer if
        p0 = body.index("(", x.start())
        p1 = _parentesis(body, p0)
        cond = " ".join(body[p0 + 1:p1].split())
        fid = f"{cls.name}.{meth}:{x.start()}"
        if x.group(1) != "if":
            ini, fin = _bloque(body, p1 + 1)
            regs.append((ini, fin, fid, "loop", 0, f"{x.group(1)} ({cond})", ""))
            continue
        op, pos, cond0 = 0, p1 + 1, cond
        while True:
            ini, fin = _bloque(body, pos)
            regs.append((ini, fin, fid, "if", op, cond, cond0))
            op += 1
            m2 = re.match(r"\s*else\s+if\s*\(", body[fin:])
            if m2:
                q0 = fin + m2.end() - 1
                q1 = _parentesis(body, q0)
                cond, pos = " ".join(body[q0 + 1:q1].split()), q1 + 1
                continue
            m3 = re.match(r"\s*else\b", body[fin:])
            if m3:
                ini, fin2 = _bloque(body, fin + m3.end())
                regs.append((ini, fin2, fid, "if", op, None, cond0))
            break
    for x in re.finditer(r"(?<![?])\?(?![.?:])", body):        # ternario: cond ? llamadaA : llamadaB
        j = x.start()
        k, d = j - 1, 0
        while k >= 0:
            ch = body[k]
            if ch in ")]}":
                d += 1
            elif ch in "([{":
                if d == 0:
                    break
                d -= 1
            elif d == 0 and (ch in ",;" or (ch == "=" and body[k - 1] not in "=!<>" and body[k + 1] != "=")
                             or body[max(0, k - 6):k + 1].endswith("return ")):
                break
            k -= 1
        cond = " ".join(body[k + 1:j].split())
        i, d, colon = j + 1, 0, None
        while i < len(body):
            ch = body[i]
            if ch in "([{":
                d += 1
            elif ch in ")]}":
                if d == 0:
                    break
                d -= 1
            elif d == 0 and ch == ":" and colon is None:
                colon = i
            elif d == 0 and ch in ",;":
                break
            i += 1
        if colon is None or not cond or "this." not in body[j:i]:
            continue
        fid = f"{cls.name}.{meth}:{j}"
        regs.append((j + 1, colon, fid, "if", 0, cond, cond))
        regs.append((colon + 1, i, fid, "if", 1, None, cond))
    for x in re.finditer(r"\.forEach\(\s*\(?\s*(\w+)", body):   # coleccion.forEach(x => ...)
        p0 = body.index("(", x.start())
        p1 = _parentesis(body, p0)
        rec = re.search(r"([\w.$\[\]]+(?:\(\))?)$", body[:x.start()])
        regs.append((p0, p1, f"{cls.name}.{meth}:{x.start()}", "loop", 0,
                     f"{rec.group(1) if rec else ''}.forEach({x.group(1)})", ""))
    return regs


def ctx_en(regs, pos):
    dentro = [r for r in regs if r[0] <= pos < r[1]]
    dentro.sort(key=lambda r: (r[0], -r[1]))
    return tuple((r[2], r[3], r[4], r[5], "ts", r[6]) for r in dentro)


def eventos(c, m, seen=None, depth=0):
    """Como generar_comunicacion.events, pero cada evento lleva los if/for del frontend que lo rodean."""
    seen = seen or set()
    if (c.name, m) in seen or m not in c.methods or depth > 4:
        return []
    seen.add((c.name, m))
    body = c.methods[m]["body"]
    regs = regiones_ts(c, m)
    found = []
    for x in T.API_RX.finditer(body):
        path = re.sub(r"\$\{[^}]*\}", "{}", x.group(3).replace("${this.endpoint}", c.endpoint or ""))
        found.append((x.start(), ("http", x.group(1), path), ctx_en(regs, x.start())))
    for x in re.finditer(r"this\.idb\.(\w+)(?:<[^>]*>)?\((\s*STORES\.(\w+))", body):
        i, d = x.start(2), 1
        while i < len(body) and d:
            d += {"(": 1, ")": -1}.get(body[i], 0)
            i += 1
        args = " ".join(body[x.start(2):i - 1].split())
        found.append((x.start(), ("idb", x.group(3), f"{x.group(1)}({args})"), ctx_en(regs, x.start())))
    for x in re.finditer(r"this\.(\w+)\.(\w+)\s*\(", body):
        f, meth = x.group(1), x.group(2)
        tcls = c.fields.get(f)
        if tcls in T.TS and tcls not in ("ApiService",):
            sub = T.TS[tcls]
            here = ctx_en(regs, x.start())
            if tcls in G.FRONT_CONTROLS:
                if meth not in sub.methods:
                    continue
                found.append((x.start(), ("fctl", tcls, meth, eventos(sub, meth, seen, depth + 1)), here))
            else:
                for i, (e, cx) in enumerate(eventos(sub, meth, seen, depth + 1)):
                    found.append((x.start() + i / 1000, e, here + cx))
    for x in re.finditer(r"this\.(\w+)\s*\(", body):
        if x.group(1) in c.methods and x.group(1) != m:
            here = ctx_en(regs, x.start())
            for i, (e, cx) in enumerate(eventos(c, x.group(1), seen, depth + 1)):
                found.append((x.start() + i / 1000, e, here + cx))
    return [(e, cx) for _, e, cx in sorted(found, key=lambda t: t[0])]


# ----------------------------------------------------------------------------- caso de uso -> mensajes
def build(cu):
    default_actor, steps = G.SPEC[cu]
    cu_routes = {k for k in AC.ENTRADAS[cu] if k.startswith("routes.")}
    objs, msgs = {}, []

    def obj(oid, name, kind):
        objs.setdefault(oid, {"name": name, "kind": kind})
        return oid

    def add(a, b, label, num, ctx=(), ret=False, op=None):
        m = {"from": a, "to": b, "label": label, "num": num, "ctx": list(ctx), "ret": ret}
        if ret:
            m["op"] = op          # respuesta UML 2.5: "num: operacion(argumentos): valor devuelto"
        msgs.append(m)

    n = 0
    for step in steps:
        if step[0] == "MANUAL":
            for fa, fb, lab, num in step[1]:
                for oid in (fa, fb):
                    kind = {"act": "actor", "bnd": "boundary", "ctl": "control", "ent": "entity"}[oid[:3]]
                    obj(oid, G.ACTORES[oid[4:]] if kind == "actor" else oid[4:], kind)
                if lab:
                    add(fa, fb, lab, num)
                    n = max(n, int(num.split(".")[0]))
            continue
        comp, meth = step[0], step[1]
        actor = step[2] if len(step) > 2 and step[2] else default_actor
        opts = step[3] if len(step) > 3 else {}
        c = G.cls_of(comp)
        ps = G.params_of(c, meth)
        n += 1
        k = 0
        if actor == "-":
            start = obj("ctl:" + comp, comp, "control")
            add(start, start, f"{meth}({', '.join(ps)})", str(n))
        else:
            a = obj("act:" + actor, G.ACTORES[actor], "actor")
            start = obj("bnd:" + comp, comp, "boundary")
            add(a, start, f"{meth}({', '.join(ps)})", str(n))
        allowed = set(opts.get("rutas", [])) or cu_routes

        def emit(sender, evs, outer=()):
            nonlocal k
            for e, cx in evs:
                cx = outer + pref(cx, f"{n}{sender}")
                if e[0] == "http":
                    r = T.match_route(e[1], e[2])
                    if not r or r["key"] not in allowed:
                        continue
                    ctl = obj("ctl:" + r["module"], r["module"], "control")
                    k += 1
                    op_ruta = f"{r['handler']}({', '.join(r['params'])})"
                    add(sender, ctl, op_ruta, f"{n}.{k}", cx)
                    llamada = f"{n}.{k}"
                    for ent, lab, ret, bcx in mensajes_control(r["key"], opts.get("solo")):
                        bcx = pref(bcx, llamada)
                        eo = obj("ent:" + ent, ent, "entity")
                        k += 1
                        add(ctl, eo, lab, f"{n}.{k}", cx + bcx)
                        add(eo, ctl, ret, f"{n}.{k}", cx + bcx, True, lab)     # se renumera al final (numero propio)
                    add(ctl, sender, retorno_ruta(r["key"]), llamada, cx, True, op_ruta)
                elif e[0] in ("fctl", "idb") and cu not in G.LOCAL_CUS:
                    continue
                elif e[0] == "fctl":
                    fc = obj("ctl:" + e[1], e[1], "control")
                    k += 1
                    add(sender, fc, f"{e[2]}({', '.join(G.params_of(T.TS[e[1]], e[2]))})", f"{n}.{k}", cx)
                    emit(fc, e[3], cx)
                elif e[0] == "idb":
                    name = G.LOCAL_ENTITY.get(e[1], e[1])
                    eo = obj("ent:" + name, name, "entity")
                    k += 1
                    add(sender, eo, e[2], f"{n}.{k}", cx)

        emit(start, eventos(c, meth))
    # Numeracion final en orden de tiempo: cada flecha (llamada o retorno) lleva un numero propio y unico.
    # El paso del actor queda como n; todo lo que ocurre dentro de ese paso es n.1, n.2, n.3 ... de arriba hacia abajo.
    paso, k = None, 0
    for m in msgs:
        if "." not in m["num"] and not m["ret"]:
            paso, k = m["num"], 0
        else:
            k += 1
            m["num"] = f"{paso}.{k}"
    nums = [m["num"] for m in msgs]
    assert len(nums) == len(set(nums)), (cu, "numero repetido")
    for m in msgs:
        if m["from"].startswith("ent:") and m["to"].startswith("ent:"):
            raise SystemExit(f"{cu}: una entidad envia un mensaje a otra entidad")
    return {"objs": objs, "msgs": msgs}


# ----------------------------------------------------------------------------- fragmentos
def fragmentos(model):
    """Agrupa los mensajes por cada if/for del codigo que los rodea. Un if con mensajes en una sola rama es opt."""
    msgs = model["msgs"]
    info = {}
    for i, m in enumerate(msgs):
        for depth, (fid, kind, op, guard, lang, cond0) in enumerate(m["ctx"]):
            f = info.setdefault(fid, {"kind": kind, "lang": lang, "cond0": cond0, "first": i, "last": i,
                                      "depth": depth, "ops": {}})
            f["last"] = i
            f["ops"].setdefault(op, {"guard": guard, "start": i})
    out = []
    for fid, f in info.items():
        ops = [f["ops"][k] for k in sorted(f["ops"])]
        if f["kind"] == "loop":
            kind = "loop"
        elif len(ops) >= 2:
            kind = "alt"
        else:
            kind = "opt"
        operands = []
        for o in ops:
            g = o["guard"]
            if g is None:      # rama else
                g = "else" if kind == "alt" else (f"not ({f['cond0']})" if f["lang"] == "py" else f"!({f['cond0']})")
            operands.append({"guard": g, "start": o["start"]})
        out.append({"id": fid, "kind": kind, "start": f["first"], "end": f["last"], "depth": f["depth"],
                    "operands": operands})
    out.sort(key=lambda f: (f["start"], f["depth"]))
    return out


# ----------------------------------------------------------------------------- orden de lineas de vida
def lineas(model):
    orden = {"actor": 0, "boundary": 1, "fctl": 2, "control": 3, "entity": 4}
    local = set(G.LOCAL_ENTITY.values())

    def col(oid):
        o = model["objs"][oid]
        if o["kind"] == "control" and o["name"] in G.FRONT_CONTROLS:
            return "fctl"
        if o["kind"] == "entity" and o["name"] in local:
            return "fctl"
        return o["kind"]
    primera = {}
    for i, m in enumerate(model["msgs"]):
        for oid in (m["from"], m["to"]):
            primera.setdefault(oid, i)
    for oid in model["objs"]:
        primera.setdefault(oid, 10 ** 6)
    return sorted(model["objs"], key=lambda o: (orden[col(o)], primera[o]))


def validar(cu, model, frames, life):
    """Reglas: alt/opt desde la interfaz; loop desde el control; nada a la izquierda del ancla dentro del marco."""
    idx = {o: i for i, o in enumerate(life)}
    kind = lambda o: model["objs"][o]["kind"]
    errores = []
    for f in frames:
        dentro = model["msgs"][f["start"]:f["end"] + 1]
        anc = "boundary" if f["kind"] in ("alt", "opt") else "control"
        cands = [idx[o] for m in dentro for o in (m["from"], m["to"]) if kind(o) == anc]
        if not cands and anc == "boundary":       # if del backend: el marco empieza en la interfaz de ese paso
            paso = next(m for m in reversed(model["msgs"][:f["start"] + 1]) if m["num"] and "." not in m["num"])
            cands = [idx[paso["to"]]] if kind(paso["to"]) == "boundary" else []
            if not cands:                         # paso disparado por el sistema: la interfaz mas a la izquierda
                cands = [min(idx[o] for o in life if kind(o) == "boundary")]
        if not cands:
            errores.append(f"{cu}: {f['kind']} sin {anc}")
            continue
        izq = min(cands)
        mas_izq = min(idx[o] for m in dentro for o in (m["from"], m["to"]))
        if mas_izq < izq:
            errores.append(f"{cu}: {f['kind']} [{f['operands'][0]['guard']}] tiene mensajes a la izquierda de su {anc}")
        f["left"] = life[izq]
    return errores


Y0, PASO = 134, 35        # EA 15 coloca cada mensaje 35 unidades debajo del anterior (comprobado al exportar)


def ancho_guarda(f):
    return max(len(o["guard"]) for o in f["operands"]) * 6.2 + 18


def contiene(g, f):
    return g is not f and g["depth"] < f["depth"] and g["start"] <= f["start"] and f["end"] <= g["end"]


def radios(frames):
    """R = distancia del borde izquierdo de cada fragmento a la linea de vida de su ancla. Si un fragmento interior
    empieza en el mismo mensaje que el exterior, se corre a la derecha de la pestana y la guarda del exterior."""
    for f in sorted(frames, key=lambda f: -f["depth"]):
        r = ancho_guarda(f) + 6
        for h in frames:
            if contiene(f, h) and h["left"] == f["left"]:
                r = max(r, h["R"] + (ancho_guarda(f) + 14 if h["start"] == f["start"] else 10))
        f["R"] = r


def posiciones(model, life, frames):
    """Centro (x) de cada linea de vida. EA 15 dibuja la linea de vida del actor en el centro de su rectangulo y la
    de interfaz / control / entidad a 24 unidades de su borde izquierdo (ancho del icono); el nombre va centrado en
    ella. Se separan para que quepan: los nombres, la etiqueta mas larga de cada mensaje entre su emisor y su
    receptor, y la guarda de los fragmentos a la izquierda de su ancla (interfaz / control)."""
    nombre = {o: len(model["objs"][o]["name"]) * 7.5 + (0 if model["objs"][o]["kind"] == "actor" else 8) for o in life}
    idx = {o: i for i, o in enumerate(life)}
    cx = {}
    x = 60
    for i, o in enumerate(life):
        if i:
            x += max(150, nombre[life[i - 1]] / 2 + nombre[o] / 2 + 30)
        cx[o] = x
    pares = []                                    # (izquierda, derecha, distancia minima entre centros)
    for m in model["msgs"]:
        if m["from"] != m["to"]:
            a, b = sorted((m["from"], m["to"]), key=lambda o: idx[o])
            txt = (m["num"] + ": " if m["num"] else ":") + (m["op"] + ": " if m["ret"] else "") + m["label"]
            pares.append((a, b, len(txt) * 6.2 + 30))
    for f in frames:
        i = idx[f["left"]]
        if i > 0:
            pares.append((life[i - 1], f["left"], f["R"] + 34))
    for _ in range(6):
        for a, b, dist in sorted(pares, key=lambda t: idx[t[1]] - idx[t[0]]):
            falta = dist - (cx[b] - cx[a])
            if falta > 0:
                for o in life[idx[b]:]:
                    cx[o] += falta
    out = {}
    for o in life:
        if model["objs"][o]["kind"] == "actor":
            w = max(60, round(nombre[o]))
            out[o] = [round(cx[o] - w / 2), w, round(cx[o])]
        else:
            out[o] = [round(cx[o] - 24), max(48, round(nombre[o] * 1.15 + 40)), round(cx[o])]
    return out


def geometria(model, life, xs, frames):
    """Alturas de los mensajes (las de EA) y rectangulo de cada fragmento ajustado a ellas."""
    ys = [Y0 + PASO * i for i in range(len(model["msgs"]))]
    ultimo = life[-1]
    for f in frames:
        c = xs[f["left"]][2]
        left = c - f["R"]
        for g in frames:                          # dentro de otro: 10 mas adentro, o tras su guarda si empiezan juntos
            if contiene(g, f):
                left = max(left, g["rect"][0] + (ancho_guarda(g) + 14 if g["start"] == f["start"] else 10))
        right = xs[ultimo][2] + max(40, len(model["objs"][ultimo]["name"]) * 3.75 + 18) - 10 * f["depth"]
        top = ys[f["start"]] - 24 + 5 * f["depth"]
        bottom = ys[f["end"]] + 14 - 5 * f["depth"]
        f["rect"] = [round(left), top, round(right), bottom]
        f["seps"] = [ys[o["start"]] - 17 for o in f["operands"][1:]]
    return ys


if __name__ == "__main__":
    # --only CU8: regenera solo ese caso de uso y lo une al secuencia.json existente (los demas quedan intactos)
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    diagrams, classifiers, problemas = [], {}, []
    for cu in [only] if only else [f"CU{i}" for i in range(1, 31)]:
        m = build(cu)
        frames = fragmentos(m)
        life = lineas(m)
        problemas += validar(cu, m, frames, life)
        for oid, o in m["objs"].items():
            if o["kind"] != "actor":
                classifiers[(o["kind"], o["name"])] = True
        for x in m["msgs"]:
            del x["ctx"]
        frames.sort(key=lambda f: (f["depth"], f["start"]))   # primero los de afuera
        radios(frames)
        xs = posiciones(m, life, frames)
        ys = geometria(m, life, xs, frames)
        diagrams.append({"cu": cu, "objs": m["objs"], "lifelines": life, "xs": xs, "ys": ys,
                         "fin": ys[-1] + 70, "msgs": m["msgs"], "frames": frames})
        kinds = {}
        for f in frames:
            kinds[f["kind"]] = kinds.get(f["kind"], 0) + 1
        print(f"{cu}: {len(life)} lineas de vida, {sum(not x['ret'] for x in m['msgs'])} mensajes, "
              f"{sum(x['ret'] for x in m['msgs'])} retornos, fragmentos {kinds or '-'}")
    for p in problemas:
        print("  PROBLEMA:", p)
    model = {"classifiers": [{"kind": k, "name": n} for k, n in sorted(classifiers)], "diagrams": diagrams}
    if only:
        previo = json.loads((HERE / "secuencia.json").read_text(encoding="utf-8"))
        model["diagrams"], model["classifiers"] = G.unir(only, diagrams[0], previo)
    (HERE / "secuencia.json").write_text(json.dumps(model, ensure_ascii=False, indent=1), encoding="utf-8")
    tpl = HERE / "plantilla_secuencia.js"
    if tpl.exists():
        js = "var MODEL = " + json.dumps(model, ensure_ascii=True) + ";\n"
        (HERE / "FashionStore_secuencia.js").write_text(tpl.read_text(encoding="utf-8").replace("/*MODEL*/\n", js),
                                                        encoding="utf-8")
        print("OK: FashionStore_secuencia.js generado")
