"""CU21 & CU24: PDF generation for official RMA slips (Ficha de Devolución y Cambio)."""
from datetime import datetime, timedelta, timezone
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.models.rma import RmaRequest, RmaRequestItem
from app.models.tenant import Tenant

LOCAL_TZ = timezone(timedelta(hours=-4))  # America/La_Paz

STATUS_LABELS = {
    "pending_inspection": "PENDIENTE DE INSPECCIÓN",
    "approved": "APROBADO",
    "partially_approved": "APROBADO PARCIAL",
    "rejected": "RECHAZADO",
    "completed": "COMPLETADO",
}

STATUS_COLORS = {
    "pending_inspection": colors.HexColor("#d97706"),  # Amber
    "approved": colors.HexColor("#16a34a"),            # Green
    "partially_approved": colors.HexColor("#2563eb"),  # Blue
    "rejected": colors.HexColor("#dc2626"),            # Red
    "completed": colors.HexColor("#475569"),          # Slate
}

REASON_LABELS = {
    "wrong_size": "Talle incorrecto",
    "wrong_color": "Color incorrecto",
    "factory_defect": "Defecto de fábrica",
    "change_of_mind": "Arrepentimiento / Cambio",
}

RESOLUTION_LABELS = {
    "exchange": "Cambio de prenda",
    "store_credit": "Crédito en Billetera",
}

CONDITION_LABELS = {
    "intact": "Intacta (Con etiquetas)",
    "factory_damaged": "Falla de confección/fábrica",
    "customer_damaged": "Uso/Daño del cliente",
}

ITEM_STATUS_LABELS = {
    "pending": "Pendiente",
    "approved_exchange": "Aprobado (Cambio)",
    "approved_refund": "Aprobado (Billetera)",
    "rejected": "Rechazado",
}


# [CU21 - Secuencia: Paso 2.18] rma_routes invoca _company_name(rma) sobre la entidad Empresa
# [CU21 - Secuencia: Paso 2.19] Empresa retorna _company_name(rma): str a rma_routes
def _company_name(db: Session, rma: RmaRequest) -> str:
    if rma.tenant:
        return rma.tenant.name
    tenant = db.query(Tenant).filter(Tenant.id == rma.tenant_id).first()
    return tenant.name if tenant else "FashionStore"


