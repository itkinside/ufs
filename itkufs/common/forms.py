from django import forms
from django.forms.models import ModelForm
from django.forms.forms import BoundField, Form
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth import get_backends

from itkufs.accounting.models import Group, Account, RoleAccount

class AccountForm(ModelForm):
    owner = forms.CharField(required=False)

    class Meta:
        model = Account
        exclude = ('slug', 'group', 'owner')

    def __init__(self, *args, **kwargs):
        group = kwargs.pop('group', None)

        if kwargs['instance'] and kwargs['instance'].owner:
            initial = kwargs.pop('initial', {})
            initial['owner'] = kwargs['instance'].owner.username
            kwargs['initial'] = initial

        super(AccountForm, self).__init__(*args, **kwargs)

        self.group = group

    def clean_name(self):
        name = self.cleaned_data['name']

        if self.group:
            accounts = self.group.account_set.filter(name=name)

            if self.instance:
                accounts = accounts.exclude(id=self.instance.id).count()
            else:
                accounts = accounts.count()

            if accounts:
                raise forms.ValidationError(
                    _('An account with this name allready exists'))

        return name

    def clean_owner(self):
        owner = self.cleaned_data['owner']

        for b in get_backends():
            if hasattr(b, 'create_user'):
                user = b.create_user(owner)

            if user:
                break

        if not user:
            raise forms.ValidationError(
                _('Username does not exist'))

        if self.group:
            accounts = self.group.account_set.filter(owner=user)

            if self.instance:
                accounts = accounts.exclude(id=self.instance.id).count()
            else:
                accounts = accounts.count()

            if accounts:
                raise forms.ValidationError(
                    _('Users may only have one account per group'))

        return user

    def save(self, group=None, **kwargs):
        original_commit = kwargs.pop('commit', True)
        kwargs['commit'] = False

        account = super(AccountForm, self).save(**kwargs)

        if not account.slug:
            if account.owner:
                account.slug = account.owner.username
            else:
                account.slug = slugify(account.name)
        if group:
            account.group = group

        if original_commit:
            account.save()
        return account


class GroupForm(ModelForm):
    delete_logo = forms.BooleanField(required=False)

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

class RoleAccountForm(Form):
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

