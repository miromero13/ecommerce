"""CU1 catalog contracts: real PostgreSQL ownership and signed JWTs.

Missing ownership predicates, omitted tenant assignment, or widened editing
roles must break these tests. Only Cloudinary's external boundary is replaced.
"""
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import text

from test_employee_authorization import DENIED, headers


ROOT = "/api/catalog"
TABLES = (
    "tenants", "users", "branches", "providers", "categories", "seasons",
    "collections", "sizes", "colors", "products", "product_variants",
    "inventory", "inventory_movements", "provider_variant_availability",
)


def snapshot(db):
    # Independent of the identity map; includes quantities and tenant counters.
    return {table: db.execute(text(
        f"SELECT row_to_json(t)::text FROM {table} t ORDER BY id"
    )).all() for table in TABLES}


def rejected(api, db, cloud, method, path, auth, message, code=404, **kwargs):
    before = snapshot(db)
    effects_before = list(cloud)
    result = api.request(method, ROOT + path, headers=auth, **kwargs)
    assert result.status_code == code, result.text
    assert result.json() == {
        "statusCode": code, "message": message, "error": "HTTPException",
    }
    assert snapshot(db) == before
    assert cloud == effects_before


def rows(api, path, auth=None, **params):
    result = api.get(ROOT + path, headers=auth or {}, params=params)
    assert result.status_code == 200, result.text
    return result.json()["data"]


@pytest.fixture(autouse=True)
def cloud(monkeypatch):
    from app.routes import catalog_routes
    effects = []

    def upload(content, folder, public_id=None):
        effects.append(("upload", content, folder, public_id))
        return {"image_url": "https://example.invalid/new.png", "image_public_id": "new-image"}

    def delete(public_id):
        effects.append(("delete", public_id))

    monkeypatch.setattr(catalog_routes, "upload_image", upload)
    monkeypatch.setattr(catalog_routes, "delete_image", delete)
    return effects


@pytest.fixture
def catalog(api_db, identities):
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
    from app.schemas.enums import GenderEnum, RolEnum

    user, tenants, branches = identities
    sizes = [Size(name=name) for name in ("M", "L")]
    colors = [Color(name=name, hex_code=value) for name, value in
              (("Blue", "#0000ff"), ("Red", "#ff0000"))]
    api_db.add_all(sizes + colors)
    groups = []
    for index, tenant in enumerate(tenants):
        supplier_user = User(name="Supplier", email=f"supplier{index}@example.com",
                             hashed_password="unused", gender=GenderEnum.femenino,
                             rol=RolEnum.proveedor, tenant_id=tenant.id, is_active=True)
        category = Category(name=f"Category {index}", tenant_id=tenant.id)
        season = Season(name=f"Season {index}", tenant_id=tenant.id)
        spare_category = Category(name=f"Spare category {index}", tenant_id=tenant.id)
        spare_season = Season(name=f"Spare season {index}", tenant_id=tenant.id)
        api_db.add_all([supplier_user, category, season, spare_category, spare_season])
        api_db.flush()
        provider = Provider(user_id=supplier_user.id, tenant_id=tenant.id,
                            business_name=f"Supplier {index}", contact_name="Contact")
        collection = Collection(name=f"Collection {index}", tenant_id=tenant.id, season_id=season.id)
        spare_collection = Collection(name=f"Spare collection {index}", tenant_id=tenant.id)
        api_db.add_all([provider, collection, spare_collection])
        api_db.flush()
        products, variants = [], []
        for state in (ProductStatusEnum.active, ProductStatusEnum.pending):
            product = Product(name=f"Product {index} {state.value}", tenant_id=tenant.id,
                              category_id=category.id, collection_id=collection.id, provider_id=provider.id)
            api_db.add(product)
            api_db.flush()
            variant = ProductVariant(tenant_id=tenant.id, product_id=product.id,
                                     sku=f"SKU-{index}-{state.value}", price=25,
                                     size_id=sizes[0].id, color_id=colors[0].id,
                                     status=state, image_url="https://example.invalid/old.png",
                                     image_public_id=f"old-{index}-{state.value}")
            api_db.add(variant)
            products.append(product)
            variants.append(variant)
        api_db.flush()
        inventory = Inventory(tenant_id=tenant.id, variant_id=variants[0].id,
                              branch_id=branches[0 if index == 0 else 2].id,
                              quantity=9, reserved_quantity=2, minimum_stock=1)
        api_db.add(inventory)
        groups.append(SimpleNamespace(
            tenant=tenant, supplier_user=supplier_user, provider=provider,
            category=category, season=season, collection=collection,
            spare_category=spare_category, spare_season=spare_season,
            spare_collection=spare_collection, product=products[0], variant=variants[0],
            pending=products[1], pending_variant=variants[1], inventory=inventory,
        ))
    api_db.commit()
    return SimpleNamespace(user=user, own=groups[0], foreign=groups[1],
                           sizes=sizes, colors=colors, branches=branches)


