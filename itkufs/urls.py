from django.conf.urls import *
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User

from itkufs import admin

if 'itkufs.accounting' in settings.INSTALLED_APPS:
    import itkufs.accounting.admin

if 'itkufs.reports' in settings.INSTALLED_APPS:
    import itkufs.reports.admin

urlpatterns = patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),

    # View for magic i18n translation of js
    url(r'^i18n/js/$', 'django.views.i18n.javascript_catalog',
        {'packages': ['itkufs']}, name='jsi18n'),
    (r'^i18n/', include('django.conf.urls.i18n')),

    # Pull in lists before so that nothing else manages to catch the url
    url(r'^lists/$', 'itkufs.reports.views.public_lists', name="public-lists"),
    url(r'^lists/(?P<group>[0-9a-z_-]+)/(?P<list>[0-9a-z_-]+)/$',
        'itkufs.reports.views.view_public_list', name="view-public-list"),

    (r'^', include('itkufs.common.urls')),
    (r'^', include('itkufs.accounting.urls')),
    (r'^', include('itkufs.billing.urls')),
    (r'^', include('itkufs.reports.urls')),

    # Only reached using test server, but always used
    # for reverse lookup of URLs from views and templates
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}, name='media')
)
