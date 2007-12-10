from django.conf.urls.defaults import *
from itkufs.accounting.views import *

urlpatterns = patterns('',
    ### Group

    # Summary
    url(r'^(?P<group>[0-9a-z_-]+)/$',
        group_summary, name='group-summary'),

    # Edit
    url(r'^(?P<group>[0-9a-z_-]+)/edit/$',
        edit_group, name='edit-group'),

    # Actions
    url(r'^(?P<group>[0-9a-z_-]+)/approve-transaction/$',
        approve_transactions, name='approve-transactions'),
    url(r'^(?P<group>[0-9a-z_-]+)/reject_transaction/$',
        reject_transactions, name='reject-transactions'),
    url(r'^(?P<group>[0-9a-z_-]+)/register-transaction/$',
        transfer, {'transfer_type': 'register'}, name='register-transactions'),
    url(r'^(?P<group>[0-9a-z_-]+)/group-transaction/$',
        create_transaction, name='multiple-transactions'),

    ### Account

    # Summary
    url(r'^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/$',
        account_summary, name='account-summary'),

    # New and edit
    url(r'^(?P<group>[0-9a-z_-]+)/add/$',
        edit_account, {'type': 'new'}, name='new-account'),
    url(r'^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/edit/$',
        edit_account, {'type': 'edit'}, name='edit-account'),

    # User actions
    url(r'^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/deposit/$',
        transfer, {'transfer_type': 'deposit'}, name='account-deposit'),
    url(r'^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/withdraw/$',
        transfer, {'transfer_type': 'withdraw'}, name='account-withdraw'),
    url(r'^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/transfer/$',
        transfer, {'transfer_type': 'transfer'}, name='account-transfer'),

    ### Transactions

    # Group
    url(r'^(?P<group>[0-9a-z_-]+)/transaction/$',
        transaction_list, name='transaction-list-group'),
    url(r'^(?P<group>[0-9a-z_-]+)/transaction/p(?P<page>\d+)/$',
        transaction_list, name='transaction-list-group-page'),

    # Account
    url(r'^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/transaction/$',
        transaction_list, name='transaction-list-account'),
    url(r'^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/transaction/p(?P<page>\d+)/$',
        transaction_list, name='transaction-list-account-page'),

    # Details
    url(r'^(?P<group>[0-9a-z_-]+)/transaction/(?P<transaction>\d+)/$',
        transaction_details, name='transaction-details'),
)
