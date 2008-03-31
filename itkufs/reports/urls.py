from django.conf.urls.defaults import *
from django.contrib import databrowse

from itkufs.reports.views import *

databrowse.site.register(List)
databrowse.site.register(ListColumn)

urlpatterns = patterns('',
    ### Lists
    url(r'^(?P<group>[0-9a-z_-]+)/list/(?P<list>[0-9a-z_-]+)/$',
        view_list, name='view-list'),
    url(r'^(?P<group>[0-9a-z_-]+)/new-list/$',
        new_edit_list, {'type': 'new'}, name='new-list'),
    url(r'^(?P<group>[0-9a-z_-]+)/edit-list/(?P<list>[0-9a-z_-]+)/$',
        new_edit_list, {'type': 'edit'}, name='edit-list'),
    url(r'^(?P<group>[0-9a-z_-]+)/delete-list/(?P<list>[0-9a-z_-]+)/$',
        delete_list, name='delete-list'),

    ### Statements
    url(r'^(?P<group>[0-9a-z_-]+)/balance/$',
        balance, name='balance'),
    url(r'^(?P<group>[0-9a-z_-]+)/income/$',
        income, name='income'),
)
