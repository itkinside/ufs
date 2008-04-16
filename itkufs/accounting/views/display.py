from django.contrib.auth.decorators import login_required
from django.core.xheaders import populate_xheaders
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.utils.translation import ugettext as _
from django.views.generic.list_detail import object_list, object_detail

from itkufs.common.decorators import limit_to_group, limit_to_admin
from itkufs.accounting.models import *
from itkufs.accounting.forms import *

@login_required
@limit_to_group
def settlement_list(request, group, page='1', is_admin=False):
    """Show paginated list of settlements"""

    # Pass on to generic view
    response = object_list(request,
        group.settlement_set.select_related(),
        paginate_by=20,
        page=page,
        allow_empty=True,
        template_name='accounting/settlement_list.html',
        extra_context={
            'is_admin': is_admin,
            'group': group,
        },
        template_object_name='settlement')
    populate_xheaders(request, response, Group, group.id)
    return response

@login_required
@limit_to_group
def settlement_details(request, group, settlement, is_admin=False):
    """Show settlement summary"""

    # Pass on to generic view
    response = object_detail(request,
        Settlement.objects.select_related(),
        settlement.id,
        template_name='accounting/settlement_details.html',
        extra_context={
            'is_admin': is_admin,
            'group': group,
        },
        template_object_name='settlement')
    populate_xheaders(request, response, Settlement, settlement.id)
    return response

@login_required
@limit_to_group
def transaction_list(request, group, account=None, page='1',
    is_admin=False, is_owner=False):
    """Lists a group or an account's transactions"""

    # FIXME: Incorporate into decorator. Jodal has an idea on this one.
    if account and not is_owner and not is_admin:
        return HttpResponseForbidden(
            _('Forbidden if not account owner or group admin.'))

    transaction_list = (account or group).transaction_set_with_rejected.select_related()

    if account:
        transaction_list = transaction_list.filter(entry_set__account=account)

    # Pass on to generic view
    response = object_list(request,
        transaction_list,
        paginate_by=20,
        page=page,
        allow_empty=True,
        template_name='accounting/transaction_list.html',
        extra_context={
            'is_admin': is_admin,
            'is_owner': is_owner,
            'group': group,
            'account': account,
            'user_account': group.account_set.get(owner=request.user),
        },
        template_object_name='transaction')
    populate_xheaders(request, response, Group, group.id)
    return response

@login_required
def transaction_details(request, group, transaction, is_admin=False):
    """Shows all details about a transaction"""

    # Check that user is party of transaction or admin of group
    # FIXME: Do this with a decorator. Jodal has an idea on this one.
    if not is_admin and TransactionEntry.objects.filter(
        transaction=transaction,
        account__owner__id=request.user.id).count() == 0:
        return HttpResponseForbidden(_('The transaction may only be'
            + 'viewed by group admins or a party of the transaction.'))

    # Pass on to generic view
    response = object_detail(request,
        Transaction.objects.all(),
        transaction.id,
        template_name='accounting/transaction_details.html',
        extra_context={
            'is_admin': is_admin,
            'group': group,
        },
        template_object_name='transaction')
    populate_xheaders(request, response, Transaction, transaction.id)
    return response
