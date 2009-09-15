from django.db import models
from django.utils.translation import ugettext_lazy as _

from itkufs.accounting.models import Transaction

class Bill(models.Model):
    created = models.DateTimeField(_('created'), auto_now_add=True)

    transaction = models.ForeignKey(Transaction)
    description = models.TextField(_('description'))

    def __unicode__(self):
        return u'%s - %s' % (self.created, self.description)

class BillingLine(models.Model):
    bill = models.ForeignKey(Bill)

    description = models.CharField(_('description'), max_length=100)
    amount = models.DecimalField(_('amount'),
        max_digits=10, decimal_places=2, default=0)

    def __unicode__(self):
        return u'%s - %s' % (self.description, self.amount)
