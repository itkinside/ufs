from datetime import date
from reportlab.pdfgen import canvas
from reportlab.platypus.tables import Table, GRID_STYLE
from reportlab.platypus.flowables import Image
from reportlab.lib.units import cm
from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import A4

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.xheaders import populate_xheaders
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify

from itkufs.common.decorators import limit_to_group, limit_to_admin
from itkufs.accounting.models import Account
from itkufs.reports.models import *
from itkufs.reports.forms import *

@login_required
@limit_to_group
def pdf(request, group, list, is_admin=False):
    """PDF version of list"""

    # Get accounts to show
    if list.accounts.all().count():
        accounts = list.accounts.all()
    else:
        accounts = group.user_account_set.filter(active=True)

    # Create response
    filename = '%s-%s-%s' % (date.today(), group, list)

    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s.pdf' % slugify(filename)

    margin = 0.5*cm

    font_name = 'Times-Roman'
    font_size = 14
    font_size_name = font_size - 2
    font_size_balance = font_size_name - 2
    font_size_min = 5

    head_height = 30 # pt
    logo_height = 25 # pt

    if list.orientation == list.LANDSCAPE:
        height, width = A4
    else:
        width, height = A4

    # Create canvas for page and set fonts
    p = canvas.Canvas(response, (width,height))

    if group.logo:
        # Find scaling ratio
        ratio = group.get_logo_width() / group.get_logo_height()

        # Load logo with correct scaling
        logo = Image(group.get_logo_filename(), width=logo_height*ratio, height=logo_height)

        # Draw on first page
        logo.drawOn(p, width - margin - logo_height*ratio, height - margin - logo_height)

    # Setup rest of header
    p.setFont(font_name, font_size)
    p.drawString(margin, height - margin - font_size, '%s: %s' % (group, list.name))
    p.setFont(font_name, font_size - 4)
    p.drawString(margin, height - margin - font_size - font_size + 2, str(date.today()))
    p.setFont(font_name, font_size)

    # Store col widths
    col_width = [list.account_width]
    header = [_('Name')]

    if list.balance_width:
        header.append(_('Balance'))
        col_width.append(list.balance_width)

    for c in list.column_set.all():
        header.append(c.name)
        col_width.append(c.width)

    # Calculate relative col widths over to absolute points
    for i,w in enumerate(col_width):
        col_width[i] = float(w) / float(list.listcolumn_width + list.balance_width + list.account_width) * (width-2*margin)

    # Intialise table with header
    data = [header]

    # Add alternating backgrounds to style
    GRID_STYLE.add('ROWBACKGROUNDS', (0,0), (-1,-1), [Color(1,1,1), Color(0.99,0.99,0.99)])

    for i,a in enumerate(accounts):

        if a.is_blocked():
            if list.balance_width:
                GRID_STYLE.add('BACKGROUND', (2,i+1), (-1,i+1), Color(0,0,0))
                GRID_STYLE.add('TEXTCOLOR', (1,i+1), (1,i+1), Color(0.63,0,0))
            else:
                GRID_STYLE.add('BACKGROUND', (1,i+1), (-1,i+1), Color(0,0,0))

        row = [a.name]

        # Check if we need to reduce col font size
        while col_width[0] < p.stringWidth(row[-1], font_name, font_size_name) and font_size_name > font_size_min:
            font_size_name -= 1

        if list.balance_width:
            row.append(a.user_balance())

            # Check if we need to reduce col font size
            while col_width[1] < p.stringWidth(str(row[-1]), font_name, font_size_balance) and font_size_balance > font_size_min:
                font_size_balance -= 1

        row.extend([''] * list.listcolumn_count)

        data.append(row)

    # Set font size for names
    GRID_STYLE.add('FONTSIZE', (0,1), (0,i+1), font_size_name)

    # Set font size for balance
    if list.balance_width:
        GRID_STYLE.add('FONTSIZE', (1,1), (1,i+1), font_size_balance)

    # Create table
    t = Table(data, colWidths=col_width, style=GRID_STYLE, repeatRows=1)

    rest = None
    while t:
        # Figure out how big table will be
        t_width, t_height = t.wrapOn(p, width-2*margin,height-margin-head_height)

        if not rest and t_height > height - 2*margin - head_height:
            t,rest = t.split(width-2*margin, height - margin - head_height)
            continue

        # Draw on canvas
        t.drawOn(p, margin, height - t_height - margin - head_height)

        if rest:
            # set t to the second table and reset rest
            t, rest= (rest, None)

            # Show new page
            p.showPage()

            # Remove header spacing
            head_height = 0
        else:
            # Leave loop
            break

    p.save()

    return response

@login_required
@limit_to_group
def view_list(request, group, list, is_admin=False):
    """Show list for printing"""

    if list.accounts.all().count():
        accounts = list.accounts.all()
    else:
        accounts = group.user_account_set.filter(active=True)

    response = render_to_response('reports/list.html',
        {
            'accounts': accounts,
            'group': group,
            'list': list,
            'is_admin': is_admin,
        },
    context_instance=RequestContext(request))
    populate_xheaders(request, response, List, list.id)
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
        columnforms = []
        listform = ListForm(data=data, group=group)
        for i in range(0,10): # Lock number of coloumns for new list
            columnforms.append( ColumnForm(data=data, prefix='new%s'%i))

    else:
        if list is None:
            raise Http404

        listform = ListForm(data, instance=list, group=group)

        columnforms = []
        for c in list.column_set.all():
            columnforms.append( ColumnForm(data, instance=c, prefix=c.id) )

        for i in range(0,3):
            columnforms.append( ColumnForm(data, prefix='new%s'%i) )

    if data and listform.is_valid():
        forms_ok = True
        for column in columnforms:
            if not column.is_valid():
                forms_ok = False
                break
        if forms_ok:
            list = listform.save(group=group)

            for column in columnforms:
                if column.cleaned_data['name'] and column.cleaned_data['width']:
                    column.save(list=list)
                elif column.instance.id:
                    column.instance.delete()

            # Not completely sure why the modelform save doesn't
            # fix this for us, so here goes:
            list.accounts = listform.cleaned_data['accounts']

            return HttpResponseRedirect(reverse('view-list',
                kwargs={
                    'group': group.slug,
                    'list': list.slug,
                }))

    return render_to_response('reports/list_form.html',
        {
            'is_admin': is_admin,
            'group': group,
            'type': type,
            'listform': listform,
            'columnforms': columnforms,
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
        balance = account.user_balance()
        accounts['as'].append((account.name, balance))
        accounts['as_sum'] += balance

    # Liabilities
    for account in group.account_set.filter(type=Account.LIABILITY_ACCOUNT,
                                            owner__isnull=True):
        balance = account.user_balance()
        accounts['li'].append((account.name, balance))
        accounts['li_sum'] += balance

    # Accumulated member accounts liabilities
    member_balance_sum = 0
    for account in group.account_set.filter(type=Account.LIABILITY_ACCOUNT,
                                            owner__isnull=False):
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
        balance = account.user_balance()
        accounts['in'].append((account.name, balance))
        accounts['in_sum'] += balance

    # Expenses
    for account in group.account_set.filter(type=Account.EXPENSE_ACCOUNT):
        balance = account.user_balance()
        accounts['ex'].append((account.name, balance))
        accounts['ex_sum'] += balance

    # Net income
    accounts['in_ex_diff'] = accounts['in_sum'] - accounts['ex_sum']

    return render_to_response('reports/income.html',
        {
            'is_admin': is_admin,
            'group': group,
            'today': date.today(),
            'accounts': accounts,
        },
        context_instance=RequestContext(request))

