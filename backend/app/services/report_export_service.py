"""Excel and paginated PDF exports for the existing scoped report rows."""
from datetime import datetime
from enum import Enum
from io import BytesIO
from xml.sax.saxutils import escape

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

COLUMN_LABELS = {
    'branch_name': 'Sucursal', 'product_name': 'Producto', 'variant_sku': 'SKU', 'type': 'Tipo',
    'quantity_sold': 'Unidades vendidas', 'gross_sales': 'Ventas brutas',
    'payment_method': 'Método de pago', 'payment_status': 'Estado de pago', 'sale_status': 'Estado de venta',
    'quantity': 'Cantidad', 'reserved_quantity': 'Reservado', 'available_quantity': 'Disponible',
    'minimum_stock': 'Stock mínimo', 'movement_type': 'Movimiento', 'movements_count': 'Movimientos',
}


def _value(value):
    if isinstance(value, Enum):
        return value.value
    return '' if value is None else value


def to_excel(rows: list[dict], headers: list[str]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Reporte'
    sheet.append([COLUMN_LABELS.get(key, key) for key in headers])
    for cell in sheet[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill('solid', fgColor='166534')
    for row in rows:
        sheet.append([_value(row.get(key)) for key in headers])
        for cell in sheet[sheet.max_row]:
            if isinstance(cell.value, str):
                # Untrusted names/SKUs are text, never executable spreadsheet formulas.
                cell.data_type = 's'
    for index, key in enumerate(headers, 1):
        sheet.column_dimensions[get_column_letter(index)].width = min(40, max(18, len(COLUMN_LABELS.get(key, key)) + 4))
    sheet.freeze_panes = 'A2'
    sheet.auto_filter.ref = sheet.dimensions
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def to_pdf(title: str, rows: list[dict], headers: list[str]) -> bytes:
    output = BytesIO()
    styles = getSampleStyleSheet()
    document = SimpleDocTemplate(output, pagesize=landscape(A4), leftMargin=24, rightMargin=24,
                                 topMargin=24, bottomMargin=24)
    cell_style = styles['BodyText']
    cell_style.fontSize = 8
    cell_style.leading = 10
    cells = [[Paragraph(escape(COLUMN_LABELS.get(key, key)), cell_style) for key in headers]]
    cells.extend([[Paragraph(escape(str(_value(row.get(key)))), cell_style) for key in headers] for row in rows])
    table = LongTable(cells, repeatRows=1, colWidths=[document.width / len(headers)] * len(headers))
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dcfce7')),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
    ]))
    document.build([Paragraph(escape(title), styles['Title']), Spacer(1, 12), table])
    return output.getvalue()


# ---- Analytics (CU08) professional exports ---------------------------------------------------
GREEN, LIGHT_GREEN = colors.HexColor('#166534'), colors.HexColor('#dcfce7')


def _num(value) -> float:
    return float(value or 0)


def _fmt(value, kind: str) -> str:
    if kind == 'money':
        return f'{_num(value):,.2f} Bs.'
    if kind == 'number':
        return f'{_num(value):,.0f}'
    return str(_value(value))


def _generated(generated_by: str) -> str:
    return f'Generado: {datetime.now():%d/%m/%Y %H:%M} por {generated_by}'


def _delta(value: float) -> str:
    return f'{value:+,.1f}'.replace(',', '').replace('.', ',') + ' %'  # "+12,5 %"


def _is_sales(result) -> bool:
    """Sales results carry revenue totals; inventory/stock/movements results do not."""
    return 'revenue' in (result.totals or {})


def _cards(result) -> list[tuple[str, str, str]]:
    cards = [('units', 'Unidades', 'number'), ('revenue', 'Ingresos', 'money'),
             ('orders', 'Pedidos', 'number'), ('avg_ticket', 'Ticket promedio', 'money')]
    return cards + [('customers', 'Clientes distintos', 'number')] if 'customers' in result.totals else cards


def _groups(result) -> list[tuple[object, list[dict], dict | None]]:
    """[(group label, rows, subtotal row)]: one group without subtotal unless there are 2 dimensions."""
    text = [c for c in result.columns if c['type'] == 'text']
    if len(text) < 2 or not result.rows or not _is_sales(result):  # stock rows: subtotals would mean nothing
        return [(None, result.rows, None)]
    metric, first, groups = result.columns[-1]['key'], text[0]['key'], {}
    for row in result.rows:
        groups.setdefault(row.get(first), []).append(row)
    out = []
    for label, rows in groups.items():
        values = [_num(r.get(metric)) for r in rows]
        mean = metric == 'avg_ticket'  # a sum of averages is meaningless
        out.append((label, rows, {first: 'Promedio' if mean else 'Subtotal',
                                  metric: sum(values) / len(values) if mean else sum(values)}))
    return out


