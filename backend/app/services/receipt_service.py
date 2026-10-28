"""Simple payment receipts (comprobantes): every payment transaction issues one, with its own correlative number.

- Company receipts (series = company): paid web orders, till sales (cash or QR) and reservation deposits.
- Platform receipts (series = "platform"): what a company pays for its subscription plan.
A receipt is a payment proof, not a tax invoice. It is downloadable as PDF and emailed to the payer by a
background loop (`send_pending_receipts`), so a mail failure never undoes a payment.
`issue_*` helpers take part in the payment's transaction: they flush but never commit."""
import base64
from datetime import timedelta, timezone
from decimal import Decimal
from io import BytesIO
from uuid import UUID
from xml.sax.saxutils import escape

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models.payment_receipt import PaymentReceipt

CENT = Decimal("0.01")
LOCAL_TZ = timezone(timedelta(hours=-4))  # America/La_Paz
MAX_EMAIL_ATTEMPTS = 5
METHOD_LABELS = {"card": "Tarjeta (Stripe)", "qr": "QR", "cash": "Efectivo"}
KIND_LABELS = {"order": "Pedido web", "sale": "Venta en tienda", "reservation_deposit": "Anticipo de reserva",
               "subscription": "Suscripción al plan"}


def _money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(CENT)


def display_number(receipt: PaymentReceipt) -> str:
    return f"{'P' if receipt.issuer == 'platform' else 'C'}-{receipt.number:06d}"


def _issue(db: Session, *, tenant_id: UUID, issuer: str, kind: str, source_id: UUID, method: str, currency: str,
           lines: list[dict], summary: list[dict], total, customer_id=None, customer_name=None, customer_email=None,
           branch_id=None) -> PaymentReceipt:
    existing = db.query(PaymentReceipt).filter(PaymentReceipt.kind == kind, PaymentReceipt.source_id == source_id).first()
    if existing:  # a payment confirmed twice (webhook retries) keeps its single receipt
        return existing
    series = "platform" if issuer == "platform" else str(tenant_id)
    # One correlative per series, without gaps or duplicates under concurrent payments.
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": f"receipts:{series}"})
    number = (db.query(func.max(PaymentReceipt.number)).filter(PaymentReceipt.series == series).scalar() or 0) + 1
    receipt = PaymentReceipt(
        tenant_id=tenant_id, issuer=issuer, series=series, number=number, kind=kind, source_id=source_id,
        branch_id=branch_id, customer_id=customer_id, customer_name=customer_name, customer_email=customer_email,
        payment_method=method, currency=currency.upper(), total=_money(total), lines=lines, summary=summary,
    )
    db.add(receipt)
    db.flush()
    return receipt


def _line(description: str, quantity, unit_price, total) -> dict:
    return {"description": description, "quantity": int(quantity), "unit_price": str(_money(unit_price)),
            "total": str(_money(total))}


def _row(label: str, amount) -> dict:
    return {"label": label, "amount": str(_money(amount))}


def _user(db: Session, user_id):
    from app.models.user import User

    return db.query(User).filter(User.id == user_id).first() if user_id else None


def issue_order_receipt(db: Session, order) -> PaymentReceipt:
    customer = _user(db, order.user_id)
    lines = [_line(f"{item.product_name} · {item.variant_sku}", item.quantity, item.unit_price, item.line_total)
             for item in order.items]
    summary = [_row("Subtotal", order.subtotal)]
    for label, amount in (("Descuento por cupón", order.discount_amount), ("Anticipo de reserva aplicado", order.deposit_applied),
                          ("Descuento por puntos", order.loyalty_discount)):
        if amount:
            summary.append(_row(label, -_money(amount)))
    if order.shipping_cost:
        summary.append(_row("Envío a domicilio", order.shipping_cost))
    return _issue(db, tenant_id=order.tenant_id, issuer="company", kind="order", source_id=order.id, method="card",
                  currency=order.currency, lines=lines, summary=summary, total=order.total_amount,
                  customer_id=order.user_id, customer_name=customer.name if customer else None,
                  customer_email=customer.email if customer else None, branch_id=order.pickup_branch_id)


