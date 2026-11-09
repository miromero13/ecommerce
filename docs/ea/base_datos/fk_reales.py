"""Lee (solo lectura) las claves foraneas reales de la base PostgreSQL y la version de Alembic -> fk_db.json."""
import json
from pathlib import Path
from sqlalchemy import text
from app.core.database import engine

SQL = text("""
SELECT tc.table_name, kcu.column_name, ccu.table_name AS ref_table, ccu.column_name AS ref_col, rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
JOIN information_schema.referential_constraints rc ON tc.constraint_name = rc.constraint_name AND tc.table_schema = rc.constraint_schema
WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
ORDER BY 1, 2""")
with engine.connect() as c:
    fks = [dict(r._mapping) for r in c.execute(SQL)]
    ver = c.execute(text("SELECT version_num FROM alembic_version")).scalar()
    tablas = [r[0] for r in c.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'"))]
out = Path(__file__).resolve().parent / "fk_db.json"
out.write_text(json.dumps({"alembic": ver, "tablas": sorted(tablas), "fks": fks}, indent=1), encoding="utf-8")
print("alembic", ver, "| tablas", len(tablas), "| FK", len(fks))
