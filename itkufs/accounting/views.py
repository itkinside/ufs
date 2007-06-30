from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response

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

def account_summary(request, account_group, account):
    """Shows a summary for the account"""

    # FIXME
    return account_list(request)

def transfer(request, account_group, account, transfer_type=None):
    """Deposit, withdraw or transfer money"""

    # FIXME
    return account_list(request)

def list(request, account_group, list_type=None):
    """Print internal and external lists"""

    # FIXME
    return account_list(request)
