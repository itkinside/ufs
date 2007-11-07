from datetime import date, datetime
from urlparse import urlparse

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _, ungettext
from django.views.generic.list_detail import object_list

from itkufs.accounting.models import *
from itkufs.accounting.forms import *

def login_user(request):
    """Login user"""

    if not request.user.is_authenticated():
        user = authenticate(request=request)
        if user is not None:
            login(request, user)
        else:
            return HttpResponseForbidden(_('Login failed'))

    return HttpResponseRedirect(reverse('group-list'))

@login_required
def group_list(request):
    """Lists the user's account groups and accounts, including admin accounts"""

    # Build account struct
    accounts = []
    for account in request.user.account_set.all().order_by('name'):
        is_admin = bool(account.group.admins.filter(
            username=request.user.username).count())
        accounts.append((account, is_admin))

    # If not coming from inside and user only got one account,
    # jump directly to account summary
    request_from_inside = ('HTTP_REFERER' in request.META and
        urlparse(request.META['HTTP_REFERER'])[2].startswith(reverse('group-list')))
    if len(accounts) == 1 and not request_from_inside:
        url = reverse('account-summary',
                      kwargs={'group': accounts[0][0].group.slug,
                              'account': accounts[0][0].slug})
        return HttpResponseRedirect(url)

    return render_to_response('accounting/group_list.html',
                              {
                                  'accounts': accounts,
                              },
                              context_instance=RequestContext(request))

@login_required
def group_summary(request, group, page='1'):
    """Account group summary and paginated list of accounts"""

    # Get account group
    try:
        group = AccountGroup.objects.get(slug=group)
    except AccountGroup.DoesNotExist:
        raise Http404

    if group.admins.filter(id=request.user.id).count():
        is_admin = True
    else:
        is_admin = False
        return HttpResponseForbidden(_('Sorry, group admins only...'))

    # Get related transactions
    accounts = Account.objects.filter(group=group)
    transactions = Transaction.objects.filter(
        Q(credit_account__in=accounts) |
        Q(debit_account__in=accounts)).order_by('-registered')

    if is_admin and group.has_pending_transactions():
        request.user.message_set.create(
            message=_('You have pending transactions in the group: %s') \
                % group.name)

    # Pass on to generic view
    return object_list(request, transactions,
                       paginate_by=20,
                       page=page,
                       allow_empty=True,
                       template_name='accounting/group_summary.html',
                       extra_context={
                            'is_admin': is_admin,
                            'group': group,
                       },
                       template_object_name='transaction')

@login_required
def account_summary(request, group, account, page='1'):
    """Account details and a paginated list with recent transactions involving
    the user"""

    # Get account object
    try:
        group = AccountGroup.objects.get(slug=group)
        account = group.account_set.get(slug=account)
    except (AccountGroup.DoesNotExist, Account.DoesNotExist):
        raise Http404

    # Save account in session
    # I think it's a bit of hack to switch account when the referrer is the
    # group-list view, but that view is in fact only used for selecting between
    # your own accounts.
    request_from_group_list = ('HTTP_REFERER' in request.META and
        urlparse(request.META['HTTP_REFERER'])[2] == reverse('group-list'))

    if request.user == account.owner:
        request.session['my_account'] = account

    # Check that user is owner of account or admin of account group
    if group.admins.filter(id=request.user.id).count():
        is_admin = True
    elif request.user.id == account.owner.id:
        is_admin = False
    else:
        return HttpResponseForbidden(_('Forbidden'))

    # Get related transactions
    transactions = Transaction.objects.filter(
        Q(credit_account=account) |
        Q(debit_account=account)).order_by('-registered')

    # Warn owner of account about a low balance
    if request.user == account.owner:
        if account.is_blocked():
            request.user.message_set.create(
                message=_('The account balance is below the block limit,'
                + ' please contact the group admin or deposit enough to'
                + ' pass the limit.'))
        elif account.needs_warning():
            request.user.message_set.create(
                message=_('The account balance is below the warning limit.'))

    # Pass on to generic view
    return object_list(request, transactions,
                       paginate_by=20,
                       page=page,
                       allow_empty=True,
                       template_name='accounting/account_summary.html',
                       extra_context={
                            'is_admin': is_admin,
                            'account': account,
                            'group': group,
                       },
                       template_object_name='transaction')

