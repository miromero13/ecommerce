from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pandas as pd
from sqlalchemy import inspect, select

from app.auth.hash import hash_password
from app.core.database import SessionLocal, engine
from app.models.branch import Branch
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.category import Category
from app.models.collection import Collection
from app.models.color import Color
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.provider import Provider
from app.models.reservation import Reservation
from app.models.reservation_item import ReservationItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.season import Season
from app.models.size import Size
from app.models.user import User
from app.schemas.catalog_enums import ProductStatusEnum
from app.schemas.cart_schema import CartStatusEnum
from app.schemas.inventory_schema import InventoryMovementTypeEnum
from app.schemas.enums import GenderEnum, ProviderStatusEnum, RolEnum
from app.schemas.order_schema import OrderStatusEnum, PaymentMethodEnum, PaymentStatusEnum
from app.schemas.reservation_schema import ReservationStatusEnum
from app.schemas.sales_schema import SaleStatusEnum


PASSWORD = "Fashion123!"


def main() -> None:
    _ensure_tables()
    session = SessionLocal()
    try:
        _reset_demo_data(session)
        branches = _seed_branches(session)
        users = _seed_users(session, branches)
        providers = _seed_providers(session, branches)
        categories = _seed_categories(session)
        sizes = _seed_sizes(session)
        colors = _seed_colors(session)
        seasons = _seed_seasons(session)
        collections = _seed_collections(session, seasons)
        product_variants = _seed_products(session, categories, sizes, colors, seasons, collections, providers)
        _seed_inventory(session, branches, users, product_variants)
        clients = [user for user in users if user.rol == RolEnum.cliente]
        cashiers = [user for user in users if user.rol == RolEnum.cajero]
        carts = _seed_carts(session, clients, branches, product_variants)
        reservations = _seed_reservations(session, clients, branches, product_variants)
        orders = _seed_orders(session, clients, product_variants)
        sales = _seed_sales(session, cashiers, branches, product_variants, reservations)
        _verify_seed(
            session,
            branches,
            users,
            providers,
            categories,
            sizes,
            colors,
            seasons,
            collections,
            product_variants,
            carts,
            reservations,
            orders,
            sales,
        )
        session.commit()
        print("Seeder demo ejecutado correctamente")
        print(f"- Sucursales: {len(branches)}")
        print(f"- Usuarios: {len(users)}")
        print(f"- Proveedores: {len(providers)}")
        print(f"- Variantes de producto: {len(product_variants)}")
        print(f"- Carritos: {len(carts)}")
        print(f"- Reservas: {len(reservations)}")
        print(f"- Ordenes: {len(orders)}")
        print(f"- Ventas: {len(sales)}")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _ensure_tables() -> None:
    required_tables = {
        "branches",
        "users",
        "providers",
        "categories",
        "sizes",
        "colors",
        "seasons",
        "collections",
        "products",
        "product_variants",
        "inventory",
        "inventory_movements",
        "carts",
        "cart_items",
        "reservations",
        "reservation_items",
        "orders",
        "order_items",
        "sales",
        "sale_items",
    }
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    missing = sorted(required_tables - existing)
    if missing:
        raise RuntimeError(
          "Faltan tablas para ejecutar el seeder. Ejecuta primero las migraciones: " + ", ".join(missing)
        )


def _hash_password() -> str:
    return hash_password(PASSWORD)


def _get_or_create(session, model, lookup: dict, defaults: dict | None = None):
    query = select(model)
    for key, value in lookup.items():
        query = query.where(getattr(model, key) == value)
    instance = session.execute(query).scalars().first()
    if instance:
        if defaults:
            for key, value in defaults.items():
                setattr(instance, key, value)
        return instance, False

    payload = {**lookup, **(defaults or {})}
    instance = model(**payload)
    session.add(instance)
    session.flush()
    return instance, True


def _reset_demo_data(session) -> None:
    """Elimina datos generados por ejecuciones anteriores para mantener conteos deterministas."""
    delete_order = [
        SaleItem,
        Sale,
        OrderItem,
        Order,
        ReservationItem,
        Reservation,
        CartItem,
        Cart,
        InventoryMovement,
        Inventory,
        ProductVariant,
        Product,
        Collection,
        Season,
        Category,
        Size,
        Color,
    ]
    for model in delete_order:
        for instance in session.execute(select(model)).scalars().all():
            session.delete(instance)
        session.flush()


def _dataframe(model, rows: list[dict]) -> pd.DataFrame:
    """Normaliza registros del seed a una tabla pandas para validarlos por lotes."""
    return pd.DataFrame(rows, columns=list(model.__table__.columns.keys()))


