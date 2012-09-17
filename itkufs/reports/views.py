from datetime import date
from subprocess import Popen, PIPE

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.xheaders import populate_xheaders
from django.forms.models import inlineformset_factory
from django.http import Http404, HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.views.generic.list_detail import object_list
from django.conf import settings
from django.db import transaction as db_transaction

from itkufs.common.decorators import limit_to_group, limit_to_admin
from itkufs.accounting.models import Account
from itkufs.reports.models import *
from itkufs.reports.forms import *
from itkufs.reports.pdf import pdf

_list = list

def public_lists(request):
    lists = List.objects.filter(public=True).select_related('group') \
        .order_by('group__name', 'name')

    return object_list(request,
        lists,
        allow_empty=True,
        template_name='reports/public_lists.html',
        template_object_name='public')

@login_required
@limit_to_group
def view_list(request, group, list, is_admin=False):
    content = pdf(group, list)

    filename = '%s-%s-%s' % (date.today(), group, list)

    response = HttpResponse(content.getvalue(), mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s.pdf' % slugify(filename)

    return response

@login_required
@limit_to_group
def view_list_preview(request, group, list, is_admin=False):
    content = pdf(group, list, show_header=True, show_footer=True)

    p = Popen(["gs", "-q", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-r40",
        "-dGraphicsAlphaBits=4", "-dTextAlphaBits=4", "-sDEVICE=png16m",
        "-sOutputFile=-", "-"], stdin=PIPE, stdout=PIPE, stderr=PIPE)

    stdout, stderr = p.communicate(content.getvalue())

    if p.returncode != 0:
        raise Exception(stdout)

    return HttpResponse(stdout, mimetype='image/png')

def view_public_list(request, group, list, is_admin=False):
    if not list.public:
        raise Http404

    content = pdf(group, list)

    filename = '%s-%s-%s' % (date.today(), group, list)

    response = HttpResponse(content.getvalue(), mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s.pdf' % slugify(filename)

    return response

@login_required
@limit_to_admin
@db_transaction.commit_on_success
def new_edit_list(request, group, list=None, is_admin=False):
    """Create new or edit existing list"""

    if request.method == 'POST':
        data = request.POST
    else:
        data = None

    if not list:
        ColumnFormSet = inlineformset_factory(List, ListColumn, extra=10, form=ColumnForm)

        listform = ListForm(data=data, group=group)
        columnformset = ColumnFormSet(data)

    else:
        ColumnFormSet = inlineformset_factory(List, ListColumn, extra=3, form=ColumnForm)
        if list is None:
            raise Http404

        listform = ListForm(data, instance=list, group=group)
        columnformset = ColumnFormSet(data, instance=list)

    if data and listform.is_valid():
        list = listform.save(group=group)
        columnformset = ColumnFormSet(data, instance=list)

        if columnformset.is_valid():
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
@db_transaction.commit_on_success
def delete_list(request, group, list, is_admin=False):
    """Delete list"""

    if request.method == 'POST':
        # FIXME maybe a bit naive here?
        list.delete()
        messages.info(request, _('List deleted.'))

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
@limit_to_admin
@db_transaction.commit_on_success
def transaction_from_list(request, group, list, is_admin=False):
    """Enter list"""

    form = ListTransactionForm(list, request.POST or None)

    if form.is_valid():
        transaction = Transaction(group=list.group)
        transaction.save()

        for entry in form.transaction_entries():
            entry.transaction = transaction
            entry.save()

        transaction.save()
        transaction.set_pending(user=request.user, message=_('Created from list: %s') % list.slug)

        return HttpResponseRedirect(reverse('edit-transaction',
            kwargs={
                'group': group.slug,
                'transaction': transaction.id,
            }))

    return render_to_response('reports/list_transaction_form.html',
        {
            'is_admin': is_admin,
            'group': group,
            'list': list,
            'form': form,
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
        accounts['as_sum'] += account.normal_balance()

    # Liabilities
    for account in group.account_set.filter(type=Account.LIABILITY_ACCOUNT,
                                            group_account=True):
        accounts['li'].append(account)
        accounts['li_sum'] += account.normal_balance()

    # Accumulated member accounts liabilities
    member_balance_sum = 0
    for account in group.account_set.filter(type=Account.LIABILITY_ACCOUNT,
                                            group_account=False):
        member_balance_sum += account.normal_balance()
    accounts['li'].append((_('Member accounts'), member_balance_sum))
    accounts['li_sum'] += member_balance_sum

    # Equities
    for account in group.account_set.filter(type=Account.EQUITY_ACCOUNT):
        accounts['eq'].append(account)
        accounts['eq_sum'] += account.normal_balance()

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
        accounts['in_sum'] += account.normal_balance()

    # Expenses
    for account in group.account_set.filter(type=Account.EXPENSE_ACCOUNT):
        accounts['ex'].append(account)
        accounts['ex_sum'] += account.normal_balance()

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