@login_required
def transfer(request, group, account=None, transfer_type=None):
    """Deposit, withdraw or transfer money"""

    # Get account object
    try:
        group = AccountGroup.objects.get(slug=group)
        if transfer_type != 'register':
            account = group.account_set.get(slug=account)
    except (AccountGroup.DoesNotExist, Account.DoesNotExist):
        raise Http404

    if group.admins.filter(id=request.user.id).count():
        is_admin = True
    else:
        is_admin = False

    if request.method == 'POST':
        data = request.POST
    else:
        data = None

    if transfer_type == 'transfer':
        title = _('Transfer from account')
        form = TransferForm(data,
            credit_options={
                'limit_to_groups': [group],
                'user_accounts': True,
                'exclude_accounts': [account],
            })
    elif transfer_type == 'register' and is_admin:
        title = 'This string is not used'
        form = TransactionForm(data,
            debit_options={
                'user_accounts': True,
                'group_accounts': True,
            },
            credit_options={
                'user_accounts': True,
                'group_accounts': True,
            })
    elif transfer_type == 'deposit':
        title = _('Deposit to account')
        form = DepositWithdrawForm(data)
    elif transfer_type == 'withdraw':
        title = _('Withdrawal from account')
        form = DepositWithdrawForm(data)
    else:
        return HttpResponseForbidden(_('Sorry, group admins only...'))

    if request.method == 'POST' and form.is_valid():
        amount = form.cleaned_data['amount']
        details = form.cleaned_data['details'].strip()

        if details == '':
            details = None

        transaction = Transaction(amount=amount, details=details)

        if transfer_type == 'deposit':
            # Deposit to user account

            transaction.credit_account = account
            transaction.debit_account = group.bank_account
            transaction.save()

        elif transfer_type == 'withdraw':
            # Withdraw from user account

            transaction.credit_account = group.bank_account
            transaction.debit_account = account
            transaction.save()

        elif transfer_type == 'transfer':
            # Transfer from user account to other user account

            credit_account = form.cleaned_data['credit_account']

            transaction.credit_account = Account.objects.get(
                id=credit_account)
            transaction.debit_account = account

            if transaction.amount <= account.balance_credit_reversed():
                transaction.payed = datetime.now()

            transaction.save()

        elif transfer_type == 'register' and is_admin:
            # General transaction by group admin

            credit_account = form.cleaned_data['credit_account']
            debit_account = form.cleaned_data['debit_account']

            transaction.credit_account = Account.objects.get(
                id=credit_account)
            transaction.debit_account = Account.objects.get(
                id=debit_account)

            if 'payed' in form.data:
                transaction.payed = datetime.now()

            transaction.save()
            return HttpResponseRedirect(reverse(group_summary,
                args=[group.slug]))
        else:
            return HttpResponseForbidden(_('Sorry, group admins only...'))

        return HttpResponseRedirect(reverse(account_summary,
            args=[account.group.slug, account.slug]))

    return render_to_response('accounting/transfer.html',
                              {
                                  'is_admin': is_admin,
                                  'account': account,
                                  'type': transfer_type,
                                  'title': title,
                                  'form': form,
                                  'group': group,
                              },
                              context_instance=RequestContext(request))

@login_required
def balance(request, group):
    """Show balance sheet for the group"""

    try:
        group = AccountGroup.objects.get(slug=group)
    except AccountGroup.DoesNotExist:
        raise Http404

    if group.admins.filter(id=request.user.id).count():
        is_admin = True
    else:
        return HttpResponseForbidden(_('Sorry, group admins only...'))

    # Balance sheet data struct
    accounts = {
        'As': [], 'AsSum': 0,
        'Li': [], 'LiSum': 0,
        'Eq': [], 'EqSum': 0,
        'LiEqSum': 0,
    }

    # Assets
    for account in group.account_set.filter(type='As'):
        balance = account.balance_credit_reversed()
        accounts['As'].append((account.name, balance))
        accounts['AsSum'] += balance

    # Liabilities
    for account in group.account_set.filter(type='Li', owner__isnull=True):
        balance = account.balance_credit_reversed()
        accounts['Li'].append((account.name, balance))
        accounts['LiSum'] += balance

    # Accumulated member accounts liabilities
    member_balance_sum = sum([a.balance_credit_reversed()
        for a in group.account_set.filter(type='Li', owner__isnull=False)])
    accounts['Li'].append((_('Member accounts'), member_balance_sum))
    accounts['LiSum'] += member_balance_sum

    # Equities
    for account in group.account_set.filter(type='Eq'):
        balance = account.balance_credit_reversed()
        accounts['Eq'].append((account.name, balance))
        accounts['EqSum'] += balance

    # Total liabilities and equities
    accounts['LiEqSum'] = accounts['LiSum'] + accounts['EqSum']

    # Current year's net income
    curr_years_net_income = accounts['AsSum'] - accounts['LiEqSum']
    accounts['Eq'].append((_("Current year's net income"),
                           curr_years_net_income))
    accounts['EqSum'] += curr_years_net_income
    accounts['LiEqSum'] += curr_years_net_income

    return render_to_response('accounting/balance.html',
                              {
                                  'is_admin': is_admin,
                                  'group': group,
                                  'today': date.today(),
                                  'accounts': accounts,
                              },
                              context_instance=RequestContext(request))

