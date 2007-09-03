from django import newforms as forms

from itkufs.accounting.models import *
from itkufs.widgets import *

amount_field = forms.DecimalField(required=True)
details_field = forms.CharField(widget=forms.widgets.Textarea(attrs={'rows':2}), required=False)

class BaseTransactionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        def _get_choices(options={}):
            limit_groups = options.pop('limit_to_groups', ())
            exclude_users = options.pop('exclude_users', ())
            user_account = options.pop('user_accounts', False)
            exclude_groups = options.pop('exclude_groups', ())
            group_account = options.pop('group_accounts', False)

            # FIXME Clean up code please
            # FIXME exlcude user not working yet...
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

            choices = [(False, (('',''),))]
            for g in groups:
                a_choices = []
                for a in g.account_set.all():
                    if (a.is_user_account() and user_account) or (not a.is_user_account() and group_account):
                        a_choices.append((a.id, a.name))
                if a_choices:
                    choices.append((g.name, a_choices))
            return choices

        to_options = kwargs.pop('to_options', {})
        from_options = kwargs.pop('from_options', {})
        super(BaseTransactionForm, self).__init__(*args, **kwargs)

        if self.fields.has_key('to_account'):
            self.fields['to_account'].choices = _get_choices(to_options)
        if self.fields.has_key('from_account'):
            self.fields['from_account'].choices = _get_choices(from_options)


class TransactionForm(BaseTransactionForm):
    to_account = GroupedChoiceField(label="To", required=True)
    from_account = GroupedChoiceField(label="From", required=True)
    amount = amount_field
    payed = forms.BooleanField(required=False)
    details = details_field

class DepositWithdrawForm(forms.Form):
    amount = amount_field
    details = details_field

class TransferForm(BaseTransactionForm):
    to_account = GroupedChoiceField(label="To", required=True)
    amount = amount_field
    details = details_field


class ApproveForm(forms.Form):
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('transactions', {})
        super(ApproveForm, self).__init__(*args, **kwargs)
        for c in choices:
            self.fields['transactions'].choices.append((c.id,c))
    transactions = forms.MultipleChoiceField(widget=forms.widgets.CheckboxSelectMultiple())
