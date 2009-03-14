import datetime

from django.conf import settings
from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _, ugettext

class Group(models.Model):
    name = models.CharField(_('name'), max_length=100)
    slug = models.SlugField(_('slug'), unique=True,
        help_text=_('A shortname used in URLs.'))
    admins = models.ManyToManyField(User, verbose_name=_('admins'),
        null=True, blank=True)
    warn_limit = models.IntegerField(_('warn limit'), null=True, blank=True,
        help_text=_('Warn user of low balance at this limit, '
            + 'leave blank for no limit.'))
    block_limit = models.IntegerField(_('block limit'), null=True, blank=True,
        help_text=_('Limit for blacklisting user, leave blank for no limit.'))
    logo = models.ImageField(upload_to='logos', blank=True, help_text=_('A small image that will be added to lists.'))

    # FIXME remove? (given that comments on lists cover this use case)
    email = models.EmailField(blank=True,
        help_text=_('Contact address for group.'))

    class Meta:
        ordering = ('name',)
        verbose_name = _('group')
        verbose_name_plural = _('groups')

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('group-summary', kwargs={
            'group': self.slug,
        })

    def save(self, *args, **kwargs):
        if not len(self.slug):
            raise ValueError('Slug cannot be empty.')
        super(Group, self).save(*args, **kwargs)

        # Create default accounts
        if not self.account_set.count():

            # TODO change this into a magic loop?
            bank = Account(name=ugettext('Bank'), slug='bank',
                group_account=True, type=Account.ASSET_ACCOUNT, group=self)
            bank.save()
            bank_role = RoleAccount(
                group=self, role=RoleAccount.BANK_ACCOUNT, account=bank)
            bank_role.save()

            cash = Account(name=ugettext('Cash'), slug='cash',
                group_account=True, type=Account.ASSET_ACCOUNT, group=self)
            cash.save()
            cash_role = RoleAccount(
                group=self, role=RoleAccount.CASH_ACCOUNT, account=cash)
            cash_role.save()

    def get_user_account_set(self):
        """Returns all user accounts belonging to group"""
        return self.account_set.exclude(group_account=True)
    user_account_set = property(get_user_account_set, None, None)

    def get_group_account_set(self):
        """Returns all non-user accounts belonging to group"""
        return self.account_set.filter(group_account=True)
    group_account_set = property(get_group_account_set, None, None)


    ### Transaction set methods
    # Please keep in sync with Account's set methods

    def get_transaction_set_with_rejected(self):
        """Returns all transactions connected to group, including rejected"""
        return self.real_transaction_set.exclude(
            state=Transaction.UNDEFINED_STATE).distinct()
    transaction_set_with_rejected = property(
        get_transaction_set_with_rejected, None, None)

    def get_transaction_set(self):
        """Returns all transactions connected to group, excluding rejected"""
        return self.transaction_set_with_rejected.exclude(
            state=Transaction.REJECTED_STATE)
    transaction_set = property(get_transaction_set, None, None)

    def get_pending_transaction_set(self):
        """Returns all pending transactions connected to group"""
        return self.transaction_set.filter(state=Transaction.PENDING_STATE)
    pending_transaction_set = property(get_pending_transaction_set, None, None)

    def get_committed_transaction_set(self):
        """Returns all committed transactions connected to group"""
        return self.transaction_set.filter(state=Transaction.COMMITTED_STATE)
    committed_transaction_set = property(
        get_committed_transaction_set, None, None)

    def get_rejected_transaction_set(self):
        """Returns all rejected transactions connected to group"""
        return self.transaction_set_with_rejected.filter(
            state=Transaction.REJECTED_STATE)
    rejected_transaction_set = property(
        get_rejected_transaction_set, None, None)


class AccountManager(models.Manager):
    def get_query_set(self):
        return super(AccountManager, self).get_query_set().extra(
            select={
            'balance_sql':
                """
                SELECT sum(debit) - sum(credit)
                FROM accounting_transactionentry AS te
                JOIN accounting_transaction AS t ON (te.transaction_id = t.id)
                WHERE account_id = accounting_account.id AND t.state = '%s'
                """ % Transaction.COMMITTED_STATE,
            'group_block_limit_sql':
                """
                SELECT accounting_group.block_limit
                FROM accounting_group
                WHERE accounting_group.id = accounting_account.group_id
                """,
            }
        )