@login_required
def income(request, group):
    """Show income statement for group"""

    try:
        group = AccountGroup.objects.get(slug=group)
    except AccountGroup.DoesNotExist:
        raise Http404

    if group.admins.filter(id=request.user.id).count():
        is_admin = True
    else:
        return HttpResponseForbidden(_('Sorry, group admins only...'))

    # Balance sheet data struct
    accounts = {
        'In': [], 'InSum': 0,
        'Ex': [], 'ExSum': 0,
        'InExDiff': 0,
    }

    # Incomes
    for account in group.account_set.filter(type='In'):
        balance = account.balance_credit_reversed()
        accounts['In'].append((account.name, balance))
        accounts['InSum'] += balance

    # Expenses
    for account in group.account_set.filter(type='Ex'):
        balance = account.balance_credit_reversed()
        accounts['Ex'].append((account.name, balance))
        accounts['ExSum'] += balance

    # Net income
    accounts['InExDiff'] = accounts['InSum'] - accounts['ExSum']

    return render_to_response('accounting/income.html',
                              {
                                  'is_admin': is_admin,
                                  'group': group,
                                  'today': date.today(),
                                  'accounts': accounts,
                              },
                              context_instance=RequestContext(request))

@login_required
def html_list(request, group, slug):
    try:
        group = AccountGroup.objects.get(slug=group)
        accounts = Account.objects.filter(group=group)
        list = group.list_set.get(slug=slug)
    except AccountGroup.DoesNotExist, AccountGroup.DoesNotExist:
        raise Http404

    return render_to_response('accounting/list.html',
                              {
                                  'accounts': accounts,
                                  'group': group,
                                  'list': list,
                              },
                              context_instance=RequestContext(request))

@login_required
def approve(request, group, page="1"):
    try:
        group = AccountGroup.objects.get(slug=group)
    except AccountGroup.DoesNotExist:
        raise Http404

    if group.admins.filter(id=request.user.id).count():
        is_admin = True
    else:
        return HttpResponseForbidden(_('Sorry, group admins only...'))

    # Get related transactions
    transactions = Transaction.objects.filter(
        Q(credit_account__group=group) &
        Q(debit_account__group=group) &
        Q(payed__isnull=True)).order_by('-registered')

    if request.method == 'POST':
        count = 0
        for t in transactions:
            if (u'transcation_id_%d' % t.id) in request.POST:
                count += 1
                t.payed = datetime.now()
                t.save()
        request.user.message_set.create(
            message=ungettext('Approved %(count)d transaction.',
                              'Approved %(count)d transactions.', count) %
                             {'count': count})

    transactions = transactions.filter(Q(payed__isnull=True))

    # Pass on to generic view
    return object_list(request, transactions,
                       paginate_by=20,
                       page=page,
                       allow_empty=True,
                       template_name='accounting/approve_transactions.html',
                       extra_context={
                            'is_admin': is_admin,
                            'group': group,
                       },
                       template_object_name='transaction')

@login_required
def settlement_summary(request, group, page="1"):
    try:
        group = AccountGroup.objects.get(slug=group)
    except AccountGroup.DoesNotExist:
        raise Http404

    if group.admins.filter(id=request.user.id).count():
        is_admin = True
    else:
        return HttpResponseForbidden(_('Sorry, group admins only...'))

    # FIXME: Finish view

@login_required
def static_page(request, group, template):
    try:
        group = AccountGroup.objects.get(slug=group)
    except AccountGroup.DoesNotExist:
        raise Http404

    if group.admins.filter(id=request.user.id).count():
        is_admin = True
    else:
        is_admin = False

    return render_to_response(template,
                              {
                                  'group': group,
                                  'is_admin': is_admin,
                              },
                              context_instance=RequestContext(request))
