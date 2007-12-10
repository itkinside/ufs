from django.utils.translation import ugettext as _
from django.http import HttpResponseForbidden, Http404

from itkufs.accounting.models import Group, Account

def limit_to_group(function):
    def wrapped(request, *args, **kwargs):
        # Let admin through immediately
        assert('is_admin' in kwargs)
        if kwargs['is_admin']:
            return function(request, *args, **kwargs)

        # Check if non-admin are members of the group
        assert('group' in kwargs and isinstance(kwargs['group'], Group))
        is_member = bool(kwargs['group'].account_set.filter(
            owner=request.user).count())
        if is_member:
            return function(request, *args, **kwargs)

        # All other
        return HttpResponseForbidden(
            _('Forbidden if not member of the group or group admin.'))
    return wrapped

def limit_to_owner(function):
    def wrapped(request, *args, **kwargs):
        # Let admins through immediately
        assert('is_admin' in kwargs)
        if kwargs['is_admin']:
            return function(request, *args, **kwargs)

        # Check if non-admin are members of the group
        # Warning: If used on views where account=None is possible, this
        # assertion will fail for non-admins trying forbidden URLs
        assert('account' in kwargs and isinstance(kwargs['account'], Account))
        is_owner = kwargs['account'].owner == request.user
        if is_owner:
            return function(request, *args, **kwargs)

        # All other
        return HttpResponseForbidden(
            _('Forbidden if not account owner or group admin.'))
    return wrapped

def limit_to_admin(function):
    def wrapped(request, *args, **kwargs):
        # Let admins through immediately
        assert('is_admin' in kwargs)
        if kwargs['is_admin']:
            return function(request, *args, **kwargs)

        # All other
        return HttpResponseForbidden(
            _('Forbidden if not group admin.'))
    return wrapped
