"""Documents that go with the demo data (run after `scripts.seed_demo`):

- docs/TEST_CREDENTIALS.md: every demo account, by company and branch.
- docs/demo/remito_demo.pdf: a supplier delivery note for the RPA ingest (CU10) with three real SKUs of the first
  branch of Ayni Moda and one unknown SKU (it must be reported, never created).

    python -m scripts.demo_documents [--database-url URL]
"""
import argparse
from pathlib import Path

from sqlalchemy import create_engine, text

from scripts import demo_people as people

DOCS = Path(__file__).parents[2] / "docs"


def credentials() -> str:
    lines = [
        "# Credenciales de la demo",
        "",
        "Generado por `python -m scripts.demo_documents` a partir de `backend/scripts/demo_people.py` (datos de "
        "`python -m scripts.seed_demo --reset`). Los correos usan dominios `.demo.bo` reservados: ningún comprobante "
        "llega a una casilla real.",
        "",
        "Ingreso: `http://localhost:4200/auth/login`. Clientes en la pestaña **Clientes**; el resto en **Administrativos**.",
        "",
        f"- Personal, proveedores y repartidores: contraseña `{people.STAFF_PASSWORD}`",
        f"- Clientes: contraseña `{people.CUSTOMER_PASSWORD}`",
        "",
        "## Plataforma",
        "",
        "| Rol | Nombre | Correo | Contraseña |",
        "|---|---|---|---|",
        f"| Superadministrador | {people.SUPERADMIN['name']} | `{people.SUPERADMIN['email']}` | `{people.SUPERADMIN['password']}` |",
    ]
    lines += [f"| Repartidor | {n} | `{people.email(n, 'repartidores.demo.bo')}` | `{people.STAFF_PASSWORD}` |"
              for n, _ in people.DRIVERS]
    plans = {"basic": "Básico", "pro": "Profesional", "enterprise": "Enterprise"}
    for company in people.COMPANIES:
        domain = company["domain"]
        lines += ["", f"## {company['name']} · plan {plans[company['plan']]}", "",
                  f"Administrador (ve todas sus sucursales): **{company['admin'][0]}** · `{people.email(company['admin'][0], domain)}`", "",
                  "| Sucursal | Ciudad | Encargado | Cajeros |", "|---|---|---|---|"]
        for b in company["branches"]:
            cashiers = "<br>".join(f"{n} · `{people.email(n, domain)}`" for n, _ in b["cashiers"])
            lines.append(f"| {b['name']} | {b['city']} | {b['manager'][0]} · `{people.email(b['manager'][0], domain)}` | {cashiers} |")
        supplier_domain = domain.replace(".demo.bo", "-proveedores.demo.bo")
        lines += ["", "Proveedores: " + "; ".join(f"{business} ({contact} · `{people.email(contact, supplier_domain)}`)"
                                                   for business, contact, _, _ in company["suppliers"])]
    lines += ["", "## Clientes", "", "| Nombre | Ciudad | Correo |", "|---|---|---|"]
    used = set()
    for name, _, city in people.CUSTOMERS:
        address = people.email(name, "clientes.demo.bo")
        while address in used:  # same rule as the seed
            address = address.replace("@", f"{len(used) % 9}@", 1)
        used.add(address)
        lines.append(f"| {name} | {city} | `{address}` |")
    return "\n".join(lines) + "\n"


def remito(db_url: str) -> Path:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    engine = create_engine(db_url)
    with engine.connect() as connection:
        rows = connection.execute(text("""
            SELECT v.sku, p.name, s.name AS size, c.name AS color, v.price
            FROM product_variants v JOIN products p ON p.id = v.product_id JOIN tenants t ON t.id = v.tenant_id
            LEFT JOIN sizes s ON s.id = v.size_id LEFT JOIN colors c ON c.id = v.color_id
            WHERE t.slug = 'ayni-moda' ORDER BY v.sku LIMIT 3""")).all()
    if len(rows) < 3:
        raise SystemExit("Primero carga la demo: python -m scripts.seed_demo --reset")
    styles = getSampleStyleSheet()
    target = DOCS / "demo" / "remito_demo.pdf"
    target.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(target), pagesize=A4, title="Remito de entrega")
    supplier = people.COMPANIES[0]["suppliers"][0]
    table = [["SKU", "Descripción", "Talla", "Color", "Cantidad", "Costo unit. (Bs)"]]
    table += [[r.sku, r.name, r.size, r.color, str(12 + i * 6), f"{float(r.price) * 0.55:.2f}"] for i, r in enumerate(rows)]
    table.append(["DEMO-NUEVO-01", "Falda plisada midi (prenda nueva, no registrada)", "M", "Negro", "8", "85.00"])
    grid = Table(table, repeatRows=1)
    grid.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3A5F")),
                              ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTSIZE", (0, 0), (-1, -1), 8),
                              ("GRID", (0, 0), (-1, -1), 0.25, colors.grey)]))
    doc.build([
        Paragraph(f"<b>{supplier[0]}</b>", styles["Title"]),
        Paragraph("REMITO DE ENTREGA N° 0001-000458 · La Paz, Bolivia", styles["Heading3"]),
        Paragraph(f"Cliente: Ayni Moda S.R.L. · Entregado por: {supplier[1]} · Tel. {supplier[3]}", styles["Normal"]),
        Spacer(1, 12), grid, Spacer(1, 12),
        Paragraph("Mercadería entregada en perfecto estado. Firma y sello de recepción: ____________________", styles["Normal"]),
    ])
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url")
    args = parser.parse_args()
    from app.core.config import settings

    (DOCS / "TEST_CREDENTIALS.md").write_text(credentials(), encoding="utf-8")
    print("docs/TEST_CREDENTIALS.md actualizado")
    print(f"Remito de prueba: {remito(args.database_url or settings.database_url)}")


if __name__ == "__main__":
    main()
