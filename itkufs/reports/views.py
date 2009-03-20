from datetime import date
from reportlab.pdfgen import canvas
from reportlab.platypus.tables import Table, GRID_STYLE
from reportlab.platypus.flowables import Image
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.xheaders import populate_xheaders
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify
from django.forms.models import inlineformset_factory

from itkufs.common.utils import callsign_sorted as ufs_sorted
from itkufs.common.decorators import limit_to_group, limit_to_admin
from itkufs.accounting.models import Account
from itkufs.reports.models import *
from itkufs.reports.forms import *

_list = list

@login_required
@limit_to_group
def pdf(request, group, list, is_admin=False):
    """PDF version of list"""

    all_accounts = group.account_set.filter(active=True)
    extra_accounts = list.extra_accounts.values_list('id', flat=True)

    if list.account_width:
        all_accounts = all_accounts.order_by('name', 'owner__username')
    else:
        all_accounts = all_accounts.order_by('short_name', 'owner__username')

    columns = list.column_set.all()

    accounts = []
    # Get accounts to show
    for a in all_accounts:
        if list.add_active_accounts and a.is_user_account():
            accounts.append(a)
        elif a.id in extra_accounts:
            accounts.append(a)

    accounts = ufs_sorted(accounts)

    # Create response
    filename = '%s-%s-%s' % (date.today(), group, list)

    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s.pdf' % slugify(filename)

    margin = 0.5*cm

    font_name = 'Times-Roman'
    font_name_bold = 'Times-Bold'
    font_size = 14
    font_size_name = font_size - 2
    font_size_short_name = font_size - 2
    font_size_balance = font_size_name - 2
    font_size_min = 5

    head_height = 30 # pt
    foot_height = 15 # pt
    logo_height = 25 # pt

    blacklisted_color = HexColor('#000000')
    blacklisted_text_color = HexColor('#A40000')
    warn_text_color = HexColor('#F57900')
    even_color = HexColor('#FFFFFF')
    odd_color = HexColor('#FAFAFA')
    faint_color = HexColor('#BABDB6')

    alternate_colors = [even_color, odd_color]

    if list.orientation == list.LANDSCAPE:
        height, width = A4
    else:
        width, height = A4

    # Create canvas for page and set fonts
    p = canvas.Canvas(response, (width,height))

    show_logo = bool(group.logo and group.logo.storage.exists(group.logo.path))

    if show_logo:
        # Find scaling ratio
        ratio = group.logo.width / group.logo.height

        # Load logo with correct scaling
        logo = Image(group.logo.path, width=logo_height*ratio, height=logo_height)

    def draw_header():
        if show_logo:
            logo.drawOn(p, width - margin - logo_height*ratio, height - margin - logo_height)

        # Setup rest of header
        p.setFont(font_name, font_size)
        p.drawString(margin, height - margin - font_size, u'%s: %s' % (group, list.name))
        p.setFont(font_name, font_size - 4)
        p.drawString(margin, height - margin - font_size - font_size + 2, u'%s: %s' % (_('Printed'), str(date.today())))

    footer = []
    if group.email:
        footer.append(group.email)
    if list.comment.strip():
        footer.append(list.comment.replace('\n', ' ').replace('\r', ' '))

    def draw_footer():
        p.drawString(margin, margin, u' - '.join(footer))

        blacklisted_note = _(u'Blacklisted accounts are marked with: ')

        p.drawRightString(width - margin - 10, margin, blacklisted_note)
        p.rect(width - margin - 10, margin, 8, 8, fill=1, stroke=0)

        p.setFont(font_name, font_size)

    if not accounts:
        no_accounts_message = _(u"Sorry, this list is empty.")
        draw_header()
        p.drawString(margin, height - font_size - margin - head_height, no_accounts_message)
        draw_footer()
        p.save()

        return response

    elif not columns:
        no_columns_message = _(u"Sorry, this list isn't set up correctly, please add some columns.")
        draw_header()
        p.drawString(margin, height - font_size - margin - head_height, no_columns_message)
        draw_footer()
        p.save()

        return response

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
        color = alternate_colors[(i+1)%2]

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
            row.append('%d' % a.user_balance())

            # XXX: currently warnings are only shown if balance is shown, this
            # if needs to be moved if you want to change that
            if a.needs_warning():
                GRID_STYLE.add('FONTNAME', (0,i), (base_x-1,i), font_name_bold)
                GRID_STYLE.add('TEXTCOLOR', (base_x-1,i), (base_x-1,i), warn_text_color)

            # Check if we need to reduce col font size
            while col_width[len(row)-1] < p.stringWidth(str(row[-1]), font_name, font_size_balance) + 12 and font_size_balance > font_size_min:
                font_size_balance -= 1

        if a.is_blocked():
            if list.balance_width:
                GRID_STYLE.add('TEXTCOLOR', (base_x-1,i), (base_x-1,i), blacklisted_text_color)
                GRID_STYLE.add('FONTNAME', (0,i), (base_x-1,i), font_name_bold)
            GRID_STYLE.add('BACKGROUND', (base_x,i), (-1,i+extra_row_height), blacklisted_color)

            row.extend([''] * len(header[base_x:]))

        else:
            row.extend(header[base_x:])

        data.append(row)

        if list.double:
            data.append([''] * len(row))

            GRID_STYLE.add('SPAN', (0,i), (0,i+extra_row_height))

            if list.balance_width:
                GRID_STYLE.add('SPAN', (1,i), (1,i+extra_row_height))

    # Set font size for names
    GRID_STYLE.add('FONTSIZE', (0,1), (0,-1), font_size_name)
    GRID_STYLE.add('ALIGN', (0,0), (-1,-1), 'LEFT')

    GRID_STYLE.add('FONTNAME', (0,0), (-1,0), font_name_bold)

    # Set font size for balance
    if list.balance_width:
        GRID_STYLE.add('FONTSIZE', (base_x-1,1), (base_x-1,-1), font_size_balance)
        GRID_STYLE.add('ALIGN', (base_x-1,1), (base_x-1,-1), 'RIGHT')

    GRID_STYLE.add('TEXTCOLOR', (base_x,1), (-1,-1), faint_color)

    if list.double:
        GRID_STYLE.add('TOPPADDING', (base_x,1), (-1,-1), 2)
        GRID_STYLE.add('BOTTOMPADDING', (base_x,1), (-1,-1), 2)

    GRID_STYLE.add('VALIGN', (0,1), (-1,-1), 'TOP')

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
        t.drawOn(p, margin, height - t_height - margin - head_height)
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

    return response

