from cStringIO import StringIO
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from accounting.models import *
from django.contrib.auth.models import User

def generate_pdf(request, list_type, group):

    start_user_list_pos_y = 40
    vert_lines_y_start = 18
    user_list_height_per_block = 36

    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=hello.pdf'

    buffer = StringIO()

    # Create the PDF object, using the StringIO object as its "file."
    p = canvas.Canvas(buffer, bottomup=0, pagesize=(841.89, 595.27))

    p.setLineCap(1)
    p.setLineJoin(1)

    # Draw things on the PDF. Here's where the PDF generation happens.
    # See the ReportLab documentation for the full list of functionality.
    p.drawString(10, 10, "%s list for %s" % (list_type, group))

    p.setFont("Helvetica", 14)
    # Draw titles
    p.drawString(10,33, "Nickname")
    p.drawString(125,33, "Beer")
    p.drawString(300,33, "20")
    p.drawString(450,33, "10")
    p.drawString(600,33, "5")
    p.drawString(750,33, "1")

    lines = [
    # Horizontal
    (10,18, 830, 18),
    (10, start_user_list_pos_y, 830, start_user_list_pos_y),
    # Vertical
    ( 90, vert_lines_y_start,  90, 400),
    (240, vert_lines_y_start, 240, 400),
    (390, vert_lines_y_start, 390, 400),
    (540, vert_lines_y_start, 540, 400),
    (690, vert_lines_y_start, 690, 400),
    ]

    group = AccountGroup.objects.get(slug=group)
    num = 0
    for account in group.account_set.all():
        if not account.is_user_account():
            continue
        # Draw background
        if (num % 2) == 0:
            p.setFillColorRGB(0.9,0.9,0.9)
        else:
            p.setFillColorRGB(1,1,1)
        p.rect(9.5, start_user_list_pos_y + user_list_height_per_block + ((user_list_height_per_block)*(num-1))-0.5,
               820, user_list_height_per_block,
               fill=1, stroke=0)

        if account.is_blocked():
            p.setFillColorRGB(0,0,0)
            p.rect(90, start_user_list_pos_y + user_list_height_per_block + ((user_list_height_per_block)*(num-1))-0.5,
                    740, user_list_height_per_block,
                    fill=1, stroke=0)

        p.setFillColorRGB(0,0,0)
        lines.append(( 10, start_user_list_pos_y + user_list_height_per_block +(user_list_height_per_block*num),
                830, start_user_list_pos_y + user_list_height_per_block + (user_list_height_per_block*num)))
        lines.append((90, start_user_list_pos_y + user_list_height_per_block + (user_list_height_per_block*num) - (user_list_height_per_block/2),
                830, start_user_list_pos_y + user_list_height_per_block + (user_list_height_per_block*num) - (user_list_height_per_block/2)))
        p.drawString(10,62+(user_list_height_per_block*num), '%s' % account.name[:11])
        num += 1

    # Close the PDF object cleanly.
    p.lines(lines)
    p.showPage()
    p.save()

    # Get the value of the StringIO buffer and write it to the response.
    response.write(buffer.getvalue())
    return response
