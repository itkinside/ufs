from django.db import models
from django.contrib.auth.models import User

class AccountGroup(models.Model):
    name = models.CharField(maxlength=100)
    slug = models.SlugField(prepopulate_from=['name'], unique=True)
    warn_limit = models.IntegerField(null=True, blank=True)
    block_limit = models.IntegerField(null=True, blank=True)
    admins = models.ManyToManyField(User, null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self):
        models.Model.save(self)
        # Create default accounts
        if not self.account_set.count():
            bank = Account(name='Bank', group=self, type='As')
            bank.save()
            cash = Account(name='Cash', group=self, type='As')
            cash.save()

    class Admin:
        pass

    class Meta:
        ordering = ['name']

class Account(models.Model):
    ACCOUNT_TYPE = [
        ('As', 'Asset'),
        ('Li', 'Liability'),
        ('Eq', 'Equity'),
        ('In', 'Income'),
        ('Ex', 'Expense'),
    ]

    name = models.CharField(maxlength=100)
    group = models.ForeignKey(AccountGroup)
    type = models.CharField(maxlength=2, choices=ACCOUNT_TYPE, default='Li')
    owner = models.ForeignKey(User, null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def balance(self):
        balance = 0

        for t in self.from_transactions.filter(payed__isnull=False):
            balance -= t.amount
        for t in self.to_transactions.filter(payed__isnull=False):
            balance += t.amount

        # For accounting reasons, income is a negative amount
        if self.type == 'In':
            balance *= -1

        return balance

    def user_account(self):
        if self.owner:
            return True
        else:
            return False

    class Admin:
        fields = (
            (None,
                {'fields': ('name', 'group', 'owner')}),
            ('Advanced options', {
                'classes': 'collapse',
                'fields' : ('type', 'active')}),
        )
        list_display = ['group', 'name', 'owner', 'balance', 'active']
        list_display_links = ['name']
        list_filter = ['active', 'group', 'name']
        list_per_page = 20
        search_fields = ['name']

    class Meta:
        ordering = ['group', 'name']

class Settlement(models.Model):
    date = models.DateField()

    def __str__(self):
        return str(self.date)

    class Admin:
        pass

    class Meta:
        ordering = ['date']

class InvalidTransaction(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return 'Invalid transaction: %s' % str(self.value)

class Transaction(models.Model):
    from_account = models.ForeignKey(Account, null=True, blank=True,
                                     related_name='from_transactions')
    to_account = models.ForeignKey(Account, null=True, blank=True,
                                   related_name='to_transactions')

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    details = models.CharField(maxlength=200, blank=True, null=True)

    registered = models.DateTimeField(auto_now_add=True)
    payed = models.DateTimeField(blank=True, null=True)

    settlement = models.ForeignKey(Settlement, null=True, blank=True)

    def __str__(self):
        return '%s from %s to %s' % (self.amount,
                                     self.from_account,
                                     self.to_account)

    def save(self):
        if self.amount < 0:
            raise InvalidTransaction, 'Amount is negative.'

        if self.from_account == self.to_account:
            raise InvalidTransaction, 'Giving yourself money?'

        if not (self.from_account or self.to_account):
            raise InvalidTransaction, 'Only to or from can be null, not both.'

        models.Model.save(self)

    class Admin:
        list_display = ['amount', 'from_account', 'to_account', 'settlement']
        list_filter = ['from_account', 'to_account', 'settlement']

    class Meta:
        ordering = ['registered', 'payed']

