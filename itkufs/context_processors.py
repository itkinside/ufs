from bzrlib.workingtree import WorkingTree
from bzrlib.errors import NotBranchError

from django.conf import settings

def bzr(request):
    try:
        rev = WorkingTree.open_containing(settings.BZR_BRANCH_DIR)[0].branch.revno()
        return {'BZRREV': rev}
    except (AttributeError, NotBranchError):
        pass

    return {}

def debug(request):
    "Returns context variables helpful for debugging."
    # Stolen from django.core.context_processors.py, but modified to accept superusers
    context_extras = {}
    if settings.DEBUG and (request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS or request.user.is_superuser):
        context_extras['debug'] = True
        from django.db import connection
        context_extras['sql_queries'] = connection.queries
    return context_extras

