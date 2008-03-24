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
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _, ungettext
from django.views.generic.list_detail import object_list, object_detail
from django.db import transaction as db_transaction

from itkufs.common.decorators import limit_to_group, limit_to_owner, limit_to_admin
from itkufs.accounting.models import *
from itkufs.accounting.forms import *

@login_required
@limit_to_group
def group_summary(request, group, is_admin=False):
    """Show group summary"""

    response = object_detail(request, Group.objects.all(), group.id,
        template_name='accounting/group_summary.html',
        template_object_name='group',
        extra_context={'is_admin': is_admin})
    populate_xheaders(request, response, Group, group.id)
    return response

@login_required
def account_switch(request, group, is_admin=False):
    """Switch to account summary for the selected account"""

    if request.method != 'POST':
        raise Http404

    group_slug = request.POST['group']
    account = get_object_or_404(Account, owner=request.user,
        group__slug=group_slug)
    url = reverse('account-summary', args=(account.group.slug, account.slug))
    return HttpResponseRedirect(url)

@login_required
@limit_to_owner
def account_summary(request, group, account,
    is_admin=False, is_owner=False):
    """Show account summary"""

    if is_owner:
        # Check if active
        if not account.active and not is_admin:
            return HttpResponseForbidden(_('This account has been disabled.'))

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

    response = object_detail(request, Account.objects.all(), account.id,
        template_name='accounting/account_summary.html',
        template_object_name='account',
        extra_context={
            'is_admin': is_admin,
            'is_owner': is_owner,
            'group': group,
        })
    populate_xheaders(request, response, Account, account.id)
    return response

@login_required
@limit_to_admin
def edit_group(request, group, is_admin=False):
    """Edit group properties"""

    old_logo = group.get_logo_filename()

    if request.method == 'POST':
        form = GroupForm(data=request.POST, files=request.FILES, instance=group)
        if form.is_valid():
            form.save()
            if old_logo and old_logo != group.get_logo_filename():
                os.remove(old_logo)

            elif 'delete_logo' in form.cleaned_data:
                os.remove(group.get_logo_filename())
                group.logo = ''
                group.save()

            request.user.message_set.create(
                message=_('Group successfully updated'))

            return HttpResponseRedirect(reverse('group-summary',
                args=(group.slug,)))
    else:
        form = GroupForm(instance=group)

    return render_to_response('accounting/group_form.html',
                              {
                                'is_admin': is_admin,
                                'group': group,
                                'form': form,
                              },
                              context_instance=RequestContext(request))

@login_required
@limit_to_admin
def edit_account(request, group, account=None, type='new',
    is_admin=False, is_owner=False):
    """Create account or edit account properties"""

    if request.method == 'POST':
        if type == 'edit':
            form = AccountForm(instance=account, data=request.POST)
        else:
            form = AccountForm(data=request.POST)
        if form.is_valid():
            if type== 'edit':
                form.save()
                request.user.message_set.create(
                    message=_('Account successfully updated'))
            else:
                account = form.save(group=group)
                request.user.message_set.create(
                    message=_('Account successfully created'))
            return HttpResponseRedirect(reverse('account-summary',
                args=(group.slug, account.slug)))
    else:
        if type == 'edit':
            form = AccountForm(instance=account)
        else:
            form = AccountForm()

    extra = {
        'is_admin': is_admin,
        'group': group,
        'form': form,
    }

    if type == 'edit':
        extra['account'] = account
        extra['is_owner'] = is_owner

    return render_to_response('accounting/account_form.html', extra,
                              context_instance=RequestContext(request))

@login_required
@limit_to_owner
def transaction_list(request, group, account=None, page='1',
    is_admin=False, is_owner=False):
    """Lists a group or an account's transactions"""

    # Get transactions
    if account is not None:
        transactions = account.transaction_set
    else:
        transactions = group.transaction_set

    # Pass on to generic view
    response = object_list(request, transactions,
                       paginate_by=20,
                       page=page,
                       allow_empty=True,
                       template_name='accounting/transaction_list.html',
                       extra_context={
                            'is_admin': is_admin,
                            'is_owner': is_owner,
                            'group': group,
                            'account': account,
                       },
                       template_object_name='transaction')
    populate_xheaders(request, response, Group, group.id)
    return response

