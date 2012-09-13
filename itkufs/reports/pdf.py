from datetime import date
from cStringIO import StringIO

from reportlab.pdfgen import canvas
from reportlab.platypus.tables import Table, GRID_STYLE
from reportlab.platypus.flowables import Image
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4

from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify


BORDER_COLOR = HexColor('#555753')
BLACKLISTED_COLOR = HexColor('#000000')
BLACKLISTED_TEXT_COLOR = HexColor('#A40000')
WARN_TEXT_COLOR = HexColor('#F57900')
FAINT_COLOR = HexColor('#BABDB6')

ALTERNATE_COLORS = [HexColor('#FFFFFF'),
                    HexColor('#F5F5F5'),]

def pdf(group, list, show_header=True, show_footer=True):
    """PDF version of list"""

    content = StringIO()

    columns = list.column_set.all()
    accounts = list.accounts()

    margin = 0.5*cm

    font_name = 'Times-Roman'
    font_name_bold = 'Times-Bold'
    font_size = 12
    font_size_small = 10
    font_size_min = 8

    head_height = 30 # pt
    foot_height = 15 # pt
    logo_height = 25 # pt

    font_size_name = font_size_small
    font_size_short_name = font_size_small
    font_size_balance = font_size_small

    if list.orientation == list.LANDSCAPE:
        height, width = A4
    else:
        width, height = A4

    # Create canvas for page and set fonts
    p = canvas.Canvas(content, (width,height))

    show_logo = bool(group.logo and group.logo.storage.exists(group.logo.path))

    if show_logo:
        # Find scaling ratio
        ratio = group.logo.width / group.logo.height

        # Load logo with correct scaling
        logo = Image(group.logo.path, width=logo_height*ratio, height=logo_height)

    def draw_header():
        if not show_header:
            return

        if show_logo:
            logo.drawOn(p, width - margin - logo_height*ratio, height - margin - logo_height)

        # Setup rest of header
        p.setFont(font_name, font_size)
        p.drawString(margin, height - margin - font_size, u'%s: %s' % (group, list.name))
        p.setFont(font_name, font_size_small)
        p.drawString(margin, height - margin - font_size - font_size + 2, u'%s: %s' % (_('Printed'), str(date.today())))

    footer = []
    if group.email:
        footer.append(group.email)
    if group.account_number:
        footer.append(group.get_account_number_display())
    if list.comment.strip():
        footer.append(list.comment.replace('\n', ' ').replace('\r', ' '))

    def draw_footer():
        if not show_footer:
            return

        p.drawString(margin, margin, u' - '.join(footer))

        blacklisted_note = _(u'Blacklisted accounts are marked with: ')

        p.drawRightString(width - margin - 10, margin, blacklisted_note)
        p.setFillColor(BLACKLISTED_COLOR)
        p.rect(width - margin - 10, margin, 8, 8, fill=1, stroke=0)

        p.setFont(font_name, font_size)

    if not accounts:
        no_accounts_message = _(u"Sorry, this list is empty.")
        draw_header()
        p.drawString(margin, height - font_size - margin - head_height, no_accounts_message)
        draw_footer()
        p.save()

        return content

    elif not columns:
        no_columns_message = _(u"Sorry, this list isn't set up correctly, please add some columns.")
        draw_header()
        p.drawString(margin, height - font_size - margin - head_height, no_columns_message)
        draw_footer()
        p.save()

        return content

    # Store col widths
    col_width = []
    header = [_(u'Name')]

    if list.account_width:
        col_width.append(list.account_width)

    if list.short_name_width:
        col_width.append(list.short_name_width)

    if list.account_width and list.short_name_width:
        header.append('')

    if list.balance_width:
        header.append(_(u'Balance'))
        col_width.append(list.balance_width)

    if list.short_name_width > 0 and list.account_width > 0:
        GRID_STYLE.add('SPAN', (0,0), (1,0))

    base_x = len(header)

    for c in columns:
        header.append(c.name)
        col_width.append(c.width)

    # Calculate relative col widths over to absolute points
    for i,w in enumerate(col_width):
        col_width[i] = float(w) / float((list.listcolumn_width or 0) + list.balance_width + (list.account_width or 0) + (list.short_name_width or 0)) * (width-2*margin)

    # Intialise table with header
    data = [header]

    for i,a in enumerate(accounts):
        color = ALTERNATE_COLORS[(i+1)%len(ALTERNATE_COLORS)]

        if list.double:
            i *= 2
            extra_row_height = 1
        else:
            extra_row_height = 0

        i += 1

        GRID_STYLE.add('BACKGROUND', (0,i), (-1,i+extra_row_height), color)

        row = []

        if list.account_width:
            row.append(a.name)

            # Check if we need to reduce col font size
            while col_width[len(row)-1] < p.stringWidth(row[-1], font_name, font_size_name) + 12 and font_size_name > font_size_min:
                font_size_name -= 1

        if list.short_name_width:
            short_name = a.short_name

            if not short_name and a.owner:
                short_name = a.owner.username

            row.append(short_name or a.name)

            # Check if we need to reduce col font size
            while col_width[len(row)-1] < p.stringWidth(row[-1], font_name, font_size_name) + 12 and font_size_short_name > font_size_min:
                font_size_short_name -= 1

        if list.balance_width:
            row.append('%d' % a.normal_balance())

            # XXX: currently warnings are only shown if balance is shown, this
            # if needs to be moved if you want to change that
            if a.needs_warning():
                GRID_STYLE.add('FONTNAME', (0,i), (base_x-1,i), font_name_bold)
                GRID_STYLE.add('TEXTCOLOR', (base_x-1,i), (base_x-1,i), WARN_TEXT_COLOR)

            # Check if we need to reduce col font size
            while col_width[len(row)-1] < p.stringWidth(str(row[-1]), font_name, font_size_balance) + 12 and font_size_balance > font_size_min:
                font_size_balance -= 1

        if a.is_blocked():
            if list.balance_width:
                GRID_STYLE.add('TEXTCOLOR', (base_x-1,i), (base_x-1,i), BLACKLISTED_TEXT_COLOR)
                GRID_STYLE.add('FONTNAME', (0,i), (base_x-1,i), font_name_bold)
            GRID_STYLE.add('BACKGROUND', (base_x,i), (-1,i+extra_row_height), BLACKLISTED_COLOR)

            row.extend([''] * len(header[base_x:]))

        else:
            row.extend(header[base_x:])

        data.append(row)

        if list.double:
            data.append([''] * len(row))

            GRID_STYLE.add('SPAN', (0,i), (0,i+extra_row_height))

            if list.balance_width:
                GRID_STYLE.add('SPAN', (1,i), (1,i+extra_row_height))

    GRID_STYLE.add('FONTSIZE', (0,0), (-1,-1), font_size_small)

    # Set font size for names
    GRID_STYLE.add('FONTSIZE', (0,1), (0,-1), font_size_name)
    GRID_STYLE.add('ALIGN', (0,0), (-1,-1), 'LEFT')
    GRID_STYLE.add('ALIGN', (base_x,0), (-1,-1), 'RIGHT')

    GRID_STYLE.add('FONTNAME', (0,0), (-1,0), font_name_bold)

    # Set font size for balance
    if list.balance_width:
        GRID_STYLE.add('FONTSIZE', (base_x-1,1), (base_x-1,-1), font_size_balance)
        GRID_STYLE.add('ALIGN', (base_x-1,1), (base_x-1,-1), 'RIGHT')

    GRID_STYLE.add('TEXTCOLOR', (base_x,1), (-1,-1), FAINT_COLOR)

    if list.double:
        GRID_STYLE.add('TOPPADDING', (base_x,1), (-1,-1), 2)
        GRID_STYLE.add('BOTTOMPADDING', (base_x,1), (-1,-1), 2)

    GRID_STYLE.add('VALIGN', (0,1), (-1,-1), 'TOP')
    GRID_STYLE.add('GRID', (0,0), (-1, -1), 0.25, BORDER_COLOR)

    # Create table
    t = Table(data, colWidths=col_width, style=GRID_STYLE, repeatRows=1)

    rest = None
    avail_w = width-2*margin
    avail_h = height - 2*margin - head_height - foot_height

    while t:
        # Figure out how big table will be
        t_width, t_height = t.wrapOn(p, avail_w, avail_h)

        if not rest and t_height > height - 2*margin - head_height:
            t,rest = t.split(avail_w, avail_h)
            continue

        # Draw on canvas
        draw_header()
        try:
            t.drawOn(p, margin, height - t_height - margin - head_height)
        except IndexError:
            raise Exception(data) # Attempt to get enough data about infrequent bug
        draw_footer()

        if rest:
            # set t to the second table and reset rest
            t, rest= (rest, None)

            # Show new page
            p.showPage()
        else:
            # Leave loop
            break

    p.save()

    return content
