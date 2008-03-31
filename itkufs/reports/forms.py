from django import newforms as forms
from django.template.defaultfilters import slugify
from django.newforms.util import ValidationError

from itkufs.reports.models import *
from itkufs.common.forms import CustomModelForm

class ListForm(CustomModelForm):
    class Meta:
        model = List
        exclude = ('slug', 'group')

    def __init__(self, *args, **kwargs):
        group = kwargs.pop('group')
        super(ListForm, self).__init__(*args, **kwargs)

        self.fields['accounts'].widget.choices = [(a.id, a) for a in group.user_account_set]

    def save(self, group=None, **kwargs):
        original_commit = kwargs.pop('commit', True)
        kwargs['commit'] = False
        list = super(ListForm, self).save(**kwargs)

        if not list.slug:
            list.slug = slugify(list.name)
        if group:
            list.group = group

        if original_commit:
            list.save()
        return list

class ColumnForm(CustomModelForm):
    name = forms.CharField(max_length=100, required=False)
    width = forms.IntegerField(min_value=0, required=False, widget=forms.TextInput(attrs={'size': 4, 'class': 'number'}))

    class Meta:
        model = ListColumn
        fields = ('name', 'width')

    def save(self, list=None, **kwargs):
        original_commit = kwargs.pop('commit', True)
        kwargs['commit'] = False
        column = super(ColumnForm, self).save(**kwargs)

        if list:
           column.list = list

        if original_commit:
            column.save()
        return column
