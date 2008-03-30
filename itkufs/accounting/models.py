from datetime import datetime

from django.db import models, transaction
from django.db.models import Q
from django.contrib import databrowse
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _, ugettext

databrowse.site.register(User)

# TODO: Replace custom save methods with validator_lists when Django supports
# this good enough

class Group(models.Model):
    name = models.CharField(_('name'), max_length=100)
    slug = models.SlugField(_('slug'), prepopulate_from=['name'], unique=True,
        help_text=_('A shortname used in URLs etc.'))
    admin_only = models.BooleanField(default=True,
        help_text=_('Only allow admins to view group details.'))
    warn_limit = models.IntegerField(_('warn limit'), null=True, blank=True,
        help_text=_('Limit for warning user, leave blank for no limit.'))
    block_limit = models.IntegerField(_('block limit'), null=True, blank=True,
        help_text=_('Limit for blacklisting user, leave blank for no limit.'))
    admins = models.ManyToManyField(User, verbose_name=_('admins'),
        null=True, blank=True, filter_interface=models.HORIZONTAL)
    bank_account = models.ForeignKey('Account', verbose_name=_('bank account'),
        null=True, blank=True, related_name='bank_account_for', editable=False)
    cash_account = models.ForeignKey('Account', verbose_name=_('cash account'),
        null=True, blank=True, related_name='cash_account_for', editable=False)
    # TODO: Probably needs to add sales_account etc. Can wait for inventory.

    logo = models.ImageField(upload_to='logos', null=True, blank=True)
    email = models.EmailField(null=True, blank=True,
        help_text=_('Contact address for group.'))

    class Meta:
        ordering = ['name']
        verbose_name = _('group')
        verbose_name_plural = _('groups')

    class Admin:
        pass

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('group-summary', kwargs={
            'group': self.slug,
        })

    def save(self):
        if not len(self.slug):
            raise ValueError('Slug cannot be empty.')
        super(Group, self).save()

        # Create default accounts
        if not self.account_set.count():
            bank = Account(name=ugettext('Bank'), slug='bank',
                           type=Account.ASSET_ACCOUNT, group=self)
            bank.save()
            cash = Account(name=ugettext('Cash'), slug='cash',
                           type=Account.ASSET_ACCOUNT, group=self)
            cash.save()

            self.bank_account = bank
            self.cash_account = cash
            super(Group, self).save()

    def get_user_account_set(self):
        """Returns all user accounts belonging to group"""
        return self.account_set.filter(type=Account.LIABILITY_ACCOUNT,
                                       owner__isnull=False)
    user_account_set = property(get_user_account_set, None, None)

    def get_group_account_set(self):
        """Returns all non-user accounts belonging to group"""
        return self.account_set.exclude(type=Account.LIABILITY_ACCOUNT,
                                        owner__isnull=False)
    group_account_set = property(get_group_account_set, None, None)


    ### Transaction set methods
    # Please keep in sync with Account's set methods

    def get_transaction_set_with_rejected(self):
        """Returns all transactions connected to group, including rejected"""
        return self.real_transaction_set.exclude(
            status=Transaction.UNDEFINED_STATE).distinct()
    transaction_set_with_rejected = property(get_transaction_set_with_rejected,
                                             None, None)

    def get_transaction_set(self):
        """Returns all transactions connected to group, that have not been
        rejected"""
        return self.transaction_set_with_rejected.exclude(
            status=Transaction.REJECTED_STATE)
    transaction_set = property(get_transaction_set, None, None)

    def get_registered_transaction_set(self):
        """Returns all transactions connected to group, that are registered and
        not rejected"""
        return self.transaction_set.exclude(status=Transaction.UNDEFINED_STATE)
    registered_transaction_set = property(get_registered_transaction_set,
                                          None, None)

    def get_payed_transaction_set(self):
        """Returns all payed transactions connected to group, that are not
        rejected"""
        return self.transaction_set.filter(
            Q(status=Transaction.PAYED_STATE) |
            Q(status=Transaction.RECEIVED_STATE))
    payed_transaction_set = property(get_payed_transaction_set, None, None)

    def get_not_payed_transaction_set(self):
        """Returns all unpayed transactions connected to group, that are not
        rejected"""
        return self.transaction_set.filter(
            Q(status=Transaction.UNDEFINED_STATE) |
            Q(status=Transaction.REGISTERED_STATE))
    not_payed_transaction_set = property(get_not_payed_transaction_set,
                                         None, None)

    def get_received_transaction_set(self):
        """Returns all received transactions connected to group"""
        return self.transaction_set.filter(
            status=Transaction.RECEIVED_STATE)
    received_transaction_set = property(get_received_transaction_set,
                                        None, None)

    def get_not_received_transaction_set(self):
        """Returns all transactions that have not been received connected to
        group"""
        return self.transaction_set.exclude(
            status=Transaction.RECEIVED_STATE)
    not_received_transaction_set = property(get_not_received_transaction_set,
                                            None, None)

    def get_rejected_transaction_set(self):
        """Returns all rejected transactions connected to group"""
        return self.transaction_set_with_rejected.filter(
            status=Transaction.REJECTED_STATE)
    rejected_transaction_set = property(get_rejected_transaction_set,
                                        None, None)

    get_not_rejected_transaction_set = get_transaction_set
    get_not_rejected_transaction_set.__doc__ = """Returns all transactions that
    have not been rejected connected to group. Same as get_transaction_set()."""
    not_rejected_transaction_set = property(get_transaction_set, None, None)

