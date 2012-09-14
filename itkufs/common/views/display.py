from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.xheaders import populate_xheaders
from django.http import HttpResponseForbidden
from django.utils.translation import ugettext as _
from django.views.generic.list_detail import object_detail

from itkufs.common.decorators import limit_to_group, limit_to_owner
from itkufs.accounting.models import *

@login_required
@limit_to_group
def group_summary(request, group, is_admin=False):
    """Show group summary"""

    response = object_detail(request, Group.objects.select_related(), group.id,
        template_name='common/group_summary.html',
        template_object_name='group',
        extra_context={'is_admin': is_admin, 'all': 'all' in request.GET})
    populate_xheaders(request, response, Group, group.id)
    return response

@login_required
@limit_to_owner
def account_summary(request, group, account,
    is_admin=False, is_owner=False):
    """Show account summary"""

    if is_owner:
        # Set active account in session
        request.session['my_account'] = account

        # Warn owner of account about a low balance
        if account.is_blocked():
            messages.error(request, 'The account balance is below the block'
                + ' limit, please contact the group admin or deposit enough to'
                + ' pass the limit.')
        elif account.needs_warning():
            messages.warning(request, 'The account balance is below the'
                + ' warning limit.')

    response = object_detail(request, Account.objects.select_related(), account.id,
        template_name='common/account_summary.html',
        template_object_name='account',
        extra_context={
            'is_admin': is_admin,
            'is_owner': is_owner,
            'group': group,
        })
    populate_xheaders(request, response, Account, account.id)
    return response

