from itkufs.settings import *

# Debug settings
DEBUG = True
TEMPLATE_DEBUG = DEBUG
TEMPLATE_STRING_IF_INVALID = '!!INVALID VAR!!'

# Do not require HTTPS
SESSION_COOKIE_SECURE = False

# Media
MEDIA_ROOT = '/home/jodal/projects/itkufs/media/'

# Templates
TEMPLATE_DIRS = (
    '/home/jodal/projects/itkufs/itkufs/templates/',
)

# bzr
BZR_BRANCH_DIR = '/home/jodal/projects/itkufs/'
