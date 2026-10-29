import io
import qrcode
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

def generate_pdf_certificate(student_name, course_title, completion_date, cert_id):
    buffer = io.BytesIO()
    
    # 1. Setup Landscape Document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    story = []
    styles = getSampleStyleSheet()

    # 2. Harmonized Brand Styles
    title_style = ParagraphStyle(
        'CertHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#006837")
    )

    subtitle_style = ParagraphStyle(
        'CertSubHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#006837")
    )

    body_lead = ParagraphStyle(
        'CertLead',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=12,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#444444")
    )

    name_style = ParagraphStyle(
        'CertName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#111111")
    )

    course_style = ParagraphStyle(
        'CertCourse',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#222222")
    )

    footer_style = ParagraphStyle(
        'CertFooter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#555555")
    )

    # 3. Content Elements (Using Your Exact Wording)
    story.append(Spacer(1, 25))
    story.append(Paragraph("FEDERAL POLYTECHNIC IDAH", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("CERTIFICATE OF COMPLETION", subtitle_style))
    story.append(Spacer(1, 20))

    story.append(Paragraph("This is proudly presented to", body_lead))
    story.append(Spacer(1, 15))

    story.append(Paragraph(student_name.title(), name_style))
    story.append(Spacer(1, 15))

    story.append(Paragraph(
        f'for successfully completing the course "<b>{course_title.upper()}</b>" on the E-Learning Portal.', 
        course_style
    ))
    story.append(Spacer(1, 30))

    # 4. Dynamic Verification QR Code
    qr_data = f"Verifier: Federal Poly Idah Portal | Cert ID: {cert_id} | Student: {student_name} | Course: {course_title}"
    qr = qrcode.make(qr_data)
    qr_io = io.BytesIO()
    qr.save(qr_io, format='PNG')
    qr_io.seek(0)
    qr_image = Image(qr_io, width=65, height=65)

    # 5. Footer Metadata Table
    footer_data = [
        [
            Paragraph(f"<b>Date Issued:</b><br/>{completion_date}", footer_style),
            qr_image,
            Paragraph(f"<b>Certificate ID:</b><br/><font size=7>{cert_id}</font>", footer_style)
        ]
    ]

    footer_table = Table(footer_data, colWidths=[240, 100, 240])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))

    story.append(footer_table)

    # 6. Green Institutional Border Canvas Function
    def draw_border(canvas, doc):
        canvas.saveState()
        # Outer Thick Green Border
        canvas.setStrokeColor(colors.HexColor("#006837"))
        canvas.setLineWidth(3)
        canvas.rect(15, 15, doc.pagesize[0] - 30, doc.pagesize[1] - 30)
        
        # Inner Thin Accent Border
        canvas.setLineWidth(1)
        canvas.rect(20, 20, doc.pagesize[0] - 40, doc.pagesize[1] - 40)
        canvas.restoreState()

    # Build PDF with Page Border
    doc.build(story, onFirstPage=draw_border)
    buffer.seek(0)
    return buffer
