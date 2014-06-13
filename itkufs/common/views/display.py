from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.xheaders import populate_xheaders
from django.shortcuts import render_to_response

from itkufs.common.decorators import limit_to_group, limit_to_owner
from itkufs.accounting.models import Account, Group


@login_required
@limit_to_group
def group_summary(request, group, is_admin=False):
    """Show group summary"""

    response = render_to_response('common/group_summary.html', {
        'is_admin': is_admin,
        'all': 'all' in request.GET,
        'group': Group.objects.select_related().get(id=group.id),
    })
    populate_xheaders(request, response, Group, group.id)
    return response


@login_required
@limit_to_owner
def account_summary(request, group, account, is_admin=False, is_owner=False):
    """Show account summary"""

    if is_owner:
        # Set active account in session
        request.session['my_account'] = account

        # Warn owner of account about a low balance
        if account.is_blocked():
            messages.error(
                request,
                'The account balance is below the block limit, please '
                'contact the group admin or deposit enough to pass the '
                'limit.')
        elif account.needs_warning():
            messages.warning(
                request,
                'The account balance is below the warning limit.')

    response = render_to_response('common/account_summary.html', {
        'is_admin': is_admin,
        'is_owner': is_owner,
        'group': group,
        'account': Account.objects.select_related().get(id=account.id),
        'balance_data': _generate_gchart_data(
            account.get_balance_history_set()),
    })
    populate_xheaders(request, response, Account, account.id)
    return response


def _generate_gchart_data(dataset):
    # aggregate data
    agg = 0.0
    history = []
    for i in range(len(dataset)):
        saldo = float(dataset[i].saldo)
        history.append((dataset[i].date, saldo + agg))
        agg += saldo

    items = [
        '[ new Date(%s), %.2f]' % (date, balance) for date, balance in history]
    return ',\n'.join(items)
