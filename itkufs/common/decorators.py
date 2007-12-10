from django.utils.translation import ugettext as _, ungettext
from django.http import HttpResponseForbidden, Http404

from itkufs.accounting.models import Group, Account

def limit_to_group(function):
    def wrapped(request, *args, **kwargs):
        assert('group' in kwargs)

        if (kwargs['group'].account_set.filter(owner=request.user).count()
            or kwargs['group'].admins.filter(id=request.user.id).count()):
            return function(request, *args, **kwargs)
        else:
            return HttpResponseForbidden(_('You must have an account in this group to be allowed to view this page.'))
    return wrapped

def limit_to_user(function):
    def wrapped(request, *args, **kwargs):
        assert('group' in kwargs)
        assert('account' in kwargs)

        if kwargs['account'].owner == request.user:
            return function(request, *args, **kwargs)

        return HttpResponseForbidden(_('You must have an account in this group to be allowed to view this page.'))

    return wrapped
