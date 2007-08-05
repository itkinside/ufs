from django.contrib.auth import authenticate, login
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.generic.list_detail import object_list

from itkufs.accounting.models import *
from itkufs.accounting.forms import *

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

    if not request.user.is_authenticated():
        # FIXME: Redirect to login page
        return HttpResponseForbidden('Forbidden')

    return render_to_response('accounting/base.html', {'user': request.user})

def group_list(request):
    """Lists the user's account groups and accounts, including admin accounts"""

    if not request.user.is_authenticated():
        user = authenticate(request=request)
        if user is not None:
            login(request, user)
        else:
            # FIXME: Redirect to login page
            return HttpResponseForbidden('Forbidden')

    # Build account struct
    accounts = []
    for account in request.user.account_set.all().order_by('group', 'name'):
        is_admin = bool(account.group.admins.filter(
            username=request.user.username).count())
        accounts.append((account, is_admin))

    # If only one account, jump directly to account summary
    if len(accounts) == 1:
        url = reverse('account-summary',
                      kwargs={'group': accounts[0][0].group.slug,
                              'account': accounts[0][0].slug})
        return HttpResponseRedirect(url)

    return render_to_response('accounting/group_list.html',
                              {'my_user': request.user,
                               'accounts': accounts})

def group_summary(request, group):
    """Account group summary and paginated list of accounts"""

    my_account = get_session_object(request, 'account')
    if not request.user.is_authenticated() or not my_account:
        # FIXME: Redirect to login page
        return HttpResponseForbidden('Forbidden')

    # Get account group
    try:
        group = AccountGroup.objects.get(slug=group)
    except AccountGroup.DoesNotExist:
        raise Http404

    if group.admins.filter(id=request.user.id).count():
        is_admin = True
    else:
        is_admin = False

    return render_to_response('accounting/group_summary.html',
                              {'my_account': my_account,
                               'is_admin': is_admin,
                               'group': group})

def account_summary(request, group, account, page='1'):
    """Account details and a paginated list with recent transactions involving the user"""

    if not request.user.is_authenticated():
        # FIXME: Redirect to login page
        #return HttpResponseForbidden('Forbidden')
        pass

    # Get account object
    try:
        group = AccountGroup.objects.get(slug=group)
        account = group.account_set.get(slug=account)
    except (AccountGroup.DoesNotExist, Account.DoesNotExist):
        raise Http404

    # Save account in session
    my_account = get_session_object(request, 'account')
    if not my_account:
        # FIXME: For now, we only save account selection the first time
        set_session_object(request, 'account', account)

    # Check that user is owner of account or admin of account group
    if group.admins.filter(id=request.user.id).count():
        is_admin = True
    elif request.user.id == account.owner.id:
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
                            'my_account': my_account,
                            'is_admin': is_admin,
                            'account': account,
                       },
                       template_object_name='transaction')

def transfer(request, group, account, transfer_type=None):
    """Deposit, withdraw or transfer money"""

    my_account = get_session_object(request, 'account')
    if not request.user.is_authenticated() or not my_account:
        # FIXME: Redirect to login page
        return HttpResponseForbidden('Forbidden')

    # Get account object
    try:
        group = AccountGroup.objects.get(slug=group)
        account = group.account_set.get(slug=account)
    except (AccountGroup.DoesNotExist, Account.DoesNotExist):
        raise Http404

    if group.admins.filter(id=request.user.id).count():
        is_admin = True
    else:
        is_admin = False

    return render_to_response('accounting/transfer.html',
                              {'my_account': my_account,
                               'is_admin': is_admin,
                               'account': account})
