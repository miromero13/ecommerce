"""Continúa el seeder desde donde quedó, SIN BORRAR los datos ya creados (empresas, sucursales, personal, catálogo y stock).

Uso:
    python -m scripts.seed_continue [--simulate-days 5] [--database-url URL] [--assets-base-url http://localhost:8000]
"""
import argparse
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

# Ensures all SQLAlchemy models are registered
import main  # noqa: F401
from app.core.config import settings
from app.models.branch import Branch
from app.models.product_variant import ProductVariant
from app.models.provider import Provider
from app.models.subscription_plan import SubscriptionPlan
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.enums import RolEnum
from scripts import demo_people as people
from scripts.seed_demo import EVENT_COLUMNS, LOCAL_TZ, RNG, Seeder
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class ResilientSeeder(Seeder):
    def today_state(self) -> None:
        from app.models.inventory import Inventory
        from app.models.inventory_movement import InventoryMovement
        from app.models.user import User
        from app.schemas.inventory_schema import InventoryMovementTypeEnum
        from app.services import cash_session_service
        from app.services.cash_session_service import CashSessionConflict
        from app.services.expert_replenishment_service import evaluate
        from app.services.recommendation_service import train

        for company in self.companies:
            # Abrir cajas del turno de la mañana (si alguna ya está abierta, no falla)
            for entry in company["branches"][:2]:
                cashier = self.db.query(User).filter(User.id == entry["cashiers"][0].id).one()
                try:
                    cash_session_service.open_session(self.db, cashier, Decimal(200))
                except CashSessionConflict:
                    pass
            # Pedidos web esperando en mostrador o para enviar
            for delivery in (False, False, True):
                self.web_order(company, self.today, delivery=delivery, finish=False)
            self.web_order(company, self.today, paid=False)
            # Reservas del día
            for outcome in ("paid_only", "paid_only"):
                self.reservation(company, self.today, outcome)
            # Solicitudes a proveedores en distintos estados
            for status in ("requested", "accepted", "preparing", "awaiting_receipt"):
                self.replenishment(company, self.today, status)
            # Stock crítico en sucursal principal para el sistema experto
            main_branch = company["branches"][0]["branch"]
            low = self.db.query(Inventory).filter(
                Inventory.branch_id == main_branch.id,
                Inventory.reserved_quantity == 0,
                Inventory.quantity > Inventory.minimum_stock,
            ).limit(4).all()
            for row in low:
                lost = row.quantity - max(row.minimum_stock - 2, 1)
                row.quantity -= lost
                self.db.add(InventoryMovement(
                    tenant_id=row.tenant_id, variant_id=row.variant_id, branch_id=row.branch_id,
                    movement_type=InventoryMovementTypeEnum.outcome, quantity=lost,
                    created_by=company["branches"][0]["manager"].id,
                    note="Baja por prendas dañadas en vitrina",
                ))
            self.db.commit()
            evaluate(self.db, company["tenant"].id)

        for company in self.companies:
            self.reservation_waiting_deposit(company)

        self.db.execute(text("UPDATE payment_receipts SET emailed_at = issued_at, email_attempts = 1 "
                             "WHERE issued_at < :today"), {"today": self.at(self.today, 0)})
        self.db.execute(text("UPDATE notifications SET read_at = created_at + interval '2 hours' "
                             "WHERE created_at < :recent"), {"recent": self.at(self.today - timedelta(days=3), 0)})
        self.db.commit()
        users, products = train(self.db)
        print(f"  ✓ Recomendador entrenado: {users} clientes, {products} prendas.")