class Account(models.Model):
    ASSET_ACCOUNT = 'As'          # Eiendeler/aktiva
    LIABILITY_ACCOUNT = 'Li'      # Gjeld/passiva
    EQUITY_ACCOUNT = 'Eq'         # Egenkapital
    INCOME_ACCOUNT = 'In'         # Inntekt
    EXPENSE_ACCOUNT = 'Ex'        # Utgift
    ACCOUNT_TYPE = (
        (ASSET_ACCOUNT, _('Asset')),
        (LIABILITY_ACCOUNT, _('Liability')),
        (EQUITY_ACCOUNT, _('Equity')),
        (INCOME_ACCOUNT, _('Income')),
        (EXPENSE_ACCOUNT, _('Expense')),
    )

    objects = AccountManager()

    name = models.CharField(_('name'), max_length=100)
    short_name = models.CharField(_('short name'), max_length=100, blank=True)
    slug = models.SlugField(_('slug'),
        help_text=_('A shortname used in URLs etc.'))
    group = models.ForeignKey(Group, verbose_name=_('group'))
    type = models.CharField(_('type'), max_length=2, choices=ACCOUNT_TYPE,
        default=LIABILITY_ACCOUNT)
    owner = models.ForeignKey(User, verbose_name=_('owner'),
        null=True, blank=True)
    active = models.BooleanField(_('active'), default=True)
    ignore_block_limit = models.BooleanField(_('ignore block limit'),
        default=False, help_text=_('Never block account automatically'))
    blocked = models.BooleanField(_('blocked'), default=False,
        help_text=_('Block account manually'))
    group_account = models.BooleanField(_('group account'), default=False,
        help_text=_('Does this account belong to the group?'))

    class Meta:
        ordering = ('group', 'name')
        unique_together = (('slug', 'group'), ('owner', 'group'))
        verbose_name = _('account')
        verbose_name_plural = _('accounts')

    def __unicode__(self):
        return u'%s: %s' % (self.group, self.name)

    def get_absolute_url(self):
        return reverse('account-summary', kwargs={
            'group': self.group.slug,
            'account': self.slug,
        })

    def save(self, *args, **kwargs):
        if not len(self.slug):
            raise ValueError('Slug cannot be empty.')
        super(Account, self).save(*args, **kwargs)

    def balance(self, date=None):
        if not date and hasattr(self, 'balance_sql'):
            return self.balance_sql or 0
        else:
            entries = self.transactionentry_set.filter(
                transaction__state=Transaction.COMMITTED_STATE)
            if date is not None:
                entries = entries.filter(transaction__date__lte=date )
            balance = 0
            for e in entries:
                balance += e.debit
                balance -= e.credit
            return balance

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
        return not self.group_account

    def is_blocked(self):
        """Returns true if user account balance is below group block limit"""

        if self.blocked:
            return True

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
                state=Transaction.UNDEFINED_STATE).distinct()
    transaction_set_with_rejected = property(
        get_transaction_set_with_rejected, None, None)

    def get_transaction_set(self):
        """Returns all transactions connected to account, excluding rejected"""
        return self.transaction_set_with_rejected.exclude(
            state=Transaction.REJECTED_STATE)
    transaction_set = property(get_transaction_set, None, None)

    def get_pending_transaction_set(self):
        """Returns all pending transactions connected to account"""
        return self.transaction_set.filter(state=Transaction.PENDING_STATE)
    pending_transaction_set = property(get_pending_transaction_set, None, None)

    def get_committed_transaction_set(self):
        """Returns all committed transactions connected to account"""
        return self.transaction_set.filter(state=Transaction.COMMITTED_STATE)
    committed_transaction_set = property(
        get_committed_transaction_set, None, None)

    def get_rejected_transaction_set(self):
        """Returns all rejected transactions connected to account"""
        return self.transaction_set_with_rejected.filter(
            state=Transaction.REJECTED_STATE)
    rejected_transaction_set = property(
        get_rejected_transaction_set, None, None)


