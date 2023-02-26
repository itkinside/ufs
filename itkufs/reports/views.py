from datetime import date
from subprocess import Popen, PIPE
import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.db.models import Q, F, Subquery, OuterRef, DecimalField
from django.forms.models import inlineformset_factory
from django.http import Http404, HttpResponseRedirect, HttpResponse, HttpRequest
from django.shortcuts import render
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils.translation import ugettext as _

from itkufs.common.decorators import limit_to_group, limit_to_admin
from itkufs.accounting.models import (
    Account,
    Transaction,
    Group,
)
from itkufs.reports.models import List, ListColumn
from itkufs.reports.forms import (
    ColumnForm,
    ListForm,
    ListTransactionForm,
    BalanceStatementForm,
    IncomeStatementForm,
)
from itkufs.reports.pdf import pdf

from typing import Optional

_list = list


def public_lists(request: HttpRequest):
    lists = (
        List.objects.filter(public=True)
        .select_related("group")
        .order_by("group__name", "name")
    )

    return render(
        request,
        "reports/public_lists.html",
        {"public_list": lists},
    )


@login_required
@limit_to_group
def view_list(request: HttpRequest, group: Group, list: List, is_admin=False):
    content = pdf(group, request.user.username, list)

    filename = "{}-{}-{}".format(date.today(), group, list)

    response = HttpResponse(content.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=%s.pdf" % (
        slugify(filename)
    )

    return response


@login_required
@limit_to_group
def view_list_preview(
    request: HttpRequest, group: Group, list: List, is_admin=False
):
    content = pdf(
        group, request.user.username, list, show_header=True, show_footer=True
    )

    p = Popen(
        [
            "gs",
            "-q",
            "-dSAFER",
            "-dBATCH",
            "-dNOPAUSE",
            "-r40",
            "-dGraphicsAlphaBits=4",
            "-dTextAlphaBits=4",
            "-sDEVICE=png16m",
            "-sOutputFile=-",
            "-",
        ],
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE,
    )

    stdout, stderr = p.communicate(content.getvalue())

    if p.returncode != 0:
        raise Exception(stdout)

    return HttpResponse(stdout, content_type="image/png")


def view_public_list(
    request: HttpRequest, group: Group, list: List, is_admin=False
):
    if not list.public:
        raise Http404

    content = pdf(group, request.user.username, list)

    filename = "{}-{}-{}".format(date.today(), group, list)

    response = HttpResponse(content.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=%s.pdf" % (
        slugify(filename)
    )

    return response


@login_required
@limit_to_admin
@db_transaction.atomic
def new_edit_list(
    request: HttpRequest,
    group: Group,
    list: Optional[List] = None,
    is_admin=False,
):
    """Create new or edit existing list"""

    if request.method == "POST":
        data = request.POST
    else:
        data = None

    if not list:
        ColumnFormSet = inlineformset_factory(
            List, ListColumn, extra=10, form=ColumnForm
        )

        listform = ListForm(data=data, group=group)
        columnformset = ColumnFormSet(data)

    else:
        ColumnFormSet = inlineformset_factory(
            List, ListColumn, extra=3, form=ColumnForm
        )
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

            return HttpResponseRedirect(
                reverse("group-summary", kwargs={"group": group.slug})
            )

    return render(
        request,
        "reports/list_form.html",
        {
            "is_admin": is_admin,
            "group": group,
            "list": list,
            "listform": listform,
            "columnformset": columnformset,
        },
    )


@login_required
@limit_to_admin
@db_transaction.atomic
def delete_list(request: HttpRequest, group: Group, list: List, is_admin=False):
    """Delete list"""

    if request.method == "POST":
        # FIXME maybe a bit naive here?
        list.delete()
        messages.info(request, _("List deleted."))

        return HttpResponseRedirect(
            reverse("group-summary", kwargs={"group": group.slug})
        )

    return render(
        request,
        "reports/list_delete.html",
        {"is_admin": is_admin, "group": group, "list": list},
    )


@login_required
@limit_to_admin
@db_transaction.atomic
def transaction_from_list(
    request: HttpRequest, group: Group, list: List, is_admin=False
):
    """Enter list"""

    form = ListTransactionForm(list, request.POST or None)

    if form.is_valid():
        transaction = Transaction(group=list.group)
        transaction.save()

        for entry in form.transaction_entries():
            entry.transaction = transaction
            entry.save()

        transaction.save()
        transaction.set_pending(
            user=request.user, message=_("Created from list: %s") % list.slug
        )

        return HttpResponseRedirect(
            reverse(
                "edit-transaction",
                kwargs={"group": group.slug, "transaction": transaction.id},
            )
        )

    return render(
        request,
        "reports/list_transaction_form.html",
        {"is_admin": is_admin, "group": group, "list": list, "form": form},
    )


