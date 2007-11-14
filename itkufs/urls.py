from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import databrowse
from django.contrib.auth.decorators import user_passes_test
from itkufs.accounting.models import *


# Setup which classes can be used with databrowse...
databrowse.site.register(Group)
databrowse.site.register(Account)
databrowse.site.register(List)
databrowse.site.register(ListItem)
databrowse.site.register(NewTransaction)
databrowse.site.register(TransactionLog)
databrowse.site.register(TransactionEntry)


urlpatterns = patterns('',
    (r'^admin/', include('django.contrib.admin.urls')),

    (r'^databrowse/(.*)',  user_passes_test(lambda u: u.is_staff)(databrowse.site.root)),

    # View for magic i18n translation of js
    url(r'^i18n/js/$', 'django.views.i18n.javascript_catalog',
        {'packages': ['itkufs']}, name='jsi18n'),
    (r'^i18n/', include('django.conf.urls.i18n')),

    (r'^inventory/', include('itkufs.inventory.urls')),
    (r'^', include('itkufs.accounting.urls')),


    # Only reached using test server, but always used
    # for reverse lookup of URLs from views and templates
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}, name='media'),
)
