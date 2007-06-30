from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    (r'^ufs/admin/', include('django.contrib.admin.urls')),
    (r'^ufs/inventory/', include('itkufs.inventory.urls')),
    (r'^ufs/', include('itkufs.accounting.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^ufs/media/(?P<path>.*)$',
            'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT},
            name='media'),
    )
