from itkufs.settings import *

# Debug settings
DEBUG = True
TEMPLATE_DEBUG = DEBUG
TEMPLATE_STRING_IF_INVALID = '!!INVALID VAR!!'

# django-logging
LOGGING_LOG_SQL = True
LOGGING_SHOW_METRICS = True

# Do not require HTTPS
SESSION_COOKIE_SECURE = False
