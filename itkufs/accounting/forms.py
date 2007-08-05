from django import newforms as forms

from itkufs.accounting.models import Transaction

DepositForm = forms.form_for_model(Transaction,
    fields=('amount', 'details'))
WithdrawalForm = forms.form_for_model(Transaction,
    fields=('amount', 'details'))

TransactionForm = forms.form_for_model(Transaction,
    fields=('to_account', 'amount', 'details'))
