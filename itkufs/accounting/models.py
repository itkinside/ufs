from datetime import datetime

from django.db import models, transaction
from django.db.models import Q
from django.contrib import databrowse
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from itkufs.common.models import Group, Account

# TODO: replace custom save method with validator_lists when Django supports
# this good enough

class InvalidTransaction(Exception):
    def __init__(self, value):
        self.value = value

    def __unicode__(self):
        return u'Invalid transaction: %s' % self.value

class InvalidTransactionEntry(InvalidTransaction):
    def __unicode__(self):
        return u'Invalid transaction entry: %s' % self.value

class InvalidTransactionLog(InvalidTransaction):
    def __unicode__(self):
        return u'Invalid transaction log: %s' % self.value

class Settlement(models.Model):
    date = models.DateField(_('date'))
    comment = models.CharField(_('comment'), max_length=200,
        blank=True, null=True)

    class Meta:
        ordering = ['date']
        verbose_name = _('settlement')
        verbose_name_plural = _('settlements')

    class Admin:
        pass

    def __unicode__(self):
        if self.comment is not None:
            return smart_unicode("%s: %s" % (self.date, self.comment))
        else:
            return smart_unicode(self.date)
databrowse.site.register(Settlement)

# FIXME change to more generic name
TRANSACTIONLOG_TYPE = (
    ('Reg', _('Registered')),
    ('Pay', _('Payed')),
    ('Rec', _('Received')),
    ('Rej', _('Rejected')),
)

class Transaction(models.Model):
    settlement = models.ForeignKey(Settlement, verbose_name=_('settlement'),
        null=True, blank=True)

    last_modified = models.DateTimeField(_('Last modified'), auto_now_add=True)
    status = models.CharField(_('status'), max_length=3, choices=TRANSACTIONLOG_TYPE, blank=True)

    class Meta:
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')
        ordering = ['last_modified']

#    class Admin:
#        list_display = ['status']
#        list_filter = ['status']

    def __unicode__(self):
        if self.entry_set.all().count():
            entries = []
            for entry in self.entry_set.all():
                if entry.debit:
                    entries.append("%s debit %.2f" % (entry.account, entry.debit))
                else:
                    entries.append("%s credit %.2f" % (entry.account, entry.credit))

            return ', '.join(entries)
        else:
            return u'Empty transaction'

    def debug(self):
        status = self.log_set.all()
        return "%s %s" % (self.__unicode__(), status)

    @transaction.commit_manually # TODO check how the state is code fails...
    def save(self):
        try:
           debit_sum = 0
           credit_sum = 0

           for entry in self.entry_set.all():
               debit_sum += float(entry.debit)
               credit_sum += float(entry.credit)

           if debit_sum != credit_sum:
               raise InvalidTransaction(_('Credit and debit do not match'))

           self.last_modifed = datetime.now()

           super(Transaction, self).save()

        except InvalidTransaction, e:
            transaction.rollback()
            raise e
        else:
            transaction.commit()

    def set_registered(self, user=None, message=''):
        self.save()

        if self.id is None:
            self.save()

        if not self.is_registered():
            log = TransactionLog(type='Reg', transaction=self)
            if user:
                log.user = user
            if message is not None and message.strip() != '':
                log.message = message
            log.save()
            self.status = 'Reg'
            self.last_modifed = datetime.now()
            self.save()
        else:
            raise InvalidTransaction(_('Could not set transaction as registered'))

    def set_payed(self, user=None, message=''):
        if not self.is_rejected() and self.is_registered():
            log = TransactionLog(type='Pay', transaction=self)
            if user:
                log.user = user
            if message.strip() != '':
                log.message = message
            log.save()
            self.status = 'Pay'
            self.last_modifed = datetime.now()
            self.save()
        else:
            raise InvalidTransaction(_('Could not set transaction as payed'))

    def set_received(self, user=None, message=''):
        if not self.is_rejected() and self.is_registered() and self.is_payed():
            log = TransactionLog(type='Rec', transaction=self)
            if user:
                log.user = user
            if message.strip() != '':
                log.message = message
            log.save()
            self.status = 'Rec'
            self.last_modifed = datetime.now()
            self.save()
        else:
            raise InvalidTransaction(_('Could not set transaction as received'))

    def reject(self, user=None, message=''):
        if self.is_registered() and not self.is_payed() and not self.is_received():
            log = TransactionLog(type='Rej', transaction=self)
            if user:
                log.user = user
            if message.strip() != '':
                log.message = message
            log.save()
            self.status = 'Rej'
            self.last_modifed = datetime.now()
            self.save()
        else:
            raise InvalidTransaction(_('Could not set transaction as rejected'))
    set_rejected = reject
    set_rejected.__doc__ = 'set_rejected() is an alias for reject()'

    def is_registered(self):
        return self.status in ['Reg', 'Pay', 'Rec']

    def is_payed(self):
        return self.status in ['Pay', 'Rec']

    def is_received(self):
        return self.status == 'Rec'

    def is_rejected(self):
        return self.status == 'Rej'

    def get_registered(self):
        if self.is_registered():
            return self.log_set.filter(type='Reg')[0];
    def get_payed(self):
        if self.is_payed():
            return self.log_set.filter(type='Pay')[0];
    def get_received(self):
        if self.is_received():
            return self.log_set.filter(type='Rec')[0];
    def get_rejected(self):
        if self.is_rejected():
            return self.log_set.filter(type='Rej')[0];

    registered = property(get_registered, None, None)
    received = property(get_received, None, None)
    rejected = property(get_rejected, None, None)
    payed = property(get_payed, None, None)

    def get_valid_logtype_choices(self, user=None):
        # FIXME remove choices that set status for other group...

        debit_group = self.entry_set.filter(debit__gt=0)[0]
        credit_group = self.entry_set.filter(credit__gt=0)[0]

        posible_state = {}
        for k,v in TRANSACTIONLOG_TYPE:
            posible_state[k] = v

        if self.is_rejected() or self.is_received():
            return [('','')]

        if self.is_registered():
            del posible_state['Reg']

        if self.is_payed():
            del posible_state['Pay']
            del posible_state['Rej']

        posible_state = posible_state.items()
        posible_state.insert(0, ('',''))
        return posible_state

    class Admin:
        pass
