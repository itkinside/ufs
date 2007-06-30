from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.generic.list_detail import object_list

from itkufs.accounting.models import *

def account_list(request):
    """Lists the users account groups and accounts, including admin accounts"""

    # FIXME
    username = 'jodal'
    user = User.objects.get(username=username)
    account = user.account_set.all()[0]
    admin = account.group.admins.filter(username=username).count()

    return render_to_response('accounting/base.html',
                              {'account': account,
                               'admin': admin})

def account_group_summary(request, account_group):
    """Shows a summery for the account group"""

    # FIXME
    return account_list(request)

def account_summary(request, account_group, account, page='1'):
    """A paginated list with recent transactions involving the user"""

    # FIXME: Check that user is owner of account or admin of account group

    try:
        account = Account.objects.get(id=account)
    except Account.DoesNotExist:
        raise Http404

    # FIXME: Use username from request to check admin status
    if account.owner:
        admin = account.group.admins.filter(username=account.owner.username).count()
    else:
        admin = False

    transactions = Transaction.objects.filter(
        Q(from_account=account) | Q(to_account=account)).order_by('-registered')

    return object_list(request, transactions,
                       paginate_by=20,
                       page=page,
                       allow_empty=True,
                       template_name='accounting/account_summary.html',
                       extra_context={
                            'account': account,
                            'admin': admin,
                       },
                       template_object_name='transaction')

def transfer(request, account_group, account, transfer_type=None):
    """Deposit, withdraw or transfer money"""

    # FIXME
    return account_list(request)

def list(request, account_group, list_type=None):
    """Print internal and external lists"""

    # FIXME
    return account_list(request)
