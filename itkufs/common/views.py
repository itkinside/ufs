from datetime import date, datetime
from urlparse import urlparse
import os

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.xheaders import populate_xheaders
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect
from django.newforms import form_for_instance, form_for_model
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _, ungettext
from django.views.generic.create_update import update_object
from django.views.generic.list_detail import object_list

from itkufs.common.decorators import *
from itkufs.accounting.models import Group, Account, Transaction

def login_user(request):
    """Login user"""

    if not request.user.is_authenticated():
        user = authenticate(request=request)
        if user is not None:
            login(request, user)
        else:
            return HttpResponseForbidden(_('Login failed'))

    return HttpResponseRedirect(reverse('group-list'))

@login_required
def group_list(request):
    """Lists the user's account groups and accounts, including admin accounts"""

    # Build account struct
    accounts = []
    for account in request.user.account_set.all().order_by('name'):
        is_admin = bool(account.group.admins.filter(
            username=request.user.username).count())
        accounts.append((account, is_admin))

    # If not coming from inside and user only got one account,
    # jump directly to account summary
    request_from_inside = ('HTTP_REFERER' in request.META and
        urlparse(request.META['HTTP_REFERER'])[2].startswith(reverse('group-list')))
    if len(accounts) == 1 and not request_from_inside:
        url = reverse('account-summary',
                      kwargs={'group': accounts[0][0].group.slug,
                              'account': accounts[0][0].slug})
        return HttpResponseRedirect(url)

    return render_to_response('accounting/group_list.html',
                              {
                                  'accounts': accounts,
                              },
                              context_instance=RequestContext(request))

@login_required
@is_group_admin
def group_summary(request, group, page='1', is_admin=False):
    """Account group summary and paginated list of accounts"""
    if not is_admin:
        return HttpResponseForbidden(_('This page may only be viewed by group admins in the current group.'))

    # Get account group
    try:
        group = Group.objects.get(slug=group)
    except Group.DoesNotExist:
        raise Http404

    # Get related transactions
    accounts = Account.objects.filter(group=group)
    transactions = group.transaction_set

    if is_admin and group.not_payed_transaction_set.count():
        request.user.message_set.create(
            message=_('You have pending transactions in the group: %s') \
                % group.name)

    # Pass on to generic view
    response = object_list(request, transactions,
                       paginate_by=20,
                       page=page,
                       allow_empty=True,
                       template_name='accounting/group_summary.html',
                       extra_context={
                            'is_admin': is_admin,
                            'group': group,
                       },
                       template_object_name='transaction')

    populate_xheaders(request, response, Group, group.id)
    return response

@login_required
@is_group_admin
def account_summary(request, group, account, page='1', is_admin=False):
    """Account details and a paginated list with recent transactions involving
    the user"""

    # Get account object
    try:
        group = Group.objects.get(slug=group)
        account = group.account_set.get(slug=account)
    except (Group.DoesNotExist, Account.DoesNotExist):
        raise Http404

    # Check that user is owner of account or admin of account group
    if not is_admin:
        if request.user.id != account.owner.id:
            return HttpResponseForbidden(_('Forbidden'))

        if not account.active:
            return HttpResponseForbidden(_('This account has been disabled.'))

    # Save account in session
    # I think it's a bit of hack to switch account when the referrer is the
    # group-list view, but that view is in fact only used for selecting between
    # your own accounts.
    request_from_group_list = ('HTTP_REFERER' in request.META and
        urlparse(request.META['HTTP_REFERER'])[2] == reverse('group-list'))

    if request.user == account.owner:
        request.session['my_account'] = account


    # Get related transactions
    # FIXME
    # transactions = account.transaction_set
    transactions = Transaction.objects.filter(entry_set__account=account)

    # Warn owner of account about a low balance
    if request.user == account.owner:
        if account.is_blocked():
            request.user.message_set.create(
                message=_('The account balance is below the block limit,'
                + ' please contact the group admin or deposit enough to'
                + ' pass the limit.'))
        elif account.needs_warning():
            request.user.message_set.create(
                message=_('The account balance is below the warning limit.'))

    # Pass on to generic view
    response = object_list(request, transactions,
                       paginate_by=20,
                       page=page,
                       allow_empty=True,
                       template_name='accounting/account_summary.html',
                       extra_context={
                            'is_admin': is_admin,
                            'account': account,
                            'group': group,
                       },
                       template_object_name='transaction')
    populate_xheaders(request, response, Account, account.id)
    return response

@login_required
@is_group_admin
def static_page(request, group, template, is_admin=False):
    try:
        group = Group.objects.get(slug=group)
    except Group.DoesNotExist:
        raise Http404

    return render_to_response(template,
                              {
                                  'group': group,
                                  'is_admin': is_admin,
                              },
                              context_instance=RequestContext(request))

@login_required
@is_group_admin
def edit_group(request, group, is_admin=False):
    if not is_admin:
        return HttpResponseForbidden(_('This page may only be viewed by group admins in the current group.'))

    try:
        group = Group.objects.get(slug=group)
    except Group.DoesNotExist:
        raise Http404

    GroupInstanceForm = form_for_instance(group)
    del GroupInstanceForm.base_fields['slug']
    del GroupInstanceForm.base_fields['placeholder']

    old_logo = group.get_logo_filename()

    if request.method == 'POST':
        form = GroupInstanceForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            if old_logo and old_logo != group.get_logo_filename():
                os.remove(old_logo)

            elif 'delete_logo' in request.POST:
                os.remove(group.get_logo_filename())
                group.logo = ''
                group.save()
            request.user.message_set.create(message=_('Group successfully updated'))
            return HttpResponseRedirect(reverse('group-summary', args=(group.slug,)))
    else:
        form = GroupInstanceForm()


    return render_to_response('accounting/group_form.html',
                              {
                                'is_admin': is_admin,
                                'group': group,
                                'form': form,
                              },
                              context_instance=RequestContext(request))

@login_required
@is_group_admin
def edit_account(request, group, account=None, type='new', is_admin=False):
    if not is_admin:
        return HttpResponseForbidden(_('This page may only be viewed by group admins in the current group.'))

    try:
        group = Group.objects.get(slug=group)
        if type == 'edit':
            account = group.account_set.get(slug=account)

    except (Group.DoesNotExist, Account.DoesNotExist):
        raise Http404


    if type=='edit':
        AccountForm = form_for_instance(account)
    else:
        AccountForm = form_for_model(Account)

    del AccountForm.base_fields['group']

    if request.method == 'POST':
        form = AccountForm(request.POST)

        if form.is_valid():
            if type== 'edit':
                form.save()
                request.user.message_set.create(message=_('Account successfully updated'))
            else:
                account = form.save(commit=False)
                account.group = group
                account.save()
                request.user.message_set.create(message=_('Account successfully created'))
            return HttpResponseRedirect(reverse('account-summary', args=(group.slug,account.slug)))
    else:
        form = AccountForm()


    return render_to_response('accounting/account_form.html',
                              {
                                'is_admin': is_admin,
                                'group': group,
                                'form': form,
                              },
                              context_instance=RequestContext(request))
