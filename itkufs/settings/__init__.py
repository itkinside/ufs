# Django settings for itkufs project.

# PROJECT_BASE, DATABASE_* and SECRET_KEY are included from a file which
# is not committed to VCS
from itkufs.settings.local import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG
TEMPLATE_STRING_IF_INVALID = ''

ADMINS = (
    ('ITK uFS', 'itk-ufs@samfundet.no'),
)

MANAGERS = ADMINS

# Local time zone for this installation. All choices can be found here:
# http://www.postgresql.org/docs/current/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
TIME_ZONE = 'Europe/Oslo'

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

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/admin/'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'itkufs.common.middleware.UfsMiddleware',
)

ROOT_URLCONF = 'itkufs.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates".
    # Always use forward slashes, even on Windows.
    PROJECT_BASE + 'itkufs/templates/',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'itkufs.common.context_processors.bzr',
    'itkufs.common.context_processors.debug',
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.webdesign',
    'django.contrib.databrowse',
    'itkufs.common',
    'itkufs.accounting',
    'itkufs.inventory',
    'itkufs.reports',
)

# Session
SESSION_COOKIE_NAME = 'itkufs'
SESSION_COOKIE_SECURE = True

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

# Development version numbering
BZR_BRANCH_DIR = PROJECT_BASE