def load_existing_seeder(db, assets_base_url: str, days: int) -> ResilientSeeder:
    seeder = ResilientSeeder(db, assets_base_url, days)

    # 1. Superadmin
    seeder.superadmin = db.query(User).filter(User.email == people.SUPERADMIN["email"]).first()
    if not seeder.superadmin:
        raise SystemExit("No se encontró el superadministrador en la base de datos. Ejecutá seed_demo primero.")

    # 2. Drivers
    seeder.drivers = db.query(User).filter(User.rol == RolEnum.delivery).all()

    # 3. Clientes
    city_by_email = {people.email(n, "clientes.demo.bo"): city for n, _, city in people.CUSTOMERS}
    customers = db.query(User).filter(User.rol == RolEnum.cliente).all()
    for c in customers:
        c.city = city_by_email.get(c.email, "La Paz")
    seeder.customers = customers

    # 4. Empresas, sucursales, proveedores, variantes y cupones
    plans = {p.slug: p for p in db.query(SubscriptionPlan).all()}
    for spec in people.COMPANIES:
        tenant = db.query(Tenant).filter(Tenant.slug == spec["slug"]).first()
        if not tenant:
            continue
        company = {
            "spec": spec,
            "tenant": tenant,
            "plan": plans.get(spec["plan"]),
            "branches": [],
            "suppliers": [],
            "variants": [],
            "coupons": [],
        }

        # Admin
        admin_name, _ = spec["admin"]
        admin_email = people.email(admin_name, spec["domain"])
        company["admin"] = db.query(User).filter(User.email == admin_email).first()

        # Sucursales y personal
        for b in spec["branches"]:
            branch = db.query(Branch).filter(Branch.tenant_id == tenant.id, Branch.name == b["name"]).first()
            if not branch:
                continue
            manager_email = people.email(b["manager"][0], spec["domain"])
            manager = db.query(User).filter(User.email == manager_email).first()
            cashiers = [
                db.query(User).filter(User.email == people.email(n, spec["domain"])).first()
                for n, g in b["cashiers"]
            ]
            company["branches"].append({"branch": branch, "manager": manager, "cashiers": cashiers})

        # Proveedores
        for business, contact, gender, phone in spec["suppliers"]:
            user_email = people.email(contact, spec["domain"].replace(".demo.bo", "-proveedores.demo.bo"))
            user = db.query(User).filter(User.email == user_email).first()
            provider = db.query(Provider).filter(Provider.tenant_id == tenant.id, Provider.user_id == user.id).first() if user else None
            company["suppliers"].append({"provider": provider, "user": user})

        # Variantes de prendas
        company["variants"] = db.query(ProductVariant).filter(ProductVariant.tenant_id == tenant.id).all()

        # Cupones
        key = company["spec"]["key"].upper()
        first_branch = company["branches"][0]["branch"] if company["branches"] else None
        company["coupons"] = [
            {"code": f"{key}BIENVENIDA", "kind": "percentage", "value": 10, "valid_from": None, "valid_until": None, "branch_id": None},
            {"code": f"{key}INVIERNO", "kind": "percentage", "value": 15, "valid_from": seeder.at(seeder.start, 0), "valid_until": seeder.at(seeder.start + timedelta(days=60), 0), "branch_id": None},
            {"code": f"{key}FIDELIDAD20", "kind": "fixed", "value": 20, "valid_from": None, "valid_until": None, "branch_id": None},
            {"code": f"{key}TIENDA{first_branch.city[:3].upper() if first_branch else 'LPZ'}", "kind": "percentage", "value": 12, "valid_from": None, "valid_until": None, "branch_id": first_branch.id if first_branch else None},
        ]

        seeder.companies.append(company)

    return seeder


def run_continue(database_url: str | None = None, simulate_days: int = 5, assets_base_url: str = "http://localhost:8000") -> ResilientSeeder:
    target_url = database_url or settings.database_url
    connect_args = {
        "connect_timeout": 30,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
        "options": "-c lock_timeout=15000",
    }
    engine = create_engine(target_url, connect_args=connect_args)
    db = sessionmaker(bind=engine, autoflush=False)()

    print("→ Cargando entidades existentes desde la base de datos (sin borrar nada)...")
    seeder = load_existing_seeder(db, assets_base_url, days=max(simulate_days, 1))
    print(f"  ✓ {len(seeder.companies)} empresas cargadas")
    print(f"  ✓ {sum(len(c['branches']) for c in seeder.companies)} sucursales")
    print(f"  ✓ {sum(len(c['variants']) for c in seeder.companies)} variantes de productos")
    print(f"  ✓ {len(seeder.customers)} clientes y {len(seeder.drivers)} repartidores")

    try:
        indexes = [f"CREATE INDEX IF NOT EXISTS seed_tmp_{t}_{k} ON {t} ({k})" for t, k, _ in EVENT_COLUMNS]
        for statement in indexes:
            db.execute(text(statement))
        db.commit()

        if simulate_days > 0:
            print(f"→ Simulando historial reciente ({simulate_days} días)...")
            seeder.start = seeder.today - timedelta(days=simulate_days)
            seeder.simulate()
        else:
            print("→ Historial omitido (--simulate-days 0)")

        print("→ Configurando estado del día de hoy (cajas abiertas, pedidos pendientes, reservas, recomendador)...")
        seeder.today_state()

        print("→ Ejecutando 12 verificaciones de integridad...")
        seeder.verify()
        print("✓ Todas las verificaciones pasaron con éxito.")

    finally:
        try:
            db.rollback()
            for table, key, _ in EVENT_COLUMNS:
                db.execute(text(f"DROP INDEX IF EXISTS seed_tmp_{table}_{key}"))
            db.commit()
        except Exception:
            pass
        finally:
            db.close()

    return seeder


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--simulate-days", type=int, default=5, help="Días recientes de historial a simular (por defecto 5, 0 para ir directo a hoy)")
    parser.add_argument("--database-url", help="Base destino (por defecto, DATABASE_URL del .env)")
    parser.add_argument("--assets-base-url", default="http://localhost:8000", help="Dónde sirve el backend /demo-assets")
    args = parser.parse_args()

    seeder = run_continue(database_url=args.database_url, simulate_days=args.simulate_days, assets_base_url=args.assets_base_url)
    print("\nResumen:")
    for key, value in sorted(seeder.stats.items()):
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
