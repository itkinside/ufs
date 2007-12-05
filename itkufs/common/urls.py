from django.conf.urls.defaults import *
from itkufs.common.views import *

urlpatterns = patterns('',
    # Index and login
    url(r'^$',
        login_user, name='index'),
    url(r'login/$',
        login_user, name='login'),

    # Help
    url(r'^(?P<group>[0-9a-z_-]+)/help/$',
        static_page, {'template': 'accounting/help.html'}, name='help'),
)
