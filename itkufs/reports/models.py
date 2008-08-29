from django.db import models
from django.utils.translation import ugettext_lazy as _

from itkufs.accounting.models import Group, Account


class ListManager(models.Manager):
    def get_query_set(self):
        return super(ListManager,self).get_query_set().extra(
            select={
            'listcolumn_count':
                """
                SELECT COUNT(*) FROM reports_listcolumn
                WHERE reports_listcolumn.list_id = reports_list.id
                """,
            'listcolumn_width':
                """
                    SELECT SUM(reports_listcolumn.width) FROM reports_listcolumn
                    WHERE reports_listcolumn.list_id = reports_list.id
                """
            }
        )


class List(models.Model):
    objects = ListManager()

    LANDSCAPE = 'L'
    PORTRAIT = 'P'
    ORIENTATION_CHOICES = (
        ('L', _('Landscape')),
        ('P', _('Portrait'))
    )

    name = models.CharField(_('name'), max_length=200)
    slug = models.SlugField(_('slug'), prepopulate_from=['name'])
    account_width = models.PositiveSmallIntegerField(_('account width'),
        help_text=_('Relative width of cell'))
    balance_width = models.PositiveSmallIntegerField(_('balance width'),
        help_text=_('Relative width of cell, 0 to hide'))
    group = models.ForeignKey(Group,
        verbose_name=_('group'), related_name='list_set')
    accounts = models.ManyToManyField(Account, blank="true")
    orientation = models.CharField(_('orientation'), max_length=1, choices=ORIENTATION_CHOICES)
    comment = models.TextField(_('comment'), blank=True, help_text=_('Comment shown at bottom on first page'))

    # Set as editable=False as pdf does not support this (FIXME?)
    double = models.BooleanField(
        help_text=_('Use two rows per account'), editable=False)
    ignore_blocked = models.BooleanField(
        help_text=_("Don't exclude blocked accounts"))

    class Meta:
        unique_together = (('slug', 'group'),)
        verbose_name = _('list')
        verbose_name_plural = _('lists')

    class Admin:
        list_filter = ('group',)
        list_display = ('group', 'name')
        list_display_links = ('name',)
        ordering = ('group', 'name')

    def __unicode__(self):
        return u'%s: %s' % (self.group, self.name)

    def total_width(self):
        return int(self.account_width
            + self.balance_width
            + self.listcolumn_width)

    def total_column_count(self):
        count = self.listcolumn_count + 1
        if self.balance_width:
            count += 1
        return int(count)


class ListColumn(models.Model):
    name = models.CharField(_('name'), max_length=200, core=True)
    width = models.PositiveSmallIntegerField(_('width'))
    list = models.ForeignKey(List, verbose_name=_('list'),
        edit_inline=models.TABULAR, num_in_admin=8, num_extra_on_change=3,
        related_name='column_set')

    class Meta:
        ordering = ['id']
        #unique_together = (('name', 'list'),)
        verbose_name = _('list item')
        verbose_name_plural = _('list items')

    def __unicode__(self):
        return u'%s: %s, %s' % (self.list.group, self.list, self.name)
