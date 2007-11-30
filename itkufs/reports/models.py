from django.db import models
from django.contrib import databrowse
from django.utils.translation import ugettext_lazy as _

from itkufs.accounting.models import *

class List(models.Model):
    name = models.CharField(_('name'), max_length=200)
    slug = models.SlugField(_('slug'), prepopulate_from=['name'])
    account_width = models.PositiveSmallIntegerField(_('account width'),
        help_text=_('Relative size of cell (everything will be converted to precent)'))
    balance_width = models.PositiveSmallIntegerField(_('balance width'),
        help_text=_('Zero value indicates that balance should be left out.'))
    group = models.ForeignKey(Group,
        verbose_name=_('group'), related_name='list_set')
    accounts = models.ManyToManyField(Account, blank="true")

    class Meta:
        #unique_together = (('slug', 'account_group'),)
        verbose_name = _('list')
        verbose_name_plural = _('lists')

    class Admin:
        list_filter = ['group']
        list_display = ['group', 'name']
        list_display_links = ['name']
        ordering = ['group', 'name']

    def __unicode__(self):
        return u'%s: %s' % (self.group, self.name)

    def total_width(self):
        sum = self.account_width + self.balance_width
        for column in self.column_set.all():
            sum += column.width
        return sum

    def total_column_count(self):
        count = self.column_set.all().count() + 1
        if self.balance_width:
            count += 1
        return count

databrowse.site.register(List)

class ListColumn(models.Model):
    name = models.CharField(_('name'), max_length=200, core=True)
    width = models.PositiveSmallIntegerField(_('width'))
    order = models.PositiveSmallIntegerField(_('order'))
    list = models.ForeignKey(List, verbose_name=_('list'),
        edit_inline=models.TABULAR, num_in_admin=5, num_extra_on_change=3, related_name='column_set')

    class Meta:
        ordering = ['order']
        #unique_together = (('name', 'list'),)
        verbose_name = _('list item')
        verbose_name_plural = _('list items')

    def __unicode__(self):
        return u'%s: %s, %s' % (self.list.group, self.list, self.name)
databrowse.site.register(ListColumn)
