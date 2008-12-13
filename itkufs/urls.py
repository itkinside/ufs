from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
from django.contrib import databrowse
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User

from itkufs import admin
databrowse.site.register(User)

if 'itkufs.accounting' in settings.INSTALLED_APPS:
    import itkufs.accounting.admin
    import itkufs.accounting.data

if 'itkufs.reports' in settings.INSTALLED_APPS:
    import itkufs.reports.admin
    import itkufs.reports.data

urlpatterns = patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/(.*)', admin.site.root),
    (r'^databrowse/(.*)',
        user_passes_test(lambda u: u.is_superuser)(databrowse.site.root)),

    # View for magic i18n translation of js
    url(r'^i18n/js/$', 'django.views.i18n.javascript_catalog',
        {'packages': ['itkufs']}, name='jsi18n'),
    (r'^i18n/', include('django.conf.urls.i18n')),

    (r'^', include('itkufs.common.urls')),
    (r'^', include('itkufs.accounting.urls')),
    (r'^', include('itkufs.reports.urls')),

    # Only reached using test server, but always used
    # for reverse lookup of URLs from views and templates
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}, name='media')
)
