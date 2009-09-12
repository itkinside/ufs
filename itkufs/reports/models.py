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
    slug = models.SlugField(_('slug'))
    account_width = models.PositiveSmallIntegerField(_('account name width'),
        help_text=_('Relative width of cell, 0 to hide'))
    short_name_width = models.PositiveSmallIntegerField(_('short name width'),
        help_text=_('Relative width of cell, 0 to hide'))
    balance_width = models.PositiveSmallIntegerField(_('balance width'),
        help_text=_('Relative width of cell, 0 to hide'))
    group = models.ForeignKey(Group,
        verbose_name=_('group'), related_name='list_set')

    public = models.BooleanField(_('Public'), default=False,
        help_text=_('Should this list be publicly available'))

    add_active_accounts = models.BooleanField(_('Add active user accounts'),
        default=True, help_text=_('Should all active accounts be added by default'))

    extra_accounts = models.ManyToManyField(Account, blank="true")

    orientation = models.CharField(_('orientation'), max_length=1, choices=ORIENTATION_CHOICES)
    comment = models.TextField(_('comment'), blank=True, help_text=_('Comment shown at bottom on first page'))

    double = models.BooleanField(
        help_text=_('Use two rows per account'), default=False)
    ignore_blocked = models.BooleanField(_('ignore blocked'),
        help_text=_("Don't exclude blocked accounts"))

    class Meta:
        unique_together = (('slug', 'group'),)
        verbose_name = _('list')
        verbose_name_plural = _('lists')

        ordering = ('name',)

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
    name = models.CharField(_('name'), max_length=200)
    width = models.PositiveSmallIntegerField(_('width'))
    list = models.ForeignKey(List, verbose_name=_('list'),
        related_name='column_set')

    class Meta:
        ordering = ['id']
        #unique_together = (('name', 'list'),)
        verbose_name = _('list item')
        verbose_name_plural = _('list items')

    def __unicode__(self):
        return u'%s: %s, %s' % (self.list.group, self.list, self.name)
