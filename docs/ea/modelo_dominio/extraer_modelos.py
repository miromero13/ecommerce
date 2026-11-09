"""Extrae de los modelos SQLAlchemy reales los datos del modelo de dominio y los guarda en modelos.json.

Uso (desde backend/):  .venv/Scripts/python.exe ../docs/ea/modelo_dominio/extraer_modelos.py
Nada se escribe a mano: tablas, columnas, tipos, FK, nulabilidad, unicidad y cascadas salen de Base.metadata
y de los relationship() declarados en app/models.
"""
import importlib
import json
import pkgutil
from pathlib import Path

import app.models as models_pkg
from app.core.database import Base
from sqlalchemy import inspect as sa_inspect

for mod in pkgutil.iter_modules(models_pkg.__path__):
    importlib.import_module(f"app.models.{mod.name}")

table_class = {}
for mapper in Base.registry.mappers:
    table_class[mapper.local_table.name] = mapper.class_.__name__

TIPOS = {"Uuid": "UUID", "UUID": "UUID", "String": "String", "Text": "Text", "Numeric": "Decimal",
         "Boolean": "bool", "Integer": "int", "BigInteger": "int", "SmallInteger": "int", "Float": "float",
         "DateTime": "DateTime", "Date": "Date", "Time": "Time", "JSON": "JSON", "JSONB": "JSON", "LargeBinary": "bytes"}


def _tipo(t):
    """Nombre del tipo tal como lo declara el modelo (los Enum muestran su clase Python)."""
    name = type(t).__name__
    if name == "Enum":
        return t.enum_class.__name__ if t.enum_class else "Enum"
    return TIPOS.get(name, name)


out = {}
for name, table in Base.metadata.tables.items():
    uniques = {c.name for c in table.columns if c.unique}
    for cons in table.constraints:  # UniqueConstraint de una sola columna
        cols = [c.name for c in getattr(cons, "columns", [])]
        if type(cons).__name__ == "UniqueConstraint" and len(cols) == 1:
            uniques.add(cols[0])
    for idx in table.indexes:
        if idx.unique and len(idx.columns) == 1:
            uniques.add(list(idx.columns)[0].name)
    columns = []
    for c in table.columns:
        fks = list(c.foreign_keys)
        columns.append({
            "column": c.name,
            "type": _tipo(c.type),
            "pk": bool(c.primary_key),
            "nullable": bool(c.nullable),
            "unique": c.name in uniques,
            "fk": fks[0].column.table.name if fks else None,
            "ondelete": (fks[0].ondelete or "").upper() if fks else "",
        })
    out[name] = {"class": table_class.get(name), "columns": columns, "cascade_from": []}

# relationship(..., cascade="all, delete-orphan") del lado del todo
for mapper in Base.registry.mappers:
    for rel in mapper.relationships:
        if rel.cascade.delete_orphan and rel.direction.name == "ONETOMANY":
            child = rel.mapper.local_table.name
            out[child]["cascade_from"].append(mapper.local_table.name)

dest = Path(__file__).resolve().parent / "modelos.json"
dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(out), "tablas ->", dest)
