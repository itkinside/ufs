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
@limit_to_admin
def settlement_list(request, group, page='1', is_admin=False):
    """Show paginated list of settlements"""

    pass # TODO: Implement using object_list

@login_required
@limit_to_admin
def settlement_details(request, group, settlement, is_admin=False):
    """Show settlement summary"""

    pass # TODO: At least show all transactions related to a settlement

@login_required
@limit_to_group
def transaction_list(request, group, account=None, page='1',
    is_admin=False, is_owner=False):
    """Lists a group or an account's transactions"""

    if account and not is_owner and not is_admin:
        # FIXME: Incorporate into decorator. Jodal has an idea on this one.
        return HttpResponseForbidden(
            _('Forbidden if not account owner or group admin.'))

    # Get transactions
    transactions = (account or group).transaction_set_with_rejected

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
    # FIXME: Do this with a decorator. Jodal has an idea on this one.
    if not is_admin and TransactionEntry.objects.filter(
        transaction__id=transaction,
        account__owner__id=request.user.id).count() == 0:
        return HttpResponseForbidden(_('The transaction may only be'
            ' viewed by group admins or a party of the transaction.'))

    # Pass on to generic view
    response = object_detail(request,
        Transaction.objects.all(),
        transaction,
        template_name='accounting/transaction_details.html',
        extra_context={
            'is_admin': is_admin,
            'group': group,
        },
        template_object_name='transaction')
    populate_xheaders(request, response, Transaction, transaction)
    return response
