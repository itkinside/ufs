from django.conf.urls import *

from itkufs.billing.views import *

urlpatterns = patterns('',
    url(r'^(?P<group>[0-9a-z_-]+)/billing/new/$',
        bill_new_edit, name='bill-new'),
    url(r'^(?P<group>[0-9a-z_-]+)/billing/(?P<bill>\d+)/edit/$',
        bill_new_edit, name='bill-edit'),
    url(r'^(?P<group>[0-9a-z_-]+)/billing/(?P<bill>\d+)/transaction/$',
        bill_create_transaction, name='bill-create-transaction'),
    url(r'^(?P<group>[0-9a-z_-]+)/billing/$',
        bill_list, name='bill-list'),
    url(r'^(?P<group>[0-9a-z_-]+)/billing/(?P<bill>\d+)/$',
        bill_details, name='bill-details'),
    url(r'^(?P<group>[0-9a-z_-]+)/billing/(?P<bill>\d+)/pdf/$',
        bill_pdf, name='bill-pdf'),
    url(r'^(?P<group>[0-9a-z_-]+)/billing/(?P<bill>\d+)/delete/$',
        bill_delete, name='bill-delete'),
)