def _enum_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _verify_seed(
    session,
    branches: list[Branch],
    users: list[User],
    providers: list[Provider],
    categories: list[Category],
    sizes: list[Size],
    colors: list[Color],
    seasons: list[Season],
    collections: list[Collection],
    product_variants: list[tuple[Product, ProductVariant]],
    carts: list[Cart],
    reservations: list[Reservation],
    orders: list[Order],
    sales: list[Sale],
) -> None:
    models = [
        Branch,
        User,
        Provider,
        Category,
        Size,
        Color,
        Season,
        Collection,
        Product,
        ProductVariant,
        Inventory,
        InventoryMovement,
        Cart,
        CartItem,
        Reservation,
        ReservationItem,
        Order,
        OrderItem,
        Sale,
        SaleItem,
    ]
    frames: dict[str, pd.DataFrame] = {}
    for model in models:
        instances = session.execute(select(model)).scalars().all()
        rows = [{column.name: getattr(instance, column.name) for column in model.__table__.columns} for instance in instances]
        frames[model.__tablename__] = _dataframe(model, rows)

    if len(branches) != 3 or len(providers) != 4 or len(categories) != 6:
        raise RuntimeError("Fallo de conteo en la estructura base del seed")
    if len(product_variants) < 50:
        raise RuntimeError("El seed debe generar al menos 50 variantes")
    if frames["products"].shape[0] != 50:
        raise RuntimeError(f"Se esperaban 50 productos y se encontraron {frames['products'].shape[0]}")

    users_frame = frames["users"]
    if users_frame["email"].duplicated().any():
        raise RuntimeError("Existen emails duplicados en users")
    internal_roles = {RolEnum.administrador.value, RolEnum.encargado.value, RolEnum.cajero.value, RolEnum.delivery.value, RolEnum.proveedor.value}
    internal_users = users_frame[users_frame["rol"].map(_enum_value).isin(internal_roles)]
    branch_ids = {str(branch.id) for branch in branches}
    if internal_users["branch_id"].isna().any() or not internal_users["branch_id"].map(str).isin(branch_ids).all():
        raise RuntimeError("Hay usuarios internos sin una sucursal valida")

    providers_frame = frames["providers"]
    if providers_frame["user_id"].duplicated().any():
        raise RuntimeError("Cada proveedor debe tener un usuario unico")
    provider_user_ids = set(providers_frame["user_id"].map(str))
    provider_users = users_frame[users_frame["id"].map(str).isin(provider_user_ids)]
    if not (provider_users["rol"].map(_enum_value) == RolEnum.proveedor.value).all():
        raise RuntimeError("Todos los usuarios de proveedores deben tener rol proveedor")

    variants_frame = frames["product_variants"]
    if variants_frame["sku"].duplicated().any():
        raise RuntimeError("Existen SKU duplicados")
    if variants_frame.duplicated(subset=["product_id", "size_id", "color_id"]).any():
        raise RuntimeError("Existen combinaciones repetidas de variante")
    variant_counts = variants_frame.groupby("product_id").size()
    if (variant_counts < 1).any() or (variant_counts > 3).any():
        raise RuntimeError("Cada producto debe tener entre 1 y 3 variantes")
    if variants_frame["image_url"].notna().any() or variants_frame["image_public_id"].notna().any():
        raise RuntimeError("El seed no debe generar imagenes externas")

    inventory_frame = frames["inventory"]
    expected_inventory = len(variants_frame) * len(branches)
    if len(inventory_frame) != expected_inventory:
        raise RuntimeError(f"Se esperaban {expected_inventory} registros de inventory y se encontraron {len(inventory_frame)}")
    if (inventory_frame["quantity"] < inventory_frame["reserved_quantity"]).any():
        raise RuntimeError("Inventory tiene reserved_quantity mayor que quantity")
    inactive_ids = set(variants_frame.loc[variants_frame["status"].map(_enum_value) == ProductStatusEnum.inactive.value, "id"].map(str))
    inactive_inventory = inventory_frame[inventory_frame["variant_id"].map(str).isin(inactive_ids)]
    if not inactive_inventory.empty and (inactive_inventory["quantity"] != 0).any():
        raise RuntimeError("Las variantes inactivas deben tener inventario cero")

    for table_name, frame in frames.items():
        if frame.empty and table_name in {"cart_items", "reservation_items", "order_items", "sale_items"}:
            raise RuntimeError(f"La tabla {table_name} no puede estar vacia")

    for parent, items, item_table in [
        (carts, frames["cart_items"], "cart_id"),
        (reservations, frames["reservation_items"], "reservation_id"),
        (orders, frames["order_items"], "order_id"),
        (sales, frames["sale_items"], "sale_id"),
    ]:
        parent_ids = {str(instance.id) for instance in parent}
        item_counts = items[items[item_table].map(str).isin(parent_ids)].groupby(item_table).size()
        if any(item_counts.get(instance.id, 0) < 1 for instance in parent):
            raise RuntimeError(f"Hay registros sin items en {item_table}")

    _verify_amounts(frames["carts"], frames["cart_items"], "cart_id", "subtotal", "discount_amount", "total_amount", "unit_price", "quantity")
    _verify_amounts(frames["reservations"], frames["reservation_items"], "reservation_id", None, None, "total_amount", "unit_price", "quantity")
    _verify_amounts(frames["orders"], frames["order_items"], "order_id", "subtotal", "discount_amount", "total_amount", "unit_price", "quantity")
    _verify_amounts(frames["sales"], frames["sale_items"], "sale_id", "subtotal", "discount_amount", "total_amount", "unit_price", "quantity")


