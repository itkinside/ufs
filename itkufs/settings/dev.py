from itkufs.settings import *

# Debug settings
DEBUG = True
TEMPLATE_DEBUG = DEBUG

# django-logging
LOGGING_LOG_SQL = True
LOGGING_SHOW_METRICS = True

# Do not require HTTPS
SESSION_COOKIE_SECURE = False

# Only add djangologging middleware if it is available
try:
    import djangologging
    MIDDLEWARE_CLASSES += ('djangologging.middleware.LoggingMiddleware',)
except ImportError:
    pass


