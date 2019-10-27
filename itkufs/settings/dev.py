from itkufs.settings import INSTALLED_APPS, MIDDLEWARE_CLASSES
from itkufs.settings import *  # noqa

# Debug settings
DEBUG = True
TEMPLATES[0]["OPTIONS"]["debug"] = True

# django-debug-toolbar
INSTALLED_APPS += ["debug_toolbar"]
INTERNAL_IPS = ["127.0.0.1"]
MIDDLEWARE_CLASSES += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

# Do not require HTTPS
SESSION_COOKIE_SECURE = False