def issue_sale_receipt(db: Session, sale, items: list[dict], cash_movement=None) -> PaymentReceipt:
    customer = _user(db, sale.customer_id)
    method = getattr(sale.payment_method, "value", sale.payment_method)
    lines = [_line(f"{item['product_name']} · {item['variant_sku']}", item["quantity"], item["unit_price"], item["line_total"])
             for item in items]
    summary = [_row("Subtotal", sale.subtotal)]
    if sale.discount_amount:
        summary.append(_row("Descuentos", -_money(sale.discount_amount)))
    if cash_movement is not None and cash_movement.cash_received is not None:
        summary += [_row("Efectivo recibido", cash_movement.cash_received), _row("Cambio entregado", cash_movement.change_given)]
    return _issue(db, tenant_id=sale.tenant_id, issuer="company", kind="sale", source_id=sale.id, method=method,
                  currency=sale.currency, lines=lines, summary=summary, total=sale.total_amount,
                  customer_id=sale.customer_id, customer_name=customer.name if customer else "Cliente en tienda",
                  customer_email=customer.email if customer else None, branch_id=sale.branch_id)


def issue_deposit_receipt(db: Session, reservation, currency: str) -> PaymentReceipt:
    customer = _user(db, reservation.user_id)
    lines = [_line(f"Anticipo del 50 % de la reserva para el {reservation.visit_date:%d/%m/%Y}", 1,
                   reservation.deposit_amount, reservation.deposit_amount)]
    summary = [_row("Se descuenta al comprar las prendas reservadas (no reembolsable)", reservation.deposit_amount)]
    return _issue(db, tenant_id=reservation.tenant_id, issuer="company", kind="reservation_deposit", source_id=reservation.id,
                  method="card", currency=currency, lines=lines, summary=summary, total=reservation.deposit_amount,
                  customer_id=reservation.user_id, customer_name=customer.name if customer else None,
                  customer_email=customer.email if customer else None, branch_id=reservation.branch_id)


def issue_subscription_receipt(db: Session, subscription, plan) -> PaymentReceipt:
    from app.models.tenant import Tenant

    tenant = db.query(Tenant).filter(Tenant.id == subscription.tenant_id).one()
    cycle = getattr(subscription.billing_cycle, "value", subscription.billing_cycle)
    method = getattr(subscription.payment_method, "value", subscription.payment_method)
    period = f"{subscription.start_date:%d/%m/%Y} – {subscription.end_date:%d/%m/%Y}" if subscription.end_date else ""
    lines = [_line(f"Plan {plan.name} · facturación {'anual' if cycle == 'yearly' else 'mensual'} · {period}", 1,
                   subscription.amount, subscription.amount)]
    return _issue(db, tenant_id=tenant.id, issuer="platform", kind="subscription", source_id=subscription.id,
                  method="cash" if method == "cash" else "card", currency="BOB", lines=lines,
                  summary=[_row("Período del plan", subscription.amount)], total=subscription.amount,
                  customer_name=tenant.name, customer_email=tenant.contact_email)


# --- Reading -------------------------------------------------------------------------------------

def _issuer_name(db: Session, receipt: PaymentReceipt) -> str:
    from app.core.config import settings
    from app.models.tenant import Tenant

    if receipt.issuer == "platform":
        return settings.app_name
    return db.query(Tenant.name).filter(Tenant.id == receipt.tenant_id).scalar() or ""


def serialize(db: Session, receipt: PaymentReceipt) -> dict:
    return {
        "id": receipt.id, "number": display_number(receipt), "issuer": receipt.issuer, "issuer_name": _issuer_name(db, receipt),
        "kind": receipt.kind, "kind_label": KIND_LABELS[receipt.kind], "source_id": receipt.source_id,
        "tenant_id": receipt.tenant_id, "branch_id": receipt.branch_id, "customer_name": receipt.customer_name,
        "customer_email": receipt.customer_email, "payment_method": receipt.payment_method,
        "payment_method_label": METHOD_LABELS[receipt.payment_method], "currency": receipt.currency,
        "total": receipt.total, "lines": receipt.lines, "summary": receipt.summary,
        "issued_at": receipt.issued_at, "emailed_at": receipt.emailed_at,
    }


def visible_query(db: Session, user):
    """Who may see a receipt: its customer; the company's admin (all), manager/cashier (their branch);
    the paying company's admin and the superadmin for platform receipts."""
    from app.schemas.enums import RolEnum

    query = db.query(PaymentReceipt)
    if user.rol == RolEnum.cliente:
        return query.filter(PaymentReceipt.customer_id == user.id)
    if user.rol == RolEnum.superadministrador:
        return query.filter(PaymentReceipt.issuer == "platform")
    if user.rol == RolEnum.administrador:
        return query.filter(PaymentReceipt.tenant_id == user.tenant_id)
    if user.rol in (RolEnum.encargado, RolEnum.cajero):
        return query.filter(PaymentReceipt.tenant_id == user.tenant_id, PaymentReceipt.issuer == "company",
                            PaymentReceipt.branch_id == user.branch_id)
    return query.filter(False)