def product_payload(catalog, **changes):
    own = catalog.own
    return {
        "name": "New garment", "category_id": str(own.category.id),
        "collection_id": str(own.collection.id), "provider_id": str(own.provider.id),
        "variants": [{"sku": "NEW-SKU", "price": "30.00",
                      "size_id": str(catalog.sizes[0].id), "color_id": str(catalog.colors[0].id)}],
        **changes,
    }


@pytest.mark.parametrize("path", ["/products/admin", "/products/pending"])
def test_private_lists_use_persisted_tenant_not_claim_or_query(api, api_db, catalog, path):
    auth = headers(catalog.user)
    catalog.user.tenant_id = catalog.foreign.tenant.id
    api_db.commit()
    result = rows(api, path, auth, tenant_id=str(catalog.own.tenant.id))
    expected = {str(catalog.foreign.pending.id)}
    if path.endswith("admin"):
        expected.add(str(catalog.foreign.product.id))
    assert {row["id"] for row in result} == expected


def test_global_customer_and_anonymous_browse_both_companies_and_filter(api, api_db, catalog):
    from app.schemas.enums import RolEnum
    catalog.user.rol = RolEnum.cliente
    catalog.user.tenant_id = None
    api_db.commit()
    for auth in ({}, headers(catalog.user)):
        products = rows(api, "/products", auth)
        assert {row["id"] for row in products} == {str(catalog.own.product.id), str(catalog.foreign.product.id)}
        assert {row["tenant_id"] for row in products} == {str(catalog.own.tenant.id), str(catalog.foreign.tenant.id)}
        assert all(row["status"] == "active" for row in products)
        filtered = rows(api, "/products", auth, tenant_id=str(catalog.foreign.tenant.id))
        assert [row["id"] for row in filtered] == [str(catalog.foreign.product.id)]
        detail = rows(api, f"/products/{catalog.foreign.product.id}", auth)
        assert detail["tenant_id"] == str(catalog.foreign.tenant.id)
        assert detail["variants"][0]["branch_stocks"][0]["quantity"] == 7
        for resource in ("categories", "seasons", "collections", "sizes", "colors"):
            assert len(rows(api, "/" + resource, auth)) >= 2


@pytest.mark.parametrize("resource,label", [("sizes", "Talla"), ("colors", "Color")])
@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
@pytest.mark.parametrize("role", ["administrador", "cliente", "proveedor", "encargado", "cajero", "delivery"])
def test_shared_vocabulary_rejects_nonplatform_writes(api, api_db, catalog, cloud, resource, label, method, role):
    from app.schemas.enums import RolEnum
    catalog.user.rol = RolEnum(role)
    catalog.user.branch_id = catalog.branches[0].id
    if role == "cliente":
        catalog.user.tenant_id = None
    api_db.commit()
    item = getattr(catalog, resource)[1]
    path = f"/{resource}" + (f"/{item.id}" if method != "POST" else "")
    kwargs = {} if method == "DELETE" else {"json": {"name": "Changed", "hex_code": "#ffffff"}}
    rejected(api, api_db, cloud, method, path, headers(catalog.user), DENIED, 403, **kwargs)
    assert any(row["id"] == str(item.id) for row in rows(api, f"/{resource}", headers(catalog.user)))