databrowse.site.register(Group)


class AccountManager(models.Manager):
    def get_query_set(self):
        return super(AccountManager,self).get_query_set().extra(
            select={
            'balance_sql':
                """
                SELECT sum(debit) - sum(credit)
                FROM accounting_transactionentry
                    JOIN accounting_transaction
                        ON (accounting_transactionentry.transaction_id
                            = accounting_transaction.id)
                WHERE account_id = accounting_account.id
                    AND accounting_transaction.status = '%s'
                """ % Transaction.RECEIVED_STATE,
            'is_user_account_sql':
                """
                (accounting_account.owner_id IS NOT NULL
                    AND accounting_account.type = '%s')
                """ % Account.LIABILITY_ACCOUNT,
            'group_block_limit_sql':
                """
                SELECT accounting_group.block_limit
                FROM accounting_group
                WHERE accounting_group.id = accounting_account.group_id
                """
            }
        )


class Account(models.Model):
    ASSET_ACCOUNT = 'As'          # Eiendeler/aktiva
    LIABILITY_ACCOUNT = 'Li'      # Gjeld/passiva
    EQUITY_ACCOUNT = 'Eq'         # Egenkapital
    INCOME_ACCOUNT = 'In'         # Inntekt
    EXPENSE_ACCOUNT = 'Ex'        # Utgift
    EXTERNAL_ACCOUNT = 'EA'       # Ektsern, ie. leverandør/kunde
    ACCOUNT_TYPE = (
        (ASSET_ACCOUNT, _('Asset')),
        (LIABILITY_ACCOUNT, _('Liability')),
        (EQUITY_ACCOUNT, _('Equity')),
        (INCOME_ACCOUNT, _('Income')),
        (EXPENSE_ACCOUNT, _('Expense')),
        (EXPENSE_ACCOUNT, _('Supplier/customer')),
    )

    objects = AccountManager()

    name = models.CharField(_('name'), max_length=100)
    slug = models.SlugField(_('slug'), prepopulate_from=['name'],
        help_text=_('A shortname used in URLs etc.'))
    group = models.ForeignKey(Group, verbose_name=_('group'))
    type = models.CharField(_('type'), max_length=2, choices=ACCOUNT_TYPE,
        default=LIABILITY_ACCOUNT)
    owner = models.ForeignKey(User, verbose_name=_('owner'),
        null=True, blank=True)
    active = models.BooleanField(_('active'), default=True)
    ignore_block_limit = models.BooleanField(_('ignore block limit'),
        default=False)

    class Meta:
        ordering = ['group', 'type', 'name']
        unique_together = (('slug', 'group'), ('owner', 'group'))
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

    def get_absolute_url(self):
        return reverse('account-summary', kwargs={
            'group': self.group.slug,
            'account': self.slug,
        })

    def save(self):
        if not len(self.slug):
            raise ValueError('Slug cannot be empty.')
        super(Account, self).save()

    def balance(self):
        if self.balance_sql:
            return self.balance_sql
        else:
            return 0

    def user_balance(self):
        """Returns account balance, but multiplies by -1 if the account is a
        liability account."""

        balance = self.balance()
        if balance == 0 or not self.is_user_account():
            return balance
        else:
            return -1 * balance

    def is_user_account(self):
        """Returns true if a user account"""
        return self.is_user_account_sql

    def is_blocked(self):
        """Returns true if user account balance is below group block limit"""

        if (not self.is_user_account()
            or self.ignore_block_limit
            or self.group_block_limit_sql is None):
            return False
        return self.user_balance() < self.group_block_limit_sql

    def needs_warning(self):
        """Returns true if user account balance is below group warn limit"""

        if (not self.is_user_account()
            or self.ignore_block_limit
            or self.group.warn_limit is None):
            return False
        return self.user_balance() < self.group.warn_limit


    ### Transaction set methods
    # Please keep in sync with Group's set methods

    def get_transaction_set_with_rejected(self):
        """Returns all transactions connected to account, including rejected"""
        return Transaction.objects.filter(
            entry_set__account=self).exclude(
            status=Transaction.UNDEFINED_STATE).distinct()
    transaction_set_with_rejected = property(get_transaction_set_with_rejected,
                                             None, None)

    def get_transaction_set(self):
        """Returns all transactions connected to account, that have not been
        rejected"""
        return self.transaction_set_with_rejected.exclude(
            status=Transaction.REJECTED_STATE)
    transaction_set = property(get_transaction_set, None, None)

    def get_registered_transaction_set(self):
        """Returns all transactions connected to account, that are registered
        and not rejected"""
        return self.transaction_set.exclude(status=Transaction.UNDEFINED_STATE)
    registered_transaction_set = property(get_registered_transaction_set,
                                          None, None)

    def get_payed_transaction_set(self):
        """Returns all payed transactions connected to account, that are not
        rejected"""
        return self.transaction_set.filter(
            Q(status=Transaction.PAYED_STATE) |
            Q(status=Transaction.RECEIVED_STATE))
    payed_transaction_set = property(get_payed_transaction_set, None, None)

    def get_not_payed_transaction_set(self):
        """Returns all unpayed transactions connected to account, that are not
        rejected"""
        return self.transaction_set.filter(
            Q(status=Transaction.UNDEFINED_STATE) |
            Q(status=Transaction.REGISTERED_STATE))
    not_payed_transaction_set = property(get_not_payed_transaction_set,
                                         None, None)

    def get_received_transaction_set(self):
        """Returns all received transactions connected to account"""
        return self.transaction_set.filter(
            status=Transaction.RECEIVED_STATE)
    received_transaction_set = property(get_received_transaction_set,
                                        None, None)

    def get_not_received_transaction_set(self):
        """Returns all transactions that have not been received connected to
        account"""
        return self.transaction_set.exclude(
            status=Transaction.RECEIVED_STATE)
    not_received_transaction_set = property(get_not_received_transaction_set,
                                            None, None)

    def get_rejected_transaction_set(self):
        """Returns all rejected transactions connected to account"""
        return self.transaction_set_with_rejected.filter(
            status=Transaction.REJECTED_STATE)
    rejected_transaction_set = property(get_rejected_transaction_set,
                                        None, None)

    get_not_rejected_transaction_set = get_transaction_set
    get_not_rejected_transaction_set.__doc__ = """Returns all transactions that
    have not been rejected connected to account. Same as
    get_transaction_set()."""
    not_rejected_transaction_set = property(get_transaction_set, None, None)