def list_receipts(db: Session, user, kind: str | None = None, tenant_id: UUID | None = None) -> list[dict]:
    query = visible_query(db, user)
    if kind:
        query = query.filter(PaymentReceipt.kind == kind)
    if tenant_id:
        query = query.filter(PaymentReceipt.tenant_id == tenant_id)
    return [serialize(db, r) for r in query.order_by(PaymentReceipt.issued_at.desc()).limit(200).all()]


def find_receipt(db: Session, user, kind: str, source_id: UUID) -> PaymentReceipt | None:
    return visible_query(db, user).filter(PaymentReceipt.kind == kind, PaymentReceipt.source_id == source_id).first()


def request_resend(db: Session, receipt: PaymentReceipt) -> None:
    if not receipt.customer_email:
        raise ValueError("El comprobante no tiene un correo de destino")
    receipt.emailed_at, receipt.email_attempts = None, 0
    db.commit()


# --- PDF and email ---------------------------------------------------------------------------------

def render_pdf(db: Session, receipt: PaymentReceipt) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A5
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A5, leftMargin=28, rightMargin=28, topMargin=28, bottomMargin=28,
                            title=f"Comprobante {display_number(receipt)}")
    issued = receipt.issued_at.astimezone(LOCAL_TZ).strftime("%d/%m/%Y %H:%M")
    story = [
        Paragraph(f"<b>{escape(_issuer_name(db, receipt))}</b>", styles["Title"]),
        Paragraph(f"Comprobante de pago N° <b>{display_number(receipt)}</b>", styles["Heading3"]),
        Paragraph(f"{KIND_LABELS[receipt.kind]} · {issued} · {METHOD_LABELS[receipt.payment_method]}", styles["Normal"]),
        Paragraph(f"Cliente: {escape(receipt.customer_name or 'Sin nombre')}"
                  + (f" · {escape(receipt.customer_email)}" if receipt.customer_email else ""), styles["Normal"]),
        Spacer(1, 10),
    ]
    rows = [["Detalle", "Cant.", "P. unit.", "Importe"]] + [
        [Paragraph(escape(line["description"]), styles["BodyText"]), line["quantity"], line["unit_price"], line["total"]]
        for line in receipt.lines]
    table = Table(rows, colWidths=[190, 40, 60, 60], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    story += [table, Spacer(1, 8)]
    totals = [[row["label"], row["amount"]] for row in receipt.summary] + [[f"TOTAL ({receipt.currency})", str(receipt.total)]]
    summary = Table(totals, colWidths=[290, 60])
    summary.setStyle(TableStyle([("ALIGN", (1, 0), (1, -1), "RIGHT"), ("FONTSIZE", (0, 0), (-1, -1), 8),
                                 ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"), ("LINEABOVE", (0, -1), (-1, -1), 0.5, colors.black)]))
    story += [summary, Spacer(1, 12),
              Paragraph("Comprobante de pago emitido por el sistema. No es una factura fiscal.", styles["Italic"])]
    doc.build(story)
    return buffer.getvalue()


async def send_pending_receipts(session_factory, email_service=None, limit: int = 20) -> int:
    """Email the PDF of receipts not sent yet; retried a few times if the mail service fails."""
    from app.services.email_service import email_service as default_email_service

    mailer = email_service or default_email_service
    sent = 0
    with session_factory() as db:
        pending = (db.query(PaymentReceipt)
                   .filter(PaymentReceipt.emailed_at.is_(None), PaymentReceipt.customer_email.is_not(None),
                           PaymentReceipt.email_attempts < MAX_EMAIL_ATTEMPTS)
                   .order_by(PaymentReceipt.issued_at).limit(limit).all())
        for receipt in pending:
            number = display_number(receipt)
            pdf = render_pdf(db, receipt)
            ok = await mailer.send_email(
                to=receipt.customer_email,
                subject=f"Comprobante de pago {number} · {_issuer_name(db, receipt)}",
                html=(f"<p>Hola {escape(receipt.customer_name or '')},</p>"
                      f"<p>Adjuntamos tu comprobante <b>{number}</b> ({KIND_LABELS[receipt.kind]}) por "
                      f"<b>{receipt.total} {receipt.currency}</b>, pagado con {METHOD_LABELS[receipt.payment_method]}.</p>"),
                category="receipt",
                attachments=[{"content": base64.b64encode(pdf).decode(), "filename": f"comprobante-{number}.pdf",
                              "type": "application/pdf", "disposition": "attachment"}],
            )
            receipt.email_attempts += 1
            if ok:
                from datetime import datetime

                receipt.emailed_at = datetime.now(timezone.utc)
                sent += 1
            db.commit()
    return sent
