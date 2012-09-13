from itkufs.settings.base import *

# DATABASE_* and SECRET_KEY are included from a file which is not in VCS
try:
    from itkufs.settings.local import *
except ImportError, e:
    import warnings
    warnings.warn('There was a problem importing local settings: %s' %  e)
