from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    (r'^admin/', include('django.contrib.admin.urls')),

    # View for magic i18n translation of js
    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog',
        {'packages': ('itkufs',)}, name='jsi18n'),
    (r'^i18n/', include('django.conf.urls.i18n')),

    (r'^inventory/', include('itkufs.inventory.urls')),
    (r'^', include('itkufs.accounting.urls')),


    # Only reached using test server, but always used
    # for reverse lookup of URLs from views and templates
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}, name='media'),
)
