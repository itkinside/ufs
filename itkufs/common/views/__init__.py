from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import ugettext as _

from itkufs.accounting.models import Group, Account


def login_user(request):
    """Login user"""

    if not request.user.is_authenticated:
        user = authenticate(request=request)
        if user is not None:
            login(request, user)
        else:
            return HttpResponseForbidden(_("Login failed"))

    try:
        # Redirect to one of the user's accounts
        account = request.user.account_set.all()[0]
        url = reverse(
            "account-summary",
            kwargs={"group": account.group.slug, "account": account.slug},
        )
        return HttpResponseRedirect(url)
    except IndexError:
        pass

    try:
        group = Group.objects.filter(admins__in=[request.user])[0]
        url = reverse("group-summary", kwargs={"group": group.slug})
        return HttpResponseRedirect(url)
    except IndexError:
        pass

    # Tell the user he has a user, but not an account
    return render(
        request,
        "common/no_account.html",
    )


@login_required
def switch_group(request, is_admin=False):
    """Switch to account summary for the selected account"""

    if request.method != "POST":
        raise Http404
    group_slug = request.POST["group"]
    account = get_object_or_404(
        Account, owner=request.user, group__slug=group_slug
    )
    return HttpResponseRedirect(
        reverse(
            "account-summary",
            kwargs={"group": account.group.slug, "account": account.slug},
        )
    )


@login_required
def static_page(request, template, is_admin=False):
    return render(
        request,
        template,
        {"is_admin": is_admin},
    )
