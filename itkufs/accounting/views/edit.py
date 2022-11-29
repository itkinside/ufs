from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.http import (
    HttpRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
    Http404,
)
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import ugettext as _

from itkufs.common.utils import callsign_sorted as ufs_sorted
from itkufs.common.decorators import limit_to_owner, limit_to_admin
from itkufs.accounting.models import (
    Account,
    Group,
    RoleAccount,
    InvalidTransaction,
    Settlement,
    Transaction,
    TransactionEntry,
)
from itkufs.accounting.forms import (
    ChangeTransactionForm,
    DepositWithdrawForm,
    EntryForm,
    RejectTransactionForm,
    SettlementForm,
    TransactionSettlementForm,
    TransferForm,
)


@login_required
@limit_to_admin
def new_edit_settlement(
    request: HttpRequest,
    group: Group,
    settlement: Optional[Settlement] = None,
    is_admin=False,
):
    """Create new and edit existing settlements"""

    if settlement is not None and not settlement.is_editable():
        return HttpResponseForbidden(
            _("Settlement is closed and cannot be edited.")
        )

    if request.method == "POST":
        if settlement is not None:
            form = SettlementForm(instance=settlement, data=request.POST)
        else:
            form = SettlementForm(data=request.POST)

        if form.is_valid():
            if settlement is not None:
                form.save()
            else:
                settlement = form.save(commit=False)
                settlement.group = group
                settlement.save()

            return HttpResponseRedirect(settlement.get_absolute_url())
    else:
        if settlement is not None:
            form = SettlementForm(instance=settlement)
        else:
            form = SettlementForm()

    return render(
        request,
        "accounting/settlement_form.html",
        {
            "is_admin": is_admin,
            "group": group,
            "settlement": settlement,
            "form": form,
        },
    )


@login_required
@limit_to_owner
@db_transaction.atomic
def transfer(
    request: HttpRequest,
    group: Group,
    account: Optional[Account] = None,
    transfer_type: Optional[str] = None,
    is_admin=False,
    is_owner=False,
):
    """Deposit, withdraw or transfer money"""

    if request.method == "POST":
        data = request.POST
    else:
        data = None

    if transfer_type == "transfer":
        title = _("Transfer from account")
        form = TransferForm(data, account=account)
    elif transfer_type == "deposit":
        title = _("Deposit to account")
        form = DepositWithdrawForm(data)
    elif transfer_type == "withdraw":
        title = _("Withdrawal from account")
        form = DepositWithdrawForm(data)
    else:
        return HttpResponseForbidden(_("Forbidden if not group admin."))

    if request.method == "POST" and form.is_valid():
        amount = form.cleaned_data["amount"]
        details = form.cleaned_data["details"].strip()

        if details == "":
            details = None

        bank_account = group.roleaccount_set.get(
            role=RoleAccount.BANK_ACCOUNT
        ).account

        transaction = Transaction(group=group)
        # FIXME: save() shouldn't be need if we figure out a reasonable hack
        transaction.save()

        if transfer_type == "deposit":
            # Deposit to user account
            transaction.entry_set.create(account=account, credit=amount)
            transaction.entry_set.create(account=bank_account, debit=amount)
            transaction.set_pending(user=request.user, message=details)

        elif transfer_type == "withdraw":
            # Withdraw from user account
            transaction.entry_set.create(account=account, debit=amount)
            transaction.entry_set.create(account=bank_account, credit=amount)
            transaction.set_pending(user=request.user, message=details)

        elif transfer_type == "transfer":
            # Transfer from user account to other user account
            credit_account = Account.objects.get(
                id=form.cleaned_data["credit_account"]
            )
            transaction.entry_set.create(account=account, debit=amount)
            transaction.entry_set.create(account=credit_account, credit=amount)
            transaction.set_pending(user=request.user, message=details)

            if amount <= account.normal_balance() - (group.block_limit or 0):
                transaction.set_committed(user=request.user)
            else:
                messages.info(
                    request,
                    _(
                        "Your transaction has been added, "
                        "but your group admin has to commit it."
                    ),
                )

        else:
            return HttpResponseForbidden(_("Forbidden if not group admin."))

        messages.success(request, _("Added transaction: %s") % transaction)

        return HttpResponseRedirect(
            reverse("account-summary", args=[account.group.slug, account.slug])
        )

    return render(
        request,
        "accounting/transfer.html",
        {
            "is_admin": is_admin,
            "is_owner": is_owner,
            "account": account,
            "type": transfer_type,
            "title": title,
            "form": form,
            "group": group,
        },
    )