@login_required
@limit_to_group
def balance(request: HttpRequest, group: Group, is_admin=False):
    """Show balance sheet for the group"""

    if request.GET:
        # Get data from user
        data = request.GET
    else:
        # Set default values
        data = {"date": datetime.date.today(), "hide_empty_inactive": True}

    form = BalanceStatementForm(data)

    if form.is_valid():
        date = form.cleaned_data["date"]
        hide_empty_active = form.cleaned_data["hide_empty_active"]
        hide_empty_inactive = form.cleaned_data["hide_empty_inactive"]
    else:
        raise ValueError("Invalid form data.")

    # Get account balances at the given date for relevant accounts
    balances = (
        Account.objects.with_historical_balance(date)
        .filter(group=group)
        .exclude(type=Account.INCOME_ACCOUNT)
        .exclude(type=Account.EXPENSE_ACCOUNT)
        .prefetch_related("group")
    )

    if hide_empty_active:
        balances = balances.exclude(Q(active=True) & Q(normal_balance=0))

    if hide_empty_inactive:
        balances = balances.exclude(Q(active=False) & Q(normal_balance=0))

    # Balance sheet data struct
    accounts = {
        "as": [],
        "li": [],
        "eq": [],
    }

    account_sums = {
        "as": 0,
        "li": 0,
        "eq": 0,
        "li_eq": 0,
    }

    # Aggregate member account liabilities
    member_negative_sum = 0
    member_positive_sum = 0

    for account in balances:
        if account.group_account:
            accounts[account.type.lower()].append(account)
            account_sums[account.type.lower()] += account.normal_balance
        else:
            if account.normal_balance > 0:
                member_positive_sum += account.normal_balance
            else:
                member_negative_sum += account.normal_balance

    # Accumulated member accounts liabilities
    accounts["li"].append(
        {"name": _("Positive member accounts"), "balance": member_positive_sum}
    )
    accounts["li"].append(
        {"name": _("Negative member accounts"), "balance": member_negative_sum}
    )
    account_sums["li"] += member_positive_sum
    account_sums["li"] += member_negative_sum

    # Total liabilities and equities
    account_sums["li_eq"] = account_sums["li"] + account_sums["eq"]

    # Current year's net income
    curr_year_net_income = account_sums["as"] - account_sums["li_eq"]
    accounts["eq"].append(
        (_("Current year's net income"), curr_year_net_income)
    )
    account_sums["eq"] += curr_year_net_income
    account_sums["li_eq"] += curr_year_net_income

    return render(
        request,
        "reports/balance.html",
        {
            "is_admin": is_admin,
            "group": group,
            "to_date": date,
            "accounts": accounts,
            "account_sums": account_sums,
            "form": form,
        },
    )


@login_required
@limit_to_group
def income(request: HttpRequest, group: Group, is_admin=False):
    """Show income statement for group"""

    if request.GET:
        # Get data from user
        data = request.GET
    else:
        # Set default values
        data = {
            "from_date": datetime.date(1929, 10, 1),
            "to_date": datetime.date.today(),
            "hide_empty_inactive": True,
        }

    form = IncomeStatementForm(data)

    if form.is_valid():
        from_date = form.cleaned_data["from_date"]
        to_date = form.cleaned_data["to_date"]
        hide_empty_active = form.cleaned_data["hide_empty_active"]
        hide_empty_inactive = form.cleaned_data["hide_empty_inactive"]
    else:
        raise ValueError("Invalid form data.")

    # Find the balance for each account at the start of the period
    starting_balances = (
        Account.objects.with_historical_balance(from_date)
        .filter(group=group)
        .filter(
            Q(type=Account.INCOME_ACCOUNT) | Q(type=Account.EXPENSE_ACCOUNT)
        )
        .prefetch_related("group")
    )

    # Find the change in balance for each account at the end of the period
    current_balances = (
        Account.objects.with_historical_balance(to_date)
        .filter(group=group)
        .filter(
            Q(type=Account.INCOME_ACCOUNT) | Q(type=Account.EXPENSE_ACCOUNT)
        )
        .annotate(
            balance_change=F("normal_balance")
            - Subquery(
                starting_balances.filter(slug=OuterRef("slug")).values(
                    "normal_balance"
                )[:1],
                output_field=DecimalField(),
            ),
        )
        .prefetch_related("group")
    )

    if hide_empty_active:
        current_balances = current_balances.exclude(
            Q(active=True) & Q(balance_change=0)
        )

    if hide_empty_inactive:
        current_balances = current_balances.exclude(
            Q(active=False) & Q(balance_change=0)
        )

    # Balance sheet data struct
    accounts = {"in": [], "ex": []}

    account_sums = {
        "in": 0,
        "ex": 0,
        "in_ex_diff": 0,
    }

    # Get balance change for all accounts
    for account in current_balances:
        if account.type == Account.INCOME_ACCOUNT:
            accounts["in"].append(account)
            account_sums["in"] += account.balance_change

        elif account.type == Account.EXPENSE_ACCOUNT:
            accounts["ex"].append(account)
            account_sums["ex"] += account.balance_change

    # Net income
    account_sums["in_ex_diff"] = account_sums["in"] - account_sums["ex"]

    return render(
        request,
        "reports/income.html",
        {
            "is_admin": is_admin,
            "group": group,
            "form": form,
            "from_date": from_date,
            "to_date": to_date,
            "accounts": accounts,
            "account_sums": account_sums,
        },
    )
