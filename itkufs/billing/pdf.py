from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    Paragraph, BaseDocTemplate, PageTemplate, Frame, Spacer, KeepTogether)
from reportlab.platypus.tables import Table, TableStyle
from reportlab.platypus.flowables import Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

from django.utils.translation import ugettext as _
from django.http import HttpResponse
from django.utils.html import escape
from django.template.defaultfilters import slugify

from itkufs.reports.pdf import ALTERNATE_COLORS, BORDER_COLOR

styles = getSampleStyleSheet()
styles['Normal'].spaceAfter = 5

table_style = TableStyle([
    ('FONT',     (0, 0), (-1, -1), 'Helvetica'),
    ('FONT',     (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONT',     (0, -1), (-1, -1), 'Helvetica-Bold'),
    ('VALIGN',   (0, 0), (-1, -1), 'MIDDLE'),
    ('ALIGN',    (0, 0), (0, -1), 'LEFT'),
    ('ALIGN',    (1, 0), (1, -1), 'RIGHT'),
    ('ROWBACKGROUNDS', (0, 0), (-1, -2), ALTERNATE_COLORS),
    ('LINEBELOW',  (0, 0), (-1, 0), 1, BORDER_COLOR),
    ('LINEBELOW',  (0, -1), (-1, -1), 2, BORDER_COLOR),
    ('LINEABOVE',  (0, -1),  (-1, -1),  1, BORDER_COLOR),
])


def pdf(group, bill):
    """PDF version of bill"""

    width, height = A4
    margin = 1*cm
    heading = 2*cm

    logo_height = 1.5*cm

    font_name = 'Times-Roman'
    font_size = 16

    filename = '%s-%s-%s-%s' % (date.today(), group, _('bill'), bill.id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s.pdf' % (
        slugify(filename))

    show_logo = bool(group.logo and group.logo.storage.exists(group.logo.path))

    if show_logo:
        ratio = group.logo.width / group.logo.height
        logo = Image(
            group.logo.path, width=logo_height*ratio, height=logo_height)

    def draw_header(canvas, doc):
        if show_logo:
            logo.drawOn(
                canvas,
                width/2 - 1*margin - logo_height*ratio,
                height - margin - logo_height)

        canvas.setFont(font_name, font_size)
        canvas.drawString(
            margin, height - margin - font_size, _('Bill #%d') % (bill.id))
        canvas.setFont(font_name, font_size - 4)
        canvas.drawString(
            margin, height - margin - 2*font_size,
            bill.created.strftime(_('%Y-%m-%d %H:%M').encode('utf-8')))

    frames = [
        Frame(
            0, 0, width/2, height-heading,
            leftPadding=margin, bottomPadding=margin,
            rightPadding=margin/2, topPadding=margin),
        Frame(
            width/2, 0, width/2, height,
            leftPadding=margin/2, bottomPadding=margin,
            rightPadding=margin, topPadding=margin),
    ]

    templates = [PageTemplate(frames=frames, onPage=draw_header)]

    doc = BaseDocTemplate(response, pagesize=(width, height))
    doc.addPageTemplates(templates)

    data = [[_('Description'), _('Amount')]]
    total = 0

    for line in bill.billingline_set.all():
        data.append([line.description, '%.2f' % line.amount])
        total += line.amount

    data.append(['', '%.2f' % total])

    table = Table(data, colWidths=[doc.width*0.4, doc.width*0.15])
    table.setStyle(table_style)
    table.hAlign = 'LEFT'

    parts = []
    for line in bill.description.split('\n'):
        parts.append(Paragraph(escape(line), styles['Normal']))
    parts.append(Spacer(0.2*cm, 0.2*cm))
    parts.append(KeepTogether(table))

    doc.build(parts)

    return response