def _verify_amounts(
    parents: pd.DataFrame,
    items: pd.DataFrame,
    parent_key: str,
    subtotal_key: str | None,
    discount_key: str | None,
    total_key: str,
    unit_price_key: str,
    quantity_key: str,
) -> None:
    for _, parent in parents.iterrows():
        child_items = items[items[parent_key].map(str) == str(parent["id"])]
        subtotal = sum(Decimal(str(row[unit_price_key])) * int(row[quantity_key]) for _, row in child_items.iterrows())
        if subtotal_key is not None and _money(subtotal) != _money(parent[subtotal_key]):
            raise RuntimeError(f"Subtotal inconsistente en {parent_key}={parent['id']}")
        discount = Decimal(str(parent[discount_key])) if discount_key is not None else Decimal("0")
        if _money(subtotal - discount) != _money(parent[total_key]):
            raise RuntimeError(f"Total inconsistente en {parent_key}={parent['id']}")


def _seed_branches(session) -> list[Branch]:
    branches_payload = [
        {"name": "Sucursal Central La Paz", "city": "La Paz", "is_default": True},
        {"name": "Sucursal Norte Santa Cruz", "city": "Santa Cruz", "is_default": False},
        {"name": "Sucursal Centro Cochabamba", "city": "Cochabamba", "is_default": False},
    ]
    branches: list[Branch] = []
    for payload in branches_payload:
        branch, _ = _get_or_create(session, Branch, {"name": payload["name"]}, payload)
        branches.append(branch)
    return branches


def _seed_users(session, branches: list[Branch]) -> list[User]:
    users: list[User] = []
    password = _hash_password()

    users_payload = [
        {"name": "Admin Global", "email": "admin.global@fashionstore.bo", "gender": GenderEnum.masculino, "rol": RolEnum.administrador, "branch_id": branches[0].id},
        {"name": "Admin La Paz", "email": "admin.lp@fashionstore.bo", "gender": GenderEnum.femenino, "rol": RolEnum.administrador, "branch_id": branches[0].id},
        {"name": "Admin Santa Cruz", "email": "admin.sc@fashionstore.bo", "gender": GenderEnum.masculino, "rol": RolEnum.administrador, "branch_id": branches[1].id},
        {"name": "Admin Cochabamba", "email": "admin.cbba@fashionstore.bo", "gender": GenderEnum.femenino, "rol": RolEnum.administrador, "branch_id": branches[2].id},
        {"name": "Encargada La Paz", "email": "encargada.lp@fashionstore.bo", "gender": GenderEnum.femenino, "rol": RolEnum.encargado, "branch_id": branches[0].id},
        {"name": "Encargado Santa Cruz", "email": "encargado.sc@fashionstore.bo", "gender": GenderEnum.masculino, "rol": RolEnum.encargado, "branch_id": branches[1].id},
        {"name": "Encargado Cochabamba", "email": "encargado.cbba@fashionstore.bo", "gender": GenderEnum.masculino, "rol": RolEnum.encargado, "branch_id": branches[2].id},
        {"name": "Cajera La Paz", "email": "cajera.lp@fashionstore.bo", "gender": GenderEnum.femenino, "rol": RolEnum.cajero, "branch_id": branches[0].id},
        {"name": "Cajero Santa Cruz", "email": "cajero.sc@fashionstore.bo", "gender": GenderEnum.masculino, "rol": RolEnum.cajero, "branch_id": branches[1].id},
        {"name": "Cajera Cochabamba", "email": "cajera.cbba@fashionstore.bo", "gender": GenderEnum.femenino, "rol": RolEnum.cajero, "branch_id": branches[2].id},
        {"name": "Delivery Uno", "email": "delivery1@fashionstore.bo", "gender": GenderEnum.masculino, "rol": RolEnum.delivery, "branch_id": branches[0].id},
        {"name": "Delivery Dos", "email": "delivery2@fashionstore.bo", "gender": GenderEnum.femenino, "rol": RolEnum.delivery, "branch_id": branches[1].id},
    ]

    for payload in users_payload:
        user, _ = _get_or_create(
            session,
            User,
            {"email": payload["email"]},
            {
                "name": payload["name"],
                "gender": payload["gender"],
                "rol": payload["rol"],
                "branch_id": payload["branch_id"],
                "hashed_password": password,
            },
        )
        users.append(user)

    clients_payload = [
        ("Valeria", "Rojas"),
        ("Daniel", "Mamani"),
        ("Paola", "Lopez"),
        ("Martin", "Vargas"),
        ("Carla", "Quispe"),
        ("Jorge", "Arce"),
        ("Lucia", "Flores"),
        ("Andres", "Soto"),
        ("Sofia", "Paredes"),
        ("Diego", "Gutierrez"),
    ]

    genders = [GenderEnum.femenino, GenderEnum.masculino]
    for index, (first, last) in enumerate(clients_payload, start=1):
        gender = genders[index % 2]
        email = f"cliente{index:02d}.demo@fashionstore.bo"
        name = f"{first} {last}"
        user, _ = _get_or_create(
            session,
            User,
            {"email": email},
            {
                "name": name,
                "gender": gender,
                "rol": RolEnum.cliente,
                "branch_id": None,
                "hashed_password": password,
            },
        )
        users.append(user)

    return users


