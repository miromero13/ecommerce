"""Genera FashionStore_modelo_relacional.js: el diagrama del modelo relacional (las 58 tablas reales) para EA 15.

Uso (desde la raiz del repo):
  1) cd backend && PYTHONPATH=. .venv/Scripts/python.exe ../docs/ea/base_datos/extraer_esquema.py
  2) python docs/ea/base_datos/generar_relacional.py

Todo sale de esquema.json (Base.metadata compilado para PostgreSQL):
  - una clase por tabla, con su nombre fisico (incluidas las tablas asociativas user_roles y role_permissions);
  - atributos = columnas con su tipo de PostgreSQL;
  - una relacion por clave foranea, nombrada con la columna FK; multiplicidades segun si la FK es nula o unica;
  - composicion solo con la misma regla del modelo de dominio (FK obligatoria, no RESTRICT, borrado en cascada).
Ubicacion y ruteo ortogonal: los mismos de generar_dominio.py (ninguna linea pasa sobre una tabla).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "modelo_dominio"))
import generar_dominio as D  # noqa: E402
sys.path.insert(0, str(HERE.parent / "diagrama_clases"))
import generar_clases as GC  # noqa: E402

E = json.loads((HERE / "esquema.json").read_text(encoding="utf-8"))
COLS = {t["tabla"]: t["columnas"] for t in E["tablas"]}
assert set(COLS) == set(D.MODELOS), set(COLS) ^ set(D.MODELOS)
TITULO = "Modelo relacional - Base de datos FashionStore SaaS"


CABECERA = """/* =====================================================================================================
 * FashionStore SaaS - Modelo relacional de la base de datos (58 tablas), para Enterprise Architect 15
 *
 * Generado por docs/ea/base_datos/generar_relacional.py (no editar a mano: cambie el .py y vuelva a generar).
 *
 * USO: en el Project Browser seleccione el paquete donde quiere el diagrama; Specialize > Tools > Scripting;
 *      clic derecho en un grupo > New JScript; pegue TODO este archivo; guarde y ejecute (Run).
 *
 * Crea el paquete "Modelo relacional - FashionStore SaaS" con:
 *   - subpaquete "Tablas": una clase por tabla real con su nombre fisico, incluidas las asociativas
 *     user_roles y role_permissions; atributos = columnas con su tipo de PostgreSQL;
 *   - una relacion por clave foranea, nombrada con su columna, con multiplicidades; composicion (rombo relleno)
 *     solo cuando la FK es obligatoria y el codigo borra en cascada;
 *   - un unico diagrama. Lineas ortogonales por pasillos: ninguna pasa sobre una tabla.
 * Si el paquete ya existe (de una ejecucion anterior) lo borra y lo crea de nuevo.
 * ===================================================================================================== */

"""


# las funciones de generar_dominio trabajan con nombres fisicos en este diagrama
D.NOMBRE = {t: t for t in COLS}
D.JUNCTION = set()                                 # las tablas asociativas tambien son tablas
D.rol = lambda col: col                            # cada relacion se nombra con su columna FK
# sin estereotipo PK / FK: EA agrupa los atributos por estereotipo y desordena las columnas; las claves se ven en
# las relaciones (nombradas con su columna FK) y en el mapeo / tabla de volumen del documento
D.atributos = lambda t: [{"nombre": c["nombre"], "tipo": c["tipo"], "columna": c["nombre"]} for c in COLS[t]]
D.operaciones = lambda t: []


def construir():
    tablas = sorted(COLS)
    todas = D.relaciones(set(tablas))
    rels, ocultas_tenant, repetidas = GC.simplificar(todas, lambda t: [c["nombre"] for c in COLS[t]])
    texto_nota = GC.nota(len(todas), rels, ocultas_tenant, repetidas, lambda t: t, "tenants", "tenant_id",
                         clases="tablas", clase="tabla", atributos="columnas")
    mejor = None
    for seed in range(1, 9):
        cell, R, C = D.ubicar(tablas, rels, seed=seed, iters=120000)
        boxes, paths, size = D.rutear(tablas, rels, cell, R, C)
        if D.verificar(boxes, paths, rels):
            continue
        if mejor is None or size[0] * size[1] < mejor[0]:
            mejor = (size[0] * size[1], seed, boxes, paths, size)
    assert mejor, "ninguna ubicacion sin lineas sobre tablas"
    _, seed, boxes, paths, size = mejor
    D.HERE = HERE
    D.vista("relacional", boxes, paths, rels, size)
    clases = [{"t": t, "name": t, "attrs": D.atributos(t), "ops": [],
               "notes": f"Tabla {t}. Columnas, tipos y claves tomados de los modelos SQLAlchemy compilados para PostgreSQL."}
              for t in tablas]
    clave = lambda r: f"{r['hijo']}|{r['padre']}|{r['columna']}"
    rel_list = [{"key": clave(r), **r} for r in todas]
    links = [{"key": clave(rels[p["rel"]]), "path": [[round(x), round(y)] for x, y in p["path"]],
              "geom": p["geom"]} for p in paths]
    print("nota:", texto_nota)
    print(f"{len(clases)} tablas, {sum(len(c['attrs']) for c in clases)} columnas, {len(todas)} FK, {len(rels)} dibujadas "
          f"({sum(r['composicion'] for r in rels)} composiciones), lienzo {size[0]:.0f}x{size[1]:.0f} (semilla {seed})")
    return {"classes": clases, "relations": rel_list,
            "diagram": {"name": TITULO, "boxes": {t: list(map(round, b)) for t, b in boxes.items()}, "links": links,
                        "hidden": [clave(r) for r in todas if r not in rels],
                        "note": {"text": texto_nota, "box": [20, round(size[1]) + 30, 900, 90]}}}


if __name__ == "__main__":
    model = construir()
    tpl = (HERE.parent / "diagrama_clases" / "plantilla_clases.js").read_text(encoding="utf-8")
    ini, fin = tpl.index("/* ====="), tpl.index("/*MODEL*/")
    tpl = tpl[:ini] + CABECERA + tpl[fin:]
    tpl = (tpl.replace("Diagrama de clases UML de toda la base de datos", "Modelo relacional de la base de datos")
              .replace("docs/ea/diagrama_clases/generar_clases.py", "docs/ea/base_datos/generar_relacional.py")
              .replace('var ROOT_NAME = "Diagrama de clases - FashionStore SaaS";', 'var ROOT_NAME = "Modelo relacional - FashionStore SaaS";')
              .replace("FashionStore_diagrama_clases.js", "FashionStore_modelo_relacional.js")
              .replace('"Diagrama de clases de toda la base de datos, generado', '"Modelo relacional de la base de datos, generado')
              .replace("generando el diagrama de clases de la base de datos", "generando el modelo relacional de la base de datos")
              .replace('"[OK] Diagrama de clases creado en', '"[OK] Modelo relacional creado en')
              .replace('" clases, " +', '" tablas, " +')
              .replace("Diagrama de clases generado correctamente.", "Modelo relacional generado correctamente.")
              .replace('newPackage(root, "Clases", "Una clase por tabla real del sistema.")', 'newPackage(root, "Tablas", "Una clase por tabla real de la base de datos.")'))
    js = "var MODEL = " + json.dumps(model, ensure_ascii=True) + ";\n"
    (HERE / "FashionStore_modelo_relacional.js").write_text(tpl.replace("/*MODEL*/\n", js), encoding="utf-8")
    print("OK: FashionStore_modelo_relacional.js generado")
