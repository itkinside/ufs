from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.db import transaction as db_transaction

from itkufs.common.decorators import limit_to_owner, limit_to_admin
from itkufs.accounting.models import *
from itkufs.accounting.forms import *


@login_required
@limit_to_admin
def new_edit_settlement(request, group, type='new', is_admin=False):
    """Create new and edit existing settlements"""

    # TODO: Implement support for editing settlements

    if request.method == 'POST':
        form = SettlementForm(request.POST)

        if form.is_valid():
            settlement = form.save(commit=False)

            settlement.group = group
            settlement.save()

            return HttpResponseRedirect(
                reverse('group-summary', args=(group.slug,)))
    else:
        form = SettlementForm()

    return render_to_response('accounting/settlement_form.html',
        {
            'is_admin': is_admin,
            'group': group,
            'form': form,
        },
        context_instance=RequestContext(request))


@login_required
@limit_to_owner
@db_transaction.commit_on_success
def transfer(request, group, account=None, transfer_type=None,
    is_admin=False, is_owner=False):
    """Deposit, withdraw or transfer money"""

    if request.method == 'POST':
        data = request.POST
    else:
        data = None

    if transfer_type == 'transfer':
        title = _('Transfer from account')
        form = TransferForm(data, account=account)
    elif transfer_type == 'deposit':
        title = _('Deposit to account')
        form = DepositWithdrawForm(data)
    elif transfer_type == 'withdraw':
        title = _('Withdrawal from account')
        form = DepositWithdrawForm(data)
    else:
        return HttpResponseForbidden(_('Forbidden if not group admin.'))

    if request.method == 'POST' and form.is_valid():
        amount = form.cleaned_data['amount']
        details = form.cleaned_data['details'].strip()

        if details == '':
            details = None

        bank_account = group.roleaccount_set.get(role=RoleAccount.BANK_ACCOUNT)

        transaction = Transaction(group=group, user_transaction=True)
        # FIXME: save() shouldn't be need if we figure out a reasonable hack
        transaction.save()

        if transfer_type == 'deposit':
            # Deposit to user account

            transaction.entry_set.add(
                TransactionEntry(account=account, credit=amount))
            transaction.entry_set.add(
                TransactionEntry(account=bank_account, debit=amount))

            transaction.set_pending(user=request.user, message=details)

        elif transfer_type == 'withdraw':
            # Withdraw from user account

            transaction.entry_set.add(
                TransactionEntry(account=account, debit=amount))
            transaction.entry_set.add(
                TransactionEntry(account=bank_account, credit=amount))

            transaction.set_pending(user=request.user, message=details)

        elif transfer_type == 'transfer':
            # Transfer from user account to other user account

            credit_account = Account.objects.get(
                id=form.cleaned_data['credit_account'])

            transaction.entry_set.add(
                TransactionEntry(account=account, debit=amount))
            transaction.entry_set.add(
                TransactionEntry(account=credit_account, credit=amount))

            transaction.set_pending(user=request.user, message=details)

            if amount <= account.user_balance() - (group.block_limit or 0):
                request.user.message_set.create(message=
                    _('Your tranfser has not been completed, your group admin
                    needs to complete the transaction.'))
                transaction.set_committed(user=request.user)

        else:
            return HttpResponseForbidden(_('Forbidden if not group admin.'))

        request.user.message_set.create(
            message='Added transaction: %s' % transaction)

        return HttpResponseRedirect(reverse('account-summary',
            args=[account.group.slug, account.slug]))

    return render_to_response('accounting/transfer.html',
        {
            'is_admin': is_admin,
            'is_owner': is_owner,
            'account': account,
            'type': transfer_type,
            'title': title,
            'form': form,
            'group': group,
        },
        context_instance=RequestContext(request))

@login_required
@limit_to_admin
def approve_transactions(request, group, page='1', is_admin=False):
    """Approve transactions from members and other groups"""

    transactions = []
    to_be_rejected = []

    for t in group.pending_transaction_set:
        choices = t.get_valid_logtype_choices()

        if request.method == 'POST':
            form = ChangeTransactionForm(request.POST,
                prefix="transaction%d" % t.id, choices=choices, label=False)

            if form.is_valid():
                change_to = form.cleaned_data['change_to']

                if change_to == t.COMMITTED_STATE:
                    t.set_committed(user=request.user)
                elif change_to == t.REJECTED_STATE:
                    to_be_rejected.append((t))

                if change_to != t.REJECTED_STATE and change_to != t.COMMITTED_STATE:
                    transactions.append((t,
                        ChangeTransactionForm(prefix='transaction%d' % t.id,
                            choices=t.get_valid_logtype_choices(), label=False)))
            else:
                transactions.append((t,form))

        else:
            form = ChangeTransactionForm(choices=choices,
                prefix="transaction%d" % t.id, label=False)
            transactions.append((t,form))

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

    return render_to_response('accounting/approve_transactions.html',
        {
            'is_admin': is_admin,
            'group': group,
            'approve': True,
            'transaction_list': transactions,
        },
        context_instance=RequestContext(request))

@login_required
@limit_to_admin
def reject_transactions(request, group, is_admin=False):
    """Reject transactions from members and other groups"""

    if request.method == 'POST':
        data = request.POST
        to_be_rejected = request.POST.getlist('transactions')
        to_be_rejected = group.pending_transaction_set.filter(id__in=to_be_rejected)
    else:
        return HttpResponseRedirect(
            reverse('group-summary', args=(group.slug,)))

    form = RejectTransactionForm(data)

    if not form.is_valid():
        return render_to_response('accounting/reject_transactions.html',
            {
                 'is_admin': is_admin,
                 'group': group,
                 'transactions': to_be_rejected,
                 'form': form,
            },
            context_instance=RequestContext(request))

    for transaction in to_be_rejected:
        transaction.set_rejected(user=request.user,
            message=request.POST['reason'])

    if group.pending_transaction_set.count():
        return HttpResponseRedirect(reverse('approve-transactions',
            kwargs={
                'group': group.slug,
            }))
    return HttpResponseRedirect(reverse('group-summary',
        kwargs={'group': group.slug,}))

@login_required
@limit_to_admin
@db_transaction.commit_manually
def new_edit_transaction(request, group, is_admin=False, transaction=None):
    """Admin view for creating transactions"""

    if transaction:
        try: # Use group to ensure that we aren't being tricked
            transaction = group.transaction_set.get(id=transaction)
        except Transaction.DoesNotExist:
            pass
    else:
        transaction = Transaction(group=group)

    if request.method == 'POST':
        data = request.POST
    elif transaction.id:
        data = {}
        # Load "fake" post data if we are editing a transaction
        for e in transaction.entry_set.all():
            if e.debit > 0:
                data['%d-debit' % e.account.id] = e.debit
            if e.credit > 0:
                data['%d-credit' % e.account.id] = e.credit
    else:
        data = None

    # Init forms
    settlement_form = TransactionSettlementForm(data, prefix='settlement',
        instance=transaction)

    user_forms = []
    group_forms = []

    for account in group.user_account_set:
        user_forms.append((account, EntryForm(data, prefix=account.id)))

    for account in group.group_account_set:
        group_forms.append((account, EntryForm(data, prefix=account.id)))

    errors = []

    if request.method == 'POST' and settlement_form.is_valid():
        entries = {}

        if transaction.id is None:
            transaction.save()
        else:
            for e in transaction.entry_set.all():
                entries[e.account.id] = e

        transaction.settlement = settlement_form.cleaned_data['settlement']

        try:
            for forms in [group_forms, user_forms]:
                for account, form in forms:
                    if not form.is_valid():
                        raise InvalidTransaction('Form was not valid, id: %d' % account.id)
                    else:
                        credit = form.cleaned_data['credit']
                        debit = form.cleaned_data['debit']

                        if account.id in entries:
                            entry = entries[account.id]
                        else:
                            entry = TransactionEntry(account=account,transaction=transaction)

                        if credit > 0 or debit > 0:
                            entry.credit = credit or 0
                            entry.debit = debit or 0
                            entry.save()
                        elif entry.id:
                            entry.delete()

            details = settlement_form.cleaned_data['details']

            transaction.save()

            transaction.set_pending(user=request.user, message=details)

            request.user.message_set.create(
                message= _('Your transaction has been added'))

        except InvalidTransaction, e:
            errors.append(e)
            db_transaction.rollback()
        else:
            db_transaction.commit()
            url = reverse('group-summary', args=(group.slug,))
            return HttpResponseRedirect(url)

    db_transaction.rollback()
    return render_to_response('accounting/transaction_form.html',
        {
            'is_admin': is_admin,
            'group': group,
            'settlement_form': settlement_form,
            'group_forms': group_forms,
            'user_forms': user_forms,
            'errors': errors,
        },
        context_instance=RequestContext(request))

