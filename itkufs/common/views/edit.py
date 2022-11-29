import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpRequest
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import ugettext as _

from itkufs.common.decorators import limit_to_admin
from itkufs.common.forms import GroupForm, AccountForm, RoleAccountForm
from itkufs.accounting.models import RoleAccount, Group, Account

from typing import Optional


@login_required
@limit_to_admin
def edit_group(request: HttpRequest, group: Group, is_admin=False):
    """Edit group properties"""

    if request.method == "POST":
        if group.logo:
            old_logo = group.logo.path
        else:
            old_logo = None

        form = GroupForm(
            data=request.POST,
            files=request.FILES,
            instance=group,
            user=request.user,
        )

        if form.is_valid():
            form.save()

            if old_logo and old_logo != group.logo.path:
                os.remove(old_logo)
            elif "delete_logo" in form.cleaned_data and old_logo:
                # FIXME see if filestorage can clean this up for us
                os.remove(group.logo.path)
                group.logo = ""
                group.save()

            messages.success(request, _("Group successfully updated."))

            return HttpResponseRedirect(
                reverse("group-summary", args=(group.slug,))
            )
    else:
        form = GroupForm(instance=group)

    return render(
        request,
        "common/group_form.html",
        {"is_admin": is_admin, "group": group, "form": form},
    )


@login_required
def activate_account(
    request: HttpRequest,
    group: Group,
    account: Optional[Account] = None,
    is_admin=False,
    is_owner=False,
):
    """Create account or edit account properties"""

    if request.method == "POST":
        if account and (is_owner or is_admin):
            account.active = True
            account.save()

            messages.success(request, _("Account successfully activated."))

    return HttpResponseRedirect(
        reverse("account-summary", args=(group.slug, account.slug))
    )


@login_required
@limit_to_admin
def new_edit_account(
    request: HttpRequest,
    group: Group,
    account: Optional[Account] = None,
    is_admin=False,
    is_owner=False,
):
    """Create account or edit account properties"""

    if request.method == "POST":
        if account is not None:
            form = AccountForm(instance=account, data=request.POST, group=group)
        else:
            form = AccountForm(data=request.POST, group=group)

        if form.is_valid():
            if account is not None:
                form.save()
                messages.success(request, _("Account successfully updated."))
            else:
                account = form.save(group=group)
                messages.success(request, _("Account successfully created."))

            return HttpResponseRedirect(
                reverse("account-summary", args=(group.slug, account.slug))
            )
    else:
        if account is not None:
            form = AccountForm(instance=account)
        else:
            form = AccountForm()

    return render(
        request,
        "common/account_form.html",
        {
            "is_admin": is_admin,
            "group": group,
            "is_owner": is_owner,
            "account": account,
            "form": form,
        },
    )


@login_required
@limit_to_admin
def assign_role_accounts(request: HttpRequest, group: Group, is_admin=False):
    """Assign role accounts to group"""

    if request.method == "POST":
        form = RoleAccountForm(request.POST, group=group)

        if form.is_valid():
            for type, name in RoleAccount.ACCOUNT_ROLE:
                account = form.cleaned_data[type]
                try:
                    role = group.roleaccount_set.get(role=type)
                    if role.account != account:
                        role.account = account
                        role.save()
                except RoleAccount.DoesNotExist:
                    role = group.roleaccount_set.create(
                        role=type, account=account
                    )
            return HttpResponseRedirect(
                reverse("group-summary", args=(group.slug,))
            )
    else:
        form = RoleAccountForm(group=group)

    return render(
        request,
        "common/role_account_form.html",
        {"is_admin": is_admin, "group": group, "form": form},
    )
