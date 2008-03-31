from django.conf.urls.defaults import *
from itkufs.accounting.views import *

urlpatterns = patterns('',
    ### Settlements
    url(r'^(?P<group>[0-9a-z_-]+)/settlement/(?P<settlement>\d+)/$',
        settlement_details, name='settlement-summary'),
    url(r'^(?P<group>[0-9a-z_-]+)/new-settlement/$',
        new_edit_settlement, {'type': 'new'}, name='new-settlement'),
    url(r'^(?P<group>[0-9a-z_-]+)/settlement/(?P<settlement>\d+)/edit/$',
        new_edit_settlement, {'type': 'edit'}, name='edit-settlement'),
    url(r'^(?P<group>[0-9a-z_-]+)/settlement/$',
        settlement_list, name='settlement-list'),
    url(r'^(?P<group>[0-9a-z_-]+)/settlement/p(?P<page>\d+)/$',
        settlement_list, name='settlement-list-page'),

    ### Transactions
    url(r'^(?P<group>[0-9a-z_-]+)/transaction/(?P<transaction>\d+)/$',
        transaction_details, name='transaction-details'),

    # Admin transaction actions
    url(r'^(?P<group>[0-9a-z_-]+)/new-transaction/$',
        new_edit_transaction, name='new-transaction'),
    url(r'^(?P<group>[0-9a-z_-]+)/edit-transaction/(?P<transaction>\d+)/$',
        new_edit_transaction, name='edit-transaction'),
    url(r'^(?P<group>[0-9a-z_-]+)/approve-transaction/$',
        approve_transactions, name='approve-transactions'),
    url(r'^(?P<group>[0-9a-z_-]+)/reject_transaction/$',
        reject_transactions, name='reject-transactions'),

    # User transaction actions
    url(r'^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/deposit/$',
        transfer, {'transfer_type': 'deposit'}, name='account-deposit'),
    url(r'^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/withdraw/$',
        transfer, {'transfer_type': 'withdraw'}, name='account-withdraw'),
    url(r'^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/transfer/$',
        transfer, {'transfer_type': 'transfer'}, name='account-transfer'),

    # Group transaction lists
    url(r'^(?P<group>[0-9a-z_-]+)/transaction/$',
        transaction_list, name='transaction-list-group'),
    url(r'^(?P<group>[0-9a-z_-]+)/transaction/p(?P<page>\d+)/$',
        transaction_list, name='transaction-list-group-page'),

    # Account transaction lists
    url(r'^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/transaction/$',
        transaction_list, name='transaction-list-account'),
    url(r'^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/transaction/p(?P<page>\d+)/$',
        transaction_list, name='transaction-list-account-page'),
)
