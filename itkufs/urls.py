from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^admin/', include('django.contrib.admin.urls')),
    (r'^accounting/', include('itkufs.accounting.urls')),
    (r'^inventory/', include('itkufs.inventory.urls')),
)
