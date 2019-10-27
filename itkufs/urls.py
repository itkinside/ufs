from django.conf.urls import include, url
from django.conf import settings
from django.contrib import admin

from itkufs import admin  # noqa: To register admin classes

if "itkufs.accounting" in settings.INSTALLED_APPS:
    import itkufs.accounting.admin  # noqa: To register admin classes

if "itkufs.reports" in settings.INSTALLED_APPS:
    import itkufs.reports.admin  # noqa: To register admin classes

urlpatterns = [
    url(r"^admin/doc/", include("django.contrib.admindocs.urls")),
    url(r"^admin/", include(admin.site.urls)),
    # View for magic i18n translation of js
    url(
        r"^i18n/js/$",
        "django.views.i18n.javascript_catalog",
        {"packages": ["itkufs"]},
        name="jsi18n",
    ),
    url(r"^i18n/", include("django.conf.urls.i18n")),
    # Pull in lists before so that nothing else manages to catch the url
    url(r"^lists/$", "itkufs.reports.views.public_lists", name="public-lists"),
    url(
        r"^lists/(?P<group>[0-9a-z_-]+)/(?P<list>[0-9a-z_-]+)/$",
        "itkufs.reports.views.view_public_list",
        name="view-public-list",
    ),
    url(r"^", include("itkufs.common.urls")),
    url(r"^", include("itkufs.accounting.urls")),
    url(r"^", include("itkufs.billing.urls")),
    url(r"^", include("itkufs.reports.urls")),
    # Only reached using test server, but always used
    # for reverse lookup of URLs from views and templates
    url(
        r"^media/(?P<path>.*)$",
        "django.views.static.serve",
        {"document_root": settings.MEDIA_ROOT},
        name="media",
    ),
]