databrowse.site.register(Transaction)

class TransactionLog(models.Model):
    transaction = models.ForeignKey(Transaction,
        verbose_name=_('transaction'), related_name='log_set',
        edit_inline=models.TABULAR, num_in_admin=3, max_num_in_admin=4,
        num_extra_on_change=1)
    type = models.CharField(_('type'), max_length=3, core=True,
        choices=TRANSACTIONLOG_TYPE)
    timestamp =  models.DateTimeField(_('timestamp'), auto_now_add=True)
    user = models.ForeignKey(User, verbose_name=_('user'))
    message = models.CharField(_('message'), max_length=200, blank=True)

    def save(self):
        if self.id is not None:
            raise InvalidTransactionLog(
                _('Altering transaction log entries is not allowed'))
        if self.transaction.id is None:
            self.transaction.save()
        super(TransactionLog, self).save()

    class Meta:
        unique_together = (('transaction', 'type'),)
        verbose_name = _('transaction log entry')
        verbose_name_plural = _('transaction log entries')

    def __unicode__(self):
        return _(u'%(type)s at %(timestamp)s by %(user)s: %(message)s') % {
            'type': self.get_type_display(),
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M'),
            'user': self.user,
            'message': self.message,
        }
databrowse.site.register(TransactionLog)

class TransactionEntry(models.Model):
    transaction = models.ForeignKey(Transaction,
        verbose_name=_('transaction'), related_name='entry_set',
        edit_inline=models.TABULAR, num_in_admin=5, num_extra_on_change=3)
    account = models.ForeignKey(Account, verbose_name=_('account'), core=True)
    debit = models.DecimalField(_('debit amount'),
        max_digits=10, decimal_places=2, default=0)
    credit = models.DecimalField(_('credit amount'),
        max_digits=10, decimal_places=2, default=0)

    def save(self):
        if self.transaction.is_registered():
            raise InvalidTransactionEntry(
                _("Can't add entries to registered transactions"))

        if self.debit < 0 or self.credit < 0:
            raise InvalidTransactionEntry(
                _('Credit and debit must be positive or zero'))

        if self.debit > 0 and self.credit > 0:
            raise InvalidTransactionEntry(
                _('Only credit or debit may be set'))

        if self.debit == 0 and self.credit == 0:
            raise InvalidTransactionEntry(
                _('Create or debit must be positive'))

        super(TransactionEntry, self).save()

    class Meta:
        unique_together = (('transaction', 'account'),)
        verbose_name = _('transaction entry')
        verbose_name_plural = _('transaction entries')

    def __unicode__(self):
        return _(u'%(account)s: debit %(debit)s, credit %(credit)s') % {
            'account': self.account,
            'debit': self.debit,
            'credit': self.credit,
        }
databrowse.site.register(TransactionEntry)
