from django.conf.urls.defaults import *
from django.views.generic import create_update

from itkufs.reports.views import *

urlpatterns = patterns('',
    # Lists
    url(r'^(?P<group>[0-9a-z_-]+)/list/add/$',
        alter_list, {'type': 'new'}, name='new-list'),
    url(r'^(?P<group>[0-9a-z_-]+)/list/(?P<slug>[0-9a-z_-]+)/edit/$',
        alter_list, {'type': 'edit'}, name='edit-list'),
    url(r'^(?P<group>[0-9a-z_-]+)/list/(?P<slug>[0-9a-z_-]+)/delete/$',
        alter_list, {'type': 'delete'}, name='delete-list'),

    url(r'^(?P<group>[0-9a-z_-]+)/list/(?P<list>[0-9a-z_-]+)/$',
        show_list, name='view-list'),

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
