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
    url(r'^switch-group/$',
        switch_group, name='switch-group'),

    # Help
    url(r'help/$',
        static_page, {'template': 'common/help.html'}, name='help'),

    ### Groups
    url(r'^(?P<group>[0-9a-z_-]+)/$',
        group_summary, name='group-summary'),
    url(r'^(?P<group>[0-9a-z_-]+)/edit/$',
        edit_group, name='edit-group'),
    url(r'^(?P<group>[0-9a-z_-]+)/assign-role-accounts/$',
        assign_role_accounts, name='assign-role-accounts'),

    ### Accounts
    url(r'^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/$',
        account_summary, name='account-summary'),
    url(r'^(?P<group>[0-9a-z_-]+)/new-account/$',
        new_edit_account, name='new-account'),
    url(r'^(?P<group>[0-9a-z_-]+)/account/(?P<account>[0-9a-z_-]+)/edit/$',
        new_edit_account, name='edit-account'),
)
