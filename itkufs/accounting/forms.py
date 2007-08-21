from datetime import datetime

from django import newforms as forms

from itkufs.accounting.models import *
from itkufs.widgets import *

all_choices = [(False, (('',''),))]
user_choices = [(False, (('',''),))]
group_choices = [(False, (('',''),))]

for g in AccountGroup.objects.all():
    all_accounts = []
    user_accounts = []
    group_accounts = []
    for a in g.account_set.all():
        all_accounts.append((a.id, a.name))
        if a.is_user_account():
            user_accounts.append((a.id, a.name))
        else:
            group_accounts.append((a.id, a.name))
    all_choices.append((g.name, all_accounts))
    group_choices.append((g.name, group_accounts))
    user_choices.append((g.name, user_accounts))

amount_field = forms.DecimalField(required=True)
details_field = forms.CharField(widget=forms.widgets.Textarea(attrs={'rows':2}), required=False)

#FIXME http://www.djangoproject.com/documentation/newforms/#subclassing-forms

class TransactionForm(forms.Form):
    def _init_(self, choices=None):
        self._init_()
        print self

    to_account = GroupedChoiceField(choices=all_choices, label="To", required=True)
    from_account = GroupedChoiceField(choices=all_choices, label="From", required=True)
    amount = amount_field
    payed = forms.BooleanField(required=False)
    details = details_field

class DepositWithdrawForm(forms.Form):
    amount = amount_field
    details = details_field

class TransferForm(forms.Form):
    # FIXME should only give choices for people in same group
    to_account = GroupedChoiceField(choices=user_choices, label="To", required=True)
    amount = amount_field
    details = details_field