def analytics_to_excel(result, company: str, generated_by: str) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Reporte'
    for index, text in enumerate([result.title, company, f"Período: {result.period.get('label', '')}",
                                  _generated(generated_by)], 1):
        sheet.cell(index, 1, str(text)).data_type = 's'
    sheet['A1'].font = Font(bold=True, size=14)
    if _is_sales(result) and 'customers' in result.totals:  # the only sales total not visible in the table
        sheet.cell(5, 1, f"Clientes distintos: {result.totals['customers']}").data_type = 's'
    columns = result.columns
    for index, column in enumerate(columns, 1):
        cell = sheet.cell(6, index, column['label'])
        cell.font, cell.fill = Font(bold=True, color='FFFFFF'), PatternFill('solid', fgColor='166534')
        cell.data_type = 's'
    widths = [len(c['label']) + 4 for c in columns]

    def put(row: dict, bold: bool):
        number = sheet.max_row + 1
        for index, column in enumerate(columns, 1):
            value, cell = row.get(column['key']), sheet.cell(number, index)
            if column['type'] == 'text':
                cell.value = '' if value is None else str(value)
                cell.data_type = 's'  # untrusted names are text, never formulas
            elif value is not None:
                cell.value = _num(value)
                cell.number_format = '#,##0.00' if column['type'] == 'money' else '#,##0'
            if bold:
                cell.font = Font(bold=True)
            widths[index - 1] = max(widths[index - 1], len(_fmt(value, column['type'])) + 2)

    for _, rows, subtotal in _groups(result):
        for row in rows:
            put(row, False)
        if subtotal:
            put(subtotal, True)
    if not result.rows:
        sheet.cell(7, 1, result.message or 'Sin datos').data_type = 's'
    for index, width in enumerate(widths, 1):
        sheet.column_dimensions[get_column_letter(index)].width = min(60, width)
    sheet.freeze_panes = 'A7'
    sheet.auto_filter.ref = f'A6:{get_column_letter(len(columns))}{max(sheet.max_row, 6)}'
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


class _NumberedCanvas(Canvas):
    """Two-pass canvas so the footer can say 'Página X de Y'."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            self.setFont('Helvetica', 8)
            self.drawRightString(landscape(A4)[0] - 24, 14, f'Página {self._pageNumber} de {total}')
            super().showPage()
        super().save()


def _chart(result):
    metric, label = result.columns[-1], result.columns[0]
    drawing = Drawing(780, 170)
    line = result.chart == 'line'
    chart = HorizontalLineChart() if line else VerticalBarChart()
    chart.x, chart.y, chart.width, chart.height = 60, 40, 700, 110
    chart.data = [[_num(r.get(metric['key'])) for r in result.rows]]
    chart.categoryAxis.categoryNames = [str(r.get(label['key']))[:18] for r in result.rows]
    chart.categoryAxis.labels.angle, chart.categoryAxis.labels.boxAnchor = 30, 'ne'
    chart.categoryAxis.labels.fontSize = chart.valueAxis.labels.fontSize = 7
    chart.valueAxis.valueMin = 0
    if line:
        chart.lines[0].strokeColor = GREEN
    else:
        chart.bars[0].fillColor = GREEN
    drawing.add(chart)
    return drawing


def analytics_to_pdf(result, company: str, generated_by: str) -> bytes:
    output = BytesIO()
    styles = getSampleStyleSheet()
    small = ParagraphStyle('small', parent=styles['BodyText'], fontSize=8, leading=10)
    right = ParagraphStyle('right', parent=small, alignment=2)
    bold = ParagraphStyle('bold', parent=small, fontName='Helvetica-Bold')
    bold_right = ParagraphStyle('boldr', parent=bold, alignment=2)
    document = SimpleDocTemplate(output, pagesize=landscape(A4), leftMargin=24, rightMargin=24,
                                 topMargin=24, bottomMargin=30)

    def p(text, style):  # every dynamic string is markup-escaped
        return Paragraph(escape(str(text)), style)

    story = [p(company, styles['Heading3']), p(result.title, styles['Title']),
             p(f"Período: {result.period.get('label', '')}", small), p(_generated(generated_by), small),
             Spacer(1, 8)]

    if _is_sales(result):  # sales total cards; other kinds show only the table
        cards = []
        for key, name, kind in _cards(result):
            text = f"<b>{name}</b><br/>{escape(_fmt((result.totals or {}).get(key), kind))}"
            delta = (result.delta_pct or {}).get(key)
            if delta is not None:
                text += f'<br/>{_delta(delta)}'
            cards.append(Paragraph(text, styles['BodyText']))
        card_table = Table([cards], colWidths=[document.width / len(cards)] * len(cards))
        card_table.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4'))]))
        story += [card_table, Spacer(1, 8)]

    columns = result.columns
    text_cols = [c for c in columns if c['type'] == 'text']
    if not result.rows:
        story.append(p(result.message or 'Sin datos para el período seleccionado.', styles['BodyText']))
    else:
        if len(text_cols) == 1 and len(result.rows) <= 20:
            story += [_chart(result), Spacer(1, 8)]
        for label, rows, subtotal in _groups(result):
            if label is not None:
                story.append(p(f"{text_cols[0]['label']}: {label}", styles['Heading4']))
            cells = [[p(c['label'], bold) for c in columns]]
            for row in rows:
                cells.append([p(_fmt(row.get(c['key']), c['type']), small if c['type'] == 'text' else right)
                              for c in columns])
            if subtotal:
                cells.append([p(_fmt(subtotal.get(c['key']), c['type']) if c['key'] in subtotal else '',
                                bold if c['type'] == 'text' else bold_right) for c in columns])
            table = LongTable(cells, repeatRows=1, colWidths=[document.width / len(columns)] * len(columns))
            style = [('BACKGROUND', (0, 0), (-1, 0), LIGHT_GREEN),
                     ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                     ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])]
            if subtotal:
                style.append(('BACKGROUND', (0, -1), (-1, -1), LIGHT_GREEN))
            table.setStyle(TableStyle(style))
            story += [table, Spacer(1, 10)]
    document.build(story, canvasmaker=_NumberedCanvas)
    return output.getvalue()
