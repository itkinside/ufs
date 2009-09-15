from django import forms
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext as _

from itkufs.accounting.models import Account
from itkufs.billing.models import Bill, BillingLine


class BillForm(forms.ModelForm):
    charge_to = forms.ModelChoiceField(Account)

    class Meta:
        model = Bill
        exclude = ('transaction',)

    def __init__(self, group, *args, **kwargs):
        super(BillForm, self).__init__(*args, **kwargs)

        instance = kwargs.get('instance', None)

        accounts = group.account_set.filter(type=Account.INCOME_ACCOUNT)

        self.fields['charge_to'].queryset = accounts
        self.fields['charge_to'].label_from_instance = lambda obj: obj.name

class BillingLineForm(forms.ModelForm):
    description = forms.CharField(max_length=100, required=False)
    amount= forms.DecimalField(min_value=0, max_digits=10, decimal_places=2,
                               required=False,
                               widget=forms.TextInput(attrs={'size': 4, 'class': 'number'}))

    def clean(self):
        amount = self.cleaned_data.get('amount', -1)
        description  = self.cleaned_data.get('description', None)
        errors = []

        if amount > 0 and description.strip():
            return self.cleaned_data

        if not description.strip():
            errors.append(_('Description missing'))

        if not amount > 0:
            errors.append(_('Amount missing'))

        raise forms.ValidationError(errors)

    class Meta:
        model = BillingLine
        fields = ('description', 'amount')


def get_billingline_formset(extra):
    return inlineformset_factory(Bill, BillingLine, extra=extra,
                                 can_delete=False, form=BillingLineForm)