@pytest.mark.parametrize("resource,created,updated,deleted", [
    ("sizes", "Talla creada exitosamente", "Talla actualizada exitosamente", "Talla eliminada exitosamente"),
    ("colors", "Color creado exitosamente", "Color actualizado exitosamente", "Color eliminado exitosamente"),
])
def test_platform_manages_shared_vocabulary_without_tenant(api, api_db, catalog, resource, created, updated, deleted):
    from app.schemas.enums import RolEnum
    catalog.user.rol = RolEnum.superadministrador
    catalog.user.tenant_id = None
    api_db.commit()
    auth = headers(catalog.user)
    result = api.post(ROOT + f"/{resource}", headers=auth, json={"name": "Platform", "hex_code": "#abcdef"})
    assert result.status_code == 201, result.text
    assert result.json()["message"] == created
    item_id = result.json()["data"]["id"]
    result = api.put(ROOT + f"/{resource}/{item_id}", headers=auth, json={"name": "Renamed", "hex_code": "#123456"})
    assert result.status_code == 200, result.text
    assert result.json()["message"] == updated
    item = next(row for row in rows(api, f"/{resource}") if row["id"] == item_id)
    assert item["name"] == "Renamed"
    if resource == "colors":
        assert item["hex_code"] == "#123456"
    result = api.delete(ROOT + f"/{resource}/{item_id}", headers=auth)
    assert result.status_code == 200, result.text
    assert result.json()["message"] == deleted
    assert item_id not in {row["id"] for row in rows(api, f"/{resource}")}


@pytest.mark.parametrize("resource,message", [
    ("sizes", "No se puede eliminar una talla con variantes asociadas"),
    ("colors", "No se puede eliminar un color con variantes asociadas"),
])
def test_platform_vocabulary_delete_retains_existing_reference_guard(api, api_db, catalog, cloud, resource, message):
    from app.schemas.enums import RolEnum
    catalog.user.rol = RolEnum.superadministrador
    catalog.user.tenant_id = None
    api_db.commit()
    item = getattr(catalog, resource)[0]
    rejected(api, api_db, cloud, "DELETE", f"/{resource}/{item.id}", headers(catalog.user), message, 400)


@pytest.mark.parametrize("resource,attribute,label", [
    ("categories", "spare_category", "Categoria"), ("seasons", "spare_season", "Temporada"),
    ("collections", "spare_collection", "Coleccion"),
])
@pytest.mark.parametrize("method", ["PUT", "DELETE"])
def test_foreign_taxonomy_is_not_found_before_mutation(api, api_db, catalog, cloud, resource, attribute, label, method):
    item = getattr(catalog.foreign, attribute)
    kwargs = {"json": {"name": "Stolen"}} if method == "PUT" else {}
    rejected(api, api_db, cloud, method, f"/{resource}/{item.id}", headers(catalog.user),
             f"{label} con id {item.id} no encontrada", **kwargs)


@pytest.mark.parametrize("resource,attribute", [("categories", "spare_category"), ("seasons", "spare_season"), ("collections", "spare_collection")])
def test_own_taxonomy_create_update_delete_preserves_contract(api, api_db, catalog, resource, attribute):
    auth = headers(catalog.user)
    result = api.post(ROOT + f"/{resource}", headers=auth, json={"name": "Created"})
    assert result.status_code == 201, result.text
    item_id = result.json()["data"]["id"]
    stored_tenant = api_db.execute(text(f"SELECT tenant_id FROM {resource} WHERE id = :id"), {"id": item_id}).scalar_one()
    assert stored_tenant == catalog.own.tenant.id
    payload = {"name": "Updated"}
    if resource == "collections":
        payload["season_id"] = str(catalog.own.season.id)
    result = api.put(ROOT + f"/{resource}/{item_id}", headers=auth, json=payload)
    assert result.status_code == 200, result.text
    assert next(row for row in rows(api, f"/{resource}") if row["id"] == item_id)["name"] == "Updated"
    result = api.delete(ROOT + f"/{resource}/{item_id}", headers=auth)
    assert result.status_code == 200, result.text
    assert item_id not in {row["id"] for row in rows(api, f"/{resource}")}


