from django import newforms as forms
from django.newforms.util import ValidationError
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _

from itkufs.accounting.models import *
from itkufs.common.forms import CustomModelForm

class AccountForm(CustomModelForm):
    class Meta:
        model = Account
        exclude = ('slug', 'group')

    def save(self, group=None, **kwargs):
        kwargs['commit'] = False
        account = super(AccountForm, self).save(**kwargs)

        if not account.slug:
            account.slug = slugify(account.name)
        if group:
            account.group = group

        account.save()
        return account

class GroupForm(CustomModelForm):
    delete_logo = forms.BooleanField()

    class Meta:
        model = Group
        exclude = ('slug',)

    def save(self, **kwargs):
        kwargs['commit'] = False
        group = super(GroupForm, self).save(**kwargs)

        if not group.slug:
            group.slug = slugify(group.name)

        group.save()
        return group

class TransactionForm(CustomModelForm):
    class Meta:
        model = Transaction
        fields = ('settlement',)

class EntryForm(CustomModelForm):
    class Meta:
        model = TransactionEntry
        fields = ('debit', 'credit')

class DepositWithdrawForm(forms.Form):
    amount = forms.DecimalField(label=_('Amount'), required=True, min_value=0)
    details = forms.CharField(label=_('Details'), required=False,
        widget=forms.widgets.Textarea(attrs={'rows': 2}))

class TransferForm(DepositWithdrawForm):
    to_account = forms.ChoiceField(label=_('To'), required=True)

    def __init__(self, *args, **kwargs):
        account = kwargs.pop('account')

        super(DepositWithdrawForm, self).__init__(*args, **kwargs)

        if account:
            self.fields['to_account'].choices = [(account.id, account.name)
                for account in account.group.user_account_set]


"""
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
                groups = Group.objects.filter(
                    pk__in=[g.id for g in limit_groups]).exclude(
                    pk__in=[g.id for g in exclude_groups])
            elif limit_groups:
                groups = Group.objects.filter(
                    pk__in=[g.id for g in limit_groups])
            elif exclude_groups:
                groups = Group.objects.exclude(
                    pk__in=[g.id for g in exclude_groups])
            else:
                groups = Group.objects.all()

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
        if 'debit_account' in self.data and 'credit_account' in self.data:
            if self.data['debit_account'] == self.data['credit_account']:
                raise ValidationError(_('Credit and debit is same account'))

        return self.cleaned_data

class TransactionForm(BaseTransactionForm):
    debit_account = GroupedChoiceField(label=_('Debit'), required=True)
    credit_account = GroupedChoiceField(label=_('Credit'), required=True)
    amount = amount_field
    registered = forms.BooleanField(label=_('Registered'), required=False)
    payed = forms.BooleanField(label=_('Payed'), required=False)
    received = forms.BooleanField(label=_('Received'), required=False)
    details = details_field

class DepositWithdrawForm(forms.Form):
    amount = amount_field
    details = details_field

class TransferForm(BaseTransactionForm):
    credit_account = GroupedChoiceField(label=_('To'), required=True)
    amount = amount_field
    details = details_field

class ChangeTransactionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices', (('',''),))
        super(forms.Form, self).__init__(*args, **kwargs)
        self.fields['state'].widget = forms.Select(choices=choices)

    state = forms.CharField(max_length=3, label='', required=False)

class RejectTransactionForm(forms.Form):
    reason = forms.CharField(label=_('Reason'),
        widget=forms.widgets.Textarea(attrs={'rows': 2}), required=True)

"""
