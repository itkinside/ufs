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

from itkufs.accounting.decorators import *
from itkufs.accounting.models import *
from itkufs.reports.models import *
from itkufs.reports.forms import *

@login_required
@limit_to_group
def html_list(request, group, slug):
    try:
        group = Group.objects.get(slug=group)
        accounts = Account.objects.filter(group=group)
        list = group.list_set.get(slug=slug)
    except (Group.DoesNotExist, List.DoesNotExist):
        raise Http404

    response = render_to_response('reports/list.html',
                              {
                                  'accounts': accounts,
                                  'group': group,
                                  'list': list,
                              },
                              context_instance=RequestContext(request))

    populate_xheaders(request, response, List, list.id)
    return response

@login_required
@is_group_admin
def edit_list(request, group, slug=None, type='new', is_admin=False):
    if not is_admin:
        return HttpResponseForbidden(_('This page may only be viewed by group admins in the current group.'))

    try:
        group = Group.objects.get(slug=group)
        if slug:
            id = group.list_set.get(slug=slug).id
    except Group.DoesNotExist:
        raise Http404

    ListForm = form_for_model(List, fields=('name', 'slug', 'account_width', 'balance_width'))
    ColumnForm = form_for_model(ListColumn, form=ColumnBaseForm, fields=('name', 'width', 'order'))
    columnforms = []

    listform = ListForm()

    for i in range(0, 6):
        columnforms.append( ColumnForm(prefix='new%s'%i) )

    return render_to_response('reports/edit_list.html',
                              {
                                  'is_admin': is_admin,
                                  'listform': listform,
                                  'columnforms': columnforms,

                              },
                              context_instance=RequestContext(request))


@login_required
@is_group_admin
def alter_list(request, group, slug=None, type='new', is_admin=False):
    if not is_admin:
        return HttpResponseForbidden(_('This page may only be viewed by group admins in the current group.'))

    # May this function could be made more genric so that it can limit acces
    # to generic views for any object?
    try:
        group = Group.objects.get(slug=group)
        if slug:
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
@is_group_admin
def balance(request, group, is_admin=False):
    """Show balance sheet for the group"""
    if not is_admin:
        return HttpResponseForbidden(_('This page may only be viewed by group admins in the current group.'))

    try:
        group = Group.objects.get(slug=group)
    except Group.DoesNotExist:
        raise Http404

    # Balance sheet data struct
    accounts = {
        'As': [], 'AsSum': 0,
        'Li': [], 'LiSum': 0,
        'Eq': [], 'EqSum': 0,
        'LiEqSum': 0,
    }

    # Assets
    for account in group.account_set.filter(type='As'):
        balance = account.balance_credit_reversed()
        accounts['As'].append((account.name, balance))
        accounts['AsSum'] += balance

    # Liabilities
    for account in group.account_set.filter(type='Li', owner__isnull=True):
        balance = account.balance_credit_reversed()
        accounts['Li'].append((account.name, balance))
        accounts['LiSum'] += balance

    # Accumulated member accounts liabilities
    member_balance_sum = sum([a.balance_credit_reversed()
        for a in group.account_set.filter(type='Li', owner__isnull=False)])
    accounts['Li'].append((_('Member accounts'), member_balance_sum))
    accounts['LiSum'] += member_balance_sum

    # Equities
    for account in group.account_set.filter(type='Eq'):
        balance = account.balance_credit_reversed()
        accounts['Eq'].append((account.name, balance))
        accounts['EqSum'] += balance

    # Total liabilities and equities
    accounts['LiEqSum'] = accounts['LiSum'] + accounts['EqSum']

    # Current year's net income
    curr_years_net_income = accounts['AsSum'] - accounts['LiEqSum']
    accounts['Eq'].append((_("Current year's net income"),
                           curr_years_net_income))
    accounts['EqSum'] += curr_years_net_income
    accounts['LiEqSum'] += curr_years_net_income

    return render_to_response('accounting/balance.html',
                              {
                                  'is_admin': is_admin,
                                  'group': group,
                                  'today': date.today(),
                                  'accounts': accounts,
                              },
                              context_instance=RequestContext(request))

@login_required
@is_group_admin
def income(request, group, is_admin=False):
    """Show income statement for group"""
    if not is_admin:
        return HttpResponseForbidden(_('This page may only be viewed by group admins in the current group.'))

    try:
        group = Group.objects.get(slug=group)
    except Group.DoesNotExist:
        raise Http404

    # Balance sheet data struct
    accounts = {
        'In': [], 'InSum': 0,
        'Ex': [], 'ExSum': 0,
        'InExDiff': 0,
    }

    # Incomes
    for account in group.account_set.filter(type='In'):
        balance = account.balance_credit_reversed()
        accounts['In'].append((account.name, balance))
        accounts['InSum'] += balance

    # Expenses
    for account in group.account_set.filter(type='Ex'):
        balance = account.balance_credit_reversed()
        accounts['Ex'].append((account.name, balance))
        accounts['ExSum'] += balance

    # Net income
    accounts['InExDiff'] = accounts['InSum'] - accounts['ExSum']

    return render_to_response('accounting/income.html',
                              {
                                  'is_admin': is_admin,
                                  'group': group,
                                  'today': date.today(),
                                  'accounts': accounts,
                              },
                              context_instance=RequestContext(request))

@login_required
@is_group_admin
def settlement_summary(request, group, page="1", is_admin=False):
    if not is_admin:
        return HttpResponseForbidden(_('This page may only be viewed by group admins in the current group.'))
    try:
        group = Group.objects.get(slug=group)
    except Group.DoesNotExist:
        raise Http404


    # FIXME: Finish view

