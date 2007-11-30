from bzrlib.workingtree import WorkingTree
from bzrlib.errors import NotBranchError

from django.conf import settings

def bzrRev(request):
    try:
        rev = WorkingTree.open_containing(settings.BZR_BRANCH_DIR)[0].branch.revno()
        return {'BZRREV': rev}
    except (AttributeError, NotBranchError):
        pass

    return {}
