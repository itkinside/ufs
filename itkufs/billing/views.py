from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.contrib import messages
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from itkufs.common.decorators import limit_to_admin
from itkufs.accounting.models import Account, Transaction
from itkufs.billing.models import Bill
from itkufs.billing.pdf import pdf
from itkufs.billing.forms import (
    BillingLineFormSet,
    NewBillingLineFormSet,
    BillForm,
    CreateTransactionForm,
)


@login_required
@limit_to_admin
def bill_new_edit(request, group, bill=None, is_admin=False):
    if bill is None:
        bill = Bill()
        LineFormSet = NewBillingLineFormSet
    else:
        LineFormSet = BillingLineFormSet

    if not bill.is_editable():
        messages.warning(request, _("This bill can no longer be edited."))
        return HttpResponseRedirect(
            reverse("bill-details", args=[group.slug, bill.id])
        )

    if request.method != "POST":
        form = BillForm(instance=bill)
        formset = LineFormSet(instance=bill)
    else:
        form = BillForm(request.POST, instance=bill)
        formset = LineFormSet(request.POST, instance=bill)

        if form.is_valid() and formset.is_valid():
            bill = form.save(commit=False)
            bill.group = group
            bill.save()

            bill_lines = formset.save(commit=False)

            for line in bill_lines:
                if line.amount and line.description:
                    line.save()

                elif line.id:
                    line.delete()

            return HttpResponseRedirect(
                reverse("bill-details", args=[group.slug, bill.id])
            )

    return render_to_response(
        "billing/bill_form.html",
        {
            "is_admin": is_admin,
            "group": group,
            "form": form,
            "formset": formset,
        },
        context_instance=RequestContext(request),
    )


@login_required
@limit_to_admin
def bill_create_transaction(request, group, bill, is_admin=False):
    if not bill.is_editable():
        messages.info(
            request, _("This bill is already linked to a transaction.")
        )
        return HttpResponseRedirect(
            reverse(
                "transaction-details", args=[group.slug, bill.transaction.id]
            )
        )

    if request.method != "POST":
        form = CreateTransactionForm(bill)
    else:
        form = CreateTransactionForm(bill, request.POST)

        if form.is_valid():
            pay_to = Account.objects.get(
                group=group, roleaccount__role=form.cleaned_data["pay_to"]
            )

            charge_to = form.cleaned_data["charge_to"]

            settlement = form.cleaned_data.get("settlement", None)

            sum = 0
            for line in bill.billingline_set.all():
                sum += line.amount

            transaction = Transaction(group=group, settlement=settlement)
            transaction.save()

            transaction.entry_set.create(account=charge_to, credit=sum)
            transaction.entry_set.create(account=pay_to, debit=sum)
            transaction.set_pending(
                user=request.user,
                message=_("Bill #%(id)s: %(description)s")
                % {"id": bill.pk, "description": bill.description},
            )

            bill.transaction = transaction
            bill.save()

            return HttpResponseRedirect(
                reverse(
                    "transaction-details", args=[group.slug, transaction.id]
                )
            )

    return render_to_response(
        "billing/bill_create_transaction.html",
        {"is_admin": is_admin, "group": group, "bill": bill, "form": form},
        context_instance=RequestContext(request),
    )


@login_required
@limit_to_admin
def bill_list(request, group, is_admin=False):
    return render_to_response(
        "billing/bill_list.html",
        {"is_admin": is_admin, "group": group, "bills": group.bill_set.all()},
        context_instance=RequestContext(request),
    )


@login_required
@limit_to_admin
def bill_details(request, group, bill, is_admin=False):
    return render_to_response(
        "billing/bill_details.html",
        {"is_admin": is_admin, "group": group, "bill": bill},
        context_instance=RequestContext(request),
    )


@login_required
@limit_to_admin
def bill_delete(request, group, bill, is_admin=False):
    if request.method == "POST":
        messages.info(request, _("Bill #%d deleted.") % bill.id)
        bill.delete()

        return HttpResponseRedirect(reverse("bill-list", args=[group.slug]))

    return render_to_response(
        "billing/bill_delete.html",
        {"is_admin": is_admin, "group": group, "bill": bill},
        context_instance=RequestContext(request),
    )


@login_required
@limit_to_admin
def bill_pdf(request, group, bill, is_admin=False):
    return pdf(group, bill)
