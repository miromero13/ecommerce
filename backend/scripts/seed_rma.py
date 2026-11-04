"""CU21 & CU24: Seeder for testing returns, exchanges, physical inspection, and mermas.
Creates diverse scenarios for Maria Quispe (Customer) and Rodrigo Choque (Store Manager at Ayni Moda).
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from app.core.database import SessionLocal
import main  # ensures all models and mappers are registered
from app.models.branch import Branch
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product_variant import ProductVariant
from app.models.rma import RmaRequest, RmaRequestItem
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.enums import RolEnum
from app.schemas.inventory_schema import InventoryMovementTypeEnum
from app.schemas.order_schema import FulfillmentStatusEnum, OrderStatusEnum, PaymentMethodEnum, PaymentStatusEnum
from app.services.rma_service import get_month_end_date


def seed_rma_scenarios() -> None:
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # 1. Locate Customer (Maria Quispe) and Manager (Rodrigo Choque)
        customer = db.query(User).filter(User.email == "maria.quispe@clientes.demo.bo").first()
        if not customer:
            print("Customer maria.quispe@clientes.demo.bo not found. Aborting.")
            return

        manager = db.query(User).filter(User.email == "rodrigo.choque@ayni-moda.demo.bo").first()
        if not manager:
            print("Manager rodrigo.choque@ayni-moda.demo.bo not found. Aborting.")
            return

        tenant = db.query(Tenant).filter(Tenant.slug == "ayni-moda").first()
        if not tenant:
            tenant = db.query(Tenant).first()

        branch = db.query(Branch).filter(Branch.tenant_id == tenant.id).first()

        # Clean up existing test RMAs for clean idempotent seeding
        db.query(RmaRequestItem).filter(RmaRequestItem.rma.has(user_id=customer.id)).delete(synchronize_session=False)
        db.query(RmaRequest).filter(RmaRequest.user_id == customer.id).delete(synchronize_session=False)
        db.commit()

        # 2. Find or create recent delivered orders for Maria Quispe (< 30 days)
        recent_orders = (
            db.query(Order)
            .filter(
                Order.user_id == customer.id,
                Order.tenant_id == tenant.id,
                Order.created_at >= now - timedelta(days=25),
            )
            .all()
        )

        variants = (
            db.query(ProductVariant)
            .filter(ProductVariant.tenant_id == tenant.id)
            .limit(10)
            .all()
        )

        if len(recent_orders) < 4:
            # Create additional recent orders so Maria has plenty to test with
            for i in range(4 - len(recent_orders)):
                v1 = variants[i % len(variants)]
                v2 = variants[(i + 1) % len(variants)]
                ord_dt = now - timedelta(days=5 + i * 4)

                new_order = Order(
                    tenant_id=tenant.id,
                    user_id=customer.id,
                    status=OrderStatusEnum.paid,
                    payment_method=PaymentMethodEnum.qr,
                    payment_status=PaymentStatusEnum.paid,
                    fulfillment_status=FulfillmentStatusEnum.delivered,
                    subtotal=Decimal("380.00"),
                    total_amount=Decimal("380.00"),
                    currency="BOB",
                    pickup_branch_id=branch.id if branch else None,
                    delivered_at=ord_dt,
                    created_at=ord_dt,
                )
                db.add(new_order)
                db.flush()

                item1 = OrderItem(
                    order_id=new_order.id,
                    variant_id=v1.id,
                    quantity=1,
                    unit_price=Decimal("180.00"),
                    line_total=Decimal("180.00"),
                    product_id=v1.product_id,
                    product_name=v1.product.name if v1.product else "Prenda Ayni",
                    variant_sku=v1.sku,
                    size_id=v1.size_id,
                    color_id=v1.color_id,
                    image_url=v1.image_url,
                )
                item2 = OrderItem(
                    order_id=new_order.id,
                    variant_id=v2.id,
                    quantity=1,
                    unit_price=Decimal("200.00"),
                    line_total=Decimal("200.00"),
                    product_id=v2.product_id,
                    product_name=v2.product.name if v2.product else "Prenda Ayni",
                    variant_sku=v2.sku,
                    size_id=v2.size_id,
                    color_id=v2.color_id,
                    image_url=v2.image_url,
                )
                db.add(item1)
                db.add(item2)
                db.flush()

            db.commit()
            recent_orders = (
                db.query(Order)
                .filter(
                    Order.user_id == customer.id,
                    Order.tenant_id == tenant.id,
                    Order.created_at >= now - timedelta(days=25),
                )
                .all()
            )

        print(f"Total recent orders available for Maria Quispe: {len(recent_orders)}")

        # --- SCENARIO 1: RMA-2026-0001 (PENDIENTE DE INSPECCIÓN FÍSICA EN SUCURSAL) ---
        order1 = recent_orders[0]
        it1 = order1.items[0]
        it2 = order1.items[1] if len(order1.items) > 1 else order1.items[0]

        # Sister variant of it1 for exchange
        sister_var = (
            db.query(ProductVariant)
            .filter(ProductVariant.product_id == it1.product_id, ProductVariant.id != it1.variant_id)
            .first()
        )

        rma1 = RmaRequest(
            tenant_id=tenant.id,
            order_id=order1.id,
            user_id=customer.id,
            rma_number="RMA-2026-0001",
            status="pending_inspection",
            customer_notes="Solicito cambio de talle para la primera prenda y devolución por defecto en la segunda.",
            created_at=now - timedelta(days=2),
        )
        db.add(rma1)
        db.flush()

        rma1_item1 = RmaRequestItem(
            rma_id=rma1.id,
            order_item_id=it1.id,
            quantity=1,
            reason="wrong_size",
            preferred_resolution="exchange",
            requested_variant_id=sister_var.id if sister_var else None,
            customer_notes="Me quedó chico de hombros, solicito cambio de talle",
            status="pending",
        )
        rma1_item2 = RmaRequestItem(
            rma_id=rma1.id,
            order_item_id=it2.id,
            quantity=1,
            reason="factory_defect",
            preferred_resolution="store_credit",
            customer_notes="Costura lateral deshilachada de fábrica",
            status="pending",
        )
        db.add(rma1_item1)
        db.add(rma1_item2)

        # --- SCENARIO 2: RMA-2026-0002 (APROBADO CON CAMBIO ENTREGADO EN EL ACTO) ---
        order2 = recent_orders[1] if len(recent_orders) > 1 else recent_orders[0]
        it3 = order2.items[0]
        sister_var2 = (
            db.query(ProductVariant)
            .filter(ProductVariant.product_id == it3.product_id, ProductVariant.id != it3.variant_id)
            .first()
        )

        rma2 = RmaRequest(
            tenant_id=tenant.id,
            order_id=order2.id,
            user_id=customer.id,
            rma_number="RMA-2026-0002",
            status="approved",
            customer_notes="Cambio de color por no haber gustado.",
            created_at=now - timedelta(days=6),
        )
        db.add(rma2)
        db.flush()

        # Movement 1: restock devuelta
        m_in = InventoryMovement(
            variant_id=it3.variant_id,
            branch_id=branch.id if branch else None,
            tenant_id=tenant.id,
            movement_type=InventoryMovementTypeEnum.rma_restock,
            quantity=1,
            note="Reingreso por RMA-2026-0002 (Prenda intacta)",
            created_by=manager.id,
            created_at=now - timedelta(days=5),
        )
        # Movement 2: dispatch entrega
        m_out = InventoryMovement(
            variant_id=sister_var2.id if sister_var2 else it3.variant_id,
            branch_id=branch.id if branch else None,
            tenant_id=tenant.id,
            movement_type=InventoryMovementTypeEnum.exchange_dispatch,
            quantity=1,
            note="Entrega de cambio en mostrador RMA-2026-0002",
            created_by=manager.id,
            created_at=now - timedelta(days=5),
        )
        db.add(m_in)
        db.add(m_out)
        db.flush()

        rma2_item = RmaRequestItem(
            rma_id=rma2.id,
            order_item_id=it3.id,
            quantity=1,
            reason="wrong_color",
            preferred_resolution="exchange",
            requested_variant_id=sister_var2.id if sister_var2 else None,
            replacement_variant_id=sister_var2.id if sister_var2 else None,
            item_condition="intact",
            action="restock_available",
            status="approved_exchange",
            branch_id=branch.id if branch else None,
            inspected_by=manager.id,
            inspected_at=now - timedelta(days=5),
            inspection_notes="Prenda intacta con etiquetas originales. Se entrega nueva variante en el acto.",
            restock_movement_id=m_in.id,
            dispatch_movement_id=m_out.id,
        )
        db.add(rma2_item)

        # --- SCENARIO 3: RMA-2026-0003 (APROBADO POR FALLA DE FÁBRICA -> MERMA TÉCNICA Y CRÉDITO FIN DE MES) ---
        order3 = recent_orders[2] if len(recent_orders) > 2 else recent_orders[0]
        it4 = order3.items[0]

        rma3 = RmaRequest(
            tenant_id=tenant.id,
            order_id=order3.id,
            user_id=customer.id,
            rma_number="RMA-2026-0003",
            status="approved",
            customer_notes="Falla de confección en costura lateral.",
            created_at=now - timedelta(days=10),
        )
        db.add(rma3)
        db.flush()

        m_scrap = InventoryMovement(
            variant_id=it4.variant_id,
            branch_id=branch.id if branch else None,
            tenant_id=tenant.id,
            movement_type=InventoryMovementTypeEnum.scrap_quarantine,
            quantity=1,
            note="Baja a merma/cuarentena QR-2026-0044 por defecto de confección RMA-2026-0003",
            created_by=manager.id,
            created_at=now - timedelta(days=8),
        )
        db.add(m_scrap)
        db.flush()

        settle_date = get_month_end_date()
        rma3_item = RmaRequestItem(
            rma_id=rma3.id,
            order_item_id=it4.id,
            quantity=1,
            reason="factory_defect",
            preferred_resolution="store_credit",
            item_condition="factory_damaged",
            action="scrap_quarantine",
            status="approved_refund",
            quarantine_record="QR-2026-0044",
            branch_id=branch.id if branch else None,
            inspected_by=manager.id,
            inspected_at=now - timedelta(days=8),
            inspection_notes="Falla de confección comprobada. No apto para venta comercial. Derivado a merma técnica.",
            refund_amount=it4.unit_price,
            wallet_settlement_date=settle_date,
            settlement_status="pending_month_end",
        )
        db.add(rma3_item)

        db.commit()
        print(" Seed de RMA completado exitosamente!")
        print("  • RMA-2026-0001: PENDIENTE de inspección (para probar revisión como Encargado)")
        print("  • RMA-2026-0002: APROBADO (Cambio en el acto con reingreso y egreso de stock)")
        print("  • RMA-2026-0003: APROBADO (Defecto de fábrica con acta de merma QR-2026-0044 y billetera a fin de mes)")
        print("  • Además, María Quispe cuenta con órdenes elegibles para solicitar un RMA nuevo desde cero.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_rma_scenarios()
