from django.conf.urls.defaults import *
from itkufs.common.views import *

urlpatterns = patterns('',
    # Login
    url(r'login/$',
        login_user, name='login'),

    # Account list
    url(r'^$',
        group_list, name='group-list'),

    # Account summary
    url(r'^(?P<group>[0-9a-z_-]+)/a/(?P<account>[0-9a-z_-]+)/$',
        account_summary, name='account-summary'),
    url(r'^(?P<group>[0-9a-z_-]+)/a/(?P<account>[0-9a-z_-]+)/(?P<page>\d+)/$',
        account_summary, name='account-summary-page'),

    url(r'^(?P<group>[0-9a-z_-]+)/add/$',
        alter_account, {'type': 'new'}, name='new-account'),
    url(r'^(?P<group>[0-9a-z_-]+)/a/(?P<account>[0-9a-z_-]+)/edit/$',
        alter_account, {'type': 'edit'}, name='edit-account'),

    # Help
    url(r'^(?P<group>[0-9a-z_-]+)/help/$',
        static_page, {'template': 'accounting/help.html'}, name='help'),

    # Group summary
    url(r'^(?P<group>[0-9a-z_-]+)/$',
        group_summary, name='group-summary'),
    url(r'^(?P<group>[0-9a-z_-]+)/(?P<page>\d+)/$',
        group_summary, name='group-summary-page'),

    # Edit group
    url(r'^(?P<group>[0-9a-z_-]+)/edit/$',
        alter_group, name='edit-group'),
)
