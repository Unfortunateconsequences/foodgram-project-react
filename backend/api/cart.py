from django.http import HttpResponse
from recipes.models import Ingredient
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def shopping_cart_pdf(shopping_list):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'
             ] = 'attachment; filename="shopping_list.pdf"'

    p = canvas.Canvas(response)

    pdfmetrics.registerFont(
        TTFont(
            'Manrope',
            'Manrope-Regular.ttf'
        )
    )

    p.setFont('Manrope', 18)
    p.drawString(250, 800, 'Список покупок')

    y = 750

    for item in shopping_list:
        ingredient = Ingredient.objects.get(id=item['ingredient'])
        p.drawString(
            50,
            y,
            f'{ingredient.name} - {item["total_amount"]} г'
        )
        y -= 20

    p.showPage()
    p.save()
    return response