databrowse.site.register(Account)


### Transaction models

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
    group = models.ForeignKey(Group, verbose_name=_('group'))
    date = models.DateField(_('date'))
    comment = models.CharField(_('comment'), max_length=200,
        blank=True, null=True)

    class Meta:
        ordering = ['date']
        verbose_name = _('settlement')
        verbose_name_plural = _('settlements')
        unique_together = (('date', 'comment', 'group'),)

    class Admin:
        pass

    def __unicode__(self):
        if self.comment is not None:
            return smart_unicode("%s: %s" % (self.date, self.comment))
        else:
            return smart_unicode(self.date)

databrowse.site.register(Settlement)


class TransactionManager(models.Manager):
    def get_query_set(self):
        return super(TransactionManager,self).get_query_set().extra(
            select={
            'entry_count_sql':
                """
                SELECT COUNT(*)
                FROM accounting_transactionentry
                WHERE accounting_transactionentry.transaction_id =
                    accounting_transaction.id
                """
            }
        )


class Transaction(models.Model):
    UNDEFINED_STATE = ''
    REGISTERED_STATE = 'Reg'
    PAYED_STATE = 'Pay'
    RECEIVED_STATE = 'Rec'
    REJECTED_STATE = 'Rej'
    TRANSACTION_STATE = (
        (REGISTERED_STATE, _('Registered')),
        (PAYED_STATE, _('Payed')),
        (RECEIVED_STATE, _('Received')),
        (REJECTED_STATE, _('Rejected')),
    )

    objects = TransactionManager()

    group = models.ForeignKey(Group, verbose_name=_('group'),
        related_name='real_transaction_set')
    settlement = models.ForeignKey(Settlement, verbose_name=_('settlement'),
        null=True, blank=True)
    last_modified = models.DateTimeField(_('Last modified'), auto_now_add=True)
    status = models.CharField(_('status'), max_length=3,
        choices=TRANSACTION_STATE, blank=True)

    class Meta:
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')
        ordering = ['-last_modified']

    class Admin:
        pass

    def __unicode__(self):
        if self.entry_set.all().count():
            entries = []
            for entry in self.entry_set.all():
                if entry.debit:
                    entries.append('%s debit %.2f' %
                        (entry.account, entry.debit))
                else:
                    entries.append('%s credit %.2f' %
                        (entry.account, entry.credit))

            return ', '.join(entries)
        else:
            return u'Empty transaction'

    def get_absolute_url(self):
        return reverse('transaction-details', kwargs={
            'group': self.group.slug,
            'transaction': self.id,
        })

    def debug(self):
        status = self.log_set.all()
        return '%s %s' % (self.__unicode__(), status)

    @transaction.commit_on_success
    def save(self):
        debit_sum = 0
        credit_sum = 0
        debit_accounts = []
        credit_accounts = []

        for entry in self.entry_set.all():
            if entry.debit > 0:
                debit_sum += float(entry.debit)
                debit_accounts.append(entry.account)
            elif entry.credit > 0:
                credit_sum += float(entry.credit)
                credit_accounts.append(entry.account)

        for account in debit_accounts + credit_accounts:
            if account.group != self.group:
                raise InvalidTransaction('Group of transaction entry account '
                    + 'does not match group of transaction.')

        account_intersection = set(debit_accounts).intersection(
            set(credit_accounts))
        if len(account_intersection):
            raise InvalidTransaction('The following accounts is both a debit '
                    + 'and a credit account for this transaction: %s'
                    % list(account_intersection))

        if debit_sum != credit_sum:
            raise InvalidTransaction('Credit and debit do not match, credit: %d, debit: %d.' % (credit_sum, debit_sum))

        self.last_modified = datetime.now()
        super(Transaction, self).save()

    def set_registered(self, user, message='', auto=False):
        if self.id is None:
            self.save()

        if not self.is_registered():
            log = TransactionLog(type=self.REGISTERED_STATE, transaction=self, auto=auto)
            log.user = user
            if message is not None and message.strip() != '':
                log.message = message
            log.save()
            self.status = self.REGISTERED_STATE
            self.last_modified = datetime.now()
            self.save()
        else:
            raise InvalidTransaction(
                'Could not set transaction as registered')

    def set_payed(self, user, message='', auto=False):
        if not self.is_rejected() and self.is_registered():
            log = TransactionLog(type=self.PAYED_STATE, transaction=self, auto=auto)
            log.user = user
            if message.strip() != '':
                log.message = message
            log.save()
            self.status = self.PAYED_STATE
            self.last_modified = datetime.now()
            self.save()
        else:
            raise InvalidTransaction(
                'Could not set transaction as payed')

    def set_received(self, user, message='', auto=False):
        if not self.is_rejected() and self.is_registered():
            if not self.is_payed():
                self.set_payed(user, auto=True)

            log = TransactionLog(type=self.RECEIVED_STATE, transaction=self, auto=auto)
            log.user = user
            if message.strip() != '':
                log.message = message
            log.save()
            self.status = self.RECEIVED_STATE
            self.last_modified = datetime.now()
            self.save()
        else:
            raise InvalidTransaction('Could not set transaction as received')

    def reject(self, user, message='', auto=False):
        if (self.is_registered()
            and not self.is_payed()
            and not self.is_received()):
            log = TransactionLog(type=self.REJECTED_STATE, transaction=self, auto=auto)
            log.user = user
            if message.strip() != '':
                log.message = message
            log.save()
            self.status = self.REJECTED_STATE
            self.last_modified = datetime.now()
            self.save()

            users = {}
            for entry in self.entry_set.all():
                if entry.account.is_user_account():
                    users[entry.account.owner] = entry.account.owner

            for user in users.values():
                user.message_set.create(message=_('A transaction containing your account has been rejected'))
        else:
            raise InvalidTransaction(
                'Could not set transaction as rejected')
    set_rejected = reject
    set_rejected.__doc__ = 'set_rejected() is an alias for reject()'

    def is_registered(self):
        return self.status in (self.REGISTERED_STATE,
                               self.PAYED_STATE,
                               self.RECEIVED_STATE)

    def is_payed(self):
        return self.status in (self.PAYED_STATE, self.RECEIVED_STATE)

    def is_received(self):
        return self.status == self.RECEIVED_STATE

    def is_rejected(self):
        return self.status == self.REJECTED_STATE

    def get_registered(self):
        if self.is_registered():
            return self.log_set.filter(type=self.REGISTERED_STATE)[0]

    def get_payed(self):
        if self.is_payed():
            return self.log_set.filter(type=self.PAYED_STATE)[0]

    def get_received(self):
        if self.is_received():
            return self.log_set.filter(type=self.RECEIVED_STATE)[0]

    def get_rejected(self):
        if self.is_rejected():
            return self.log_set.filter(type=self.REJECTED_STATE)[0]

    registered = property(get_registered, None, None)
    received = property(get_received, None, None)
    rejected = property(get_rejected, None, None)
    payed = property(get_payed, None, None)

    def get_valid_logtype_choices(self, user=None):
        possible_state = dict(self.TRANSACTION_STATE)

        if self.is_rejected() or self.is_received():
            return [('','')]

        if self.is_registered():
            del possible_state[self.REGISTERED_STATE]

        if self.is_payed():
            del possible_state[self.PAYED_STATE]
            del possible_state[self.REJECTED_STATE]

        possible_state = possible_state.items()
        possible_state.insert(0, ('',''))
        return possible_state

