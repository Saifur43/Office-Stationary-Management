from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def generate_requisition_pdf(requisition, requisition_items):
    # Create a PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="requisition_{requisition.id}.pdf"'

    # Register the Nikosh font
    pdfmetrics.registerFont(TTFont('kalpurush', 'static/fonts/NotoSansBengali-Regular.ttf'))  # Update path to your font file

    # Create the PDF document
    doc = SimpleDocTemplate(response, pagesize=A4)

    # Define styles
    styles = getSampleStyleSheet()
    
    # Create a custom ParagraphStyle for using the Nikosh font
    nikosh_style = ParagraphStyle(name='kalpurushStyle', fontName='kalpurush', fontSize=12)

    content = []

    # Title
    title = Paragraph(f'Requisition #{requisition.id}', styles['Title'])
    content.append(title)

    # Requisition details
    requisition_details = [
        Paragraph(f'User: {requisition.user.username}', styles['Normal']),
        Paragraph(f'Status: {requisition.status}', styles['Normal']),
        Paragraph(f'Date Created: {requisition.date_created}', styles['Normal']),
    ]
    content.extend(requisition_details)

    # Add a table for requisition items
    data = [['Item Name', 'Requested Quantity', 'Approved Quantity']]
    for item in requisition_items:
        data.append([
            Paragraph(item.inventory_item.name, nikosh_style),  # Use the Nikosh style
            Paragraph(str(item.quantity_requested), nikosh_style),
            Paragraph(str(item.quantity_approved), nikosh_style),
        ])

    # Create a table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # You can keep Helvetica for headers
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    content.append(table)

    # Build the PDF
    doc.build(content)

    return response
