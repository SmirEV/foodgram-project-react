import io

from django.http import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def generate_pdf(request, data):
    """ Выгрузка pdf-файла со списком покупок. """
    buffer = io.BytesIO()

    pdf_canvas = canvas.Canvas(buffer, pagesize=A4)
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
    pdf_canvas.setFont("DejaVuSans", 18)
    y = 750
    pdf_canvas.drawString(50, y, 'СПИСОК ПОКУПОК:')
    y -= 20
    for key, value in data.items():
        y -= 20
        text = u'- {item}:  {amount} {unit}'.format(
            item=key, amount=value[0], unit=value[1])
        text = text.encode('utf-8')
        pdf_canvas.drawString(50, y, text)

    pdf_canvas.showPage()
    pdf_canvas.save()

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="data.pdf")
