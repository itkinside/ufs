from django.conf.urls import include
from django.urls import re_path
from django.conf import settings
from django.contrib import admin
from django.views.i18n import JavaScriptCatalog
from django.views.static import serve

from itkufs import admin  # noqa: To register admin classes
from itkufs.reports.views import public_lists, view_public_list

if "itkufs.accounting" in settings.INSTALLED_APPS:
    import itkufs.accounting.admin  # noqa: To register admin classes

if "itkufs.reports" in settings.INSTALLED_APPS:
    import itkufs.reports.admin  # noqa: To register admin classes

urlpatterns = [
    re_path(r"^admin/doc/", include("django.contrib.admindocs.urls")),
    re_path(r"^admin/", admin.site.urls),
    # View for magic i18n translation of js
    re_path(
        r"^i18n/js/$",
        JavaScriptCatalog.as_view(packages=['itkufs']),
        name="jsi18n",
    ),
    re_path(r"^i18n/", include("django.conf.urls.i18n")),
    # Pull in lists before so that nothing else manages to catch the url
    re_path(r"^lists/$", public_lists, name="public-lists"),
    re_path(
        r"^lists/(?P<group>[0-9a-z_-]+)/(?P<list>[0-9a-z_-]+)/$",
        view_public_list,
        name="view-public-list",
    ),
    re_path(r"^", include("itkufs.common.urls")),
    re_path(r"^", include("itkufs.accounting.urls")),
    re_path(r"^", include("itkufs.billing.urls")),
    re_path(r"^", include("itkufs.reports.urls")),
    # Only reached using test server, but always used
    # for reverse lookup of URLs from views and templates
    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {"document_root": settings.MEDIA_ROOT},
        name="media",
    ),
]

if settings.DEBUG:
    try:
        import debug_toolbar
    except ImportError:
        pass
    else:
        urlpatterns = [
            re_path(r"^__debug__/", include(debug_toolbar.urls))
        ] + urlpatterns
