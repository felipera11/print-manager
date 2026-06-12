from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from models import Client, Quote, QuoteItem


def build_quote_pdf(quote: Quote, issuer: Client, recipient: Client, items: list[QuoteItem]) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=f"Quote #{quote.id}")
    styles = getSampleStyleSheet()

    elements = [
        Paragraph(f"Quote #{quote.id}", styles["Title"]),
        Spacer(1, 12),
        _build_header_table(doc, styles, issuer, recipient, quote),
        Spacer(1, 18),
        _build_items_table(doc, items),
        Spacer(1, 18),
        _build_totals_table(doc, quote, items),
    ]

    doc.build(elements)
    return buffer.getvalue()


def _client_block(client: Client) -> str:
    lines = [f"<b>{client.name}</b>", client.email, f"CNPJ: {client.cnpj}", client.mobile]
    if client.address:
        lines.append(client.address)
    return "<br/>".join(lines)


def _build_header_table(doc, styles, issuer, recipient, quote):
    table = Table(
        [
            [Paragraph(_client_block(issuer), styles["Normal"]), Paragraph(_client_block(recipient), styles["Normal"])],
            [Paragraph(f"Emission date: {quote.date.isoformat()}", styles["Normal"]), ""],
        ],
        colWidths=[doc.width / 2.0, doc.width / 2.0],
    )
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 1), (-1, 1), 12),
    ]))
    return table


def _build_items_table(doc, items):
    rows = [["Part", "Qty", "Unit price", "Total"]]
    for item in items:
        rows.append([
            item.part_name,
            str(item.quantity),
            f"${float(item.unit_price):.2f}",
            f"${float(item.total):.2f}",
        ])

    table = Table(rows, colWidths=[doc.width * 0.4, doc.width * 0.15, doc.width * 0.225, doc.width * 0.225])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return table


def _build_totals_table(doc, quote, items):
    subtotal = sum(float(item.total) for item in items)
    discount_amount = subtotal - float(quote.total)

    rows = [
        ["Subtotal", f"${subtotal:.2f}"],
        [f"Discount ({float(quote.discount):.2f}%)", f"-${discount_amount:.2f}"],
        ["Grand total", f"${float(quote.total):.2f}"],
    ]
    table = Table(rows, colWidths=[doc.width * 0.775, doc.width * 0.225])
    table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE", (0, -1), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, -1), (-1, -1), 6),
    ]))
    return table
