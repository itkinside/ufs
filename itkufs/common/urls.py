from django.conf.urls.defaults import *

from itkufs.common.views import *
from itkufs.common.views.display import *
from itkufs.common.views.edit import *

urlpatterns = patterns('',
    # Index and login
    url(r'^$',
        login_user, name='index'),
    url(r'login/$',
        login_user, name='login'),
    url(r'^account-switch/$',
        account_switch, name='account-switch'),

    # Help
    url(r'help/$',
        static_page, {'template': 'common/help.html'}, name='help'),


    ### Groups
    url(r'^(?P<group>[0-9a-z_-]+)/$',
        group_summary, name='group-summary'),
    url(r'^(?P<group>[0-9a-z_-]+)/edit/$',
        edit_group, name='edit-group'),

    ### Accounts
    url(r'^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/$',
        account_summary, name='account-summary'),
    url(r'^(?P<group>[0-9a-z_-]+)/new-account/$',
        edit_account, {'type': 'new'}, name='new-account'),
    url(r'^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/edit/$',
        edit_account, {'type': 'edit'}, name='edit-account'),
)
