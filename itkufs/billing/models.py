from django.db import models
from django.utils.translation import ugettext_lazy as _

from itkufs.accounting.models import Group, Transaction


class Bill(models.Model):
    created = models.DateTimeField(_('created'), auto_now_add=True)
    description = models.TextField(_('description'))

    group = models.ForeignKey(Group)
    transaction = models.ForeignKey(Transaction, null=True, blank=True)

    def __unicode__(self):
        return u'%s - %s' % (self.created, self.description[:30])

    def is_editable(self):
        return self.transaction_id is None

    @property
    def status(self):
        if self.is_editable():
            return _('Pending')
        else:
            return _('Committed')

    def css_class(self):
        if self.is_editable():
            return 'pending'
        else:
            return 'committed'


class BillingLine(models.Model):
    bill = models.ForeignKey(Bill)

    description = models.CharField(_('description'), max_length=100)
    amount = models.DecimalField(
        _('amount'), max_digits=10, decimal_places=2, default=0)

    def __unicode__(self):
        return u'%s - %s' % (self.description, self.amount)