class RoleAccount(models.Model):
    BANK_ACCOUNT = 'Bank'
    CASH_ACCOUNT = 'Cash'
    SALE_ACCOUNT = 'Sale'
    ACCOUNT_ROLE = (
        (BANK_ACCOUNT, _('Bank account')),
        (CASH_ACCOUNT, _('Cash account')),
        (SALE_ACCOUNT, _('Sale account')),
    )

    group = models.ForeignKey(Group, verbose_name=_('group'))
    role = models.CharField(_('role'), max_length=4, choices=ACCOUNT_ROLE)
    account = models.ForeignKey(Account, verbose_name=_('account'))

    class Meta:
        ordering = ('group', 'role')
        # FIXME: waiting for http://code.djangoproject.com/ticket/6523
        #unique_together = (('group', 'role'),)
        verbose_name = _('role account')
        verbose_name_plural = _('role accounts')

    def __unicode__(self):
        return _(u'%(account)s is %(role)s for %(group)s') % {
            'account': self.account.name,
            'role': self.get_role_display().lower(),
            'group': self.group,
        }


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
    comment = models.CharField(_('comment'), max_length=200, blank=True)
    closed = models.BooleanField(default=False,
        help_text=_('Mark as closed when done adding transactions '
            + 'to the settlement.'))

    class Meta:
        ordering = ('-date',)
        verbose_name = _('settlement')
        verbose_name_plural = _('settlements')
        # FIXME: waiting for http://code.djangoproject.com/ticket/6523
        # unique_together = (('date', 'comment', 'group'),)

    def __unicode__(self):
        if self.comment is not None:
            return u'%s: %s' % (self.date, self.comment)
        else:
            return smart_unicode(self.date)

    def get_absolute_url(self):
        return reverse('settlement-details', kwargs={
            'group': self.group.slug,
            'settlement': self.id,
        })

    def is_editable(self):
        return self.closed == False


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
    PENDING_STATE = 'Pen'
    COMMITTED_STATE = 'Com'
    REJECTED_STATE = 'Rej'
    TRANSACTION_STATE = (
        (PENDING_STATE, _('Pending')),
        (COMMITTED_STATE, _('Committed')),
        (REJECTED_STATE, _('Rejected')),
    )

    objects = TransactionManager()

    group = models.ForeignKey(Group, verbose_name=_('group'),
        related_name='real_transaction_set')
    settlement = models.ForeignKey(Settlement, verbose_name=_('settlement'),
        null=True, blank=True)
    date = models.DateField(_('date'),
        help_text=_('May be used for date of the transaction if not today.'))
    last_modified = models.DateTimeField(_('Last modified'), auto_now_add=True)
    state = models.CharField(_('state'), max_length=3,
        choices=TRANSACTION_STATE, blank=True)

    class Meta:
        ordering = ('-last_modified',)
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')

    def __unicode__(self):
        if self.entry_set.all().count():
            entries = []
            for entry in self.entry_set.all():
                if entry.debit:
                    entries.append(u'%s debit %.2f' %
                        (entry.account, entry.debit))
                else:
                    entries.append(u'%s credit %.2f' %
                        (entry.account, entry.credit))

            return u', '.join(entries)
        else:
            return u'Empty transaction'

    def get_absolute_url(self):
        return reverse('transaction-details', kwargs={
            'group': self.group.slug,
            'transaction': self.id,
        })

    # FIXME is this the right place to have commit on succes? Shouldn't it be
    # higher up in a view etc?
    @transaction.commit_on_success
    def save(self, *args, **kwargs):
        debit_sum = 0
        credit_sum = 0
        debit_accounts = []
        credit_accounts = []

        for entry in self.entry_set.all():
            if entry.debit > 0:
                debit_sum += entry.debit
                debit_accounts.append(entry.account)
            elif entry.credit > 0:
                credit_sum += entry.credit
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
            raise InvalidTransaction('Credit and debit do not match, '
                + 'credit: %d, debit: %d.' % (credit_sum, debit_sum))

        if self.date is None:
            self.date = datetime.date.today()
        self.last_modified = datetime.datetime.now()
        super(Transaction, self).save(*args, **kwargs)

    def set_pending(self, user, message=''):
        if self.id is None:
            self.save()

        if not self.is_committed() and not self.is_rejected():
            log = TransactionLog(type=self.PENDING_STATE, transaction=self)
            log.user = user
            if message is not None and message.strip() != '':
                log.message = message
            log.save()
            self.state = self.PENDING_STATE
            self.last_modified = datetime.datetime.now()
            self.save()
        else:
            raise InvalidTransaction('Could not set transaction as pending')

    def set_committed(self, user, message=''):
        if self.is_pending() and not self.is_committed():
            log = TransactionLog(type=self.COMMITTED_STATE, transaction=self)
            log.user = user
            if message.strip() != '':
                log.message = message
            log.save()

            self.state = self.COMMITTED_STATE
            self.last_modified = datetime.datetime.now()
            self.save()
        else:
            raise InvalidTransaction('Could not set transaction as committed')

    def set_rejected(self, user, message=''):
        if self.is_pending() and not self.is_committed():
            log = TransactionLog(type=self.REJECTED_STATE, transaction=self)
            log.user = user
            if message.strip() != '':
                log.message = message
            log.save()

            self.state = self.REJECTED_STATE
            self.last_modified = datetime.datetime.now()
            self.save()

            for user in User.objects.filter(account__transactionentry__transaction=self):
                user.message_set.create(
                    message=_('Transaction %(id)d regarding your account '
                        + 'has been rejected.') % {'id': self.id})
        else:
            raise InvalidTransaction(
                'Could not set transaction as rejected')


    def is_pending(self):
        return self.state == self.PENDING_STATE
    def has_pending(self):
        return self.state in (
            self.PENDING_STATE, self.COMMITTED_STATE, self.REJECTED_STATE)
    is_editable = is_pending

    def is_committed(self):
        return self.state == self.COMMITTED_STATE
    has_committed = is_committed

    def is_rejected(self):
        return self.state == self.REJECTED_STATE
    has_committed = is_rejected

    def get_pending(self):
        if self.has_pending():
            return self.log_set.filter(type=self.PENDING_STATE).lastest('timestamp')
    pending = property(get_pending, None, None)

    def get_committed(self):
        if self.has_committed():
            return self.log_set.filter(type=self.COMMITTED_STATE).lastest('timestamp')
    committed = property(get_committed, None, None)

    def get_rejected(self):
        if self.has_rejected():
            return self.log_set.filter(type=self.REJECTED_STATE).lastest('timestamp')
    rejected = property(get_rejected, None, None)

    def get_valid_logtype_choices(self):
        if self.is_committed() or self.is_rejected():
            return [('','')]
        else:
            states = dict(self.TRANSACTION_STATE)
            del states[self.PENDING_STATE]
            states = states.items()
            states.insert(0, ('',''))
            return states

    def css_class(self):
        if self.is_rejected():
            return 'rejected'
        elif self.is_pending():
            return 'pending'
        else:
            return 'committed'