databrowse.site.register(Transaction)


class TransactionLog(models.Model):
    transaction = models.ForeignKey(Transaction,
        verbose_name=_('transaction'), related_name='log_set',
        edit_inline=models.TABULAR, num_in_admin=3, max_num_in_admin=4,
        num_extra_on_change=1)
    type = models.CharField(_('type'), max_length=3, core=True,
        choices=Transaction.TRANSACTION_STATE)
    timestamp =  models.DateTimeField(_('timestamp'), auto_now_add=True)
    user = models.ForeignKey(User, verbose_name=_('user'))
    message = models.CharField(_('message'), max_length=200, blank=True)
    auto = models.BooleanField(default=False)

    def save(self):
        if self.id is not None:
            raise InvalidTransactionLog(
                'Altering transaction log entries is not allowed')
        if self.transaction.id is None:
            self.transaction.save()
        if self.transaction.log_set.filter(type=self.type).count():
            raise InvalidTransactionLog(
                'Only one instance of each log type is allowed.')
        super(TransactionLog, self).save()

    class Meta:
        ordering = ('timestamp',)
        unique_together = (('transaction', 'type'),)
        verbose_name = _('transaction log entry')
        verbose_name_plural = _('transaction log entries')

    def __unicode__(self):
        d = {
            'type': self.get_type_display(),
            'user': self.user,
            'message': self.message,
        }
        if self.timestamp is None:
            d['timestamp'] = '(not saved)'
        else:
            d['timestamp'] = self.timestamp.strftime('%Y-%m-%d %H:%M')
        return _(u'%(type)s at %(timestamp)s by %(user)s: %(message)s') % d

