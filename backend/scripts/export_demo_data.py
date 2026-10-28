"""Export the populated demo database to `scripts/data/demo_data.sql.gz` (for the deployed database).

The file holds DATA ONLY: the deployed database gets its tables from the migrations (alembic upgrade head),
then this file is loaded with psql (see backend/README.md, "Datos de demostración en el despliegue"). Loading it:
- refuses to run unless the target is at the same migration as the export;
- empties every table and loads everything in ONE transaction (all or nothing).

    python -m scripts.export_demo_data [--database-url URL]
"""
import argparse
import gzip
import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

from sqlalchemy import create_engine, text

OUTPUT = Path(__file__).parent / "data" / "demo_data.sql.gz"
# Lines that only newer psql/PostgreSQL versions understand; the data does not need them.
INCOMPATIBLE = ("SET transaction_timeout", "\\restrict", "\\unrestrict")


def _pg_dump() -> str:
    found = shutil.which("pg_dump")
    if found:
        return found
    for version in ("18", "17", "16", "15"):
        candidate = Path(f"C:/Program Files/PostgreSQL/{version}/bin/pg_dump.exe")
        if candidate.exists():
            return str(candidate)
    raise SystemExit("No se encontró pg_dump: instala PostgreSQL o agrégalo al PATH")


def export(database_url: str) -> Path:
    engine = create_engine(database_url)
    with engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
        tables = connection.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename <> 'alembic_version' "
            "ORDER BY tablename")).scalars().all()
        companies = connection.execute(text("SELECT count(*) FROM tenants")).scalar()
    url = urlsplit(database_url.replace("postgresql+psycopg2://", "postgresql://"))
    env = {**os.environ, "PGPASSWORD": unquote(url.password or "")}
    dump = subprocess.run(
        [_pg_dump(), "--data-only", "--no-owner", "--no-privileges", "--exclude-table=alembic_version",
         "-h", url.hostname or "localhost", "-p", str(url.port or 5432), "-U", unquote(url.username or "postgres"),
         url.path.lstrip("/")],
        capture_output=True, check=True, env=env).stdout.decode("utf-8")
    body = "\n".join(line for line in dump.splitlines() if not line.startswith(INCOMPATIBLE))
    header = f"""-- FashionStore demo data ({companies} empresas). Data only: create the tables first with
--   alembic upgrade head   (must be at migration {revision})
-- then load:   psql "<DATABASE_URL>" -v ON_ERROR_STOP=1 -f demo_data.sql
\\set ON_ERROR_STOP on
BEGIN;
DO $$
BEGIN
  IF (SELECT version_num FROM alembic_version) <> '{revision}' THEN
    RAISE EXCEPTION 'La base debe estar en la migración {revision}: ejecuta "alembic upgrade head" antes de cargar';
  END IF;
END $$;
TRUNCATE TABLE {", ".join(tables)} RESTART IDENTITY CASCADE;
"""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUTPUT, "wt", encoding="utf-8", compresslevel=9) as out:
        out.write(header + body + "\nCOMMIT;\n")
    return OUTPUT


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url")
    args = parser.parse_args()
    from app.core.config import settings

    path = export(args.database_url or settings.database_url)
    print(f"{path} ({path.stat().st_size / 1_048_576:.1f} MB)")


if __name__ == "__main__":
    main()
