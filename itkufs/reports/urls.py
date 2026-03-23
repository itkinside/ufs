from django.urls import re_path

from itkufs.reports.views import (
    balance,
    delete_list,
    income,
    new_edit_list,
    transaction_from_list,
    view_list,
    view_list_preview,
)

urlpatterns = [
    # --- Lists
    re_path(r"^(?P<group>[0-9a-z_-]+)/list/new/$", new_edit_list, name="new-list"),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/list/(?P<list>[0-9a-z_-]+)/$",
        view_list,
        name="view-list",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/list/(?P<list>[0-9a-z_-]+)/preview/$",
        view_list_preview,
        name="view-list-preview",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/list/(?P<list>[0-9a-z_-]+)/edit/$",
        new_edit_list,
        name="edit-list",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/list/(?P<list>[0-9a-z_-]+)/delete/$",
        delete_list,
        name="delete-list",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/list/(?P<list>[0-9a-z_-]+)/transaction/$",
        transaction_from_list,
        name="transaction-from-list",
    ),
    # --- Statements
    re_path(r"^(?P<group>[0-9a-z_-]+)/balance/$", balance, name="balance"),
    re_path(r"^(?P<group>[0-9a-z_-]+)/income/$", income, name="income"),
]
