"""Realistic demo data for every use case, built through the REAL services.

    python -m scripts.seed_demo --reset [--database-url URL] [--assets-base-url http://localhost:8000] [--days 200]

What it does
1. --reset deletes every company and all business data (orders, sales, users...). It keeps the SaaS plans, the
   permission catalog and the system roles. Without --reset it refuses to run on a database that has companies.
2. Creates the superadmin, 4 companies (one per plan, see scripts/demo_people.py), 11 branches with their staff
   (1 manager and 2 cashiers each), suppliers, platform drivers, 66 customers and the 72-garment catalog of the
   first partial (scripts/data/demo_catalog.json), split by brand style, with stock per branch.
3. Simulates ~6 months of activity day by day with the same services the API uses: cash drawers with change,
   till sales (cash/QR, coupons, points), web orders paid with Stripe (pickup and delivery with drivers and PIN),
   reservations with their 50 % deposit, wishlists, views, supplier replenishments, subscription renewals and
   daily settlements. Each operation is then moved to its date, so every payment has its receipt, loyalty points,
   ledger row, stock movement and notification exactly as in real use.
4. Leaves today's state ready to demo: open drawers, orders to hand over or ship, reservations to attend,
   replenishment requests in every state, critical stock for the expert system, and retrains the recommender.

Receipts of the history are marked as already emailed, so the email loop never sends thousands of old mails.
"""
import argparse
import json
import random
import secrets
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from scripts import demo_people as people

LOCAL_TZ = timezone(timedelta(hours=-4))  # America/La_Paz
CATALOG = Path(__file__).parent / "data" / "demo_catalog.json"
KEEP_TABLES = {"saas_plans", "permissions"}
RNG = random.Random(2026)

# Event rows created by each simulated operation and the timestamp columns to move to the operation's date.
EVENT_COLUMNS = [
    ("orders", "created_at", ["created_at", "updated_at", "pickup_expires_at", "delivered_at"]),
    ("sales", "created_at", ["created_at", "updated_at"]),
    ("payment_transactions", "created_at", ["created_at"]),
    ("payment_receipts", "issued_at", ["issued_at"]),
    ("inventory_movements", "created_at", ["created_at"]),
    ("loyalty_ledger", "created_at", ["created_at"]),
    ("loyalty_accounts", "created_at", ["created_at", "updated_at"]),
    ("user_product_interactions", "created_at", ["created_at"]),
    ("notifications", "created_at", ["created_at"]),
    ("cash_sessions", "opened_at", ["opened_at", "closed_at"]),
    ("cash_movements", "created_at", ["created_at"]),
    ("reservations", "created_at", ["created_at", "updated_at", "expires_at", "payment_expires_at"]),
    ("promotion_code_usages", "used_at", ["used_at"]),
    ("qr_payments", "created_at", ["created_at", "expires_at", "paid_at"]),
    ("wishlist_items", "created_at", ["created_at"]),
    ("payment_attempts", "created_at", ["created_at", "updated_at"]),
    ("stripe_events", "created_at", ["created_at"]),
    ("replenishment_requests", "created_at", ["created_at", "updated_at", "accepted_at", "preparing_at",
                                               "awaiting_receipt_at", "delivered_at"]),
    ("tenant_subscriptions", "created_at", ["created_at", "updated_at", "start_date", "end_date"]),
    ("expert_transfer_suggestions", "created_at", ["created_at", "applied_at"]),
]


