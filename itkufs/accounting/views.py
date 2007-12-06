from datetime import date, datetime
import os
from urlparse import urlparse

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

from itkufs.common.decorators import is_group_admin, limit_to_group
from itkufs.common.forms import BaseForm
from itkufs.accounting.models import *
from itkufs.accounting.forms import *

@login_required
@is_group_admin
def group_summary(request, group, page='1', is_admin=False):
    """Account group summary and paginated list of accounts"""

    # Admins only
    if not is_admin:
        return HttpResponseForbidden(
            _('This page may only be viewed by group admins.'))

    # Get group
    try:
        group = Group.objects.get(slug=group)
    except Group.DoesNotExist:
        raise Http404

    # Check pending transactions
    if is_admin and group.not_payed_transaction_set.count():
        request.user.message_set.create(
            message=_('You have pending transactions in &ldquo;%s&rdquo;."') \
                % group.name)

    # Pass on to generic view
    response = object_list(request, group.transaction_set,
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

    # Get group and account
    try:
        group = Group.objects.get(slug=group)
        account = group.account_set.get(slug=account)
    except (Group.DoesNotExist, Account.DoesNotExist):
        raise Http404

    # Check that user is owner of account or admin of account group
    if not is_admin:
        if request.user.id != account.owner.id:
            return HttpResponseForbidden(_('The account may only be viewed' +
                ' by group admins and the account owner.'))
        if not account.active:
            return HttpResponseForbidden(_('This account has been disabled.'))

    # If owner
    if request.user == account.owner:
        # Set active account in session
        request.session['my_account'] = account

        # Warn owner of account about a low balance
        if account.is_blocked():
            request.user.message_set.create(
                message=_('The account balance is below the block limit,'
                + ' please contact the group admin or deposit enough to'
                + ' pass the limit.'))
        elif account.needs_warning():
            request.user.message_set.create(
                message=_('The account balance is below the warning limit.'))

    # Pass on to generic view
    response = object_list(request, account.transaction_set_with_rejected,
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
def edit_group(request, group, is_admin=False):
    """Edit group properties"""

    # Admins only
    if not is_admin:
        return HttpResponseForbidden(
            _('This page may only be viewed by group admins.'))

    # Get group
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
            request.user.message_set.create(
                message=_('Group successfully updated'))
            return HttpResponseRedirect(reverse('group-summary',
                args=(group.slug,)))
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
    """Create account or edit account properties"""

    # Admins only
    if not is_admin:
        return HttpResponseForbidden(
            _('This page may only be viewed by group admins.'))

    # Get group and account
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
                request.user.message_set.create(
                    message=_('Account successfully updated'))
            else:
                account = form.save(commit=False)
                account.group = group
                account.save()
                request.user.message_set.create(
                    message=_('Account successfully created'))
            return HttpResponseRedirect(reverse('account-summary',
                args=(group.slug, account.slug)))
    else:
        form = AccountForm()

    return render_to_response('accounting/account_form.html',
                              {
                                'is_admin': is_admin,
                                'group': group,
                                'form': form,
                              },
                              context_instance=RequestContext(request))

@login_required
@is_group_admin
def transaction_list(request, group, account=None):
    """Lists a group or an account's transactions"""
    pass # FIXME

@login_required
@is_group_admin
def transaction_details(request, group, transaction):
    """Shows all details about a transaction"""
    pass # FIXME

@login_required
@is_group_admin
def transfer(request, group, account=None, transfer_type=None, is_admin=False):
    """Deposit, withdraw or transfer money"""

    # Get group and account
    try:
        group = Group.objects.get(slug=group)
        if transfer_type != 'register':
            account = group.account_set.get(slug=account)
    except (Group.DoesNotExist, Account.DoesNotExist):
        raise Http404

    if transfer_type != 'register' and account.owner != request.user:
        return HttpResponseForbidden(
            _('This page is only available to the account owner.'))

    if request.method == 'POST':
        data = request.POST
    else:
        data = None

    if transfer_type == 'transfer':
        title = _('Transfer from account')
        form = TransferForm(data,
            credit_options={
                'limit_to_groups': [group],
                'user_accounts': True,
                'exclude_accounts': [account],
            })
    elif transfer_type == 'register' and is_admin:
        title = 'This string is not used'
        form = TransactionForm(data,
            debit_options={
                'user_accounts': True,
                'group_accounts': True,
            },
            credit_options={
                'user_accounts': True,
                'group_accounts': True,
            })
    elif transfer_type == 'deposit':
        title = _('Deposit to account')
        form = DepositWithdrawForm(data)
    elif transfer_type == 'withdraw':
        title = _('Withdrawal from account')
        form = DepositWithdrawForm(data)
    else:
        return HttpResponseForbidden(
            _('This page may only be viewed by group admins.'))

    if request.method == 'POST' and form.is_valid():
        amount = form.cleaned_data['amount']
        details = form.cleaned_data['details'].strip()

        if details == '':
            details = None

        transaction = Transaction()
        # FIXME this shouldn't be need if we figure out a reasonable hack
        transaction.save()

        if transfer_type == 'deposit':
            # Deposit to user account

            transaction.entry_set.add(
                TransactionEntry(account=account, credit=amount))
            transaction.entry_set.add(
                TransactionEntry(account=group.bank_account, debit=amount))

            transaction.set_registered(user=request.user, message=details)
            transaction.set_payed(user=request.user)

        elif transfer_type == 'withdraw':
            # Withdraw from user account

            transaction.entry_set.add(
                TransactionEntry(account=account, debit=amount))
            transaction.entry_set.add(
                TransactionEntry(account=group.bank_account, credit=amount))

            transaction.set_registered(user=request.user, message=details)

        elif transfer_type == 'transfer':
            # Transfer from user account to other user account

            credit_account = Account.objects.get(
                id=form.cleaned_data['credit_account'])

            transaction.entry_set.add(
                TransactionEntry(account=account, debit=amount))
            transaction.entry_set.add(
                TransactionEntry(account=credit_account, credit=amount))

            transaction.set_registered(user=request.user, message=details)

            if amount <= account.user_balance():
                transaction.set_payed(user=request.user)
                transaction.set_received(user=request.user)

        elif transfer_type == 'register' and is_admin:
            # General transaction by group admin

            credit_account = Account.objects.get(
                id=form.cleaned_data['credit_account'])
            debit_account = Account.objects.get(
                id=form.cleaned_data['debit_account'])

            transaction.entry_set.add(
                TransactionEntry(account=debit_account, debit=amount))
            transaction.entry_set.add(
                TransactionEntry(account=credit_account, credit=amount))

            if 'registered' in form.data:
                transaction.set_registered(user=request.user, message=details)

            # FIXME sanity check please
            if 'payed' in form.data:
            # and debit_account.group.admins.filter(id=request.user.id).count
            # elns
                transaction.set_payed(user=request.user)

            # FIXME sanity check please
            if 'received' in form.data:
                transaction.set_received(user=request.user)

            return HttpResponseRedirect(reverse('group-summary',
                args=[group.slug]))
        else:
            return HttpResponseForbidden(
                _('This page may only be viewed by group admins.'))

        request.user.message_set.create(
            message='Added transaction: %s' % transaction)

        return HttpResponseRedirect(reverse('account-summary',
            args=[account.group.slug, account.slug]))

    return render_to_response('accounting/transfer.html',
                              {
                                  'is_admin': is_admin,
                                  'account': account,
                                  'type': transfer_type,
                                  'title': title,
                                  'form': form,
                                  'group': group,
                              },
                              context_instance=RequestContext(request))

@login_required
@is_group_admin
def approve_transactions(request, group, page="1", is_admin=False):

    # Admins only
    if not is_admin:
        return HttpResponseForbidden(
            _('This page may only be viewed by group admins.'))

    # Get group
    try:
        group = Group.objects.get(slug=group)
    except Group.DoesNotExist:
        raise Http404

    # Get related transactions
    transactions = group.not_received_transaction_set

    forms = []
    to_be_rejected = []

    for t in transactions:
        choices = t.get_valid_logtype_choices()

        if request.method == 'POST':
            form = ChangeTransactionForm(request.POST,
                prefix="transaction%d" % t.id, choices=choices)

            if form.is_valid():
                change_to = form.cleaned_data['state']

                if change_to == 'Reg':
                    t.set_registered(user=request.user)
                elif change_to == 'Pay':
                    t.set_payed(user=request.user)
                elif change_to == 'Rec':
                    t.set_received(user=request.user)
                elif change_to == 'Rej':
                    to_be_rejected.append(t)
            else:
                forms.append(form)

        else:
            form = ChangeTransactionForm(prefix="transaction%d" % t.id,
                choices=choices)
            forms.append(form)

    if to_be_rejected:
        form = RejectTransactionForm()
        return render_to_response('accounting/reject_transactions.html',
                           {
                                'is_admin': is_admin,
                                'group': group,
                                'transactions': to_be_rejected,
                                'form': form,
                           },
                           context_instance=RequestContext(request))

    transactions = zip(transactions, forms)

    return render_to_response('accounting/approve_transactions.html',
                       {
                            'is_admin': is_admin,
                            'group': group,
                            'approve': True,
                            'transaction_list': transactions,
                       },
                       context_instance=RequestContext(request))
@login_required
@is_group_admin
def reject_transactions(request, group, is_admin=False):
    """Admin view for rejecting transactions"""

    # Admins only
    if not is_admin:
        return HttpResponseForbidden(
            _('This page may only be viewed by group admins.'))

    # XXX: HACK!!! needs more work ;)

    if request.method != 'POST':
        raise Exception()

    if request.POST['reason'].strip() == '':
        raise Exception()

    transaction = []
    for key in request.POST.keys():
        parts = key.split('_')
        if parts[0] == 'transaction' and parts[1].isdecimal():
            transaction.append(int(parts[1]))

    for id in transaction:
        t = Transaction.objects.get(id=id)

        # FIXME check the we are allowed to reject this transaction

        t.set_rejected(user=request.user, message=request.POST['reason'])

    raise Exception('done')

@login_required
@is_group_admin
def create_transaction(request, group, other_group, is_admin=False):
    """Admin view for creating transactions"""

    # Admins only
    if not is_admin:
        return HttpResponseForbidden(
            _('This page may only be viewed by group admins.'))

    # Get groups
    try:
        group = Group.objects.get(slug=group)
        other = Group.objects.get(slug=other_group)
    except Group.DoesNotExist:
        raise Http404

    TransactionForm =  form_for_model(Transaction)
    del TransactionForm.base_fields['status']

    EntryForm =  form_for_model(TransactionEntry, form=BaseForm)
    del EntryForm.base_fields['account']
    del EntryForm.base_fields['transaction']

    form = TransactionForm()
    other_forms, group_forms = [], []

    for account in group.account_set.all():
        group_forms.append((account, EntryForm(prefix=account.id)))
    for account in other.account_set.all():
        other_forms.append((account, EntryForm(prefix=account.id)))

    return render_to_response('accounting/transaction_form.html',
                              {
                                'is_admin': is_admin,
                                'group': group,
                                'other': other,
                                'form': form,
                                'group_forms': group_forms,
                                'other_forms': other_forms,
                              },
                              context_instance=RequestContext(request))
