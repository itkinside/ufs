from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import DetailView, ListView

from itkufs.common.decorators import limit_to_group
from itkufs.accounting.models import (
    Account,
    Settlement,
    Transaction,
    TransactionEntry,
)


class SettlementList(ListView):
    model = Settlement
    allow_empty = True
    paginate_by = 20

    @method_decorator(login_required)
    @method_decorator(limit_to_group)
    def dispatch(self, request, *args, **kwargs):
        self.is_admin = kwargs.get("is_admin", False)
        self.group = kwargs["group"]
        return super(SettlementList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.group.settlement_set.select_related()

    def get_context_data(self, **kwargs):
        context = super(SettlementList, self).get_context_data(**kwargs)
        context["is_admin"] = self.is_admin
        context["group"] = self.group
        return context


class SettlementDetails(DetailView):
    model = Settlement
    template_name_suffix = "_details"

    @method_decorator(login_required)
    @method_decorator(limit_to_group)
    def dispatch(self, request, *args, **kwargs):
        self.is_admin = kwargs.get("is_admin", False)
        self.group = kwargs["group"]
        self.settlement = kwargs["settlement"]
        return super(SettlementDetails, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.settlement

    def get_context_data(self, **kwargs):
        context = super(SettlementDetails, self).get_context_data(**kwargs)
        context["is_admin"] = self.is_admin
        context["group"] = self.group
        return context


class TransactionList(ListView):
    model = Transaction
    allow_empty = True
    paginate_by = 20

    @method_decorator(login_required)
    @method_decorator(limit_to_group)
    def dispatch(self, request, *args, **kwargs):
        self.is_admin = kwargs.get("is_admin", False)
        self.is_owner = kwargs.get("is_owner", False)
        self.group = kwargs["group"]
        self.account = kwargs.get("account")

        # FIXME: Incorporate into decorator.
        if self.account and not self.is_owner and not self.is_admin:
            return HttpResponseForbidden(
                _("Forbidden if not account owner or group admin.")
            )

        return super(TransactionList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.account:
            return self.account.transaction_set_with_rejected.filter(
                entry_set__account=self.account
            )
        else:
            return self.group.transaction_set_with_rejected.all()

    def get_context_data(self, **kwargs):
        context = super(TransactionList, self).get_context_data(**kwargs)

        try:
            user_account = self.group.account_set.get(owner=self.request.user)
        except Account.DoesNotExist:
            user_account = None

        context["is_admin"] = self.is_admin
        context["is_owner"] = self.is_owner
        context["group"] = self.group
        context["account"] = self.account
        context["user_account"] = user_account

        return context


class TransactionDetails(DetailView):
    model = Transaction
    template_name_suffix = "_details"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.is_admin = kwargs.get("is_admin", False)
        self.group = kwargs["group"]
        self.transaction = kwargs["transaction"]

        # Check that user is party of transaction or admin of group
        # FIXME: Do this with a decorator.
        if (
            not self.is_admin
            and TransactionEntry.objects.filter(
                transaction=self.transaction, account__owner__id=request.user.id
            ).count()
            == 0
        ):
            return HttpResponseForbidden(
                _(
                    "The transaction may only be viewed by group admins or a "
                    "party of the transaction."
                )
            )

        return super(TransactionDetails, self).dispatch(
            request, *args, **kwargs
        )

    def get_object(self, queryset=None):
        return self.transaction

    def get_context_data(self, **kwargs):
        context = super(TransactionDetails, self).get_context_data(**kwargs)
        context["is_admin"] = self.is_admin
        context["group"] = self.group
        return context
