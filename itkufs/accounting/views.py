from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.generic.list_detail import object_list

from itkufs.accounting.models import *

# Session functions

def set_session_object(request, key, object):
    """Add object to session"""

    if not key in request.session:
        request.session[key] = object
        return True
    else:
        return False

def get_session_object(request, key):
    """Get object from session"""

    if key in request.session:
        return request.session[key]
    else:
        return None

# Views

def account_list(request):
    """Lists the users account groups and accounts, including admin accounts"""

     # FIXME: Dev hack
    user = User.objects.get(username='klette')
    set_session_object(request, 'user', user)

    user = get_session_object(request, 'user')
    if not user:
        # FIXME: Redirect to login page
        return HttpResponseForbidden('Forbidden')

    account = user.account_set.all()[0] # FIXME: Dev hack
    is_admin = account.group.admins.filter(username=user.username).count()

    return render_to_response('accounting/base.html',
                              {'account': account,
                               'is_admin': is_admin})

def group_summary(request, group):
    """Shows a summery for the account group"""

    user = get_session_object(request, 'user')
    if not user:
        # FIXME: Redirect to login page
        return HttpResponseForbidden('Forbidden')

    # FIXME
    return account_list(request)

def account_summary(request, group, account, page='1'):
    """A paginated list with recent transactions involving the user"""

    user = get_session_object(request, 'user')
    if not user:
        # FIXME: Redirect to login page
        return HttpResponseForbidden('Forbidden')

    # Get account object
    try:
        account = Account.objects.get(slug=account)
    except Account.DoesNotExist:
        raise Http404

    # Check that user is owner of account or admin of account group
    if account.group.admins.filter(id=user.id).count():
        is_admin = True
    elif user.id == acount.owner.id:
        pass # Account owner
    else:
        return HttpResponseForbidden('Forbidden')

    # Get related transactions
    transactions = Transaction.objects.filter(
        Q(from_account=account) | Q(to_account=account)).order_by('-registered')

    return object_list(request, transactions,
                       paginate_by=20,
                       page=page,
                       allow_empty=True,
                       template_name='accounting/account_summary.html',
                       extra_context={
                            'account': account,
                            'is_admin': is_admin,
                       },
                       template_object_name='transaction')

def transfer(request, group, account, transfer_type=None):
    """Deposit, withdraw or transfer money"""

    user = get_session_object(request, 'user')
    if not user:
        # FIXME: Redirect to login page
        return HttpResponseForbidden('Forbidden')

    # FIXME
    return account_list(request)

def list(request, group, list_type=None):
    """Print internal and external lists"""
    username = 'klette'
    user = User.objects.get(username=username)
    account = user.account_set.all()[0]
    admin = account.group.admins.filter(username=username).count()

    user = get_session_object(request, 'user')
    if not user:
        # FIXME: Redirect to login page
        return HttpResponseForbidden('Forbidden')

    # FIXME
    return render_to_response('accounting/internal_list.html',
                                {'group': account_group,
                                 'admin': admin})