def _seed_providers(session, branches: list[Branch]) -> list[Provider]:
    providers_payload = [
        {
            "email": "proveedor1@fashionstore.bo",
            "name": "Textiles Andinos SRL",
            "contact": "Ana Villca",
            "phone": "+59170010001",
            "branch_id": branches[0].id,
            "gender": GenderEnum.femenino,
        },
        {
            "email": "proveedor2@fashionstore.bo",
            "name": "Moda Urbana Bolivia",
            "contact": "Luis Teran",
            "phone": "+59170010002",
            "branch_id": branches[1].id,
            "gender": GenderEnum.masculino,
        },
        {
            "email": "proveedor3@fashionstore.bo",
            "name": "Atelier del Sur",
            "contact": "Mariana Roca",
            "phone": "+59170010003",
            "branch_id": branches[2].id,
            "gender": GenderEnum.femenino,
        },
        {
            "email": "proveedor4@fashionstore.bo",
            "name": "Linea Nova",
            "contact": "Ricardo Flores",
            "phone": "+59170010004",
            "branch_id": branches[0].id,
            "gender": GenderEnum.masculino,
        },
    ]

    providers: list[Provider] = []
    for payload in providers_payload:
        user, _ = _get_or_create(
            session,
            User,
            {"email": payload["email"]},
            {
                "name": payload["contact"],
                "gender": payload["gender"],
                "rol": RolEnum.proveedor,
                "branch_id": payload["branch_id"],
                "hashed_password": _hash_password(),
            },
        )

        provider, _ = _get_or_create(
            session,
            Provider,
            {"user_id": user.id},
            {
                "branch_id": payload["branch_id"],
                "business_name": payload["name"],
                "contact_name": payload["contact"],
                "phone": payload["phone"],
                "status": ProviderStatusEnum.active,
            },
        )
        provider.branch_id = payload["branch_id"]
        provider.business_name = payload["name"]
        provider.contact_name = payload["contact"]
        provider.phone = payload["phone"]
        provider.status = ProviderStatusEnum.active
        providers.append(provider)

    return providers


def _seed_categories(session) -> list[Category]:
    names = ["Blusas", "Vestidos", "Faldas", "Pantalones", "Chaquetas", "Tops"]
    items = []
    for name in names:
        item, _ = _get_or_create(session, Category, {"name": name})
        items.append(item)
    return items


def _seed_sizes(session) -> list[Size]:
    names = ["XS", "S", "M", "L", "XL", "28", "30", "32", "34", "36", "38", "40"]
    items = []
    for name in names:
        item, _ = _get_or_create(session, Size, {"name": name})
        items.append(item)
    return items


def _seed_colors(session) -> list[Color]:
    colors = [
        ("Negro", "#111111"),
        ("Blanco", "#F8F8F8"),
        ("Azul Marino", "#1D3557"),
        ("Rojo", "#E63946"),
        ("Verde Oliva", "#606C38"),
        ("Beige", "#D4B483"),
        ("Gris", "#8D99AE"),
        ("Rosa", "#E9A3B4"),
        ("Marrón", "#7F5539"),
    ]
    items = []
    for name, hex_code in colors:
        item, _ = _get_or_create(session, Color, {"name": name}, {"hex_code": hex_code})
        item.hex_code = hex_code
        items.append(item)
    return items


def _seed_seasons(session) -> list[Season]:
    names = ["Primavera-Verano", "Otoño-Invierno"]
    items = []
    for name in names:
        item, _ = _get_or_create(session, Season, {"name": name})
        items.append(item)
    return items


