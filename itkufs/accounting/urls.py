from django.conf.urls.defaults import *
from itkufs.accounting.views import *

urlpatterns = patterns('',
    # Account list
    url(r'^$',
        account_list, name='account-list'),

    # My account
    url(r'^(?P<account_group>[0-9a-z_-]+)/(?P<account>\w+)/(?P<page>\d*)$',
        account_summary, name='account-summary'),
    url(r'(?P<account_group>[0-9a-z_-]+)/(?P<account>\d+)/deposit/$',
        transfer, {'transfer_type': 'deposit'}, name='account-deposit'),
    url(r'(?P<account_group>[0-9a-z_-]+)/(?P<account>\d+)/withdraw/$',
        transfer, {'transfer_type': 'withdraw'}, name='account-withdraw'),
    url(r'(?P<account_group>[0-9a-z_-]+)/(?P<account>\d+)/transfer/$',
        transfer, {'transfer_type': 'transfer'}, name='account-transfer'),

    # Print lists
    url(r'(?P<account_group>[0-9a-z_-]+)/list/$',
        list, name='list-select'),
    url(r'(?P<account_group>[0-9a-z_-]+)/list/internal/$',
        list, {'list_type': 'internal'}, name='list-internal'),
    url(r'(?P<account_group>[0-9a-z_-]+)/list/external/$',
        list, {'list_type': 'external'}, name='list-external'),


    # Admin: Account group summary
    url(r'^(?P<account_group>[0-9a-z_-]+)/$',
        account_group_summary, name='account-group-summary'),

    # Admin: Transactions
    # FIXME

    # Admin: Settlements
    # FIXME

    # Admin: Balance
    # FIXME
)
