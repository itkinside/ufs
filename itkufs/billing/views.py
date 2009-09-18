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
from itkufs.billing.forms import BillingLineFormSet, NewBillingLineFormSet, BillForm, PaymentForm

@login_required
@limit_to_admin
def bill_new_edit(request, group, bill=None, is_admin=False):
    if bill is None:
        bill = Bill()
        LineFormSet = NewBillingLineFormSet
    else:
        LineFormSet = BillingLineFormSet

    if not bill.is_editable():
        request.user.message_set.create(message=_('This bill can no longer be edited'))
        return HttpResponseRedirect(reverse('bill-details', args=[group.slug, bill.id]))

    if request.method != 'POST':
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

    if request.method != 'POST':
        form = PaymentForm(bill)
    else:
        form = PaymentForm(bill, request.POST)

        if form.is_valid():
            bank = Account.objects.get(group=group,
                roleaccount__role=RoleAccount.BANK_ACCOUNT)

            other = form.cleaned_data['charge_to']

            settlement = form.cleaned_data.get('settlement', None)

            sum = 0
            for line in bill.billingline_set.all():
                sum += line.amount

            transaction = Transaction(group=group, settlement=settlement)
            transaction.save()

            transaction.entry_set.add(
                TransactionEntry(account=other, credit=sum))
            transaction.entry_set.add(
                TransactionEntry(account=bank, debit=sum))

            transaction.set_pending(user=request.user,
                message=_('Bill #%s: %s') % (bill.pk, bill.description))

            bill.transaction = transaction
            bill.save()

            return HttpResponseRedirect(reverse('transaction-details',
                args=[group.slug,transaction.id]))

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
def bill_delete(request, group, bill, is_admin=False):
    if request.method == 'POST':
        request.user.message_set.create(message=_('Bill #%d deleted') % bill.id)
        bill.delete()

        return HttpResponseRedirect(reverse('bill-list', args=[group.slug]))

    return render_to_response('billing/bill_delete.html',
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
