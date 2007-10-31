from django.db import models
from django.contrib.auth.models import User
from django.utils.encoding import smart_unicode

class AccountGroup(models.Model):
    name = models.CharField(maxlength=100)
    slug = models.SlugField(prepopulate_from=['name'], unique=True,
        help_text='A shortname used in URLs etc.')
    warn_limit = models.IntegerField(null=True, blank=True)
    block_limit = models.IntegerField(null=True, blank=True)
    admins = models.ManyToManyField(User, null=True, blank=True)
    bank_account = models.ForeignKey('Account', null=True, blank=True, related_name="foo", editable=False)
    cash_account = models.ForeignKey('Account', null=True, blank=True, related_name="bar", editable=False)

    def __unicode__(self):
        return self.name
    def __str__(self):
        return self.name

    def save(self):
        models.Model.save(self)
        # Create default accounts
        if not self.account_set.count():
            bank = Account(name='Bank', slug='bank', group=self, type='As')
            bank.save()
            cash = Account(name='Cash', slug='cash', group=self, type='As')
            cash.save()

            self.bank_account = bank;
            self.cash_account = cash;
            models.Model.save(self)


    class Admin:
        pass

    class Meta:
        ordering = ['name']

class Account(models.Model):
    ACCOUNT_TYPE = [
        ('As', 'Asset'),     # Eiendeler/aktiva
        ('Li', 'Liability'), # Gjeld/passiva
        ('Eq', 'Equity'),    # Egenkapital
        ('In', 'Income'),    # Inntekt
        ('Ex', 'Expense'),   # Utgift
    ]

    name = models.CharField(maxlength=100)
    slug = models.SlugField(prepopulate_from=['name'],
        help_text='A shortname used in URLs etc.')
    group = models.ForeignKey(AccountGroup)
    type = models.CharField(maxlength=2, choices=ACCOUNT_TYPE, default='Li')
    owner = models.ForeignKey(User, null=True, blank=True)
    active = models.BooleanField(default=True)
    ignore_block_limit = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def debit_to_increase(self):
        """Returns true if account type uses debit to increase, false if using
        credit to increase. Will return true for all equity accounts, even if
        some of those (drawing accounts) may require debit to increase."""

        if self.type in ('Li', 'Eq', 'In'):
            # Credit to increase
            return False
        else:
            # Debit to increase
            return True

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

        if not self.debit_to_increase():
            return -1 * self.balance()
        else:
            return self.balance()

    def is_user_account(self):
        """Returns true if a user account"""

        if self.owner and self.type == 'Li':
            return True
        else:
            return False

    def is_blocked(self):
        """Returns true if user account balance is below group block limit"""

        if not self.is_user_account() or self.ignore_block_limit:
            return False
        return self.balance_credit_reversed() < self.group.block_limit

    def needs_warning(self):
        """Returns true if user account balance is below group warn limit"""

        if not self.is_user_account() or self.ignore_block_limit:
            return False
        return self.balance_credit_reversed() < self.group.warn_limit

    class Admin:
        fields = (
            (None,
                {'fields': ('name', 'slug', 'group', 'owner')}),
            ('Advanced options', {
                'classes': 'collapse',
                'fields' : ('type', 'active', 'ignore_block_limit')}),
        )
        list_display = ['group', 'name', 'owner', 'balance', 'active']
        list_display_links = ['name']
        list_filter = ['active', 'group', 'name']
        list_per_page = 20
        search_fields = ['name']

    class Meta:
        ordering = ['group', 'name']
        unique_together = (('slug', 'group'),)

class Settlement(models.Model):
    date = models.DateField()
    comment = models.CharField(maxlength=200, blank=True, null=True)

    def __unicode__(self):
        if self.comment:
            return smart_unicode("%s: %s" % (self.date, self.comment))
        else:
            return smart_unicode(self.date)

    class Admin:
        pass

    class Meta:
        ordering = ['date']

class InvalidTransaction(Exception):
    def __init__(self, value):
        self.value = value

    def __unicode__(self):
        return u'Invalid transaction: %s' % self.value

class Transaction(models.Model):
    credit_account = models.ForeignKey(Account,
        related_name='credit_transactions')
    debit_account = models.ForeignKey(Account,
        related_name='debit_transactions')

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    details = models.CharField(maxlength=200, blank=True, null=True)

    registered = models.DateTimeField(auto_now_add=True)
    payed = models.DateTimeField(blank=True, null=True)

    settlement = models.ForeignKey(Settlement, null=True, blank=True)

    def __unicode__(self):
        return u'%s from %s to %s' % (self.amount,
                                      self.credit_account,
                                      self.debit_account)

    def save(self):
        if float(self.amount) < 0:
            raise InvalidTransaction, 'Amount is negative.'

        if self.amount == 0:
            raise InvalidTransaction, 'Amount is zero.'

        if self.credit_account == self.debit_account:
            raise InvalidTransaction, 'Credit and debit is same account.'

        models.Model.save(self)

    class Admin:
        list_display = ['amount', 'credit_account', 'debit_account',
                        'settlement']
        list_filter = ['credit_account', 'debit_account', 'settlement']

    class Meta:
        ordering = ['registered', 'payed']

class List(models.Model):
    name = models.CharField(maxlength=200)
    account_width = models.IntegerField(help_text="Width in percent for account name cell in table")
    balance_width = models.IntegerField(help_text="Zero value indicates that balance should be left out")
    account_group = models.ForeignKey(AccountGroup, related_name='lists')
    slug = models.SlugField(prepopulate_from=['name'])

    def __unicode__(self):
        return u'%s: %s' % (self.account_group, self.name)

    class Admin:
        list_filter = ['account_group']

#    class Meta:
#        unique_together = (('slug', 'account_group'),)

class ListItem(models.Model):
    name = models.CharField(maxlength=200, core=True)
    width = models.IntegerField()
    order = models.IntegerField()
    list = models.ForeignKey(List, edit_inline=models.TABULAR, num_in_admin=5, related_name='items')

    def __unicode__(self):
        return u'%s, %s' % (self.list, self.name)

#    class Meta:
#        Unique_together = (('name', 'list'),)