@pytest.mark.parametrize("method", ["POST", "PUT"])
def test_collection_rejects_foreign_season_without_changes(api, api_db, catalog, cloud, method):
    path = "/collections" + (f"/{catalog.own.spare_collection.id}" if method == "PUT" else "")
    rejected(api, api_db, cloud, method, path, headers(catalog.user),
             f"Temporada con id {catalog.foreign.season.id} no encontrada",
             json={"name": "Invalid", "season_id": str(catalog.foreign.season.id)})


@pytest.mark.parametrize("method", ["POST", "PUT"])
def test_missing_provider_preserves_existing_error_contract(api, api_db, catalog, cloud, method):
    path = "/products" + (f"/{catalog.own.product.id}" if method == "PUT" else "")
    rejected(api, api_db, cloud, method, path, headers(catalog.user),
             "El proveedor no existe", 400,
             json=product_payload(catalog, provider_id=str(uuid4())))


@pytest.mark.parametrize("field,attribute,label,ending", [
    ("provider_id", "provider", "Proveedor", "no encontrado"),
    ("category_id", "category", "Categoria", "no encontrada"),
    ("collection_id", "collection", "Coleccion", "no encontrada"),
])
@pytest.mark.parametrize("method", ["POST", "PUT"])
def test_product_rejects_foreign_relation_without_changes(api, api_db, catalog, cloud, field, attribute, label, ending, method):
    item = getattr(catalog.foreign, attribute)
    path = "/products" + (f"/{catalog.own.product.id}" if method == "PUT" else "")
    message = "El proveedor no existe" if field == "provider_id" else f"{label} con id {item.id} {ending}"
    code = 400 if field == "provider_id" else 404
    rejected(api, api_db, cloud, method, path, headers(catalog.user), message, code,
             json=product_payload(catalog, **{field: str(item.id)}))


@pytest.mark.parametrize("method,path,payload", [
    ("POST", "/categories", {"name": "Forbidden"}),
    ("POST", "/seasons", {"name": "Forbidden"}),
    ("POST", "/collections", {"name": "Forbidden"}),
    ("POST", "/products", "product"),
    ("POST", "/products/provider-submission", "product"),
    ("PUT", "/products/{product}", "product"),
    ("DELETE", "/products/{product}", None),
    ("PATCH", "/products/{product}/status", {"status": "inactive"}),
    ("PATCH", "/variants/{variant}/status", {"status": "inactive"}),
    ("DELETE", "/variants/{variant}/image", None),
    ("PUT", "/categories/{category}", {"name": "Forbidden"}),
    ("DELETE", "/categories/{category}", None),
    ("PUT", "/seasons/{season}", {"name": "Forbidden"}),
    ("DELETE", "/seasons/{season}", None),
    ("PUT", "/collections/{collection}", {"name": "Forbidden"}),
    ("DELETE", "/collections/{collection}", None),
])
def test_global_customer_cannot_write_other_catalog_data(api, api_db, catalog, cloud, method, path, payload):
    from app.schemas.enums import RolEnum
    catalog.user.rol = RolEnum.cliente
    catalog.user.tenant_id = None
    api_db.commit()
    path = path.format(**{name: getattr(catalog.own, name).id for name in
                          ("product", "variant", "category", "season", "collection")})
    kwargs = {} if payload is None else {"json": product_payload(catalog) if payload == "product" else payload}
    rejected(api, api_db, cloud, method, path, headers(catalog.user), DENIED, 403, **kwargs)


def test_update_cannot_attach_a_variant_from_another_product(api, api_db, catalog, cloud):
    payload = product_payload(catalog)
    payload["variants"][0]["id"] = str(catalog.foreign.variant.id)
    rejected(api, api_db, cloud, "PUT", f"/products/{catalog.own.product.id}", headers(catalog.user),
             "La variante no pertenece al producto", 400, json=payload)


def test_old_assignment_cannot_mutate_previous_company_catalog(api, api_db, catalog, cloud):
    auth = headers(catalog.user)
    catalog.user.tenant_id = catalog.foreign.tenant.id
    api_db.commit()
    rejected(api, api_db, cloud, "PATCH", f"/variants/{catalog.own.variant.id}/status", auth,
             f"Variante con id {catalog.own.variant.id} no encontrada", json={"status": "inactive"})