def _seed_collections(session, seasons: list[Season]) -> list[Collection]:
    collection_payload = [
        {"name": "Mujer Urbana", "season": seasons[0]},
        {"name": "Elegancia Diaria", "season": seasons[1]},
        {"name": "Capsule Mujer", "season": seasons[0]},
        {"name": "Nocturna", "season": seasons[1]},
    ]
    items = []
    for payload in collection_payload:
        item, _ = _get_or_create(session, Collection, {"name": payload["name"]}, {"season_id": payload["season"].id})
        item.season_id = payload["season"].id
        items.append(item)
    return items


def _seed_products(
    session,
    categories: list[Category],
    sizes: list[Size],
    colors: list[Color],
    seasons: list[Season],
    collections: list[Collection],
    providers: list[Provider],
) -> list[tuple[Product, ProductVariant]]:
    category_styles = {
        "Blusas": ["Básica", "Satinada", "Manga Larga", "Volante", "Crop", "Lino", "Oversize", "Ajustada", "Tela Ligera"],
        "Vestidos": ["Casual", "Midi", "Fluido", "Noche", "Lino", "Camiseros", "Manga Corta", "Escote V", "Tirantes"],
        "Faldas": ["Mini", "Midi", "Plisada", "Recta", "A-line", "Corte Alto", "Denim", "Lino"],
        "Pantalones": ["Recto", "Palazzo", "Wide Leg", "Slim", "Tiro Alto", "Jogger", "Cropped", "Sastre"],
        "Chaquetas": ["Blazer", "Denim", "Biker", "Larga", "Ligera", "Acolchada", "Crop", "Estructurada"],
        "Tops": ["Rib", "Básico", "Escote Redondo", "Asimétrico", "Fitness", "Corto", "Satinado", "Sin Mangas"],
    }

    all_products: list[tuple[Product, ProductVariant]] = []
    sku_counter = 1001
    singular_names = {
        "Blusas": "Blusa",
        "Vestidos": "Vestido",
        "Faldas": "Falda",
        "Pantalones": "Pantalón",
        "Chaquetas": "Chaqueta",
        "Tops": "Top",
    }

    for category in categories:
        styles = category_styles[category.name]
        for index, style in enumerate(styles, start=1):
            status_cycle = [
                ProductStatusEnum.active,
                ProductStatusEnum.pending,
                ProductStatusEnum.active,
                ProductStatusEnum.inactive,
                ProductStatusEnum.active,
            ]
            status = status_cycle[(sku_counter + index) % len(status_cycle)]
            provider = None
            if (sku_counter + index) % 3 == 0:
                provider = providers[0]
            elif (sku_counter + index) % 4 == 0:
                provider = providers[1]

            variant_count = 1 + ((sku_counter + index) % 3)
            season = seasons[(sku_counter + index) % len(seasons)]
            collection = collections[(sku_counter + index) % len(collections)]

            price = Decimal(str(79 + ((sku_counter + index) % 7) * 15 + (index * 2)))
            product_name = f"{singular_names[category.name]} {style}"

            product, _ = _get_or_create(
                session,
                Product,
                {"name": product_name},
                {
                    "name": product_name,
                    "description": f"{product_name} de FashionStore, pensado para la demo del MVP.",
                    "price": price,
                    "provider_id": provider.id if provider else None,
                    "category_id": category.id,
                    "season_id": season.id,
                    "collection_id": collection.id,
                },
            )

            product.name = product_name
            product.description = f"{product_name} de FashionStore, pensado para la demo del MVP."
            product.price = price
            product.provider_id = provider.id if provider else None
            product.category_id = category.id
            product.season_id = season.id
            product.collection_id = collection.id

            size_palette = sizes[:5]
            combo_pool = [(size_item, color_item) for size_item in size_palette for color_item in colors]
            combo_offset = (sku_counter + index) % len(combo_pool)

            for variant_index in range(variant_count):
                sku = f"FS-{sku_counter}-{variant_index + 1}"
                size, color = combo_pool[(combo_offset + variant_index) % len(combo_pool)]
                variant_status = status_cycle[(sku_counter + index + variant_index) % len(status_cycle)]

                variant, _ = _get_or_create(
                    session,
                    ProductVariant,
                    {"sku": sku},
                    {
                        "product_id": product.id,
                        "price": price,
                        "size_id": size.id,
                        "color_id": color.id,
                        "status": variant_status,
                        "image_url": None,
                        "image_public_id": None,
                    },
                )
                variant.product_id = product.id
                variant.price = price
                variant.size_id = size.id
                variant.color_id = color.id
                variant.status = variant_status
                variant.image_url = None
                variant.image_public_id = None

                all_products.append((product, variant))

            sku_counter += 1

            if sku_counter > 1050:
                return all_products

    return all_products


