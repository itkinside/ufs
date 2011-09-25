from itkufs.settings import *

# Debug settings
DEBUG = True
TEMPLATE_DEBUG = DEBUG

# django-debug-toolbar
INSTALLED_APPS += ('debug_toolbar',)
INTERNAL_IPS = ('127.0.0.1',)
MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)

# Do not require HTTPS
SESSION_COOKIE_SECURE = False
