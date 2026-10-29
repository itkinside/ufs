from django.urls import re_path

from itkufs.common.views import login_user, switch_group
from itkufs.common.views.display import (
    account_summary,
    group_summary,
    group_balance_graph,
    export_transactions,
)
from itkufs.common.views.edit import (
    activate_account,
    assign_role_accounts,
    edit_group,
    new_edit_account,
)

urlpatterns = [
    # --- Index and login
    re_path(r"^$", login_user, name="index"),
    re_path(r"login/$", login_user, name="login"),
    re_path(r"^switch-group/$", switch_group, name="switch-group"),
    # --- Groups
    re_path(r"^(?P<group>[0-9a-z_-]+)/$", group_summary, name="group-summary"),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/export$",
        export_transactions,
        name="export-transactions",
    ),
    re_path(r"^(?P<group>[0-9a-z_-]+)/edit/$", edit_group, name="edit-group"),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/assign-role-accounts/$",
        assign_role_accounts,
        name="assign-role-accounts",
    ),
    # --- Accounts
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/$",
        account_summary,
        name="account-summary",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/new-account/$",
        new_edit_account,
        name="new-account",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/edit/$",
        new_edit_account,
        name="edit-account",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/activate/$",
        activate_account,
        name="activate-account",
    ),
    # --- Graphs
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/graphs/group-balance/$",
        group_balance_graph,
        name="group-balance-graph",
    ),
]
