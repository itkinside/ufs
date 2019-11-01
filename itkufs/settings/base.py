# Django settings for itkufs project.

import os

PROJECT_BASE = os.path.dirname(os.path.abspath(__file__)) + "/../../"

DEBUG = False
TEMPLATE_DEBUG = DEBUG
TEMPLATE_STRING_IF_INVALID = ""

# Disable superbackoffice
BACKOFFICE = False

ADMINS = ()
MANAGERS = ADMINS

# Local time zone for this installation. All choices can be found here:
# http://www.postgresql.org/docs/current/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
TIME_ZONE = "Europe/Oslo"

DATE_FORMAT = "Y-m-d"
TIME_FORMAT = "H:i"
DATETIME_FORMAT = "Y-m-d H:i"

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = "en-us"

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    "itkufs.common.kerberos.KerberosBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = PROJECT_BASE + "media/"

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
MEDIA_URL = "/media/"

STATIC_ROOT = PROJECT_BASE + "static/"
STATIC_URL = "/static/"

MIDDLEWARE_CLASSES = [
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.RemoteUserMiddleware",
    "django.contrib.admindocs.middleware.XViewMiddleware",
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "itkufs.common.middleware.UfsMiddleware",
]

ROOT_URLCONF = "itkufs.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [PROJECT_BASE + "itkufs/templates/"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ],
            "debug": False,
        },
    }
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.admindocs",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.flatpages",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "itkufs.common",
    "itkufs.accounting",
    "itkufs.reports",
    "itkufs.billing",
]

# Session
SESSION_COOKIE_NAME = "itkufs"
SESSION_COOKIE_SECURE = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SERIALIZER = "django.contrib.sessions.serializers.JSONSerializer"

# WSGI application used by manage.py runserver
WSGI_APPLICATION = "itkufs.wsgi.application"

# Authentication
MAIL_DOMAIN = "samfundet.no"
LOGIN_URL = "/login/"

TEST_RUNNER = "django.test.runner.DiscoverRunner"

# Languages
def ugettext(s):
    return s


LANGUAGES = (("en", ugettext("English")), ("no", ugettext("Norwegian")))
LOCALE_PATHS = (PROJECT_BASE + "itkufs/locale/",)