# [CU21 - Secuencia: Paso 2.16] rma_routes invoca generate_rma_pdf(rma) sobre la entidad SolicitudDevolucion
# [CU21 - Secuencia: Paso 2.17] SolicitudDevolucion retorna generate_rma_pdf(rma): bytes a rma_routes
def generate_rma_pdf(db: Session, rma: RmaRequest) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
        title=f"Ficha {rma.rma_number}",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "RmaTitle",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "RmaSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
    )
    badge_style = ParagraphStyle(
        "RmaBadge",
        parent=styles["Normal"],
        fontSize=10,
        leading=12,
        textColor=colors.white,
        alignment=1,
    )
    body_bold = ParagraphStyle(
        "RmaBodyBold",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1e293b"),
    )
    body_small = ParagraphStyle(
        "RmaBodySmall",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#334155"),
    )

    company = _company_name(db, rma)
    created_dt = rma.created_at.astimezone(LOCAL_TZ).strftime("%d/%m/%Y %H:%M")
    status_label = STATUS_LABELS.get(rma.status, rma.status.upper())
    badge_color = STATUS_COLORS.get(rma.status, colors.HexColor("#475569"))

    # Top Header Banner
    header_data = [
        [
            Paragraph(f"<b>{escape(company)}</b><br/><font size=9 color='#64748b'>Ficha Oficial de Devolución y Cambio (RMA)</font>", title_style),
            Paragraph(f"<b>N° {escape(rma.rma_number)}</b><br/><font size=8 color='#64748b'>Fecha: {created_dt}</font>", subtitle_style),
        ]
    ]
    header_table = Table(header_data, colWidths=[340, 180])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ]))

    # Status ribbon
    badge_cell = Table([[Paragraph(f"<b>ESTADO: {status_label}</b>", badge_style)]], colWidths=[520])
    badge_cell.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), badge_color),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))

    # Customer & Order Info Box
    customer_name = rma.user.name if rma.user and rma.user.name else rma.user.email
    order_number = f"PED-{str(rma.order_id)[:8].upper()}"
    info_data = [
        [
            Paragraph("<b>Datos del Cliente</b>", body_bold),
            Paragraph("<b>Referencia de Compra Original</b>", body_bold),
        ],
        [
            Paragraph(f"Nombre: {escape(customer_name)}<br/>Email: {escape(rma.user.email)}", body_small),
            Paragraph(f"Orden: {order_number}<br/>Fecha Compra: {rma.order.created_at.astimezone(LOCAL_TZ).strftime('%d/%m/%Y')}", body_small),
        ],
    ]
    if rma.customer_notes:
        info_data.append([
            Paragraph(f"<b>Nota del Cliente:</b> {escape(rma.customer_notes)}", body_small),
            Paragraph("", body_small),
        ])

    info_table = Table(info_data, colWidths=[260, 260])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))

    # Items Table
    headers = [
        Paragraph("<b>Prenda / Ítem</b>", body_bold),
        Paragraph("<b>Motivo</b>", body_bold),
        Paragraph("<b>Resolución Pedida</b>", body_bold),
        Paragraph("<b>Inspección / Dictamen</b>", body_bold),
        Paragraph("<b>Estado</b>", body_bold),
    ]
    rows = [headers]

    for item in rma.items:
        # Prenda original
        prod_title = item.order_item.product_name if item.order_item else "Prenda"
        sku = item.order_item.variant_sku if item.order_item else ""
        price = f"Bs. {item.order_item.unit_price:.2f}" if item.order_item else ""
        item_col = f"<b>{escape(prod_title)}</b><br/><font color='#64748b' size=7>SKU: {escape(sku)} · {price} (Cant: {item.quantity})</font>"

        # Motivo
        reason_text = REASON_LABELS.get(item.reason, item.reason)
        if item.customer_notes:
            reason_text += f"<br/><font color='#475569' size=7><i>'{escape(item.customer_notes)}'</i></font>"

        # Resolución
        res_text = RESOLUTION_LABELS.get(item.preferred_resolution, item.preferred_resolution)
        if item.preferred_resolution == "exchange" and item.requested_variant:
            size_name = item.requested_variant.size.name if item.requested_variant.size else ""
            color_name = item.requested_variant.color.name if item.requested_variant.color else ""
            res_text += f"<br/><font color='#0284c7' size=7>Por: Talle {escape(size_name)} · {escape(color_name)}</font>"

        # Dictamen / Inspección
        cond_text = CONDITION_LABELS.get(item.item_condition, "Sin inspeccionar")
        dictamen_text = f"<b>Condición:</b> {cond_text}"
        if item.replacement_variant:
            rep_size = item.replacement_variant.size.name if item.replacement_variant.size else ""
            rep_color = item.replacement_variant.color.name if item.replacement_variant.color else ""
            dictamen_text += f"<br/><font color='#16a34a' size=7>Entregada en acto: Talle {escape(rep_size)} · {escape(rep_color)}</font>"
        if item.quarantine_record:
            dictamen_text += f"<br/><font color='#dc2626' size=7>Merma Oficial: {escape(item.quarantine_record)}</font>"
        if item.refund_amount and item.wallet_settlement_date:
            settle_date = item.wallet_settlement_date.astimezone(LOCAL_TZ).strftime("%d/%m/%Y")
            dictamen_text += f"<br/><font color='#d97706' size=7>Billetera: Bs. {item.refund_amount:.2f} (Cierre {settle_date})</font>"
        if item.inspection_notes:
            dictamen_text += f"<br/><font color='#64748b' size=7>Nota: {escape(item.inspection_notes)}</font>"

        item_status = ITEM_STATUS_LABELS.get(item.status, item.status)

        rows.append([
            Paragraph(item_col, body_small),
            Paragraph(reason_text, body_small),
            Paragraph(res_text, body_small),
            Paragraph(dictamen_text, body_small),
            Paragraph(f"<b>{escape(item_status)}</b>", body_small),
        ])

    items_table = Table(rows, colWidths=[140, 95, 95, 130, 60], repeatRows=1)
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))

    # Policy notice
    policy_text = (
        "<b>Política Oficial de Cambios y Devoluciones:</b><br/>"
        "• Plazo máximo de 30 días posteriores a la fecha de entrega original.<br/>"
        "• Los cambios de prenda aplican exclusivamente a variantes (talle/color) del mismo modelo original y se entregan en el acto en sucursal sujeta a stock.<br/>"
        "• Las prendas devueltas por cambio o gusto deben estar intactas, sin uso y con etiquetas de origen adheridas.<br/>"
        "• Las devoluciones de dinero se realizan a la Billetera Digital del cliente y se efectivizan al cierre del mes contable para resguardo del inventario.<br/>"
        "• Las prendas con defectos de fabricación comprobados son derivadas a merma y baja técnica definitiva sin reingreso al catálogo comercial."
    )
    policy_paragraph = Paragraph(policy_text, ParagraphStyle("PolicyStyle", parent=styles["Normal"], fontSize=7.5, leading=10, textColor=colors.HexColor("#475569")))

    # Signature blocks
    sign_data = [
        [
            Paragraph("________________________________________<br/><b>Firma del Cliente</b><br/><font size=7 color='#64748b'>Conformidad de solicitud y/o entrega</font>", body_small),
            Paragraph("________________________________________<br/><b>Firma y Sello de la Sucursal</b><br/><font size=7 color='#64748b'>Encargado responsable de inspección</font>", body_small),
        ]
    ]
    sign_table = Table(sign_data, colWidths=[260, 260])
    sign_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 15),
    ]))

    story = [
        header_table,
        Spacer(1, 8),
        badge_cell,
        Spacer(1, 10),
        info_table,
        Spacer(1, 12),
        Paragraph("<b>Detalle de Prendas Solicitadas e Inspección Técnica</b>", body_bold),
        Spacer(1, 4),
        items_table,
        Spacer(1, 14),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8),
        policy_paragraph,
        Spacer(1, 20),
        sign_table,
    ]

    doc.build(story)
    return buffer.getvalue()
