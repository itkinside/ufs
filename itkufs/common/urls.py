from django.conf.urls.defaults import *
from itkufs.common.views import *

urlpatterns = patterns('',
    # Login
    url(r'login/$',
        login_user, name='login'),

    # Account list
    url(r'^$',
        login_user, name='index'),

    # Help
    url(r'^(?P<group>[0-9a-z_-]+)/help/$',
        static_page, {'template': 'accounting/help.html'}, name='help'),
)
