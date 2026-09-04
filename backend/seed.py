from __future__ import annotations

from decimal import Decimal

from sqlalchemy import inspect, select

from app.auth.hash import hash_password
from app.core.database import SessionLocal, engine
from app.models.branch import Branch
from app.models.category import Category
from app.models.collection import Collection
from app.models.color import Color
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.provider import Provider
from app.models.season import Season
from app.models.size import Size
from app.models.user import User
from app.schemas.catalog_enums import ProductStatusEnum
from app.schemas.enums import GenderEnum, ProviderStatusEnum, RolEnum


PASSWORD = "Fashion123!"


def main() -> None:
    _ensure_tables()
    session = SessionLocal()
    try:
        branches = _seed_branches(session)
        users = _seed_users(session, branches)
        providers = _seed_providers(session, branches)
        categories = _seed_categories(session)
        sizes = _seed_sizes(session)
        colors = _seed_colors(session)
        seasons = _seed_seasons(session)
        collections = _seed_collections(session, seasons)
        product_variants = _seed_products(session, categories, sizes, colors, seasons, collections, providers)
        _seed_inventory(session, branches, product_variants)
        session.commit()
        print("Seeder demo ejecutado correctamente")
        print(f"- Sucursales: {len(branches)}")
        print(f"- Usuarios: {len(users)}")
        print(f"- Proveedores: {len(providers)}")
        print(f"- Productos/variantes: {len(product_variants)}")
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
        {"name": "Admin Global", "email": "admin.global@fashionstore.bo", "gender": GenderEnum.masculino, "rol": RolEnum.administrador, "branch_id": None},
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
        ("Valeria", "Rojas"), ("Daniel", "Mamani"), ("Paola", "Lopez"), ("Martin", "Vargas"),
        ("Carla", "Quispe"), ("Jorge", "Arce"), ("Lucia", "Flores"), ("Andres", "Soto"),
        ("Sofia", "Paredes"), ("Diego", "Gutierrez"), ("Mariana", "Torrez"), ("Oscar", "Mendoza"),
        ("Camila", "Salazar"), ("Fernando", "Cruz"), ("Eliana", "Rivera"), ("Raul", "Choque"),
        ("Natalia", "Mendez"), ("Pablo", "Carrasco"), ("Juliana", "Arias"), ("Kevin", "Siles"),
        ("Rocio", "Nina"), ("Luis", "Fernandez"), ("Micaela", "Luna"), ("Ivan", "Perez"),
        ("Gabriela", "Romero"), ("Bruno", "Castro"), ("Nadia", "Zeballos"), ("Esteban", "Rojas"),
        ("Ariana", "Guerrero"), ("Hector", "Paz"),
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
    names = ["Camisetas", "Jeans", "Vestidos", "Abrigos", "Zapatos", "Accesorios"]
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
        {"name": "Urban Summer", "season": seasons[0]},
        {"name": "City Warm", "season": seasons[1]},
        {"name": "Weekend Basics", "season": seasons[0]},
        {"name": "Night Edition", "season": seasons[1]},
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
        "Camisetas": ["Básica", "Oversize", "Estampada", "Manga Larga", "Slim Fit"],
        "Jeans": ["Skinny", "Straight", "Wide Leg", "Mom Fit", "Jogger"],
        "Vestidos": ["Casual", "Midi", "Fluido", "Noche", "Lino"],
        "Abrigos": ["Trench", "Acolchado", "Biker", "Largo", "Impermeable"],
        "Zapatos": ["Casuales", "Urbanos", "Deportivos", "Botines", "Mocasines"],
        "Accesorios": ["Mochila", "Cinturón", "Gorra", "Bufanda", "Bolso"],
    }

    all_products: list[tuple[Product, ProductVariant]] = []
    sku_counter = 1001
    singular_names = {
        "Camisetas": "Camiseta",
        "Jeans": "Jean",
        "Vestidos": "Vestido",
        "Abrigos": "Abrigo",
        "Zapatos": "Zapato",
        "Accesorios": "Accesorio",
    }

    for category in categories:
        styles = category_styles[category.name]
        for index, style in enumerate(styles, start=1):
            status_cycle = [ProductStatusEnum.active, ProductStatusEnum.pending, ProductStatusEnum.active, ProductStatusEnum.inactive, ProductStatusEnum.active]
            status = status_cycle[(sku_counter + index) % len(status_cycle)]
            provider = None
            if (sku_counter + index) % 3 == 0:
                provider = providers[0]
            elif (sku_counter + index) % 4 == 0:
                provider = providers[1]

            size = None
            if category.name in {"Camisetas", "Jeans", "Vestidos", "Abrigos"}:
                size = sizes[(sku_counter + index) % 5]
            elif category.name == "Zapatos":
                size = sizes[6 + ((sku_counter + index) % 6)]

            color = colors[(sku_counter + index) % len(colors)]
            season = seasons[(sku_counter + index) % len(seasons)]
            collection = collections[(sku_counter + index) % len(collections)]

            price = Decimal(str(79 + ((sku_counter + index) % 7) * 15 + (index * 2)))
            sku = f"FS-{sku_counter}"
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

            variant, _ = _get_or_create(
                session,
                ProductVariant,
                {"sku": sku},
                {
                    "product_id": product.id,
                    "price": price,
                    "size_id": size.id if size else None,
                    "color_id": color.id,
                    "status": status,
                },
            )
            variant.product_id = product.id
            variant.price = price
            variant.size_id = size.id if size else None
            variant.color_id = color.id
            variant.status = status

            all_products.append((product, variant))
            sku_counter += 1

    return all_products


def _seed_inventory(session, branches: list[Branch], product_variants: list[tuple[Product, ProductVariant]]) -> None:
    for p_index, (product, variant) in enumerate(product_variants, start=1):
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


if __name__ == "__main__":
    main()