def test_create_and_update_assign_company_to_product_and_new_variants(api, api_db, catalog):
    auth = headers(catalog.user, tenant_id=str(catalog.foreign.tenant.id))
    payload = product_payload(catalog)
    result = api.post(ROOT + "/products", headers=auth, json=payload)
    assert result.status_code == 201, result.text
    assert result.json()["message"] == "Producto creado exitosamente"
    product = result.json()["data"]
    assert product["tenant_id"] == str(catalog.own.tenant.id)
    first_id = product["variants"][0]["id"]
    # A new request Session must observe both commits, not an old identity map.
    assert rows(api, f"/products/{product['id']}")["name"] == "New garment"
    payload["name"] = "Persisted update"
    payload["variants"][0]["id"] = first_id
    payload["variants"].append({"sku": "SECOND-SKU", "price": "35.00",
                                "size_id": str(catalog.sizes[1].id), "color_id": str(catalog.colors[1].id)})
    result = api.put(ROOT + f"/products/{product['id']}", headers=auth, json=payload)
    assert result.status_code == 200, result.text
    assert result.json()["message"] == "Producto actualizado exitosamente"
    updated = rows(api, f"/products/{product['id']}")
    assert updated["name"] == "Persisted update"
    assert {variant["sku"] for variant in updated["variants"]} == {"NEW-SKU", "SECOND-SKU"}
    stored = api_db.execute(text("SELECT tenant_id FROM product_variants WHERE product_id = :id"), {"id": product["id"]}).scalars().all()
    assert stored == [catalog.own.tenant.id, catalog.own.tenant.id]


@pytest.mark.parametrize("method,suffix,payload", [
    ("PUT", "", "product"), ("DELETE", "", None),
    ("PATCH", "/status", {"status": "inactive"}),
])
def test_foreign_product_mutations_are_not_found(api, api_db, catalog, cloud, method, suffix, payload):
    kwargs = {} if payload is None else {"json": product_payload(catalog) if payload == "product" else payload}
    item_id = catalog.foreign.product.id
    rejected(api, api_db, cloud, method, f"/products/{item_id}{suffix}", headers(catalog.user),
             f"Producto con id {item_id} no encontrado", **kwargs)


@pytest.mark.parametrize("method,suffix,kwargs", [
    ("PATCH", "/status", {"json": {"status": "inactive"}}),
    ("PATCH", "/garment-points", {"json": {"garment_points": [{"x": 0.2, "y": 0.3}] * 17}}),
    ("PATCH", "/image", {"files": {"file": ("garment.png", b"image-bytes", "image/png")}}),
    ("DELETE", "/image", {}),
])
def test_foreign_variant_rejected_before_database_or_cloud_effects(api, api_db, catalog, cloud, method, suffix, kwargs):
    item_id = catalog.foreign.variant.id
    rejected(api, api_db, cloud, method, f"/variants/{item_id}{suffix}", headers(catalog.user),
             f"Variante con id {item_id} no encontrada", **kwargs)


@pytest.mark.parametrize("role", ["cliente", "proveedor", "encargado", "cajero", "delivery", "superadministrador"])
def test_garment_points_do_not_grant_new_catalog_editing_roles(api, api_db, catalog, cloud, role):
    from app.schemas.enums import RolEnum
    catalog.user.rol = RolEnum(role)
    catalog.user.branch_id = catalog.branches[0].id
    if role in ("cliente", "superadministrador"):
        catalog.user.tenant_id = None
    api_db.commit()
    rejected(api, api_db, cloud, "PATCH", f"/variants/{catalog.own.variant.id}/garment-points",
             headers(catalog.user), DENIED, 403, json={"garment_points": None})


@pytest.mark.parametrize("count", [17, 19, None])
def test_own_admin_retains_garment_point_calibration_and_clear(api, catalog, count):
    points = [{"x": 0.2, "y": 0.3}] * count if count else None
    result = api.patch(ROOT + f"/variants/{catalog.own.variant.id}/garment-points",
                       headers=headers(catalog.user), json={"garment_points": points})
    assert result.status_code == 200, result.text
    assert result.json()["message"] == "Puntos de calibracion actualizados exitosamente"
    assert rows(api, f"/products/{catalog.own.product.id}")["variants"][0]["garment_points"] == points


