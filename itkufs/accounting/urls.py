from django.urls import re_path

from itkufs.accounting.views.edit import (
    new_edit_settlement,
    new_edit_transaction,
    approve_transactions,
    reject_transactions,
    transfer,
)
from itkufs.accounting.views.display import (
    SettlementDetails,
    SettlementList,
    TransactionDetails,
    TransactionList,
    APIAccountDetails,
)

urlpatterns = [
    # --- Settlements
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/settlement/(?P<settlement>\d+)/$",
        SettlementDetails.as_view(),
        name="settlement-details",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/new-settlement/$",
        new_edit_settlement,
        name="new-settlement",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/settlement/(?P<settlement>\d+)/edit/$",
        new_edit_settlement,
        name="edit-settlement",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/settlement/$",
        SettlementList.as_view(),
        name="settlement-list",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/settlement/p(?P<page>\d+)/$",
        SettlementList.as_view(),
        name="settlement-list-page",
    ),
    # --- Transactions
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/transaction/(?P<transaction>\d+)/$",
        TransactionDetails.as_view(),
        name="transaction-details",
    ),
    # Admin transaction actions
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/transaction/new/$",
        new_edit_transaction,
        name="new-transaction",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/transaction/(?P<transaction>\d+)/edit/$",
        new_edit_transaction,
        name="edit-transaction",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/approve-transaction/$",
        approve_transactions,
        name="approve-transactions",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/reject-transaction/$",
        reject_transactions,
        name="reject-transactions",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/transaction/(?P<transaction>\d+)/reject/$",
        reject_transactions,
        name="reject-transaction",
    ),
    # User transaction actions
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/deposit/$",
        transfer,
        {"transfer_type": "deposit"},
        name="account-deposit",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/withdraw/$",
        transfer,
        {"transfer_type": "withdraw"},
        name="account-withdraw",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/transfer/$",
        transfer,
        {"transfer_type": "transfer"},
        name="account-transfer",
    ),
    # Group transaction lists
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/transaction/$",
        TransactionList.as_view(),
        name="transaction-list-group",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/transaction/p(?P<page>\d+)/$",
        TransactionList.as_view(),
        name="transaction-list-group-page",
    ),
    # Account transaction lists
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/account/"
        r"(?P<account>[0-9a-z_-]+)/transaction/$",
        TransactionList.as_view(),
        name="transaction-list-account",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/account/"
        r"(?P<account>[0-9a-z_-]+)/transaction/p(?P<page>\d+)/$",
        TransactionList.as_view(),
        name="transaction-list-account-page",
    ),
    re_path(r"^(?P<group>[0-9a-z_-]+)/api/accounts/$",
        APIAccountDetails.as_view(),
        name="account-list"
    ),
]
