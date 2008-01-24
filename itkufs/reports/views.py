from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.xheaders import populate_xheaders
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _, ungettext
from django.views.generic.create_update import create_object, update_object, delete_object
from django.newforms import form_for_instance, form_for_model

from itkufs.common.forms import BaseForm
from itkufs.common.decorators import limit_to_group, limit_to_owner, limit_to_admin
from itkufs.accounting.models import Group, Account
from itkufs.reports.models import *

@login_required
@limit_to_group
def show_list(request, group, list, is_admin=False):
    """Show list for printing"""

    if list.accounts.all().count():
        accounts = list.accounts.filter(group=group).select_related(depth=1)
    else:
        accounts = group.user_account_set.select_related(depth=1)

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
def new_list(request, group, is_admin=False):
    """Create new list"""

    columnforms = []

    ListForm = form_for_model(List, fields=('name', 'slug', 'account_width', 'balance_width'))
    ColumnForm = form_for_model(ListColumn, form=ColumnBaseForm, fields=('name', 'width'))

    listform = ListForm()
    for i in range(0,5):
        columnforms.append( ColumnForm(prefix='new%s'%i) )

    return render_to_response('reports/edit_list.html',
                              {
                                  'is_admin': is_admin,
                                  'listform': listform,
                                  'columnforms': columnforms,

                              },
                              context_instance=RequestContext(request))

@login_required
@limit_to_admin
def edit_list(request, group, slug, is_admin=False):
    """Edit list"""

    try:
        list = group.list_set.get(slug=slug)
    except List.DoesNotExist:
        raise Http404

    ListForm = form_for_instance(list, fields=('name', 'slug', 'account_width', 'balance_width'))
    listform = ListForm()

    columnforms = []
    for c in list.column_set.all():
        ColumnForm = form_for_instance(c, form=ColumnBaseForm, fields=('name', 'width'))
        columnforms.append( ColumnForm(prefix=c.id) )
    for i in range(0,3):
        ColumnForm = form_for_model(ListColumn, form=ColumnBaseForm, fields=('name', 'width'))
        columnforms.append( ColumnForm(prefix='new%s'%i) )

    return render_to_response('reports/edit_list.html',
                              {
                                  'is_admin': is_admin,
                                  'listform': listform,
                                  'columnforms': columnforms,

                              },
                              context_instance=RequestContext(request))


@login_required
@limit_to_admin
def alter_list(request, group, slug=None, type='new', is_admin=False):
    """FIXME"""
    # FIXME: Rename to edit_list
    # FIXME: Err, we already got a view named edit_list? adamcik?

    # TODO: Maybe this function could be made more generic so that it can limit
    # access to generic views for any object?
    if slug is not None:
        try:
            id = group.list_set.get(slug=slug).id
        except Group.DoesNotExist:
            raise Http404

    if request.method == 'POST':
        if u'group' in request.POST:
            if group.id != int(request.POST['group']):
                return HttpResponseForbidden(_('This page may only be viewed by group admins in the current group.'))
        else:
            raise Exception()

    context={
        'is_admin': is_admin,
        'group': group,
    }

    redirect = reverse('group-summary',args=(group.slug,))

    if type == 'new':
        return create_object(request, model=List, extra_context=context,
            post_save_redirect=redirect)

    elif type == 'edit':
        return update_object(request, model=List, extra_context=context, object_id=id,
            post_save_redirect=redirect)

    elif type == 'delete':
        if request.method == 'POST' and request.POST['submit'] != 'yes':
            return HttpResponseRedirect(redirect)

        return delete_object(request, model=List, extra_context=context, object_id=id,
            post_delete_redirect=redirect)

@login_required
@limit_to_admin
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
@limit_to_admin
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

@login_required
@limit_to_admin
def settlement_summary(request, group, page='1', is_admin=False):
    """Show settlement summary"""

    pass # FIXME
