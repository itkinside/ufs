from django import newforms as forms

from itkufs.accounting.models import Transaction

class AccountTransactionForm(forms.Form):
    amount  = forms.DecimalField()
    details = forms.CharField(widget=forms.widgets.Textarea(attrs={'rows':2}))

TransactionForm = forms.form_for_model(Transaction,
    fields=('to_account', 'amount', 'details'))
