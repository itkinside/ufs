from django import forms
from django.forms.forms import BoundField
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify

from itkufs.reports.models import List, ListColumn
from itkufs.accounting.models import Account, TransactionEntry


class ListTransactionForm(forms.Form):
    def __init__(self, list_, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.column_fields = []
        self.account_fields = []

        credit_accounts = Account.objects.filter(
            active=True, group_account=True, group=list_.group_id
        )
        self.fields["credit_account"] = forms.ModelChoiceField(credit_accounts)
        self.fields["credit_account"].label_from_instance = lambda a: a.name

        columns = list(list_.column_set.all())
        for c in columns:
            name = "entry-%d" % c.id
            fieldkwargs = {"min_value": 0, "label": c.name}
            if c.name.isdigit():
                fieldkwargs["initial"] = c.name
            formfield = forms.IntegerField(**fieldkwargs)
            formfield.widget.attrs["size"] = 1
            self.fields[name] = formfield
            self.column_fields.append((name, formfield))

        for a in list_.accounts():
            account_columns_field = []
            for c in columns:
                name = "entry-%d-%d" % (c.id, a.id)
                formfield = forms.IntegerField(
                    min_value=0, label=c.name, required=False
                )
                formfield.widget.attrs["size"] = 1
                self.fields[name] = formfield
                account_columns_field.append((name, formfield))
            self.account_fields.append((a, account_columns_field))

    def columns(self):
        for name, field in self.column_fields:
            yield BoundField(self, field, name)

    def accounts(self):
        for account, fields in self.account_fields:
            boundfields = []
            for name, field in fields:
                boundfields.append(BoundField(self, field, name))
            yield (account, boundfields)

    def clean(self):
        for account, fields in self.account_fields:
            for name, field in fields:
                if self.cleaned_data.get(name, 0) > 0:
                    return self.cleaned_data
        raise forms.ValidationError(
            _("Please fill in at least one account entry.")
        )

    def transaction_entries(self):
        if not self.is_valid():
            return None

        credit_account = self.cleaned_data["credit_account"]
        entries = []
        total = 0

        for account, fields in self.account_fields:
            amount = 0
            for name, field in fields:
                count = self.cleaned_data.get(name, 0) or 0
                price = self.cleaned_data["-".join(name.split("-")[:-1])]
                amount += count * price
            if amount > 0:
                total += amount
                entries.append(TransactionEntry(account=account, debit=amount))

        if total > 0:
            entries.append(
                TransactionEntry(account=credit_account, credit=total)
            )

        return entries


class ListForm(forms.ModelForm):
    class Meta:
        model = List
        exclude = ("slug", "group")

    def __init__(self, *args, **kwargs):
        group = kwargs.pop("group")
        super().__init__(*args, **kwargs)

        self.fields["extra_accounts"].choices = [
            (a.id, a.name) for a in group.account_set.all()
        ]

    def clean(self):
        account_width = self.cleaned_data.get("account_width", 0)
        short_name_width = self.cleaned_data.get("short_name_width", 0)

        if account_width == 0 and short_name_width == 0:
            fields = {
                "field1": self.fields["account_width"].label,
                "field2": self.fields["short_name_width"].label,
            }

            raise forms.ValidationError(
                _('"%(field1)s" or "%(field2)s" must be greater than zero')
                % fields
            )
        return self.cleaned_data

    def save(self, group=None, **kwargs):
        original_commit = kwargs.pop("commit", True)

        kwargs["commit"] = False
        list = super().save(**kwargs)

        if not list.slug:
            list.slug = slugify(list.name)
        if group:
            list.group = group

        if original_commit:
            list.save()
            list.extra_accounts = self.cleaned_data["extra_accounts"]

        return list


class ColumnForm(forms.ModelForm):
    name = forms.CharField(max_length=100, required=False)
    width = forms.IntegerField(
        min_value=0,
        required=False,
        widget=forms.TextInput(attrs={"size": 4, "class": "number"}),
    )

    def clean(self):
        if self.cleaned_data["width"] and not self.cleaned_data["name"]:
            raise forms.ValidationError(_("Name missing"))
        elif not self.cleaned_data["width"] and self.cleaned_data["name"]:
            raise forms.ValidationError(_("Width missing"))

        return self.cleaned_data

    class Meta:
        model = ListColumn
        fields = ("name", "width")
