from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _
from django.core.validators import *

#FIXME replace custom save method with validator_lists where this can be done
#      and makes sense

class Group(models.Model):
    name = models.CharField(_('name'), max_length=100)
    slug = models.SlugField(_('slug'), prepopulate_from=['name'], unique=True,
        help_text=_('A shortname used in URLs etc.'))
    warn_limit = models.IntegerField(_('warn limit'), null=True, blank=True)
    block_limit = models.IntegerField(_('block limit'), null=True, blank=True)
    admins = models.ManyToManyField(User, verbose_name=_('admins'),
        null=True, blank=True)
    bank_account = models.ForeignKey('Account', verbose_name=_('bank account'),
        null=True, blank=True, related_name='foo', editable=False)
    cash_account = models.ForeignKey('Account', verbose_name=_('cash account'),
        null=True, blank=True, related_name='bar', editable=False)
    # FIXME: Fix related name of *_account
    # FIXME: Probably needs to add sales_account etc.

    logo = models.ImageField(upload_to='logos', null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('group')
        verbose_name_plural = _('groups')

    class Admin:
        pass

    def __unicode__(self):
        return self.name

    def save(self):
        super(Group, self).save()
        # Create default accounts
        if not self.account_set.count():
            # FIXME _('Bank') and _('Cash') does not seem to work here...
            # Could the problem be related to lazy/non-lazy ugettext?
            bank = Account(name='Bank', slug='bank', type='As', group=self)
            bank.save()
            cash = Account(name='Cash', slug='cash', type='As', group=self)
            cash.save()

            self.bank_account = bank;
            self.cash_account = cash;
            super(Group, self).save()

    def user_account_set(self):
        """Returns queryset of user accounts"""
        return self.account_set.filter(type='Li', owner__isnull=False)

    def group_account_set(self):
        """Returns array of group accounts"""
        return self.account_set.exclude(type='Li', owner__isnull=False)

    def transaction_set(self):
        """Returns all transactions connected to group"""
        return Transaction.objects.filter(
                Q(credit_account__group=self) &
                Q(debit_account__group=self))

    def registered_transaction_set(self):
        """Returns all transactions connected to group, that are not rejected"""
        # FIXME implement
        return Transaction.objects.none()

    def payed_transaction_set(self):
        """Returns all payed transactions connected to group, that are not rejected"""
        # FIXME filter out rejected
        return self.transaction_set().filter(payed__isnull=False)

    def not_payed_transaction_set(self):
        """Returns all unpayed transactions connected to group, that are not rejected"""
        # FIXME filter out rejected
        return self.transaction_set().filter(payed__isnull=True)

    def recieved_transaction_set(self):
        """Returns all recieved transactions connected to group"""
        # FIXME implement
        return Transaction.objects.none()

    def not_recieved_transaction_set(self):
        """Returns all transactions that have not been recieved connected to group"""
        # FIXME implement
        return Transaction.objects.none()

    def rejected_transaction_set(self):
        """Returns all transactions connected to group, that have been rejected"""
        # FIXME implement
        return Transaction.objects.none()


ACCOUNT_TYPE = (
    ('As', _('Asset')),     # Eiendeler/aktiva
    ('Li', _('Liability')), # Gjeld/passiva
    ('Eq', _('Equity')),    # Egenkapital
    ('In', _('Income')),    # Inntekt
    ('Ex', _('Expense')),   # Utgift
)

class Account(models.Model):
    name = models.CharField(_('name'), max_length=100)
    slug = models.SlugField(_('slug'), prepopulate_from=['name'],
        help_text=_('A shortname used in URLs etc.'))
    group = models.ForeignKey(Group, verbose_name=_('group'))
    type = models.CharField(_('type'), max_length=2, choices=ACCOUNT_TYPE,
        default='Li')
    owner = models.ForeignKey(User, verbose_name=_('owner'),
        null=True, blank=True)
    active = models.BooleanField(_('active'), default=True)
    ignore_block_limit = models.BooleanField(_('ignore block limit'),
        default=False)

    class Meta:
        ordering = ['group', 'type', 'name']
        unique_together = (('slug', 'group'),)
        verbose_name = _('account')
        verbose_name_plural = _('accounts')

    class Admin:
        fields = (
            (None,
                {'fields': ('name', 'slug', 'group', 'owner')}),
            (_('Advanced options'), {
                'classes': 'collapse',
                'fields' : ('type', 'active', 'ignore_block_limit')}),
        )
        list_display = ['group', 'name', 'type', 'owner', 'balance',
            'active', 'ignore_block_limit']
        list_display_links = ['name']
        list_filter = ['active', 'type', 'group']
        list_per_page = 20
        search_fields = ['name']

    def __unicode__(self):
        return "%s: %s" % (self.group, self.name)

    def debit_to_increase(self):
        """Returns True if account type uses debit to increase, False if using
        credit to increase, and None for all equity accounts."""

        if self.type in ('Li', 'In'):
            # Credit to increase
            return False
        elif self.type in ('As', 'Ex'):
            # Debit to increase
            return True
        else:
            # Equity accounts: Credit to increase for capital accounts, debit
            # to increase of drawing accounts
            return None

    def balance(self):
        """Returns account balance"""

        balance = 0

        for t in self.credit_transactions.filter(payed__isnull=False):
            balance -= t.amount
        for t in self.debit_transactions.filter(payed__isnull=False):
            balance += t.amount

        return balance

    def balance_credit_reversed(self):
        """Returns account balance. If the account is an credit account, the
        balance is multiplied with -1."""

        balance = self.balance()
        if balance == 0 or self.debit_to_increase():
            return balance
        else:
            return -1 * balance

    def is_user_account(self):
        """Returns true if a user account"""

        if self.owner is not None and self.type == 'Li':
            return True
        else:
            return False

    def is_blocked(self):
        """Returns true if user account balance is below group block limit"""

        if (not self.is_user_account()
            or self.ignore_block_limit
            or self.group.block_limit is None):
            return False
        return self.balance_credit_reversed() < self.group.block_limit

    def needs_warning(self):
        """Returns true if user account balance is below group warn limit"""

        if (not self.is_user_account()
            or self.ignore_block_limit
            or self.group.warn_limit is None):
            return False
        return self.balance_credit_reversed() < self.group.warn_limit

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

class InvalidTransaction(Exception):
    def __init__(self, value):
        self.value = value

    def __unicode__(self):
        return u'Invalid transaction: %s' % self.value

class Transaction(models.Model):
    # FIXME: This model is deprecated and should be removed
    credit_account = models.ForeignKey(Account,
        verbose_name=_('credit account'), related_name='credit_transactions')
    debit_account = models.ForeignKey(Account,
        verbose_name=_('debit account'), related_name='debit_transactions')
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    details = models.CharField(_('details'), max_length=200,
        blank=True, null=True)
    registered = models.DateTimeField(_('registered'), auto_now_add=True)
    payed = models.DateTimeField(_('payed'), blank=True, null=True)
    settlement = models.ForeignKey(Settlement, verbose_name=_('settlement'),
        null=True, blank=True)

    class Meta:
        ordering = ['registered', 'payed']
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')

    class Admin:
        list_display = ['amount', 'credit_account', 'debit_account',
                        'settlement']
        list_filter = ['credit_account', 'debit_account', 'settlement']

    def __unicode__(self):
        return _(u'%(amount)s, credit %(credit_acc)s, debit %(debit_acc)s') % {
            'amount': self.amount,
            'credit_acc': self.credit_account,
            'debit_acc': self.debit_account
        }

    def save(self):
        if float(self.amount) < 0:
            raise InvalidTransaction, _('Amount is negative.')
        if self.amount == 0:
            raise InvalidTransaction, _('Amount is zero.')
        if self.credit_account == self.debit_account:
            raise InvalidTransaction, _('Credit and debit is same account.')
        super(Transaction, self).save()

class NewTransaction(models.Model):
    settlement = models.ForeignKey(Settlement, verbose_name=_('settlement'),
        null=True, blank=True)

    class Meta:
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')

    def __init__(self, *args, **kwargs):
        entries = kwargs.pop('entries', [])
        user = kwargs.pop('user', None)
        super(NewTransaction, self).__init__(*args, **kwargs)
        self.entries = entries
        self.user = user

    def save(self):
        # FIXME transaction or some other form of rollback
        try:
            seen = []
            debit_sum = 0
            credit_sum = 0

            for e in self.entry_set.all():
                if e.account in seen:
                    raise InvalidTransaction('Account is already part of this transaction')
                else:
                    seen.append(e.account)

                debit_sum += float(e.debit)
                credit_sum += float(e.credit)

            if debit_sum != credit_sum:
                raise InvalidTransaction('Credit and debit do not match')

            super(NewTransaction, self).save()

            if not self.is_registered():
                TransactionLog(type='Reg', transaction=self).save()

        except InvalidTransaction:
            # Nuke all transaction entries on error
            self.entry_set.all().delete()
            # self.delete() # FIXME? self implode?
            raise

    def set_payed(self):
        if not self.is_rejected() and self.is_registered():
            TransactionLog(type='Pay', transaction=self).save()
        else:
            raise InvalidTransaction('Could not set transaction as payed')

    def set_recieved(self):
        if not self.is_rejected() and self.is_registered() and self.is_payed():
            TransactionLog(type='Rec', transaction=self).save()
        else:
            raise InvalidTransaction('Could not set transaction as recieved')

    def reject(self, reason):
        if self.is_registered() and not self.is_payed() and not self.is_received():
            TransactionLog(type='Rej', transaction=self, message=reason).save()
        else:
            raise InvalidTransaction('Could not set transaction as rejected')

    def is_registered(self):
        return self.log_set.filter(type='Reg').count() > 0

    def is_payed(self):
        return self.log_set.filter(type='Pay').count() > 0

    def is_received(self):
        return self.log_set.filter(type='Rec').count() > 0

    def is_rejected(self):
        return self.log_set.filter(type='Rej').count() > 0

    class Admin:
        pass

TRANSACTIONLOG_TYPE = (
    ('Reg', _('Registered')),
    ('Pay', _('Payed')),
    ('Rec', _('Received')),
    ('Rej', _('Rejected')),
)

class TransactionLog(models.Model):
    transaction = models.ForeignKey(NewTransaction,
        verbose_name=_('transaction'), related_name='log_set',
        edit_inline=models.TABULAR, num_in_admin=1, max_num_in_admin=4,
        num_extra_on_change=1)
    type = models.CharField(_('type'), max_length=3, core=True,
        choices=TRANSACTIONLOG_TYPE)
    # FIXME: Rename to timestamp?
    time = models.DateTimeField(_('timestamp'), auto_now_add=True)
    user = models.ForeignKey(User, verbose_name=_('user'),
        null=True, blank=True)
    message = models.CharField(_('message'), max_length=200,
        blank=True, null=True)

    class Meta:
        unique_together = (('transaction', 'type'),)
        verbose_name = _('transaction log entry')
        verbose_name_plural = _('transaction log entries')

    def __unicode__(self):
        return _(u'%(type)s at %(timestamp)s by %(user)s: %(message)s') % {
            'type': self.get_type_display(),
            # FIXME: Rename time to timestamp
            'timestamp': self.time.strftime('%Y-%m-%d %H:%M'),
            'user': self.user,
            'message': self.message,
        }

class TransactionEntry(models.Model):
    transaction = models.ForeignKey(NewTransaction,
        verbose_name=_('transaction'), related_name='entry_set',
        edit_inline=models.TABULAR, num_in_admin=5, num_extra_on_change=3)
    account = models.ForeignKey(Account, verbose_name=_('account'), core=True)
    debit = models.DecimalField(_('debit amount'),
        max_digits=10, decimal_places=2, default=0)
    credit = models.DecimalField(_('credit amount'),
        max_digits=10, decimal_places=2, default=0)

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

class List(models.Model):
    name = models.CharField(_('name'), max_length=200)
    slug = models.SlugField(_('slug'), prepopulate_from=['name'])
    account_width = models.PositiveSmallIntegerField(_('account width'),
        help_text=_('Relative size of cell (everything will be converted to precent)'))
    balance_width = models.PositiveSmallIntegerField(_('balance width'),
        help_text=_('Zero value indicates that balance should be left out.'))
    group = models.ForeignKey(Group,
        verbose_name=_('group'), related_name='list_set')

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
        for item in self.item_set.all():
            sum += item.width
        return sum

class ListItem(models.Model):
    name = models.CharField(_('name'), max_length=200, core=True)
    width = models.PositiveSmallIntegerField(_('width'))
    order = models.PositiveSmallIntegerField(_('order'))
    list = models.ForeignKey(List, verbose_name=_('list'),
        edit_inline=models.TABULAR, num_in_admin=5, related_name='item_set')

    class Meta:
        ordering = ['order']
        #unique_together = (('name', 'list'),)
        verbose_name = _('list item')
        verbose_name_plural = _('list items')

    def __unicode__(self):
        return u'%s: %s, %s' % (self.list.group, self.list, self.name)