databrowse.site.register(TransactionLog)


class TransactionEntry(models.Model):
    transaction = models.ForeignKey(Transaction,
        verbose_name=_('transaction'), related_name='entry_set',
        edit_inline=models.TABULAR, num_in_admin=5, num_extra_on_change=3)
    account = models.ForeignKey('Account', verbose_name=_('account'), core=True)
    debit = models.DecimalField(_('debit amount'),
        max_digits=10, decimal_places=2, default=0)
    credit = models.DecimalField(_('credit amount'),
        max_digits=10, decimal_places=2, default=0)

    def save(self):
        if self.transaction.is_registered():
            raise InvalidTransactionEntry(
                'Can not add entries to registered transactions')

        if self.debit < 0 or self.credit < 0:
            raise InvalidTransactionEntry(
                'Credit and debit must be positive or zero')

        if self.debit > 0 and self.credit > 0:
            raise InvalidTransactionEntry(
                'Only credit or debit may be set')

        if self.debit == 0 and self.credit == 0:
            raise InvalidTransactionEntry(
                'Create or debit must be positive')

        super(TransactionEntry, self).save()

    class Meta:
        unique_together = (('transaction', 'account'),)
        verbose_name = _('transaction entry')
        verbose_name_plural = _('transaction entries')
        ordering = ['credit', 'debit']

    def __unicode__(self):
        return _(u'%(account)s: debit %(debit)s, credit %(credit)s') % {
            'account': self.account,
            'debit': self.debit,
            'credit': self.credit,
        }

databrowse.site.register(TransactionEntry)
