from django.conf.urls.defaults import *
from django.contrib import databrowse

from itkufs.reports.views import *

databrowse.site.register(List)
databrowse.site.register(ListColumn)

urlpatterns = patterns('',
    ### Lists
    url(r'^(?P<group>[0-9a-z_-]+)/list/(?P<list>[0-9a-z_-]+)/$',
        pdf, name='view-list'),
    url(r'^(?P<group>[0-9a-z_-]+)/new-list/$',
        new_edit_list, name='new-list'),
    url(r'^(?P<group>[0-9a-z_-]+)/list/(?P<list>[0-9a-z_-]+)/edit/$',
        new_edit_list, name='edit-list'),
    url(r'^(?P<group>[0-9a-z_-]+)/list/(?P<list>[0-9a-z_-]+)/delete/$',
        delete_list, name='delete-list'),

    ### Statements
    url(r'^(?P<group>[0-9a-z_-]+)/balance/$',
        balance, name='balance'),
    url(r'^(?P<group>[0-9a-z_-]+)/income/$',
        income, name='income'),
)
