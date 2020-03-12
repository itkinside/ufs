from operator import itemgetter

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render

from itkufs.common.decorators import limit_to_group, limit_to_owner
from itkufs.accounting.models import Account, Group


@login_required
@limit_to_group
def group_summary(request, group, is_admin=False):
    """Show group summary"""

    return render(
        request,
        "common/group_summary.html",
        {
            "is_admin": is_admin,
            "all": "all" in request.GET,
            "group": Group.objects.select_related().get(id=group.id),
        },
    )


@login_required
@limit_to_owner
def account_summary(request, group, account, is_admin=False, is_owner=False):
    """Show account summary"""

    if is_owner:
        # Set active account in session
        request.session["my_account"] = {
            "group_slug": account.group.slug,
            "account_slug": account.slug,
        }

        # Warn owner of account about a low balance
        if account.is_blocked():
            messages.error(
                request,
                "The account balance is below the block limit, please "
                "contact the group admin or deposit enough to pass the "
                "limit.",
            )
        elif account.needs_warning():
            messages.warning(
                request, "The account balance is below the warning limit."
            )

    return render(
        request,
        "common/account_summary.html",
        {
            "is_admin": is_admin,
            "is_owner": is_owner,
            "group": group,
            "account": Account.objects.select_related().get(id=account.id),
            "balance_data": _generate_gchart_data(
                account.get_balance_history_set()
            ),
        },
    )


@login_required
@limit_to_group
def group_balance_graph(request, group, is_admin=False):
    accounts = (
        Account.objects.all()
        .filter(group_id=group.id, active=True, group_account=False)
        .order_by("name")
    )

    data = []

    for a in accounts:
        data.append([a.short_name, a.normal_balance()])

    graph_data = ['[ "%s", %d ]' % (a[0], a[1]) for a in data]

    data = sorted(data, key=itemgetter(1), reverse=True)

    graph_data_sorted = ['[ "%s", %d ]' % (a[0], a[1]) for a in data]

    graph_data_positive = []
    graph_data_negative = []

    for a in data:
        if a[1] >= 0:
            graph_data_positive.append('[ "%s", %d ]' % (a[0], a[1]))
        else:
            graph_data_negative.append('[ "%s", %d ]' % (a[0], -a[1]))

    return render(
        request,
        "common/group_balance_graph.html",
        {
            "group": Group.objects.select_related().get(id=group.id),
            "graph_data": ",\n".join(graph_data),
            "graph_data_sorted": ",\n".join(graph_data_sorted),
            "graph_data_positive": ",\n".join(graph_data_positive),
            "graph_data_negative": ",\n".join(graph_data_negative),
        },
    )


def _generate_gchart_data(dataset):
    # aggregate data
    agg = 0.0
    history = []
    for i in range(len(dataset)):
        saldo = float(dataset[i].saldo)
        history.append((dataset[i].date, saldo + agg))
        agg += saldo

    items = [f"[ new Date({date}), {balance:.2f}]" for date, balance in history]
    return ",\n".join(items)