@login_required
@limit_to_admin
def approve_transactions(
    request: HttpRequest, group: Group, page="1", is_admin=False
):
    """Approve transactions from members and other groups"""

    transactions = []
    to_be_rejected = []

    for t in group.pending_transaction_set:
        choices = t.get_valid_logtype_choices()

        if request.method == "POST":
            form = ChangeTransactionForm(
                request.POST,
                prefix="transaction%d" % t.id,
                choices=choices,
                label=False,
            )

            if form.is_valid():
                change_to = form.cleaned_data["change_to"]

                if change_to == t.COMMITTED_STATE:
                    t.set_committed(user=request.user)
                elif change_to == t.REJECTED_STATE:
                    to_be_rejected.append(t)

                if change_to not in (t.REJECTED_STATE, t.COMMITTED_STATE):
                    transactions.append(
                        (
                            t,
                            ChangeTransactionForm(
                                prefix="transaction%d" % t.id,
                                choices=t.get_valid_logtype_choices(),
                                label=False,
                            ),
                        )
                    )
            else:
                transactions.append((t, form))

        else:
            form = ChangeTransactionForm(
                choices=choices, prefix="transaction%d" % t.id, label=False
            )
            transactions.append((t, form))

    if to_be_rejected:
        form = RejectTransactionForm()
        return render(
            request,
            "accounting/reject_transactions.html",
            {
                "is_admin": is_admin,
                "group": group,
                "transactions": to_be_rejected,
                "form": form,
            },
        )

    if not transactions:
        messages.info(request, _("No pending transactions found."))
        return HttpResponseRedirect(reverse("group-summary", args=[group.slug]))

    return render(
        request,
        "accounting/approve_transactions.html",
        {
            "is_admin": is_admin,
            "group": group,
            "approve": True,
            "transaction_list": transactions,
        },
    )


@login_required
@limit_to_owner
def reject_transactions(
    request: HttpRequest,
    group: Group,
    transaction: Optional[Transaction] = None,
    is_admin=False,
):
    """Reject transactions from members and other groups"""

    if request.method == "POST":
        data = request.POST
        to_be_rejected = request.POST.getlist("transactions")
        to_be_rejected = group.pending_transaction_set.filter(
            id__in=to_be_rejected
        )
    elif transaction is not None:
        data = None
        try:
            # FIXME add count == 0 check for log_set__account__owner !=
            # request.user
            # FIXME add can_reject to transaction
            to_be_rejected = [
                group.pending_transaction_set.get(
                    id=transaction.id, entry_set__account__owner=request.user
                )
            ]
        except Transaction.DoesNotExist:
            raise Http404
    else:
        return HttpResponseRedirect(
            reverse("group-summary", args=(group.slug,))
        )

    form = RejectTransactionForm(data)

    if not form.is_valid():
        return render(
            request,
            "accounting/reject_transactions.html",
            {
                "is_admin": is_admin,
                "group": group,
                "transactions": to_be_rejected,
                "form": form,
            },
        )

    for transaction in to_be_rejected:
        transaction.set_rejected(
            user=request.user, message=request.POST["reason"]
        )

    if transaction is not None:
        try:
            return HttpResponseRedirect(
                reverse(
                    "account-summary",
                    kwargs={
                        "group": group.slug,
                        "account": group.account_set.get(
                            owner=request.user
                        ).slug,
                    },
                )
            )
        except Account.DoesNotExist:
            return HttpResponseRedirect(
                reverse("group-summary", kwargs={"group": group.slug})
            )

    if group.pending_transaction_set.count():
        return HttpResponseRedirect(
            reverse("approve-transactions", kwargs={"group": group.slug})
        )

    return HttpResponseRedirect(
        reverse("group-summary", kwargs={"group": group.slug})
    )


