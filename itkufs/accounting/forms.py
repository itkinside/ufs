from django import newforms as forms

from itkufs.accounting.models import *
from itkufs.widgets import *

class TransactionForm(forms.Form):
    choices = []

    for g in AccountGroup.objects.all():
        accounts = []
        for a in g.account_set.all():
            if a.is_user_account():
                accounts.append((a.id, a.name))
        choices.append((g.name, accounts))

    to_account = GroupedChoiceField(choices=choices, label="To")
    from_account = GroupedChoiceField(choices=choices, label="From")
    amount = forms.DecimalField(required=True)
    details = forms.CharField(
        widget=forms.widgets.Textarea(attrs={'rows':2}),
        required=False
    )
