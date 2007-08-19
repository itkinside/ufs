from datetime import datetime

from django import newforms as forms

from itkufs.accounting.models import *
from itkufs.widgets import *

choices = [(False, (('',''),))]

for g in AccountGroup.objects.all():
    accounts = []
    for a in g.account_set.all():
        if a.is_user_account():
            accounts.append((a.id, a.name))
    choices.append((g.name, accounts))

to_field = GroupedChoiceField(choices=choices, label="To", required=True)
from_field = GroupedChoiceField(choices=choices, label="From", required=True)
amount_field = forms.DecimalField(required=True)
details_field = forms.CharField(widget=forms.widgets.Textarea(attrs={'rows':2}), required=False)
payed_field = forms.DateTimeField(initial=datetime.now().strftime('%Y-%m-%d %H:%M'), required=False)

#FIXME http://www.djangoproject.com/documentation/newforms/#subclassing-forms

class TransactionForm(forms.Form):
    to_account = to_field
    from_account = to_field
    amount = amount_field
    payed = payed_field
    details = details_field

class DepositWithdrawForm(forms.Form):
    amount = amount_field
    details = details_field

class TransferForm(forms.Form):
    to_account = to_field
    amount = amount_field
    details = details_field