@login_required
@limit_to_admin
@db_transaction.atomic
def new_edit_transaction(
    request: HttpRequest,
    group: Group,
    transaction: Optional[Transaction] = None,
    is_admin=False,
):
    """Admin view for creating transactions"""

    savepoint_id = db_transaction.savepoint()
    if transaction is None:
        transaction = Transaction(group=group)
    elif not transaction.is_editable():
        messages.error(
            request, _("Transaction %d can't be changed." % transaction.id)
        )

        db_transaction.savepoint_rollback(savepoint_id)

        url = reverse("group-summary", args=(group.slug,))
        return HttpResponseRedirect(url)

    if request.method == "POST":
        data = request.POST
    elif transaction.id:
        data = {}
        # Load "fake" post data if we are editing a transaction
        data["settlement-date"] = transaction.date
        for e in transaction.entry_set.all():
            if e.debit > 0:
                data["%d-debit" % e.account.id] = e.debit
            if e.credit > 0:
                data["%d-credit" % e.account.id] = e.credit

        data["settlement-settlement"] = transaction.settlement_id
    else:
        data = None

    # Init forms
    settlement_form = TransactionSettlementForm(
        data, prefix="settlement", instance=transaction
    )

    user_forms = []
    group_forms = []

    for account in ufs_sorted(group.user_account_set.filter(active=True)):
        user_forms.append((account, EntryForm(data, prefix=account.id)))

    for account in ufs_sorted(group.group_account_set.filter(active=True)):
        group_forms.append((account, EntryForm(data, prefix=account.id)))

    errors = []

    if request.method == "POST" and settlement_form.is_valid():
        entries = {}

        if transaction.id is None:
            transaction.save()
        else:
            for e in transaction.entry_set.all():
                entries[e.account.id] = e

        transaction.settlement = settlement_form.cleaned_data["settlement"]

        try:
            for forms in [group_forms, user_forms]:
                for account, form in forms:
                    if not form.is_valid():
                        raise InvalidTransaction(
                            "Form was not valid, id: %d" % account.id
                        )
                    else:
                        credit = form.cleaned_data["credit"] or 0
                        debit = form.cleaned_data["debit"] or 0

                        if account.id in entries:
                            entry = entries[account.id]
                        else:
                            entry = TransactionEntry(
                                account=account, transaction=transaction
                            )

                        if credit > 0 or debit > 0:
                            entry.credit = credit or 0
                            entry.debit = debit or 0
                            entry.save()
                        elif entry.id:
                            entry.delete()

            details = settlement_form.cleaned_data["details"]

            transaction.save()

            transaction.set_pending(user=request.user, message=details)

            messages.success(request, _("Your transaction has been added."))

        except InvalidTransaction as e:
            errors.append(e)
            db_transaction.savepoint_rollback(savepoint_id)
        else:
            db_transaction.savepoint_commit(savepoint_id)
            url = reverse("group-summary", args=(group.slug,))
            return HttpResponseRedirect(url)

    db_transaction.savepoint_rollback(savepoint_id)

    return render(
        request,
        "accounting/transaction_form.html",
        {
            "is_admin": is_admin,
            "group": group,
            "settlement_form": settlement_form,
            "group_forms": group_forms,
            "user_forms": user_forms,
            "errors": errors,
            "transaction": transaction,
        },
    )