class TransactionLog(models.Model):
    transaction = models.ForeignKey(Transaction,
        verbose_name=_('transaction'), related_name='log_set')
    type = models.CharField(_('type'), max_length=3,
        choices=Transaction.TRANSACTION_STATE)
    timestamp =  models.DateTimeField(_('timestamp'), auto_now_add=True)
    user = models.ForeignKey(User, verbose_name=_('user'))
    message = models.CharField(_('message'), max_length=200, blank=True)

    def save(self, *args, **kwargs):
        if self.id is not None:
            raise InvalidTransactionLog(
                'Altering transaction log entries is not allowed')
        if self.transaction.id is None:
            self.transaction.save()
        if self.type != Transaction.PENDING_STATE and self.transaction.log_set.filter(type=self.type).count():
            raise InvalidTransactionLog(
                'Only one instance of each log type is allowed.')
        super(TransactionLog, self).save(*args, **kwargs)

    class Meta:
        ordering = ('timestamp',)
        verbose_name = _('transaction log entry')
        verbose_name_plural = _('transaction log entries')

    def __unicode__(self):
        d = {
            'type': self.get_type_display(),
            'user': self.user,
            'message': self.message,
        }
        if self.timestamp is None:
            d['timestamp'] = u'(not saved)'
        else:
            d['timestamp'] = self.timestamp.strftime(settings.DATETIME_FORMAT)
        return _(u'%(type)s at %(timestamp)s by %(user)s: %(message)s') % d

    def css_class(self):
        if self.type == Transaction.REJECTED_STATE:
            return 'rejected'
        elif self.type == Transaction.PENDING_STATE:
            return 'pending'
        else:
            return 'committed'

class TransactionEntry(models.Model):
    transaction = models.ForeignKey(Transaction, verbose_name=_('transaction'),
        related_name='entry_set')
    account = models.ForeignKey('Account', verbose_name=_('account'))
    debit = models.DecimalField(_('debit amount'),
        max_digits=10, decimal_places=2, default=0)
    credit = models.DecimalField(_('credit amount'),
        max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if self.transaction.is_rejected():
            raise InvalidTransactionEntry(
                'Can not add entries to rejected transactions')
        if self.transaction.is_committed():
            raise InvalidTransactionEntry(
                'Can not add entries to committed transactions')

        if self.debit < 0 or self.credit < 0:
            raise InvalidTransactionEntry(
                'Credit and debit must be positive or zero')

        if self.debit == 0 and self.credit == 0:
            raise InvalidTransactionEntry(
                'Create or debit must be positive')

        super(TransactionEntry, self).save(*args, **kwargs)

    class Meta:
        unique_together = (('transaction', 'account'),)
        verbose_name = _('transaction entry')
        verbose_name_plural = _('transaction entries')
        ordering = ('credit', 'debit')

    def __unicode__(self):
        return _(u'%(account)s: debit %(debit)s, credit %(credit)s') % {
            'account': self.account.name,
            'debit': self.debit,
            'credit': self.credit,
        }
