from django.utils.translation import ugettext as _, ungettext
from django.http import HttpResponseForbidden, Http404

from itkufs.accounting.models import Group, Account

def limit_to_group(function):
    def wrapped(request, *args, **kwargs):
        assert('group' in kwargs)

        try:
            group = Group.objects.get(slug=kwargs['group'])
        except Group.DoesNotExist:
            raise Http404

        if (group.account_set.filter(owner=request.user).count()
            or group.admins.filter(id=request.user.id).count()):
            return function(request, *args, **kwargs)
        else:
            return HttpResponseForbidden(_('You must have an account in this group to be allowed to view this page.'))
    return wrapped

def limit_to_user(function):
    def wrapped(request, *args, **kwargs):
        assert('group' in kwargs)
        assert('account' in kwargs)

        try:
            group = Group.objects.get(slug=kwargs['group'])
            account = group.account_set.get(slug=kwargs['account'])
        except (Group.DoesNotExist, Account.DoesNotExist):
            raise Http404

        if account.owner == request.user:
            return function(request, *args, **kwargs)

        return HttpResponseForbidden(_('You must have an account in this group to be allowed to view this page.'))

    return wrapped
