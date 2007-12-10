# Django settings for itkufs project.
from settings_base import *
from settings_local import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG
TEMPLATE_STRING_IF_INVALID = ''

# DB stuff moved to setting_local which is not versioned

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = '/home/cassarossa/itk/felles/itkufs/media/'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates".
    # Always use forward slashes, even on Windows.
    '/home/cassarossa/itk/felles/itkufs/itkufs/templates/',
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

BZR_BRANCH_DIR = '/home/cassarossa/itk/felles/itkufs/'
