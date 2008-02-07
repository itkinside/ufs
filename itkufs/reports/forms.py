from django import newforms as forms
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _

from itkufs.reports.models import *
from itkufs.common.forms import CustomModelForm

class ListForm(CustomModelForm):
    class Meta:
        model = List
        exclude = ('slug', 'group')

class ColumnForm(CustomModelForm):
    class Meta:
        model = ListColumn
        fields = ('name', 'width')
