from django.conf.urls.defaults import *
from itkufs.accounting.views import *

# Setup which classes can be used with databrowse...
from django.contrib.auth.decorators import user_passes_test
from django.contrib import databrowse
databrowse.site.register(Group)
databrowse.site.register(Account)
databrowse.site.register(List)
databrowse.site.register(ListItem)
databrowse.site.register(NewTransaction)
databrowse.site.register(TransactionLog)
databrowse.site.register(TransactionEntry)

urlpatterns = patterns('',
    # Superuser can use databrowse :)
    (r'^databrowse/(.*)',  user_passes_test(lambda u: u.is_superuser)(databrowse.site.root)),

    # Login
    url(r'login/$',
        login_user, name='login'),

    # Account list
    url(r'^$',
        group_list, name='group-list'),

    # Account summary
    url(r'^(?P<group>[0-9a-z_-]+)/a/(?P<account>[0-9a-z_-]+)/$',
        account_summary, name='account-summary'),
    url(r'^(?P<group>[0-9a-z_-]+)/a/(?P<account>[0-9a-z_-]+)/(?P<page>\d+)/$',
        account_summary, name='account-summary-page'),

    # Account actions
    url(r'^(?P<group>[0-9a-z_-]+)/a/(?P<account>[0-9a-z_-]+)/deposit/$',
        transfer, {'transfer_type': 'deposit'}, name='account-deposit'),
    url(r'^(?P<group>[0-9a-z_-]+)/a/(?P<account>[0-9a-z_-]+)/withdraw/$',
        transfer, {'transfer_type': 'withdraw'}, name='account-withdraw'),
    url(r'^(?P<group>[0-9a-z_-]+)/a/(?P<account>[0-9a-z_-]+)/transfer/$',
        transfer, {'transfer_type': 'transfer'}, name='account-transfer'),

    # Help
    url(r'^(?P<group>[0-9a-z_-]+)/help/$',
        static_page, {'template': 'accounting/help.html'}, name='help'),

    # Group summary
    url(r'^(?P<group>[0-9a-z_-]+)/$',
        group_summary, name='group-summary'),
    url(r'^(?P<group>[0-9a-z_-]+)/(?P<page>\d+)/$',
        group_summary, name='group-summary-page'),

    # Lists
    url(r'^(?P<group>[0-9a-z_-]+)/list/(?P<slug>[0-9a-z_-]+)/$',
        html_list, name='view-list'),
    url(r'^(?P<group>[0-9a-z_-]+)/list/(?P<slug>[0-9a-z_-]+)/new/$',
        html_list, name='new-list'),
    url(r'^(?P<group>[0-9a-z_-]+)/list/(?P<slug>[0-9a-z_-]+)/edit/$',
        html_list, name='edit-list'),
    url(r'^(?P<group>[0-9a-z_-]+)/list/(?P<slug>[0-9a-z_-]+)/delete/$',
        html_list, name='delete-list'),

    # Admin: Transactions
    url(r'^(?P<group>[0-9a-z_-]+)/approve/$',
        approve, name='approve-transactions'),
    url(r'^(?P<group>[0-9a-z_-]+)/approve/(?P<page>\d+)/$',
        approve, name='approve-transactions-page'),
    url(r'^(?P<group>[0-9a-z_-]+)/register/$',
        transfer, {'transfer_type': 'register'}, name='register-transactions'),

    # Admin: Settlements
    url(r'^(?P<group>[0-9a-z_-]+)/settlement/$',
        settlement_summary, name='settlement-summary'),
    url(r'^(?P<group>[0-9a-z_-]+)/settlement/(?P<page>\d+)/$',
        settlement_summary, name='settlement-summary-page'),

    # Admin: Statements
    url(r'^(?P<group>[0-9a-z_-]+)/balance/$',
        balance, name='balance'),
    url(r'^(?P<group>[0-9a-z_-]+)/income/$',
        income, name='income'),
)
