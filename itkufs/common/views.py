from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _, ungettext

from itkufs.common.decorators import is_group_admin
from itkufs.accounting.models import Group

def login_user(request):
    """Login user"""

    if not request.user.is_authenticated():
        user = authenticate(request=request)
        if user is not None:
            login(request, user)
        else:
            return HttpResponseForbidden(_('Login failed'))

    try:
        # Redirect to one of the user's accounts
        account = request.user.account_set.all()[0]
        url = reverse('account-summary',
                      kwargs={'group': account.group.slug,
                              'account': account.slug})
        return HttpResponseRedirect(url)
    except IndexError:
        pass

    # Tell the user he has a user, but not an account
    return render_to_response('accounting/no_account.html',
                              context_instance=RequestContext(request))

@login_required
@is_group_admin
def static_page(request, group, template, is_admin=False):
    try:
        group = Group.objects.get(slug=group)
    except Group.DoesNotExist:
        raise Http404

    return render_to_response(template,
                              {
                                  'group': group,
                                  'is_admin': is_admin,
                              },
                              context_instance=RequestContext(request))

