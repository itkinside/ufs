from bzrlib.workingtree import WorkingTree
from bzrlib.errors import NotBranchError

from django.conf import settings

def bzrRev(request):
    try:
        tree = WorkingTree.open_containing(settings.BZR_BRANCH_DIR)[0]
        rev  = tree.branch.revision_id_to_revno(tree.last_revision())

        return {'REV': rev}
    except (AttributeError, NotBranchError):
        pass

    return {}
