from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    (r'^admin/', include('django.contrib.admin.urls')),
    (r'^inventory/', include('itkufs.inventory.urls')),
    (r'^', include('itkufs.accounting.urls')),

    # Only reached using test server, but always used
    # for reverse lookup of URLs from views and templates
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}, name='media'),
)
