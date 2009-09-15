from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from itkufs.common.decorators import limit_to_admin
from itkufs.accounting.models import RoleAccount, Account, Transaction, TransactionEntry
from itkufs.billing.models import Bill
from itkufs.billing.pdf import pdf
from itkufs.billing.forms import BillingLineFormSet, BillForm

@login_required
@limit_to_admin
def bill_new_edit(request, group, bill=None, is_admin=False):
    if bill is None:
        bill = Bill()

    if request.method != 'POST':
        form = BillForm(instance=bill)
        formset = BillingLineFormSet(instance=bill)
    else:
        form = BillForm(request.POST, instance=bill)
        formset = BillingLineFormSet(request.POST, instance=bill)

        if 'more-lines' not in request.POST and form.is_valid() and formset.is_valid():
            bill = form.save(commit=False)
            bill.group = group
            bill.save()

            bill_lines = formset.save(commit=False)

            for line in bill_lines:
                if line.amount and line.description:
                    line.save()

                elif line.id:
                    line.delete()

            return HttpResponseRedirect(reverse('bill-details', args=[group.slug, bill.id]))

    return render_to_response('billing/bill_form.html',
        {
            'is_admin': is_admin,
            'group': group,
            'form': form,
            'formset': formset,
        },
        context_instance=RequestContext(request))

@login_required
@limit_to_admin
def bill_payment(request, group, bill, is_admin=False):
    form = PaymentForm()

    return render_to_response('billing/bill_payment.html',
        {
            'is_admin': is_admin,
            'group': group,
            'bill': bill,
            'form': form,
        },
        context_instance=RequestContext(request))

@login_required
@limit_to_admin
def bill_list(request, group, is_admin=False):
    return render_to_response('billing/bill_list.html',
        {
            'is_admin': is_admin,
            'group': group,
            'bills': group.bill_set.all(),
        },
        context_instance=RequestContext(request))

@login_required
@limit_to_admin
def bill_details(request, group, bill, is_admin=False):
    return render_to_response('billing/bill_details.html',
        {
            'is_admin': is_admin,
            'group': group,
            'bill': bill,
        },
        context_instance=RequestContext(request))

@login_required
@limit_to_admin
def bill_pdf(request, group, bill, is_admin=False):
    return pdf(group, bill)
