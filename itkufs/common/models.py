from django.db import models, transaction
from django.db.models import Q
from django.contrib import databrowse
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

databrowse.site.register(User)

# TODO: replace custom save method with validator_lists when Django supports
# this good enough

class Group(models.Model):
    name = models.CharField(_('name'), max_length=100)
    slug = models.SlugField(_('slug'), prepopulate_from=['name'], unique=True,
        help_text=_('A shortname used in URLs etc.'))
    warn_limit = models.IntegerField(_('warn limit'), null=True, blank=True,
        help_text=_('Limit for warning user, leave blank for no limit.'))
    block_limit = models.IntegerField(_('block limit'), null=True, blank=True,
        help_text=_('Limit for blacklisting user, leave blank for no limit.'))
    admins = models.ManyToManyField(User, verbose_name=_('admins'),
        null=True, blank=True)
    bank_account = models.ForeignKey('Account', verbose_name=_('bank account'),
        null=True, blank=True, related_name='foo', editable=False)
    cash_account = models.ForeignKey('Account', verbose_name=_('cash account'),
        null=True, blank=True, related_name='bar', editable=False)
    # FIXME: Fix related name of *_account
    # FIXME: Probably needs to add sales_account etc.

    logo = models.ImageField(upload_to='logos', null=True, blank=True)
    email = models.EmailField(null=True, blank=True, help_text=_('Contact address for group.'))

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

    # FIXME Use property for all elements?
    def get_user_account_set(self):
        """Returns queryset of user accounts"""
        return self.account_set.filter(type='Li', owner__isnull=False)
    user_account_set = property(get_user_account_set,None,None)

    def group_account_set(self):
        """Returns array of group accounts"""
        return self.account_set.exclude(type='Li', owner__isnull=False)

    def transaction_set_with_rejected(self):
        """Returns all transactions connected to group, including rejected"""
        return Transaction.objects.filter(
            entry_set__account__group=self).distinct()

    def transaction_set(self):
        """Returns all transactions connected to group, that have not been
        rejected"""
        return self.transaction_set_with_rejected().exclude(status='Rej')

    def registered_transaction_set(self):
        """Returns all transactions connected to group, that are registered and not rejected"""
        return self.transaction_set().exclude(status='')

    def payed_transaction_set(self):
        """Returns all payed transactions connected to group, that are not
        rejected"""
        return self.transaction_set().filter(Q(status='Pay')|Q(status='Rec'))

    def not_payed_transaction_set(self):
        """Returns all unpayed transactions connected to group, that are not
        rejected"""
        return self.transaction_set().filter(Q(status='')|Q(status='Reg'))

    def received_transaction_set(self):
        """Returns all received transactions connected to group"""
        return self.transaction_set().filter(status='Rec')

    def not_received_transaction_set(self):
        """Returns all transactions that have not been received connected to
        group"""
        return self.transaction_set().exclude(status='Rec')

    def rejected_transaction_set(self):
        """Returns all rejected transactions connected to group"""
        return self.transaction_set_with_rejected().filter(status='Rej')

    not_rejected_transaction_set = transaction_set
    not_rejected_transaction_set.__doc__ = """Returns all transactions that
    have not been rejected connected to group. Same as transaction_set()."""
databrowse.site.register(Group)

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

        for e in self.transactionentry_set.filter(transaction__log_set__type='Rec'):
            balance -= e.debit
            balance += e.credit

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
databrowse.site.register(Account)
