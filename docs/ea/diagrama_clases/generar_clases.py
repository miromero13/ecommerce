"""Genera FashionStore_diagrama_clases.js: el diagrama de clases UML de TODA la base de datos para EA 15.

Uso (desde la raiz del repo), despues de actualizar los datos del modelo de dominio:
  1) cd backend && PYTHONPATH=. .venv/Scripts/python.exe ../docs/ea/modelo_dominio/extraer_modelos.py
  2) python docs/ea/modelo_dominio/analizar_codigo.py
  3) python docs/ea/diagrama_clases/generar_clases.py

Usa exactamente las mismas reglas que el modelo de dominio (generar_dominio.py), sin nada escrito a mano:
  - una clase por tabla de los modelos SQLAlchemy, con el mismo nombre en espanol;
  - atributos = columnas con su tipo; operaciones = funciones reales de los servicios que trabajan sobre la tabla;
  - una relacion por clave foranea, con multiplicidades segun si la FK es nula o unica;
  - composicion solo si la FK es obligatoria, no RESTRICT, y el codigo borra en cascada (un solo duenio);
  - las tablas puente (PermisosRoles, AsignacionRolesUsuarios) se dibujan como asociaciones M:N.
Legibilidad (misma regla que la figura anterior del documento): todas las relaciones se crean en el modelo de EA,
pero en el diagrama no se dibujan (quedan ocultas) y una nota lo explica:
  1) la linea id_empresa -> Empresa de las clases que ademas tienen otras relaciones;
  2) la segunda y siguientes FK de una clase hacia la misma clase (se dibuja una: la composicion o la obligatoria).
"""
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "modelo_dominio"))
import generar_dominio as D  # noqa: E402

TITULO = "Diagrama de clases - Base de datos FashionStore SaaS"


def simplificar(rels, columnas):
    """(relaciones que se dibujan, cuantas lineas a Empresa se ocultan, FK repetidas ocultas).
    columnas(t) = nombres de columna de la tabla t en su orden."""
    es_tenant = lambda r: r["columna"] == "tenant_id" and r["padre"] == "tenants"
    otras = collections.Counter(r["hijo"] for r in rels if not es_tenant(r))
    sin_tenant = [r for r in rels if not (es_tenant(r) and otras[r["hijo"]])]
    grupos = collections.OrderedDict()
    for r in sin_tenant:
        grupos.setdefault((r["hijo"], r["padre"]), []).append(r)
    dibujar, repetidas = [], []
    for (h, _), rs in grupos.items():
        rs.sort(key=lambda r: (not r["composicion"], r["mult_padre"] != "1", (columnas(h) + [r["columna"]]).index(r["columna"])))   # M:N: la columna es la tabla puente
        dibujar.append(rs[0])
        repetidas += rs[1:]
    return dibujar, len(rels) - len(sin_tenant), repetidas


def nota(total, dibujar, ocultas_tenant, repetidas, nombre, empresa, col_empresa, clases="clases", clase="clase",
         atributos="atributos"):
    (h, p), n = collections.Counter((r["hijo"], r["padre"]) for r in repetidas).most_common(1)[0]
    return (f"Para que el diagrama se lea se dibujan {len(dibujar)} de las {total} relaciones; las demás existen en el "
            f"modelo y sus claves se ven como {atributos} de cada {clase}: (1) no se dibuja la línea {col_empresa} -> "
            f"{empresa} de las {ocultas_tenant} {clases} que además tienen otras relaciones (todas pertenecen a una "
            f"empresa); (2) cuando una {clase} tiene varias claves foráneas hacia la misma {clase} se dibuja una sola "
            f"línea ({len(repetidas)} líneas no dibujadas; por ejemplo, {nombre(h)} tiene {n + 1} hacia {nombre(p)}).")


def construir():
    tablas = sorted(t for t in D.MODELOS if t not in D.JUNCTION)
    todas = D.relaciones(set(tablas))
    rels, ocultas_tenant, repetidas = simplificar(todas, lambda t: [c["column"] for c in D.MODELOS[t]["columns"]])
    texto_nota = nota(len(todas), rels, ocultas_tenant, repetidas, lambda t: D.NOMBRE[t], "Empresa", "id_empresa")
    mejor = None
    for seed in range(1, 9):                      # varias ubicaciones iniciales; se queda con el lienzo mas chico
        cell, R, C = D.ubicar(tablas, rels, seed=seed, iters=120000)
        boxes, paths, size = D.rutear(tablas, rels, cell, R, C)
        if D.verificar(boxes, paths, rels):
            continue
        area = size[0] * size[1]
        if mejor is None or area < mejor[0]:
            mejor = (area, seed, boxes, paths, size)
    assert mejor, "ninguna ubicacion sin lineas sobre clases"
    _, seed, boxes, paths, size = mejor
    D.HERE = HERE                               # la vista previa se guarda en esta carpeta
    D.vista("clases", boxes, paths, rels, size)
    clases = [{"t": t, "name": D.NOMBRE[t], "attrs": D.atributos(t), "ops": D.operaciones(t),
               "notes": f"Tabla {t} ({D.MODELOS[t]['class']}). Atributos y FK del modelo SQLAlchemy; operaciones: "
                        f"funciones de servicio que trabajan sobre la tabla."} for t in tablas]
    clave = lambda r: f"{r['hijo']}|{r['padre']}|{r['columna']}"
    rel_list = [{"key": clave(r), **r} for r in todas]
    links = [{"key": clave(rels[p["rel"]]), "path": [[round(x), round(y)] for x, y in p["path"]],
              "geom": p["geom"]} for p in paths]
    print(f"{len(clases)} clases, {len(todas)} relaciones en el modelo, {len(rels)} dibujadas "
          f"({sum(r['composicion'] for r in rels)} composiciones), lienzo {size[0]:.0f}x{size[1]:.0f} (semilla {seed})")
    print("nota:", texto_nota)
    return {"classes": clases, "relations": rel_list,
            "diagram": {"name": TITULO, "boxes": {t: list(map(round, b)) for t, b in boxes.items()}, "links": links,
                        "hidden": [clave(r) for r in todas if r not in rels],
                        "note": {"text": texto_nota, "box": [20, round(size[1]) + 30, 900, 90]}}}


if __name__ == "__main__":
    model = construir()
    tpl = (HERE / "plantilla_clases.js").read_text(encoding="utf-8")
    js = "var MODEL = " + json.dumps(model, ensure_ascii=True) + ";\n"
    (HERE / "FashionStore_diagrama_clases.js").write_text(tpl.replace("/*MODEL*/\n", js), encoding="utf-8")
    print("OK: FashionStore_diagrama_clases.js generado")
