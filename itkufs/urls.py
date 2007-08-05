from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    (r'^ufs/admin/', include('django.contrib.admin.urls')),
    (r'^ufs/inventory/', include('itkufs.inventory.urls')),
    (r'^ufs/', include('itkufs.accounting.urls')),

    # Only reached using test server, but always used
    # for reverse lookup of URLs from views and templates
    url(r'^ufs/media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}, name='media'),
)