@login_required
def transaction_details(request, group, transaction, is_admin=False):
    """Shows all details about a transaction"""

    # Check that user is party of transaction or admin of group
    # TODO: Look into doing this with a decorator
    if not is_admin and TransactionEntry.objects.filter(
        transaction__id=transaction,
        account__owner__id=request.user.id).count() == 0:
        return HttpResponseForbidden(_('The transaction may only be'
            ' viewed by group admins or a party of the transaction.'))

    # Pass on to generic view
    response = object_detail(request, Transaction.objects.all(), transaction,
                       template_name='accounting/transaction_details.html',
                       extra_context={
                            'is_admin': is_admin,
                            'group': group,
                       },
                       template_object_name='transaction')
    populate_xheaders(request, response, Transaction, transaction)
    return response

@login_required
@limit_to_owner
@db_transaction.commit_on_success
def transfer(request, group, account=None, transfer_type=None,
    is_admin=False, is_owner=False):
    """Deposit, withdraw or transfer money"""

    # FIXME: When adding a transfer from one self to one self, which should not
    # be allowed, an IntegrityError ("columns transaction_id, account_id are
    # not unique") is raised. Even if commit_on_success is used, an empty
    # transaction without entries are saved to the database. In other words, we
    # need more error checking here, or try out commit_manually instead.

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
        return HttpResponseForbidden(
            _('Forbidden if not group admin.'))

    if request.method == 'POST' and form.is_valid():
        amount = form.cleaned_data['amount']
        details = form.cleaned_data['details'].strip()

        if details == '':
            details = None

        transaction = Transaction(group=group)
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

        else:
            return HttpResponseForbidden(
                _('Forbidden if not group admin.'))

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

    for t in group.not_received_transaction_set:
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
                    to_be_rejected.append((t))

                if change_to != 'Rej' and change_to != 'Rec':
                    transactions.append((t, ChangeTransactionForm(prefix="transaction%d" %
                        t.id, choices=t.get_valid_logtype_choices())))
            else:
                transactions.append((t,form))

        else:
            form = ChangeTransactionForm(choices=choices,
                prefix="transaction%d" % t.id)
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

    if request.method != 'POST':
        # request.user.message_set.create('') # FIXME Write user message
        return HttpResponseRedirect(reverse('group-summary', args=(group.slug,)))

    form = RejectTransactionForm(request.POST)
    to_be_rejected = request.POST.getlist('transactions')

    to_be_rejected = Transaction.objects.filter(id__in=to_be_rejected, group=group)

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
        transactions.set_rejected(user=request.user, message=request.POST['reason'])

    # FIXME insert user message
    return HttpResponseRedirect(reverse('approve-transactions', args=(group.slug,)))

@login_required
@limit_to_admin
@db_transaction.commit_manually
def create_transaction(request, group, is_admin=False):
    """Admin view for creating transactions"""

    if request.method == 'POST':
        post = request.POST
    else:
        post = None

    settlement = SettlementForm(post, prefix='settlement')
    user_forms = [(account, EntryForm(post, prefix=account.id))
        for account in group.user_account_set]
    group_forms = [(account, EntryForm(post, prefix=account.id))
        for account in group.group_account_set]

    if post:
        valid = True

        # FIXME support settlment 
        transaction = Transaction(group=group)
        transaction.save()

        for account, form in user_forms:
            if not form.is_valid():
                valid = False
            else:
                if form.cleaned_data['credit'] > 0:
                    transaction.entry_set.add(TransactionEntry(account=account, credit=form.cleaned_data['credit'], debit=0))
                elif form.cleaned_data['debit']:
                    transaction.entry_set.add(TransactionEntry(account=account, debit=form.cleaned_data['debit'], credit=0))
        for account, form in group_forms:
            if not form.is_valid():
                valid = False
            else:
                if form.cleaned_data['credit'] > 0:
                    transaction.entry_set.add(TransactionEntry(account=account, credit=form.cleaned_data['credit'], debit=0))
                elif form.cleaned_data['debit']:
                    transaction.entry_set.add(TransactionEntry(account=account, debit=form.cleaned_data['debit'], credit=0))

        if valid:
            db_transaction.commit()
        else:
            db_transaction.rollback()

    return render_to_response('accounting/transaction_form.html',
                              {
                                'is_admin': is_admin,
                                'group': group,
                                'form': settlement,
                                'group_forms': group_forms,
                                'user_forms': user_forms,
                              },
                              context_instance=RequestContext(request))
