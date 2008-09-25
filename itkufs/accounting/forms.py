from django import forms
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
from django.forms.models import ModelForm
from django.forms.forms import Form

from itkufs.accounting.models import *

class SettlementForm(ModelForm):
    class Meta:
        model = Settlement
        exclude = ['group']

    def __init__(self, *args, **kwargs):
        super(SettlementForm, self).__init__(*args, **kwargs)
        if 'instance' not in kwargs:
            del self.fields['closed']


class TransactionSettlementForm(ModelForm):
    details = forms.CharField(label=_('Details'), required=False,
        widget=forms.widgets.Textarea(attrs={'rows': 2}))

    def __init__(self, *args, **kwargs):
        super(TransactionSettlementForm, self).__init__(*args, **kwargs)

        if 'instance' in kwargs:
            self.fields['settlement'].choices = [('', '')] + [(s.id, s)
                for s in kwargs['instance'].group.settlement_set.filter(closed=False)]

    class Meta:
        model = Transaction
        fields = ('settlement',)


class ChangeTransactionForm(forms.Form):
    change_to = forms.CharField(max_length=3, required=False)

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices', (('',''),))
        label = kwargs.pop('label', True)
        super(forms.Form, self).__init__(*args, **kwargs)

        if not label:
            self.fields['change_to'].label = ''
        self.fields['change_to'].widget = forms.Select(choices=choices)


class EntryForm(Form):
    # FIXME add clean_debit/credit so that we can ignore whitespaces :)
    debit = forms.DecimalField(min_value=0, required=False,
        widget=forms.TextInput(attrs={'size': 4, 'class': 'number'}))
    credit = forms.DecimalField(min_value=0, required=False,
        widget=forms.TextInput(attrs={'size': 4, 'class': 'number'}))


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