def _seed_inventory(
    session,
    branches: list[Branch],
    users: list[User],
    product_variants: list[tuple[Product, ProductVariant]],
) -> None:
    creator_id = users[0].id if users else None
    inventory_by_key: dict[tuple[str, str], Inventory] = {}

    for p_index, (product, variant) in enumerate(product_variants, start=1):
        variant_rows: list[tuple[Branch, Inventory, int]] = []
        for b_index, branch in enumerate(branches, start=1):
            if variant.status == ProductStatusEnum.inactive:
                quantity = 0
            elif variant.status == ProductStatusEnum.pending:
                quantity = 1 if b_index == 1 and p_index % 2 == 0 else 0
            else:
                base = 18 - ((p_index + b_index) % 7)
                branch_factor = {1: 1.0, 2: 0.7, 3: 0.4}.get(b_index, 0.5)
                quantity = max(0, int(round(base * branch_factor)))

            reserved_quantity = 0
            if quantity > 0 and variant.status == ProductStatusEnum.active and (p_index + b_index) % 4 == 0:
                reserved_quantity = min(3, max(1, quantity // 4))

            inventory, _ = _get_or_create(
                session,
                Inventory,
                {"variant_id": variant.id, "branch_id": branch.id},
                {"quantity": quantity, "reserved_quantity": reserved_quantity},
            )
            inventory.quantity = quantity
            inventory.reserved_quantity = reserved_quantity

            inventory_by_key[(str(variant.id), str(branch.id))] = inventory
            variant_rows.append((branch, inventory, quantity))

        for branch, inventory, quantity in variant_rows:
            if quantity <= 0:
                continue

            _get_or_create(
                session,
                InventoryMovement,
                {
                    "variant_id": variant.id,
                    "branch_id": branch.id,
                    "movement_type": InventoryMovementTypeEnum.income,
                    "quantity": quantity,
                    "reference_branch_id": None,
                    "note": f"Carga inicial de inventario para {product.name}",
                    "created_by": creator_id,
                },
            )

            if variant.status == ProductStatusEnum.active and quantity > 1 and p_index % 6 == 0:
                sale_qty = 1
                inventory.quantity = max(0, inventory.quantity - sale_qty)
                _get_or_create(
                    session,
                    InventoryMovement,
                    {
                        "variant_id": variant.id,
                        "branch_id": branch.id,
                        "movement_type": InventoryMovementTypeEnum.outcome,
                        "quantity": sale_qty,
                        "reference_branch_id": None,
                        "note": f"Salida simulada por venta de {product.name}",
                        "created_by": creator_id,
                    },
                )

            if branch == branches[0] and variant.status == ProductStatusEnum.active and quantity > 2 and p_index % 8 == 0:
                transfer_qty = 1
                target_branch = branches[1]
                inventory.quantity = max(0, inventory.quantity - transfer_qty)
                target_inventory = inventory_by_key.get((str(variant.id), str(target_branch.id)))
                if target_inventory is not None:
                    target_inventory.quantity += transfer_qty

                _get_or_create(
                    session,
                    InventoryMovement,
                    {
                        "variant_id": variant.id,
                        "branch_id": branch.id,
                        "movement_type": InventoryMovementTypeEnum.transfer_out,
                        "quantity": transfer_qty,
                        "reference_branch_id": target_branch.id,
                        "note": f"Traslado hacia {target_branch.name}",
                        "created_by": creator_id,
                    },
                )
                _get_or_create(
                    session,
                    InventoryMovement,
                    {
                        "variant_id": variant.id,
                        "branch_id": target_branch.id,
                        "movement_type": InventoryMovementTypeEnum.transfer_in,
                        "quantity": transfer_qty,
                        "reference_branch_id": branch.id,
                        "note": f"Ingreso por traslado desde {branch.name}",
                        "created_by": creator_id,
                    },
                )


def _money(value: Decimal | int | float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _product_variant_snapshot(product: Product, variant: ProductVariant) -> dict:
    return {
        "product_id": product.id,
        "product_name": product.name,
        "variant_sku": variant.sku,
        "size_id": variant.size_id,
        "color_id": variant.color_id,
        "image_url": None,
        "image_public_id": None,
    }


def _branch_inventories(session, branch: Branch) -> list[Inventory]:
    statement = select(Inventory).where(Inventory.branch_id == branch.id).order_by(Inventory.quantity.desc(), Inventory.reserved_quantity.asc())
    return session.execute(statement).scalars().all()


def _pick_available_inventory(
    session,
    branch: Branch,
    used_variant_ids: set[str] | None = None,
) -> tuple[Inventory, int] | None:
    used_variant_ids = used_variant_ids or set()
    for inventory in _branch_inventories(session, branch):
        if str(inventory.variant_id) in used_variant_ids:
            continue
        if inventory.variant.status != ProductStatusEnum.active:
            continue
        available = inventory.quantity - inventory.reserved_quantity
        if available <= 0:
            continue
        quantity = 2 if available >= 2 else 1
        return inventory, quantity
    return None


def _seed_carts(session, clients: list[User], branches: list[Branch], product_variants: list[tuple[Product, ProductVariant]]) -> list[Cart]:
    carts: list[Cart] = []
    cart_statuses = [CartStatusEnum.active, CartStatusEnum.checked_out, CartStatusEnum.cancelled]

    for index, client in enumerate(clients[:3]):
        branch = branches[index % len(branches)]
        cart, _ = _get_or_create(
            session,
            Cart,
            {"user_id": client.id},
            {"status": cart_statuses[index % len(cart_statuses)]},
        )
        cart.status = cart_statuses[index % len(cart_statuses)]

        used_variant_ids: set[str] = set()
        selected_items: list[tuple[Inventory, int]] = []
        for _ in range(2):
            picked = _pick_available_inventory(session, branch, used_variant_ids)
            if not picked:
                break
            inventory, quantity = picked
            used_variant_ids.add(str(inventory.variant_id))
            selected_items.append((inventory, quantity))

        subtotal = Decimal("0")
        for inventory, quantity in selected_items:
            unit_price = inventory.variant.price
            line_total = unit_price * quantity
            subtotal += line_total
            item, _ = _get_or_create(
                session,
                CartItem,
                {"cart_id": cart.id, "variant_id": inventory.variant_id},
                {"quantity": quantity, "unit_price": unit_price},
            )
            item.quantity = quantity
            item.unit_price = unit_price

        discount = _money(subtotal * Decimal("0.05")) if index == 1 and subtotal > 0 else Decimal("0.00")
        cart.subtotal = _money(subtotal)
        cart.discount_amount = discount
        cart.total_amount = _money(subtotal - discount)
        carts.append(cart)

    return carts


def _seed_reservations(
    session,
    clients: list[User],
    branches: list[Branch],
    product_variants: list[tuple[Product, ProductVariant]],
) -> list[Reservation]:
    reservations: list[Reservation] = []
    status_cycle = [
        ReservationStatusEnum.pending,
        ReservationStatusEnum.confirmed,
        ReservationStatusEnum.attended,
        ReservationStatusEnum.pending,
    ]
    today = date.today()

    reservation_plan = [(clients[0], 50)]
    reservation_plan.extend((client, 1) for client in clients[1:5])

    for client_index, (client, count) in enumerate(reservation_plan):
        for item_index in range(count):
            branch = branches[(client_index + item_index) % len(branches)]
            visit_date = today + timedelta(days=len(reservations) + 2)
            expires_at = visit_date + timedelta(days=1)
            reservation, _ = _get_or_create(
                session,
                Reservation,
                {"branch_id": branch.id, "user_id": client.id, "visit_date": visit_date},
                {"expires_at": expires_at, "status": status_cycle[len(reservations) % len(status_cycle)]},
            )
            reservation.expires_at = expires_at
            reservation.status = status_cycle[len(reservations) % len(status_cycle)]

            picked = _pick_available_inventory(session, branch)
            if not picked:
                continue
            inventory, quantity = picked
            quantity = 1 if quantity > 0 else 0
            if quantity <= 0:
                continue

            total = Decimal("0")
            unit_price = inventory.variant.price
            total += unit_price * quantity
            item, _ = _get_or_create(
                session,
                ReservationItem,
                {"reservation_id": reservation.id, "variant_id": inventory.variant_id},
                {"quantity": quantity, "unit_price": unit_price},
            )
            item.quantity = quantity
            item.unit_price = unit_price
            inventory.reserved_quantity += quantity

            reservation.total_amount = _money(total)
            reservations.append(reservation)

    return reservations


def _seed_orders(session, clients: list[User], product_variants: list[tuple[Product, ProductVariant]]) -> list[Order]:
    orders: list[Order] = []
    payment_methods = [PaymentMethodEnum.cash, PaymentMethodEnum.stripe]

    for index, client in enumerate(clients[:4]):
        payment_method = payment_methods[index % len(payment_methods)]
        order, _ = _get_or_create(
            session,
            Order,
            {"user_id": client.id, "cash_reference": f"CASH-ORD-{index + 1:03d}" if payment_method == PaymentMethodEnum.cash else None},
            {
                "status": OrderStatusEnum.paid,
                "payment_method": payment_method,
                "payment_status": PaymentStatusEnum.paid,
                "stripe_payment_intent_id": f"pi_demo_{index + 1:03d}" if payment_method == PaymentMethodEnum.stripe else None,
                "cash_reference": f"CASH-ORD-{index + 1:03d}" if payment_method == PaymentMethodEnum.cash else None,
                "currency": "usd",
            },
        )
        order.status = OrderStatusEnum.paid
        order.payment_method = payment_method
        order.payment_status = PaymentStatusEnum.paid
        order.stripe_payment_intent_id = f"pi_demo_{index + 1:03d}" if payment_method == PaymentMethodEnum.stripe else None
        order.cash_reference = f"CASH-ORD-{index + 1:03d}" if payment_method == PaymentMethodEnum.cash else None

        used_variant_ids: set[str] = set()
        selected_items: list[ProductVariant] = []
        for product, variant in product_variants:
            if variant.status != ProductStatusEnum.active:
                continue
            if str(variant.id) in used_variant_ids:
                continue
            selected_items.append(variant)
            used_variant_ids.add(str(variant.id))
            if len(selected_items) == 2:
                break

        subtotal = Decimal("0")
        for variant in selected_items:
            quantity = 1
            product = variant.product
            line_total = variant.price * quantity
            subtotal += line_total
            item, _ = _get_or_create(
                session,
                OrderItem,
                {"order_id": order.id, "variant_id": variant.id},
                {
                    "quantity": quantity,
                    "unit_price": variant.price,
                    "line_total": line_total,
                    **_product_variant_snapshot(product, variant),
                },
            )
            item.quantity = quantity
            item.unit_price = variant.price
            item.line_total = line_total
            item.product_id = product.id
            item.product_name = product.name
            item.variant_sku = variant.sku
            item.size_id = variant.size_id
            item.color_id = variant.color_id
            item.image_url = None
            item.image_public_id = None

        discount = _money(subtotal * Decimal("0.03")) if index == 2 and subtotal > 0 else Decimal("0.00")
        order.subtotal = _money(subtotal)
        order.discount_amount = discount
        order.total_amount = _money(subtotal - discount)
        orders.append(order)

    return orders


def _seed_sales(
    session,
    cashiers: list[User],
    branches: list[Branch],
    product_variants: list[tuple[Product, ProductVariant]],
    reservations: list[Reservation],
) -> list[Sale]:
    sales: list[Sale] = []
    def _cashier_for_branch(branch: Branch, fallback_index: int = 0) -> User | None:
        branch_cashiers = [user for user in cashiers if user.branch_id == branch.id]
        if branch_cashiers:
            return branch_cashiers[0]
        return cashiers[fallback_index % len(cashiers)] if cashiers else None

    def _create_sale_for_reservation(reservation: Reservation, sale_index: int) -> Sale | None:
        branch = next(branch for branch in branches if branch.id == reservation.branch_id)
        cashier = _cashier_for_branch(branch, sale_index)
        if cashier is None:
            return None
        reference = f"CASH-RES-{str(reservation.id)[:8]}"
        sale, _ = _get_or_create(
            session,
            Sale,
            {"branch_id": branch.id, "user_id": cashier.id, "reservation_id": reservation.id},
            {
                "status": SaleStatusEnum.completed,
                "payment_method": PaymentMethodEnum.cash,
                "payment_status": PaymentStatusEnum.paid,
                "cash_reference": reference,
                "currency": "usd",
            },
        )
        sale.branch_id = branch.id
        sale.user_id = cashier.id
        sale.reservation_id = reservation.id
        sale.status = SaleStatusEnum.completed
        sale.payment_method = PaymentMethodEnum.cash
        sale.payment_status = PaymentStatusEnum.paid
        sale.cash_reference = reference
        sale.currency = "usd"

        subtotal = Decimal("0")
        for reservation_item in reservation.items:
            inventory = session.execute(
                select(Inventory).where(Inventory.branch_id == branch.id, Inventory.variant_id == reservation_item.variant_id)
            ).scalars().first()
            if inventory is None:
                continue
            product = reservation_item.variant.product
            variant = reservation_item.variant
            quantity = reservation_item.quantity
            line_total = _money(variant.price * quantity)
            subtotal += line_total

            sale_item, _ = _get_or_create(
                session,
                SaleItem,
                {"sale_id": sale.id, "variant_id": variant.id},
                {
                    "quantity": quantity,
                    "unit_price": variant.price,
                    "line_total": line_total,
                    **_product_variant_snapshot(product, variant),
                },
            )
            sale_item.quantity = quantity
            sale_item.unit_price = variant.price
            sale_item.line_total = line_total
            sale_item.product_id = product.id
            sale_item.product_name = product.name
            sale_item.variant_sku = variant.sku
            sale_item.size_id = variant.size_id
            sale_item.color_id = variant.color_id
            sale_item.image_url = None
            sale_item.image_public_id = None

            inventory.reserved_quantity = max(0, inventory.reserved_quantity - quantity)
            inventory.quantity = max(0, inventory.quantity - quantity)

        sale.subtotal = subtotal
        sale.discount_amount = Decimal("0.00")
        sale.total_amount = subtotal
        return sale

    for sale_index, reservation in enumerate(reservations):
        sale = _create_sale_for_reservation(reservation, sale_index)
        if sale is not None:
            sales.append(sale)

    return sales


if __name__ == "__main__":
    main()