@pytest.mark.parametrize("target", ["product", "variant"])
def test_own_admin_retains_legacy_and_variant_status_updates(api, catalog, target):
    item = getattr(catalog.own, target)
    result = api.patch(ROOT + f"/{target}s/{item.id}/status", headers=headers(catalog.user), json={"status": "pending"})
    assert result.status_code == 200, result.text
    assert result.json()["data"]["variants"][0]["status"] == "pending"
    assert str(catalog.own.product.id) in {row["id"] for row in rows(api, "/products/pending", headers(catalog.user))}


def test_own_admin_retains_image_replace_and_clear(api, catalog, cloud):
    path = ROOT + f"/variants/{catalog.own.variant.id}/image"
    auth = headers(catalog.user)
    result = api.patch(path, headers=auth, files={"file": ("garment.png", b"image-bytes", "image/png")})
    assert result.status_code == 200, result.text
    assert result.json()["data"]["variants"][0]["image_public_id"] == "new-image"
    assert cloud[0][0:2] == ("upload", b"image-bytes")
    assert cloud[1] == ("delete", "old-0-active")
    result = api.delete(path, headers=auth)
    assert result.status_code == 200, result.text
    assert cloud[-1] == ("delete", "new-image")
    detail = rows(api, f"/products/{catalog.own.product.id}")
    assert detail["variants"][0]["image_url"] is None
    assert detail["variants"][0]["image_public_id"] is None


def test_own_admin_retains_product_delete_without_touching_foreign_company(api, api_db, catalog):
    foreign_before = rows(api, f"/products/{catalog.foreign.product.id}")
    result = api.delete(ROOT + f"/products/{catalog.own.product.id}", headers=headers(catalog.user))
    assert result.status_code == 200, result.text
    assert result.json()["message"] == "Producto eliminado exitosamente"
    assert str(catalog.own.product.id) not in {row["id"] for row in rows(api, "/products")}
    assert rows(api, f"/products/{catalog.foreign.product.id}") == foreign_before


@pytest.mark.parametrize("foreign_target", ["branch", "variant", "legacy_product"])
def test_legacy_inventory_setter_rejects_foreign_scope_without_stock_effects(api, api_db, catalog, cloud, foreign_target):
    params = {"branch_id": str(catalog.branches[0].id), "variant_id": str(catalog.own.variant.id), "quantity": 99}
    if foreign_target == "branch":
        params["branch_id"] = str(catalog.branches[2].id)
        message = f"Sucursal con id {catalog.branches[2].id} no encontrada"
    elif foreign_target == "variant":
        params["variant_id"] = str(catalog.foreign.variant.id)
        message = f"Variante con id {catalog.foreign.variant.id} no encontrada"
    else:
        params.pop("variant_id")
        params["product_id"] = str(catalog.foreign.product.id)
        message = f"Producto con id {catalog.foreign.product.id} no encontrado"
    rejected(api, api_db, cloud, "PUT", "/inventory", headers(catalog.user), message, params=params)


@pytest.mark.parametrize("target", ["product_id", "variant_id"])
def test_legacy_inventory_setter_preserves_existing_own_stock_accounting(api, api_db, catalog, target):
    item = catalog.own.product if target == "product_id" else catalog.own.variant
    result = api.put(ROOT + "/inventory", headers=headers(catalog.user), params={
        target: str(item.id), "branch_id": str(catalog.branches[0].id), "quantity": 12})
    assert result.status_code == 200, result.text
    assert result.json()["data"]["quantity"] == 12
    assert rows(api, "/availability", variant_id=str(catalog.own.variant.id), branch_id=str(catalog.branches[0].id))["quantity"] == 10
    api_db.refresh(catalog.own.inventory)
    assert (catalog.own.inventory.reserved_quantity, catalog.own.inventory.minimum_stock) == (2, 1)


