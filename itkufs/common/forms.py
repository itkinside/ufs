from django import forms
from django.forms.models import ModelForm
from django.forms.forms import BoundField, Form
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from itkufs.accounting.models import Group, Account, RoleAccount

def as_table_row(self):
    """Returns this form rendered as HTML <td>s -- excluding the
       <table></table> and <tr></tr>."""
    output = []
    for name, field in self.fields.items():
        bf = BoundField(self, field, name)

        if bf.errors:
            error = u' class="error"'
        else:
            error = u''

        output.append("<td%s>%s</td>" %(error, bf))

    return mark_safe(u'\n'.join(output))


class CustomModelForm(ModelForm):
    pass
CustomModelForm.as_table_row = as_table_row


class CustomForm(Form):
    pass
CustomForm.as_table_row = as_table_row


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

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(GroupForm, self).__init__(*args, **kwargs)
        if 'instance' not in kwargs or kwargs['instance'].logo == '':
            del self.fields['delete_logo']

    def clean_admins(self):
        errors = []
        if len(self.cleaned_data['admins']) == 0:
            errors.append(_('The group must have at least one admin'))

        if self.user and self.user not in self.cleaned_data['admins']:
            errors.append(_('You are not allowed to remove your own admin privileges'))

        if errors:
            raise forms.ValidationError(errors)

        return self.cleaned_data['admins']

    def save(self, *args, **kwargs):
        original_commit = kwargs.pop('commit', True)
        kwargs['commit'] = False
        group = super(GroupForm, self).save(*args, **kwargs)

        if not group.slug:
            group.slug = slugify(group.name)

        kwargs['commit'] = original_commit
        return super(GroupForm, self).save(*args, **kwargs)

class RoleAccountModelChoiceField(forms.models.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name

class RoleAccountForm(CustomForm):
    def __init__(self, *args, **kwargs):
        group = kwargs.pop('group', None)
        super(RoleAccountForm, self).__init__(*args, **kwargs)

        if group:
            for type, name in RoleAccount.ACCOUNT_ROLE:
                try:
                    intial = RoleAccount.objects.get(group=group, role=type).account.id
                except RoleAccount.DoesNotExist:
                    intial = ''

                self.fields[type] = RoleAccountModelChoiceField(group.group_account_set, initial=intial)
        else:
            raise Exception('Please supply a group kwarg for RoleAccountForm')

