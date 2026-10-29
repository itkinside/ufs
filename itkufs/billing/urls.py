from django.urls import re_path

from itkufs.billing.views import (
    bill_create_transaction,
    bill_delete,
    bill_details,
    bill_list,
    bill_new_edit,
    bill_pdf,
)

urlpatterns = [
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/billing/new/$", bill_new_edit, name="bill-new"
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/billing/(?P<bill>\d+)/edit/$",
        bill_new_edit,
        name="bill-edit",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/billing/(?P<bill>\d+)/transaction/$",
        bill_create_transaction,
        name="bill-create-transaction",
    ),
    re_path(r"^(?P<group>[0-9a-z_-]+)/billing/$", bill_list, name="bill-list"),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/billing/(?P<bill>\d+)/$",
        bill_details,
        name="bill-details",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/billing/(?P<bill>\d+)/pdf/$",
        bill_pdf,
        name="bill-pdf",
    ),
    re_path(
        r"^(?P<group>[0-9a-z_-]+)/billing/(?P<bill>\d+)/delete/$",
        bill_delete,
        name="bill-delete",
    ),
]
