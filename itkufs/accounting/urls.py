from django.conf.urls.defaults import *
from itkufs.accounting.views import *

urlpatterns = patterns('',
    url('^$', accounting_view),
)
