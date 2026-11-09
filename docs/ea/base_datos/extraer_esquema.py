"""Extrae el esquema fisico real (PostgreSQL) de los modelos SQLAlchemy y lo guarda en esquema.json.

Uso (desde backend/):  PYTHONPATH=. .venv/Scripts/python.exe ../docs/ea/base_datos/extraer_esquema.py
Tipos, nulos, claves, FK con su ON DELETE, unicidad, indices y el DDL salen de Base.metadata compilado con el
dialecto de PostgreSQL. Nada se escribe a mano.
"""
import importlib
import json
import pkgutil
from pathlib import Path

import app.models as models_pkg
from app.core.database import Base
from sqlalchemy import Enum
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

for mod in pkgutil.iter_modules(models_pkg.__path__):
    importlib.import_module(f"app.models.{mod.name}")

PG = postgresql.dialect()
clase = {m.local_table.name: m.class_ for m in Base.registry.mappers}
tablas, enums = [], {}
for t in Base.metadata.sorted_tables:          # orden de dependencias (padres antes que hijos)
    unicas = {c.name for c in t.columns if c.unique}
    compuestas = []
    for cons in t.constraints:
        cols = [c.name for c in getattr(cons, "columns", [])]
        if type(cons).__name__ == "UniqueConstraint":
            if len(cols) == 1:
                unicas.add(cols[0])
            else:
                compuestas.append(cols)
    for ix in t.indexes:
        cols = [c.name for c in ix.columns]
        if ix.unique and len(cols) == 1:
            unicas.add(cols[0])
    cols = []
    for c in t.columns:
        if isinstance(c.type, Enum) and c.type.name:
            enums[c.type.name] = list(c.type.enums)
        fk = next(iter(c.foreign_keys), None)
        cols.append({
            "nombre": c.name, "tipo": c.type.compile(dialect=PG), "nulo": bool(c.nullable), "pk": bool(c.primary_key),
            "fk": f"{fk.column.table.name}.{fk.column.name}" if fk else None,
            "ondelete": (fk.ondelete or "") if fk else "", "unica": c.name in unicas,
            "comentario": c.comment or "", "doc": c.doc or "",
        })
    cls = clase.get(t.name)
    tablas.append({
        "tabla": t.name, "clase": cls.__name__ if cls else None,
        "doc": (cls.__doc__ or "").strip() if cls else "", "columnas": cols, "unicas_compuestas": compuestas,
        "indices": [{"nombre": ix.name, "columnas": [c.name for c in ix.columns], "unico": bool(ix.unique)}
                    for ix in sorted(t.indexes, key=lambda i: i.name or "")],
        "ddl": str(CreateTable(t).compile(dialect=PG)).strip(),
        "ddl_indices": [str(CreateIndex(ix).compile(dialect=PG)).strip() for ix in sorted(t.indexes, key=lambda i: i.name or "")],
    })
out = Path(__file__).resolve().parent / "esquema.json"
out.write_text(json.dumps({"tablas": tablas, "enums": enums}, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(tablas), "tablas,", sum(len(t["columnas"]) for t in tablas), "columnas,", len(enums), "enums ->", out)