@pytest.mark.parametrize("requested_status", [None, "active", "inactive"])
def test_supplier_submission_assigns_provider_company_and_pending_status(api, api_db, catalog, requested_status):
    supplier = catalog.own.supplier_user
    # Forged provider and variant status cannot override submission ownership/moderation.
    payload = product_payload(catalog, provider_id=str(catalog.foreign.provider.id))
    payload["variants"][0]["status"] = requested_status
    result = api.post(ROOT + "/products/provider-submission", headers=headers(supplier), json=payload)
    assert result.status_code == 201, result.text
    assert result.json()["message"] == "Producto enviado exitosamente"
    product = result.json()["data"]
    assert product["tenant_id"] == str(catalog.own.tenant.id)
    assert product["provider_id"] == str(catalog.own.provider.id)
    assert product["variants"][0]["status"] == "pending"
    assert product["id"] not in {row["id"] for row in rows(api, "/products")}
    assert product["id"] in {row["id"] for row in rows(api, "/products/pending", headers(catalog.user))}
    tenant = api_db.execute(text("SELECT tenant_id FROM product_variants WHERE product_id = :id"), {"id": product["id"]}).scalar_one()
    assert tenant == catalog.own.tenant.id


def test_legacy_inventory_insert_assigns_company_without_changing_other_stock(api, api_db, catalog):
    before = rows(api, "/availability", variant_id=str(catalog.own.variant.id),
                  branch_id=str(catalog.branches[0].id))
    result = api.put(ROOT + "/inventory", headers=headers(catalog.user), params={
        "variant_id": str(catalog.own.variant.id),
        "branch_id": str(catalog.branches[1].id), "quantity": 6,
    })
    assert result.status_code == 200, result.text
    assert result.json()["data"] == {
        "variant_id": str(catalog.own.variant.id),
        "branch_id": str(catalog.branches[1].id), "quantity": 6,
    }
    assert rows(api, "/availability", variant_id=str(catalog.own.variant.id),
                branch_id=str(catalog.branches[1].id))["quantity"] == 6
    assert rows(api, "/availability", variant_id=str(catalog.own.variant.id),
                branch_id=str(catalog.branches[0].id)) == before
    stored = api_db.execute(text(
        "SELECT tenant_id, reserved_quantity, minimum_stock FROM inventory "
        "WHERE variant_id = :variant AND branch_id = :branch"
    ), {"variant": catalog.own.variant.id, "branch": catalog.branches[1].id}).one()
    assert tuple(stored) == (catalog.own.tenant.id, 0, 0)


@pytest.mark.parametrize("field,attribute,label", [
    ("category_id", "category", "Categoria"), ("collection_id", "collection", "Coleccion"),
])
def test_supplier_submission_rejects_foreign_catalog_relations(api, api_db, catalog, cloud, field, attribute, label):
    item = getattr(catalog.foreign, attribute)
    rejected(api, api_db, cloud, "POST", "/products/provider-submission", headers(catalog.own.supplier_user),
             f"{label} con id {item.id} no encontrada", json=product_payload(catalog, **{field: str(item.id)}))


def test_supplier_profile_must_belong_to_current_user_company(api, api_db, catalog, cloud):
    supplier = catalog.own.supplier_user
    auth = headers(supplier)
    supplier.tenant_id = catalog.foreign.tenant.id
    api_db.commit()
    rejected(api, api_db, cloud, "POST", "/products/provider-submission", auth,
             f"Proveedor con id {catalog.own.provider.id} no encontrado",
             json=product_payload(catalog, category_id=str(catalog.foreign.category.id),
                                  collection_id=str(catalog.foreign.collection.id)))


def test_two_companies_can_use_the_same_category_season_and_collection_names(api_db, identities):
    from sqlalchemy.exc import IntegrityError

    from app.models.category import Category
    from app.models.collection import Collection
    from app.models.season import Season

    _, tenants, _ = identities
    for tenant in tenants:  # CU1: names are unique per company, not platform-wide
        season = Season(tenant_id=tenant.id, name="Invierno 2026")
        api_db.add_all([Category(tenant_id=tenant.id, name="Vestidos"), season])
        api_db.flush()
        api_db.add(Collection(tenant_id=tenant.id, name="Colección Invierno", season_id=season.id))
    api_db.flush()
    api_db.add(Category(tenant_id=tenants[0].id, name="Vestidos"))
    with pytest.raises(IntegrityError):
        api_db.flush()  # but one company cannot repeat its own name
    api_db.rollback()
