from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _

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
            bank = Account(name=_('Bank'), slug='bank', group=self, type='As')
            bank.save()
            cash = Account(name=_('Cash'), slug='cash', group=self, type='As')
            cash.save()

            self.bank_account = bank;
            self.cash_account = cash;
            super(Group, self).save()

    def has_pending_transactions(self):
        transactions = Transaction.objects.filter(
                Q(credit_account__group=self) &
                Q(debit_account__group=self) &
                Q(payed__isnull=True))
        return transactions.count() > 0

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
        return self.name

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
    credit_account = models.ForeignKey(Account,
        verbose_name=_('credit account'), related_name='credit_transactions')
    debit_account = models.ForeignKey(Account,
        verbose_name=_('debit account'), related_name='debit_transactions')
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    details = models.CharField(_('details'), max_length=200,
        blank=True, null=True)
    registered = models.DateTimeField(_('registered'), auto_now_add=True)
    payed = models.DateTimeField(_('payed'), blank=True, null=True)
    #received = models.DateTimeField(blank=True, null=True) # FIXME
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

