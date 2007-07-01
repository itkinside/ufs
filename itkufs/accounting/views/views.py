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

def test_view(request):
    """Temporary test view"""

    user = get_session_object(request, 'user')
    if not user:
        # FIXME: Redirect to login page
        return HttpResponseForbidden('Forbidden')

    return render_to_response('accounting/base.html', {'user': user})

def group_list(request):
    """Lists the user's account groups and accounts, including admin accounts"""

    # FIXME: Dev hack
    user = User.objects.get(username='jodal')
    set_session_object(request, 'user', user)

    user = get_session_object(request, 'user')
    if not user:
        # FIXME: Redirect to login page
        return HttpResponseForbidden('Forbidden')

    # Build account struct
    accounts = []
    for account in user.account_set.all().order_by('group', 'name'):
        is_admin = bool(account.group.admins.filter(
            username=user.username).count())
        accounts.append((account, is_admin))

    return render_to_response('accounting/group_list.html',
                              {'user': user,
                              'accounts': accounts})

def group_summary(request, group):
    """Account group summary and paginated list of accounts"""

    user = get_session_object(request, 'user')
    if not user:
        # FIXME: Redirect to login page
        return HttpResponseForbidden('Forbidden')

    # Get account group
    try:
        group = AccountGroup.objects.get(slug=group)
    except AccountGroup.DoesNotExist:
        raise Http404

    if group.admins.filter(id=user.id).count():
        is_admin = True
    else:
        is_admin = False

    return render_to_response('accounting/group_summary.html',
                              {'group': group,
                               'is_admin': is_admin})

def account_summary(request, group, account, page='1'):
    """Account details and a paginated list with recent transactions involving the user"""

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
        is_admin = False
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
    return test_view(request)

