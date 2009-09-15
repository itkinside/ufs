from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from itkufs.common.decorators import limit_to_admin
from itkufs.accounting.models import RoleAccount, Account, Transaction, TransactionEntry
from itkufs.billing.models import Bill
from itkufs.billing.forms import get_billingline_formset, BillForm

@login_required
@limit_to_admin
def new_bill(request, group, is_admin=False):
    bill = Bill()

    lines = request.POST.get('more-lines', '')

    if lines.isdigit() and int(lines) > 0:
        lines = int(lines)
    else:
        lines = 5

    BillingLineFormSet = get_billingline_formset(lines)

    if request.method != 'POST':
        form = BillForm(group, instance=bill)
        formset = BillingLineFormSet(instance=bill)
    else:
        post = request.POST.copy()
        post['billingline_set-TOTAL_FORMS'] = lines

        form = BillForm(group, post, instance=bill)
        formset = BillingLineFormSet(post, instance=bill)

        if 'more-lines' not in request.POST and form.is_valid() and formset.is_valid():
            bank = Account.objects.get(group=group,
                roleaccount__role=RoleAccount.BANK_ACCOUNT)

            other = form.cleaned_data['charge_to']

            bill = form.save(commit=False)

            transaction = Transaction(group=group)
            transaction.save()

            bill.transaction = transaction
            bill.save()

            bill_lines = formset.save(commit=False)

            sum = 0
            for line in bill_lines:
                if line.amount and line.description:
                    sum += line.amount
                    line.save()

                elif line.id:
                    line.delete()

            transaction.entry_set.add(
                TransactionEntry(account=other, credit=sum))
            transaction.entry_set.add(
                TransactionEntry(account=bank, debit=sum))

            transaction.set_pending(user=request.user,
                message=_('Bill #%s: %s') % (bill.pk, bill.description))

            return HttpResponseRedirect(reverse('bill-list', args=[group.slug]))

    return render_to_response('billing/bill_form.html',
        {
            'is_admin': is_admin,
            'group': group,
            'form': form,
            'formset': formset,
            'lines': lines,
        },
        context_instance=RequestContext(request))

@login_required
@limit_to_admin
def bill_list(request, group, is_admin=False):
    return render_to_response('billing/bill_list.html',
        {
            'is_admin': is_admin,
            'group': group,
            'bills': Bill.objects.filter(transaction__group=group),
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