class Seeder:
    def __init__(self, db, assets_base_url: str, days: int):
        self.db = db
        self.assets = assets_base_url.rstrip("/") + "/demo-assets/"
        self.today = datetime.now(LOCAL_TZ).date()
        self.start = self.today - timedelta(days=days)
        self.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        self.companies: list[dict] = []
        self.customers = []
        self.drivers = []
        self.superadmin = None
        self.stats: dict[str, int] = {}

    # --- helpers -----------------------------------------------------------------------------------------

    def count(self, key: str, n: int = 1) -> None:
        self.stats[key] = self.stats.get(key, 0) + n

    def skipped(self, what: str, error: Exception) -> None:
        """A business rule refused the operation (as it would in the app): report why instead of hiding it."""
        detail = getattr(error, "detail", None) or str(error)
        self.count(f"omitidas · {what}: {detail[:90]}")

    def url(self, value: str | None) -> str | None:
        if not value:
            return None
        return value if value.startswith("http") else self.assets + value

    def clock(self) -> datetime:
        """Lower bound of the rows the next operation creates (tolerates DB/app clock skew)."""
        db_now = self.db.execute(text("SELECT clock_timestamp()")).scalar()
        return min(db_now, datetime.now(timezone.utc)) - timedelta(seconds=60)

    def stamp(self, since: datetime, when: datetime) -> None:
        """Move everything created since `since` to `when` (keeps the intervals between them)."""
        delta = datetime.now(timezone.utc) - when
        for table, key, columns in EVENT_COLUMNS:
            sets = ", ".join(f"{c} = {c} - :delta" for c in columns)
            self.db.execute(text(f"UPDATE {table} SET {sets} WHERE {key} >= :since"), {"delta": delta, "since": since})
        days = (datetime.now(LOCAL_TZ).date() - when.astimezone(LOCAL_TZ).date()).days
        if days:
            self.db.execute(text("UPDATE reservations SET visit_date = visit_date - :d WHERE created_at >= :since"),
                            {"d": days, "since": since})
        self.db.commit()

    @staticmethod
    def at(day: date, hour: int, minute: int = 0) -> datetime:
        """A moment of that day; for today, always earlier than now (rows must never land in the future, and
        stay out of the next operation's capture window)."""
        moment = datetime.combine(day, time(hour, minute), tzinfo=LOCAL_TZ).astimezone(timezone.utc)
        latest = datetime.now(timezone.utc) - timedelta(minutes=10 + RNG.randint(0, 90))
        return min(moment, latest)

    def user(self, name, email, rol, gender, password, tenant_id=None, branch_id=None):
        from app.models.user import User
        from app.services.user_service import pwd_context

        row = User(name=name, email=email, hashed_password=pwd_context.hash(password), gender=gender, rol=rol,
                   tenant_id=tenant_id, branch_id=branch_id, is_active=True)
        self.db.add(row)
        self.db.flush()
        self.count(f"usuarios ({rol.value})")
        return row

    # --- 1. reset ----------------------------------------------------------------------------------------

    def reset(self, force: bool) -> None:
        import importlib
        import pathlib

        from app.core.database import Base

        has_data = self.db.execute(text("SELECT count(*) FROM tenants")).scalar()
        if has_data and not force:
            raise SystemExit(f"La base tiene {has_data} empresas. Usa --reset para borrarlas y cargar la demo.")
        for path in sorted(pathlib.Path(__file__).parents[1].joinpath("app/models").glob("*.py")):
            importlib.import_module("app.models." + path.stem)
        # Custom (company) roles go; system roles and the permission catalog stay.
        self.db.execute(text("DELETE FROM user_roles"))
        self.db.execute(text("DELETE FROM role_permissions WHERE role_id IN (SELECT id FROM roles WHERE NOT is_system)"))
        self.db.execute(text("DELETE FROM roles WHERE NOT is_system"))
        for table in reversed(Base.metadata.sorted_tables):  # children first
            if table.name not in KEEP_TABLES | {"roles", "role_permissions"}:
                self.db.execute(text(f"DELETE FROM {table.name}"))
        self.db.commit()
        print("Datos anteriores eliminados (se conservan planes, permisos y roles del sistema).")

    # --- 2. structure ------------------------------------------------------------------------------------

    def platform(self) -> None:
        from app.schemas.enums import GenderEnum, RolEnum

        sa = people.SUPERADMIN
        self.superadmin = self.user(sa["name"], sa["email"], RolEnum.superadministrador, GenderEnum.masculino, sa["password"])
        for name, gender in people.DRIVERS:
            self.drivers.append(self.user(name, people.email(name, "repartidores.demo.bo"), RolEnum.delivery,
                                          GenderEnum(gender), people.STAFF_PASSWORD))
        used = set()
        for name, gender, city in people.CUSTOMERS:
            address = people.email(name, "clientes.demo.bo")
            while address in used:
                address = address.replace("@", f"{len(used) % 9}@", 1)
            used.add(address)
            customer = self.user(name, address, RolEnum.cliente, GenderEnum(gender), people.CUSTOMER_PASSWORD)
            customer.city = city  # helper attribute (not a column): where the customer usually buys
            self.customers.append(customer)
        self.db.commit()

    def companies_and_staff(self) -> None:
        from app.models.branch import Branch
        from app.models.provider import Provider
        from app.models.subscription_plan import SubscriptionPlan
        from app.models.tenant import Tenant
        from app.schemas.enums import GenderEnum, RolEnum, TenantStatusEnum

        plans = {p.slug: p for p in self.db.query(SubscriptionPlan).all()}
        for spec in people.COMPANIES:
            plan = plans[spec["plan"]]
            tenant = Tenant(name=spec["name"], slug=spec["slug"], contact_email=spec["contact"], currency="BOB",
                            country="Bolivia", status=TenantStatusEnum.active, primary_color=spec["color"],
                            bank_name=spec["bank"][0], bank_account_number=spec["bank"][1], bank_account_holder=spec["bank"][2])
            self.db.add(tenant)
            self.db.flush()
            company = {"spec": spec, "tenant": tenant, "plan": plan, "branches": []}
            admin_name, admin_gender = spec["admin"]
            company["admin"] = self.user(admin_name, people.email(admin_name, spec["domain"]), RolEnum.administrador,
                                         GenderEnum(admin_gender), people.STAFF_PASSWORD, tenant.id)
            for b in spec["branches"]:
                branch = Branch(tenant_id=tenant.id, name=b["name"], city=b["city"], latitude=b["lat"], longitude=b["lng"],
                                is_default=b.get("default", False), is_active=True)
                self.db.add(branch)
                self.db.flush()
                manager = self.user(b["manager"][0], people.email(b["manager"][0], spec["domain"]), RolEnum.encargado,
                                    GenderEnum(b["manager"][1]), people.STAFF_PASSWORD, tenant.id, branch.id)
                cashiers = [self.user(n, people.email(n, spec["domain"]), RolEnum.cajero, GenderEnum(g),
                                      people.STAFF_PASSWORD, tenant.id, branch.id) for n, g in b["cashiers"]]
                company["branches"].append({"branch": branch, "manager": manager, "cashiers": cashiers})
                self.count("sucursales")
            company["suppliers"] = []
            for business, contact, gender, phone in spec["suppliers"]:
                owner = self.user(contact, people.email(contact, spec["domain"].replace(".demo.bo", "-proveedores.demo.bo")),
                                  RolEnum.proveedor, GenderEnum(gender), people.STAFF_PASSWORD, tenant.id)
                provider = Provider(tenant_id=tenant.id, user_id=owner.id, business_name=business, contact_name=contact,
                                    phone=phone)
                self.db.add(provider)
                self.db.flush()
                company["suppliers"].append({"provider": provider, "user": owner})
            self.count("empresas")
            self.companies.append(company)
        self.db.commit()

    def subscriptions(self) -> None:
        """Monthly periods since the start (each payment issues a platform receipt); the last one is current."""
        from app.schemas.enums import BillingCycleEnum, SubscriptionPaymentMethodEnum, SubscriptionStatusEnum
        from app.services.subscription_service import create_or_update_tenant_subscription

        for company in self.companies:
            tenant = company["tenant"]
            period_start = self.start
            while period_start <= self.today:
                since = self.clock()
                sub = create_or_update_tenant_subscription(
                    self.db, tenant.id, company["plan"].id, BillingCycleEnum.monthly,
                    SubscriptionPaymentMethodEnum.simulated_card, duration_days=30)
                self.db.commit()
                self.stamp(since, self.at(period_start, 9))
                period_start += timedelta(days=30)
                self.count("períodos de suscripción pagados")
            # A renewed period simply expired: it was not replaced by a plan change.
            self.db.execute(text("UPDATE tenant_subscriptions SET status = :active WHERE tenant_id = :t"),
                            {"active": SubscriptionStatusEnum.active.name, "t": tenant.id})
            self.db.commit()

    # --- 3. catalog --------------------------------------------------------------------------------------

    def catalog_and_stock(self) -> None:
        from app.models.category import Category
        from app.models.collection import Collection
        from app.models.color import Color
        from app.models.inventory import Inventory
        from app.models.inventory_movement import InventoryMovement
        from app.models.product import Product
        from app.models.product_variant import ProductVariant
        from app.models.provider_variant_availability import ProviderVariantAvailability
        from app.models.season import Season
        from app.models.size import Size
        from app.models.expert_replenishment import ExpertReplenishmentRule
        from app.schemas.catalog_enums import ProductStatusEnum
        from app.schemas.inventory_schema import InventoryMovementTypeEnum

        colors = {c["name"]: Color(name=c["name"], hex_code=c["hex"]) for c in self.catalog["colors"]}
        sizes = {s: Size(name=s) for s in self.catalog["sizes"]}
        self.db.add_all([*colors.values(), *sizes.values()])
        self.db.flush()
        dresses = [p for p in self.catalog["products"] if p["category"] == "Vestidos"]
        half = len(dresses) // 2
        stock_day = self.at(self.start - timedelta(days=1), 8)
        for company in self.companies:
            spec, tenant = company["spec"], company["tenant"]
            selected = [p for p in self.catalog["products"] if p["category"] in spec["categories"]]
            if spec.get("vestidos") == "first":
                selected = [p for p in selected if p["category"] != "Vestidos" or p in dresses[:half + 2]]
            elif spec.get("vestidos") == "second":
                selected = [p for p in selected if p["category"] != "Vestidos" or p in dresses[half - 2:]]
            categories = {name: Category(tenant_id=tenant.id, name=name) for name in sorted({p["category"] for p in selected})}
            seasons = {name: Season(tenant_id=tenant.id, name=name) for name in self.catalog["seasons"]}
            self.db.add_all([*categories.values(), *seasons.values()])
            self.db.flush()
            collections = {name: Collection(tenant_id=tenant.id, name=f"Colección {name}", season_id=season.id)
                           for name, season in seasons.items()}
            self.db.add_all(collections.values())
            self.db.flush()
            self.db.add(ExpertReplenishmentRule(tenant_id=tenant.id, lookback_days=14, coverage_days=10, is_auto_enabled=True))
            company["variants"] = []
            prefix = spec["key"][:3].upper()
            for index, item in enumerate(selected, start=1):
                provider = company["suppliers"][index % len(company["suppliers"])]["provider"]
                on_sale = index % 7 == 0  # some garments on sale
                product = Product(tenant_id=tenant.id, name=item["name"], description=item["description"],
                                  provider_id=provider.id, category_id=categories[item["category"]].id,
                                  collection_id=collections[item["season"]].id,
                                  discount_type="percentage" if on_sale else None, discount_value=15 if on_sale else None)
                self.db.add(product)
                self.db.flush()
                price = Decimal(str(round(item["price"] * spec["price_factor"]))).quantize(Decimal("1"))
                for variant_spec in item["variants"]:
                    color_code = "".join(w[0] for w in variant_spec["color"].replace("/", " ").split())[:3].upper()
                    variant = ProductVariant(
                        tenant_id=tenant.id, product_id=product.id,
                        sku=f"{prefix}-{item['key']:03d}-{color_code}-{variant_spec['size']}",
                        price=Decimal(str(variant_spec["price"])) if variant_spec["price"] else price,
                        size_id=sizes[variant_spec["size"]].id, color_id=colors[variant_spec["color"]].id,
                        image_url=self.url(item["image_url"]), image_public_id=item["image_public_id"],
                        try_on_image_url=self.url(item["try_on_image_url"]), status=ProductStatusEnum.active)
                    self.db.add(variant)
                    self.db.flush()
                    company["variants"].append(variant)
                    self.db.add(ProviderVariantAvailability(provider_id=provider.id, variant_id=variant.id,
                                                            quantity=RNG.randint(40, 200)))
                    for entry in company["branches"]:
                        branch = entry["branch"]
                        if RNG.random() < 0.12 and not branch.is_default:
                            continue  # not every branch carries every size
                        quantity = RNG.randint(14, 34)
                        self.db.add(Inventory(tenant_id=tenant.id, variant_id=variant.id, branch_id=branch.id,
                                              quantity=quantity, reserved_quantity=0, minimum_stock=RNG.choice([4, 5, 6, 8])))
                        self.db.add(InventoryMovement(tenant_id=tenant.id, variant_id=variant.id, branch_id=branch.id,
                                                      movement_type=InventoryMovementTypeEnum.income, quantity=quantity,
                                                      created_by=company["admin"].id, note="Inventario inicial de apertura",
                                                      created_at=stock_day))
                self.count("prendas (productos)")
            self.count("variantes (talla/color)", len(company["variants"]))
        self.db.commit()

    def coupons(self) -> None:
        from app.schemas.promotion_schema import PromotionCodeCreate
        from app.services.promotion_service import create_code

        for company in self.companies:
            key = company["spec"]["key"].upper()
            first = company["branches"][0]["branch"]
            specs = [
                (f"{key}BIENVENIDA", "percentage", 10, None, None, None),
                (f"{key}INVIERNO", "percentage", 15, self.at(self.start, 0), self.at(self.start + timedelta(days=60), 0), None),
                (f"{key}FIDELIDAD20", "fixed", 20, None, None, None),
                (f"{key}TIENDA{first.city[:3].upper()}", "percentage", 12, None, None, first.id),
            ]
            company["coupons"] = []
            for code, kind, value, start, end, branch_id in specs:
                created = create_code(self.db, PromotionCodeCreate(code=code, discount_type=kind, discount_value=value,
                                                                   valid_from=start, valid_until=end, branch_id=branch_id),
                                      company["admin"].id, company["tenant"].id)
                company["coupons"].append({"code": created.code, "valid_until": end, "branch_id": branch_id})
            self.count("cupones", len(specs))
        self.db.commit()

    # --- 4. daily simulation -------------------------------------------------------------------------------

    def stock_rows(self, branch_id):
        from app.models.inventory import Inventory

        return [row for row in self.db.query(Inventory).filter(Inventory.branch_id == branch_id).all()
                if row.quantity - row.reserved_quantity > 2]

    def pick_items(self, branch_id, max_lines=3):
        rows = self.stock_rows(branch_id)
        if not rows:
            return []
        chosen = RNG.sample(rows, k=min(len(rows), RNG.choice([1, 1, 1, 2, 2, max_lines])))
        return [(row.variant_id, 1 if RNG.random() < 0.85 else 2) for row in chosen]

    def customers_near(self, city):
        near = [c for c in self.customers if c.city == city]
        return near or self.customers

    def till_day(self, company, entry, day: date) -> None:
        """One cashier opens the drawer, sells during the day (cash with change or QR) and closes counting."""
        from app.models.user import User
        from app.schemas.order_schema import PaymentMethodEnum
        from app.schemas.sales_schema import SaleCreate, SaleItemCreate
        from app.services import cash_session_service
        from app.services.qr_payment_service import confirm_qr_payment, create_qr
        from app.services.sales_service import create_sale, quote_sale_total

        weekend = day.weekday() >= 5
        sales_today = RNG.randint(1, 4) + (2 if weekend else 0) - (1 if RNG.random() < 0.25 else 0)
        if sales_today <= 0:
            return
        cashier = entry["cashiers"][day.toordinal() % 2]
        cashier = self.db.query(User).filter(User.id == cashier.id).one()
        branch, tenant_id = entry["branch"], company["tenant"].id
        since = self.clock()
        cash_session_service.open_session(self.db, cashier, Decimal(RNG.choice([100, 150, 200, 300])))
        self.stamp(since, self.at(day, 9, RNG.randint(0, 20)))
        for n in range(sales_today):
            items = self.pick_items(branch.id)
            if not items:
                break
            customer = RNG.choice(self.customers_near(branch.city)) if RNG.random() < 0.45 else None
            payload = {"items": [SaleItemCreate(variant_id=v, quantity=q) for v, q in items],
                       "payment_method": PaymentMethodEnum.cash}
            if customer:
                payload["customer_email"] = customer.email
                if RNG.random() < 0.08:
                    active = [c for c in company["coupons"] if (c["valid_until"] is None or c["valid_until"] > self.at(day, 12))
                              and c["branch_id"] in (None, branch.id)]
                    if active:
                        payload["promotion_code"] = RNG.choice(active)["code"]
            when = self.at(day, RNG.randint(10, 19), RNG.randint(0, 59))
            since = self.clock()
            try:
                if RNG.random() < 0.3:
                    payload["payment_method"] = PaymentMethodEnum.qr
                    total = quote_sale_total(self.db, cashier.id, SaleCreate(**payload), branch.id, tenant_id)
                    qr = create_qr(self.db, tenant_id=tenant_id, purpose="sale", amount=total, currency="bob",
                                   created_by=cashier.id, branch_id=branch.id)
                    self.db.commit()
                    confirm_qr_payment(self.db, qr.reference)
                    payload["qr_reference"] = qr.reference
                else:
                    total = quote_sale_total(self.db, cashier.id, SaleCreate(**payload), branch.id, tenant_id)
                    # Customers usually pay with a round bill: the drawer records the change.
                    payload["cash_received"] = max(total, Decimal(str(((int(total) // 50) + 1) * 50)) if RNG.random() < 0.7 else total)
                create_sale(self.db, cashier.id, SaleCreate(**payload), branch.id, tenant_id)
                self.count("ventas en caja")
            except (ValueError, HTTPException) as error:
                self.db.rollback()  # e.g. a coupon already used by that customer
                self.skipped("venta en caja", error)
            self.stamp(since, when)  # also what a refused attempt left (e.g. a paid QR)
        drawer = cash_session_service.get_open_session(self.db, cashier.id)
        expected = cash_session_service.expected_cash(drawer)
        difference = Decimal(RNG.choice([0] * 18 + [-5, -10, 2]))  # most drawers balance
        since = self.clock()
        # Closing keeps the opening row's date; only the closing time is set to the evening.
        cash_session_service.close_session(self.db, cashier, expected + difference,
                                           "Faltó sencillo" if difference < 0 else ("Sobrante del día" if difference > 0 else None))
        close_at = self.at(day, 20, RNG.randint(0, 30))
        self.db.execute(text("UPDATE cash_sessions SET closed_at = :at WHERE id = :id"), {"at": close_at, "id": drawer.id})
        self.db.commit()
        self.count("cajas abiertas y cerradas")

    def web_order(self, company, day: date, delivery: bool = False, reservation=None, paid=True, finish=True):
        """Customer buys online (Stripe), picks it up or receives it at home (driver + PIN)."""
        from app.models.order import Order
        from app.schemas.cart_schema import CartItemCreate
        from app.schemas.delivery_schema import DeliveryAddress
        from app.schemas.order_schema import PaymentMethodEnum
        from app.schemas.promotion_schema import PromotionCodeApply
        from app.services import cart_service, delivery_service
        from app.services.order_service import _consume_order, _locked_cart, _new_order, hand_over_order, mark_order_ready

        entry = RNG.choice(company["branches"])
        branch = entry["branch"]
        customer = reservation["customer"] if reservation else RNG.choice(self.customers_near(branch.city))
        when = self.at(day, RNG.randint(8, 22), RNG.randint(0, 59))
        since = self.clock()
        try:
            if reservation:
                branch = reservation["branch"]  # its garments were already moved to the cart
            else:
                items = self.pick_items(branch.id, max_lines=2)
                if not items:
                    return None
                for variant_id, quantity in items:
                    cart_service.add_cart_item(self.db, customer.id, CartItemCreate(variant_id=variant_id, branch_id=branch.id,
                                                                                    quantity=quantity))
                if RNG.random() < 0.12:
                    active = [c for c in company["coupons"] if c["branch_id"] is None
                              and (c["valid_until"] is None or c["valid_until"] > when)]
                    if active:
                        try:
                            cart_service.apply_coupon(self.db, customer.id, PromotionCodeApply(code=RNG.choice(active)["code"]))
                        except (ValueError, HTTPException):
                            self.db.rollback()  # e.g. the customer already used that coupon
            address = None
            if delivery:
                street, lat, lng = RNG.choice(people.NEIGHBORHOODS[branch.city])
                address = DeliveryAddress(address=street, reference=RNG.choice([None, "Portón negro", "Edificio, 3er piso", "Frente a la plaza"]),
                                          latitude=lat, longitude=lng)
            cart = _locked_cart(self.db, customer.id)
            order = _new_order(self.db, cart, customer.id, branch.id, PaymentMethodEnum.stripe, address,
                               self.points_to_use(company, customer))
            order.stripe_payment_intent_id = f"pi_demo_{secrets.token_hex(8)}"
            self.db.commit()
            if not paid:
                self.stamp(since, when)
                return order
            _consume_order(self.db, order)  # what the Stripe webhook does on payment_intent.succeeded
            self.db.commit()
            if finish and delivery:
                mark_order_ready(self.db, order.id, branch.id, company["tenant"].id)
                driver = RNG.choice(self.drivers)
                delivery_service.claim_order(self.db, order.id, driver.id)
                pin = self.db.query(Order.delivery_pin).filter(Order.id == order.id).scalar()
                delivery_service.confirm_delivery(self.db, order.id, pin, driver.id)
            elif finish:
                code = self.db.query(Order.pickup_code).filter(Order.id == order.id).scalar()
                hand_over_order(self.db, order.id, code, branch.id, company["tenant"].id)
            self.count("pedidos web pagados con Stripe" + (" (envío)" if delivery else ""))
        except (ValueError, LookupError, HTTPException) as error:
            self.db.rollback()
            self.clear_cart(customer.id)
            self.skipped("pedido web", error)
            self.stamp(since, when)
            return None
        self.stamp(since, when)
        return order

    def points_to_use(self, company, customer) -> int:
        from app.models.loyalty import LoyaltyAccount

        balance = self.db.query(LoyaltyAccount.points_balance).filter(
            LoyaltyAccount.tenant_id == company["tenant"].id, LoyaltyAccount.user_id == customer.id).scalar() or 0
        return (balance // 10 // 2) * 10 if balance >= 100 and RNG.random() < 0.3 else 0

    def clear_cart(self, user_id) -> None:
        from app.models.cart import Cart
        from app.models.cart_item import CartItem
        from app.services.cart_service import refresh_cart_totals

        cart = self.db.query(Cart).filter(Cart.user_id == user_id).first()
        if cart:
            self.db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
            cart.promotion_code_id = None
            refresh_cart_totals(self.db, cart)
            self.db.commit()

    def reservation(self, company, day: date, outcome: str):
        """Reserve with the 50 % deposit (Stripe) and follow it to the outcome: sold, not_sold, cancelled, expired."""
        from app.schemas.reservation_schema import ReservationCreate, ReservationItemCreate
        from app.services import reservation_service as rs

        entry = RNG.choice(company["branches"])
        branch = entry["branch"]
        customer = RNG.choice(self.customers_near(branch.city))
        items = self.pick_items(branch.id, max_lines=2)
        if not items:
            return
        since = self.clock()
        when = self.at(day, RNG.randint(9, 21), RNG.randint(0, 59))
        try:
            created = rs.create_reservation(self.db, customer.id, ReservationCreate(
                branch_id=branch.id, visit_date=datetime.now(LOCAL_TZ).date() + timedelta(days=RNG.randint(1, 3)),
                items=[ReservationItemCreate(variant_id=v, quantity=q) for v, q in items]))
            reservation_id = created["id"]
            if outcome == "expired":
                self.db.execute(text("UPDATE reservations SET payment_expires_at = now() - interval '1 minute' WHERE id = :id"),
                                {"id": reservation_id})
                self.db.commit()
                rs.expire_due_reservations(self.db)
            else:
                rs.complete_deposit_payment(self.db, reservation_id, "card", f"pi_demo_dep_{secrets.token_hex(6)}")
                self.db.commit()
                if outcome == "cancelled":
                    rs.cancel_reservation(self.db, customer.id, reservation_id)
                elif outcome != "paid_only":
                    rs.confirm_reservation_arrival(self.db, reservation_id, branch.id)
                    rs.attend_reservation(self.db, reservation_id, branch.id)
                    if outcome == "sold":
                        rs.decide_reservation(self.db, customer.id, reservation_id, True)
                        rs.transfer_reservation_to_cart(self.db, customer.id, reservation_id)
                        self.stamp(since, when)
                        self.web_order(company, day, reservation={"customer": customer, "branch": branch})
                        self.count("reservas vendidas")
                        return
                    rs.decide_reservation(self.db, customer.id, reservation_id, False)
            self.count(f"reservas ({outcome})")
        except (ValueError, LookupError, HTTPException) as error:
            self.db.rollback()
            self.skipped("reserva", error)
        self.stamp(since, when)

    def browsing(self, company, day: date) -> None:
        """Views, favorites and carts: the signals of the recommender (CU6)."""
        from app.services.recommendation_service import record_product_view
        from app.services.wishlist_service import AlreadySaved, add_item

        since = self.clock()
        for _ in range(RNG.randint(2, 6)):
            customer = RNG.choice(self.customers)
            variant = RNG.choice(company["variants"])
            record_product_view(self.db, customer.id, variant.product_id, variant.id, None)
            if RNG.random() < 0.18:
                try:
                    add_item(self.db, customer.id, variant.product_id)
                    self.count("favoritos")
                except (AlreadySaved, LookupError):
                    self.db.rollback()
        self.stamp(since, self.at(day, RNG.randint(8, 23)))

    def replenishment(self, company, day: date, final_status: str) -> None:
        from app.schemas.enums import RolEnum
        from app.schemas.replenishment_schema import ReplenishmentItemCreate, ReplenishmentRequestCreate, ReplenishmentStatusEnum
        from app.services.replenishment_service import create_request, transition_request

        entry = RNG.choice(company["branches"])
        supplier = RNG.choice(company["suppliers"])
        from app.models.product import Product

        variants = [v for v in company["variants"]
                    if self.db.query(Product.provider_id).filter(Product.id == v.product_id).scalar() == supplier["provider"].id]
        if not variants:
            return
        since = self.clock()
        request = create_request(self.db, ReplenishmentRequestCreate(
            provider_id=supplier["provider"].id, branch_id=entry["branch"].id,
            items=[ReplenishmentItemCreate(variant_id=v.id, requested_quantity=RNG.choice([10, 12, 15, 20]))
                   for v in RNG.sample(variants, k=min(3, len(variants)))]),
            entry["manager"].id, tenant_id=company["tenant"].id)
        steps = ["accepted", "preparing", "awaiting_receipt", "delivered"]
        for step in steps[:steps.index(final_status) + 1] if final_status != "requested" else []:
            is_supplier = step != "delivered"
            transition_request(self.db, request.id, ReplenishmentStatusEnum(step),
                               RolEnum.proveedor.value if is_supplier else RolEnum.encargado.value,
                               supplier["user"].id if is_supplier else entry["manager"].id,
                               None if is_supplier else entry["branch"].id, tenant_id=company["tenant"].id)
        self.stamp(since, self.at(day, 11, RNG.randint(0, 59)))
        self.count(f"solicitudes a proveedor ({final_status})")

    def settle(self, day: date) -> None:
        """Daily settlement of the online payments; transfers registered by the superadmin two days later."""
        from app.services.payout_service import mark_settlement_paid, run_daily_settlements

        for settlement in run_daily_settlements(self.db, today=day + timedelta(days=1)):
            self.db.execute(text("UPDATE settlements SET created_at = :at WHERE id = :id"),
                            {"at": self.at(day + timedelta(days=1), 1), "id": settlement.id})
            if day < self.today - timedelta(days=2):
                mark_settlement_paid(self.db, settlement.id, f"TRF-{day:%Y%m%d}-{secrets.token_hex(3).upper()}",
                                     self.superadmin.id)
                self.db.execute(text("UPDATE settlements SET paid_at = :at WHERE id = :id"),
                                {"at": self.at(day + timedelta(days=2), 10), "id": settlement.id})
            self.count("liquidaciones diarias")
        self.db.commit()

    def simulate(self) -> None:
        day = self.start
        total = (self.today - self.start).days
        while day < self.today:
            for company in self.companies:
                for entry in company["branches"]:
                    self.till_day(company, entry, day)
                for _ in range(RNG.choice([0, 1, 1, 2, 2, 3])):
                    self.web_order(company, day, delivery=RNG.random() < 0.3)
                if RNG.random() < 0.35:
                    self.reservation(company, day, RNG.choice(["sold", "sold", "sold", "not_sold", "cancelled", "expired"]))
                self.browsing(company, day)
                if day.day in (5, 20):
                    self.replenishment(company, day, "delivered")
            self.settle(day)
            if (day - self.start).days % 15 == 0:
                print(f"  {day:%d/%m/%Y}  ({(day - self.start).days}/{total} días)")
            day += timedelta(days=1)

    # --- 5. today's state ----------------------------------------------------------------------------------

    def today_state(self) -> None:
        from app.models.inventory import Inventory
        from app.models.inventory_movement import InventoryMovement
        from app.models.user import User
        from app.schemas.inventory_schema import InventoryMovementTypeEnum
        from app.services import cash_session_service
        from app.services.expert_replenishment_service import evaluate
        from app.services.recommendation_service import train

        for company in self.companies:
            # Open drawers of the morning shift, with a couple of sales already.
            for entry in company["branches"][:2]:
                cashier = self.db.query(User).filter(User.id == entry["cashiers"][0].id).one()
                cash_session_service.open_session(self.db, cashier, Decimal(200))
            # Orders waiting at the counter / to be shipped, and one pending payment.
            for delivery in (False, False, True):
                self.web_order(company, self.today, delivery=delivery, finish=False)
            self.web_order(company, self.today, paid=False)
            # Reservations to attend today and one waiting for its deposit.
            for outcome in ("paid_only", "paid_only"):
                self.reservation(company, self.today, outcome)
            # Supplier requests in every state of the workflow.
            for status in ("requested", "accepted", "preparing", "awaiting_receipt"):
                self.replenishment(company, self.today, status)
            # Critical stock in the main branch so the expert system has something to suggest.
            main = company["branches"][0]["branch"]
            low = self.db.query(Inventory).filter(Inventory.branch_id == main.id, Inventory.reserved_quantity == 0,
                                                  Inventory.quantity > Inventory.minimum_stock).limit(4).all()
            for row in low:
                # Damaged garments written off: an outcome movement keeps stock and history consistent.
                lost = row.quantity - max(row.minimum_stock - 2, 1)
                row.quantity -= lost
                self.db.add(InventoryMovement(tenant_id=row.tenant_id, variant_id=row.variant_id, branch_id=row.branch_id,
                                              movement_type=InventoryMovementTypeEnum.outcome, quantity=lost,
                                              created_by=company["branches"][0]["manager"].id,
                                              note="Baja por prendas dañadas en vitrina"))
            self.db.commit()
            evaluate(self.db, company["tenant"].id)
        # Last of all: nothing runs after them, so their 30-minute deposit window stays open.
        for company in self.companies:
            self.reservation_waiting_deposit(company)
        # History receipts count as already delivered: the email loop must not send months of old mail.
        self.db.execute(text("UPDATE payment_receipts SET emailed_at = issued_at, email_attempts = 1 "
                             "WHERE issued_at < :today"), {"today": self.at(self.today, 0)})
        self.db.execute(text("UPDATE notifications SET read_at = created_at + interval '2 hours' "
                             "WHERE created_at < :recent"), {"recent": self.at(self.today - timedelta(days=3), 0)})
        self.db.commit()
        users, products = train(self.db)
        print(f"  Recomendador entrenado: {users} clientes, {products} prendas.")

    def reservation_waiting_deposit(self, company) -> None:
        from app.schemas.reservation_schema import ReservationCreate, ReservationItemCreate
        from app.services import reservation_service as rs

        branch = company["branches"][0]["branch"]
        items = self.pick_items(branch.id, max_lines=1)
        if not items:
            return
        try:
            rs.create_reservation(self.db, RNG.choice(self.customers_near(branch.city)).id, ReservationCreate(
                branch_id=branch.id, visit_date=self.today + timedelta(days=2),
                items=[ReservationItemCreate(variant_id=v, quantity=q) for v, q in items]))
            self.count("reservas esperando anticipo")
        except ValueError:
            self.db.rollback()

    # --- 6. checks ---------------------------------------------------------------------------------------

    def verify(self) -> None:
        checks = {
            "stock negativo": "SELECT count(*) FROM inventory WHERE quantity < 0 OR reserved_quantity < 0 OR reserved_quantity > quantity",
            "pedido pagado sin comprobante": "SELECT count(*) FROM orders o WHERE o.payment_status = 'paid' AND NOT EXISTS "
                                             "(SELECT 1 FROM payment_receipts r WHERE r.kind = 'order' AND r.source_id = o.id)",
            "venta sin comprobante": "SELECT count(*) FROM sales s WHERE NOT EXISTS "
                                     "(SELECT 1 FROM payment_receipts r WHERE r.kind = 'sale' AND r.source_id = s.id)",
            "venta sin caja": "SELECT count(*) FROM sales s WHERE NOT EXISTS "
                              "(SELECT 1 FROM cash_movements m WHERE m.source_id = s.id)",
            "personal sin sucursal": "SELECT count(*) FROM users WHERE rol IN ('encargado', 'cajero') AND branch_id IS NULL",
            "sucursal de otra empresa": "SELECT count(*) FROM users u JOIN branches b ON b.id = u.branch_id WHERE u.tenant_id <> b.tenant_id",
            "inventario de otra empresa": "SELECT count(*) FROM inventory i JOIN branches b ON b.id = i.branch_id WHERE i.tenant_id <> b.tenant_id",
            "venta en sucursal ajena al cajero": "SELECT count(*) FROM sales s JOIN users u ON u.id = s.user_id WHERE u.branch_id <> s.branch_id",
            "caja mezclando sucursales": "SELECT count(*) FROM cash_sessions c JOIN users u ON u.id = c.cashier_id WHERE u.branch_id <> c.branch_id",
            "cajas abiertas por cajero > 1": "SELECT count(*) FROM (SELECT cashier_id FROM cash_sessions WHERE status = 'open' "
                                             "GROUP BY cashier_id HAVING count(*) > 1) x",
            "pedido web en efectivo o QR": "SELECT count(*) FROM orders WHERE payment_method <> 'stripe'",
            "fechas en el futuro": "SELECT count(*) FROM sales WHERE created_at > now() + interval '1 minute'",
        }
        failed = False
        for label, sql in checks.items():
            value = self.db.execute(text(sql)).scalar()
            failed |= bool(value)
            print(f"  [{'OK' if not value else 'ERROR'}] {label}: {value}")
        if failed:
            raise SystemExit("La verificación encontró inconsistencias.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="Borrar las empresas actuales y sus datos")
    parser.add_argument("--database-url", help="Base destino (por defecto, DATABASE_URL del .env)")
    parser.add_argument("--assets-base-url", default="http://localhost:8000", help="Dónde sirve el backend /demo-assets")
    parser.add_argument("--days", type=int, default=200, help="Días de historial a simular")
    args = parser.parse_args()

    from app.core.config import settings

    engine = create_engine(args.database_url or settings.database_url)
    db = sessionmaker(bind=engine, autoflush=False)()
    seeder = Seeder(db, args.assets_base_url, args.days)
    try:
        print("1/6 Reinicio")
        seeder.reset(args.reset)
        indexes = [f"CREATE INDEX IF NOT EXISTS seed_tmp_{t}_{k} ON {t} ({k})" for t, k, _ in EVENT_COLUMNS]
        for statement in indexes:  # the per-operation date moves stay fast while tables grow
            db.execute(text(statement))
        db.commit()
        print("2/6 Plataforma, empresas, sucursales y personal")
        seeder.platform()
        seeder.companies_and_staff()
        seeder.subscriptions()
        print("3/6 Catálogo, stock y cupones")
        seeder.catalog_and_stock()
        seeder.coupons()
        print(f"4/6 Historial de {args.days} días")
        seeder.simulate()
        print("5/6 Estado de hoy")
        seeder.today_state()
        print("6/6 Verificación")
        seeder.verify()
    finally:
        for table, key, _ in EVENT_COLUMNS:
            db.execute(text(f"DROP INDEX IF EXISTS seed_tmp_{table}_{key}"))
        db.commit()
        db.close()
    print("\nResumen:")
    for key, value in sorted(seeder.stats.items()):
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
