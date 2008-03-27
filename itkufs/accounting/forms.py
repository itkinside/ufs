from django import newforms as forms
from django.newforms.util import ValidationError
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _

from itkufs.accounting.models import *
from itkufs.common.forms import CustomModelForm, CustomForm

class AccountForm(CustomModelForm):
    class Meta:
        model = Account
        exclude = ('slug', 'group')

    def save(self, group=None, **kwargs):
        original_commit = kwargs.pop('commit', True)
        kwargs['commit'] = False
        account = super(AccountForm, self).save(**kwargs)

        if not account.slug:
            account.slug = slugify(account.name)
        if group:
            account.group = group

        if original_commit:
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


class TransactionSettlementForm(CustomModelForm):
    class Meta:
        model = Transaction
        fields = ('settlement',)

class SettlementForm(CustomModelForm):
    class Meta:
        model = Settlement
        exclude = ['group']

class ChangeTransactionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices', (('',''),))
        super(forms.Form, self).__init__(*args, **kwargs)
        self.fields['state'].widget = forms.Select(choices=choices)

    state = forms.CharField(max_length=3, label='', required=False)


class EntryForm(CustomForm):
    debit = forms.DecimalField(min_value=0, required=False)
    credit = forms.DecimalField(min_value=0, required=False)


class DepositWithdrawForm(forms.Form):
    amount = forms.DecimalField(label=_('Amount'), required=True, min_value=0)
    details = forms.CharField(label=_('Details'), required=False,
        widget=forms.widgets.Textarea(attrs={'rows': 2}))


class TransferForm(DepositWithdrawForm):
    credit_account = forms.ChoiceField(label=_('To'), required=True)

    def __init__(self, *args, **kwargs):
        account = kwargs.pop('account')

        super(DepositWithdrawForm, self).__init__(*args, **kwargs)

        if account:
            choices = []

            for a in account.group.user_account_set:
                if a != account:
                    choices.append((a.id, a.name))

            self.fields['credit_account'].choices = choices

class RejectTransactionForm(forms.Form):
    reason = forms.CharField(label=_('Reason'),
        widget=forms.widgets.Textarea(attrs={'rows': 2}), required=True)
