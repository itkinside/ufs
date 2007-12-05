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

from itkufs.common.decorators import is_group_admin, limit_to_group
from itkufs.accounting.models import *
from itkufs.accounting.forms import *

@login_required
@is_group_admin
def transaction_list(request, group, account):
    """Lists an account's transactions"""
    pass # FIXME

def transaction_details(request, group, account, transaction):
    """Shows all details about a transaction"""
    pass # FIXME

@login_required
@is_group_admin
def transfer(request, group, account=None, transfer_type=None, is_admin=False):
    """Deposit, withdraw or transfer money"""

    # Get account object
    try:
        group = Group.objects.get(slug=group)
        if transfer_type != 'register':
            account = group.account_set.get(slug=account)
    except (Group.DoesNotExist, Account.DoesNotExist):
        raise Http404

    if transfer_type != 'register' and account.owner != request.user:
        return HttpResponseForbidden(_('This page is only available to the owner of the account'))

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
        return HttpResponseForbidden(_('This page may only be viewed by group admins in the current group.'))

    if request.method == 'POST' and form.is_valid():
        amount = form.cleaned_data['amount']
        details = form.cleaned_data['details'].strip()

        if details == '':
            details = None

        transaction = Transaction()
        transaction.save() # FIXME this shouldn't be need if we figure out a reasonable hack

        if transfer_type == 'deposit':
            # Deposit to user account

            transaction.entry_set.add(TransactionEntry(account=account, debit=amount))
            transaction.entry_set.add(TransactionEntry(account=group.bank_account, credit=amount))

            transaction.set_registered(user=request.user, message=details)
            transaction.set_payed(user=request.user)

        elif transfer_type == 'withdraw':
            # Withdraw from user account

            transaction.entry_set.add(TransactionEntry(account=account, credit=amount))
            transaction.entry_set.add(TransactionEntry(account=group.bank_account, debit=amount))

            transaction.set_registered(user=request.user, message=details)

        elif transfer_type == 'transfer':
            # Transfer from user account to other user account

            credit_account = Account.objects.get(id=form.cleaned_data['credit_account'])

            transaction.entry_set.add(TransactionEntry(account=account, credit=amount))
            transaction.entry_set.add(TransactionEntry(account=credit_account, debit=amount))

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

            # FIXME check that i havent mixed up debit/credit
            transaction.entry_set.add(TransactionEntry(account=debit_account, debit=amount))
            transaction.entry_set.add(TransactionEntry(account=credit_account, credit=amount))

            if 'registered' in form.data:
                transaction.set_registered(user=request.user, message=details)

            # FIXME sanity check please
            if 'payed' in form.data: # and debit_account.group.admins.filter(id=request.user.id).count # elns
                transaction.set_payed(user=request.user)

            # FIXME sanity check please
            if 'received' in form.data:
                transaction.set_received(user=request.user)

            return HttpResponseRedirect(reverse('group-summary',
                args=[group.slug]))
        else:
            return HttpResponseForbidden(_('This page may only be viewed by group admins in the current group.'))

        request.user.message_set.create(message='Added transaction: %s' % transaction)

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
def approve(request, group, page="1", is_admin=False):
    # FIXME: Rename to approve_transactions

    if not is_admin:
        return HttpResponseForbidden(_('This page may only be viewed by group admins in the current group.'))
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
            form = ChangeTransactionForm(request.POST, prefix="transaction%d" % t.id, choices=choices)

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
            form = ChangeTransactionForm(prefix="transaction%d" % t.id, choices=choices)

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

    transactions = zip(transactions,forms)

    return render_to_response('accounting/approve_transactions.html',
                       {
                            'is_admin': is_admin,
                            'group': group,
                            'approve': True,
                            'transaction_list': transactions,
                       },
                       context_instance=RequestContext(request))

def reject_transactions(request, group):
    #HACK!!! needs more work ;)

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
