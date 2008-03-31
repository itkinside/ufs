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
        extra_context={'is_admin': is_admin, 'all': 'all' in request.GET})
    populate_xheaders(request, response, Group, group.id)
    return response

@login_required
@limit_to_owner
def account_summary(request, group, account,
    is_admin=False, is_owner=False):
    """Show account summary"""

    if is_owner:
        # Check if active
        if not account.active and not is_admin:
            return HttpResponseForbidden(_('This account is inactive.'))

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

