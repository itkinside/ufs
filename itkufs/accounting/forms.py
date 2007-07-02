from django import newforms as forms

from itkufs.accounting.models import Transaction

NewDepositForm = forms.form_for_model(Transaction,
    fields=('to_account', 'amount', 'details'))
NewWithdrawalForm = forms.form_for_model(Transaction,
    fields=('from_account', 'amount', 'details'))
NewTransferForm = forms.form_for_model(Transaction,
    fields=('from_account', 'to_account', 'amount', 'details'))

NewTransactionFrom = forms.form_for_model(Transaction)
#ApproveTransactionForm = forms.form_for_model(...)
#ApproveTransactionForm.field['transactions'].widget = \
#   forms.widgets.CheckboxSelectMultiple(
#       choices=...)
