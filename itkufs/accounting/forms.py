from django import newforms as forms
from django.utils.translation import ugettext as _
from django.newforms.util import ValidationError

from itkufs.accounting.models import *
from itkufs.widgets import *

amount_field = forms.DecimalField(label=_('Amount'), required=True, min_value=0)
details_field = forms.CharField(label=_('Details'),
    widget=forms.widgets.Textarea(attrs={'rows': 2}), required=False)

class BaseTransactionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        def _get_choices(options={}):
            limit_groups = options.pop('limit_to_groups', ())
            exclude_accounts = options.pop('exclude_accounts', ())
            user_account = options.pop('user_accounts', False)
            exclude_groups = options.pop('exclude_groups', ())
            group_account = options.pop('group_accounts', False)

            # Run a diffrent query depending on which combo of limit and
            # exclude is present:
            if limit_groups and exclude_groups:
                groups = AccountGroup.objects.filter(
                    pk__in=[g.id for g in limit_groups]).exclude(
                    pk__in=[g.id for g in exclude_groups])
            elif limit_groups:
                groups = AccountGroup.objects.filter(
                    pk__in=[g.id for g in limit_groups])
            elif exclude_groups:
                groups = AccountGroup.objects.exclude(
                    pk__in=[g.id for g in exclude_groups])
            else:
                groups = AccountGroup.objects.all()

            # Build the choices data structure:
            choices = [(False, (('',''),))]

            # Loop over all accounts in group:
            for g in groups:
                a_choices = []

                # Loop over accounts in group:
                for a in g.account_set.all():

                    # Filter based on options telling if user/group accounts
                    # should be added.
                    if ( (a.is_user_account() and user_account) or
                        (not a.is_user_account() and group_account) ):

                        # Finally, remove excluded accounts (might be doable
                        # with filter() on qs, but this is easier
                        if a not in exclude_accounts:
                            a_choices.append((a.id, a.name))
                if a_choices:
                    choices.append((g.name, a_choices))

            return choices

        debit_options = kwargs.pop('debit_options', {})
        credit_options = kwargs.pop('credit_options', {})
        super(BaseTransactionForm, self).__init__(*args, **kwargs)

        if self.fields.has_key('debit_account'):
            self.fields['debit_account'].choices = _get_choices(debit_options)
        if self.fields.has_key('credit_account'):
            self.fields['credit_account'].choices = _get_choices(credit_options)

    def clean(self):
        if self.data['debit_account'] == self.data['credit_account']:
            raise ValidationError(_('Credit and debit is same account'))

        return self.cleaned_data

class TransactionForm(BaseTransactionForm):
    debit_account = GroupedChoiceField(label=_('Debit'), required=True)
    credit_account = GroupedChoiceField(label=_('Credit'), required=True)
    amount = amount_field
    payed = forms.BooleanField(label=_('Payed'), required=False)
    details = details_field

class DepositWithdrawForm(forms.Form):
    amount = amount_field
    details = details_field

class TransferForm(BaseTransactionForm):
    credit_account = GroupedChoiceField(label=_('To'), required=True)
    amount = amount_field
    details = details_field
