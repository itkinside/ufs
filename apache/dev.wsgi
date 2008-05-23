import os, sys
path = '/home/cassarossa/itk/ufs-web/itkufs/'
if path not in sys.path:
	sys.path.append(path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'itkufs.settings.dev'

import django.core.handlers.wsgi

_application = django.core.handlers.wsgi.WSGIHandler()

def application(environ, start_response):
    environ['PATH_INFO'] = environ['SCRIPT_NAME'] + environ['PATH_INFO']
    return _application(environ, start_response)