@login_required
@limit_to_admin
def new_edit_list(request, group, list=None, is_admin=False):
    """Create new or edit existing list"""

    if request.method == 'POST':
        data = request.POST
    else:
        data = None

    if not list:
        ColumnFormSet = inlineformset_factory(List, ListColumn, extra=10, form=ColumnForm)

        columnformset = ColumnFormSet(data)
        listform = ListForm(data=data, group=group)

    else:
        ColumnFormSet = inlineformset_factory(List, ListColumn, extra=3, form=ColumnForm)
        if list is None:
            raise Http404

        listform = ListForm(data, instance=list, group=group)
        columnformset = ColumnFormSet(data, instance=list)

    if data and listform.is_valid() and columnformset.is_valid():
        list = listform.save(group=group)

        columnformset.instance = list
        columns = columnformset.save(commit=False)

        for c in columns:
            if not c.name and not c.width:
                if c.id:
                    c.delete()
            else:
                c.save()

        return HttpResponseRedirect(reverse('group-summary',
            kwargs={
                'group': group.slug,
            }))

    return render_to_response('reports/list_form.html',
        {
            'is_admin': is_admin,
            'group': group,
            'list': list,
            'listform': listform,
            'columnformset': columnformset,
        },
        context_instance=RequestContext(request))

@login_required
@limit_to_admin
def delete_list(request, group, list, is_admin=False):
    """Delete list"""

    if request.method == 'POST':
        # FIXME maybe a bit naive here?
        list.delete()
        request.user.message_set.create(message=_('List deleted'))
        return HttpResponseRedirect(reverse('group-summary',
            kwargs={
                'group': group.slug,
            }))

    return render_to_response('reports/list_delete.html',
        {
            'is_admin': is_admin,
            'group': group,
            'list': list,
        },
        context_instance=RequestContext(request))


@login_required
@limit_to_group
def balance(request, group, is_admin=False):
    """Show balance sheet for the group"""

    # Balance sheet data struct
    accounts = {
        'as': [], 'as_sum': 0,
        'li': [], 'li_sum': 0,
        'eq': [], 'eq_sum': 0,
        'li_eq_sum': 0,
    }

    # Assets
    for account in group.account_set.filter(type=Account.ASSET_ACCOUNT):
        accounts['as'].append(account)
        accounts['as_sum'] += account.user_balance()

    # Liabilities
    for account in group.account_set.filter(type=Account.LIABILITY_ACCOUNT,
                                            group_account=True):
        balance = account.user_balance()
        accounts['li'].append((account.name, balance))
        accounts['li_sum'] += balance

    # Accumulated member accounts liabilities
    member_balance_sum = 0
    for account in group.account_set.filter(type=Account.LIABILITY_ACCOUNT,
                                            group_account=False):
        member_balance_sum += account.user_balance()
    accounts['li'].append((_('Member accounts'), member_balance_sum))
    accounts['li_sum'] += member_balance_sum

    # Equities
    for account in group.account_set.filter(type=Account.EQUITY_ACCOUNT):
        balance = account.user_balance()
        accounts['eq'].append((account.name, balance))
        accounts['eq_sum'] += balance

    # Total liabilities and equities
    accounts['li_eq_sum'] = accounts['li_sum'] + accounts['eq_sum']

    # Current year's net income
    curr_year_net_income = accounts['as_sum'] - accounts['li_eq_sum']
    accounts['eq'].append((_("Current year's net income"),
                           curr_year_net_income))
    accounts['eq_sum'] += curr_year_net_income
    accounts['li_eq_sum'] += curr_year_net_income

    return render_to_response('reports/balance.html',
        {
            'is_admin': is_admin,
            'group': group,
            'today': date.today(),
            'accounts': accounts,
        },
        context_instance=RequestContext(request))

@login_required
@limit_to_group
def income(request, group, is_admin=False):
    """Show income statement for group"""

    # Balance sheet data struct
    accounts = {
        'in': [], 'in_sum': 0,
        'ex': [], 'ex_sum': 0,
        'in_ex_diff': 0,
    }

    # Incomes
    for account in group.account_set.filter(type=Account.INCOME_ACCOUNT):
        accounts['in'].append(account)
        accounts['in_sum'] += account.balance()

    # Expenses
    for account in group.account_set.filter(type=Account.EXPENSE_ACCOUNT):
        accounts['ex'].append(account)
        accounts['ex_sum'] += account.balance()

    # Net income
    accounts['in_ex_diff'] = accounts['in_sum'] + accounts['ex_sum']

    return render_to_response('reports/income.html',
        {
            'is_admin': is_admin,
            'group': group,
            'today': date.today(),
            'accounts': accounts,
        },
        context_instance=RequestContext(request))

