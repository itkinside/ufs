# Django settings for itkufs project.

import os
PROJECT_BASE = os.path.dirname(os.path.abspath(__file__)) + '/../../'

DEBUG = False
TEMPLATE_DEBUG = DEBUG
TEMPLATE_STRING_IF_INVALID = ''

# Disable superbackoffice
BACKOFFICE = False

ADMINS = ()
MANAGERS = ADMINS

# Local time zone for this installation. All choices can be found here:
# http://www.postgresql.org/docs/current/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
TIME_ZONE = 'Europe/Oslo'

DATE_FORMAT = 'Y-m-d'
TIME_FORMAT = 'H:i'
DATETIME_FORMAT = 'Y-m-d H:i'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

AUTHENTICATION_BACKENDS = (
    'itkufs.common.kerberos.KerberosBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = PROJECT_BASE + 'media/'

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
MEDIA_URL = '/media/'

STATIC_URL = '/media/'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'itkufs.common.middleware.UfsMiddleware',
)

ROOT_URLCONF = 'itkufs.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates".
    # Always use forward slashes, even on Windows.
    PROJECT_BASE + 'itkufs/templates/',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.webdesign',
    'django.contrib.sites',
    'django.contrib.flatpages',
    'django.contrib.messages',
    'itkufs.common',
    'itkufs.accounting',
    'itkufs.reports',
    'itkufs.billing',
    'south',
)

# Session
SESSION_COOKIE_NAME = 'itkufs'
SESSION_COOKIE_SECURE = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# WSGI application used by manage.py runserver
WSGI_APPLICATION = 'itkufs.wsgi.application'

# Authentication
MAIL_DOMAIN = 'samfundet.no'
LOGIN_URL = '/login/'

# Languages
ugettext = lambda s: s
LANGUAGES = (
    ('en', ugettext('English')),
    ('no', ugettext('Norwegian')),
)
LOCALE_PATHS = (
    PROJECT_BASE + 'itkufs/locale/',
)

# Test runner with code coverage
#TEST_RUNNER = 'itkufs.common.test_runner.test_runner_with_coverage'
COVERAGE_MODULES = (
    'itkufs',
    'itkufs.accounting',
    'itkufs.accounting.admin',
    'itkufs.accounting.forms',
    'itkufs.accounting.models',
    'itkufs.accounting.urls',
    'itkufs.accounting.views',
    'itkufs.accounting.views.display',
    'itkufs.accounting.views.edit',
    'itkufs.reports',
    'itkufs.reports.admin',
    'itkufs.reports.forms',
    'itkufs.reports.models',
    'itkufs.reports.urls',
    'itkufs.reports.views',
)

# Development version numbering
BZR_BRANCH_DIR = PROJECT_BASE
