import pytest
import unittest
import datetime

from itkufs.accounting.models import (
    Account,
    Group,
    InvalidTransaction,
    InvalidTransactionEntry,
    InvalidTransactionLog,
    RoleAccount,
    Transaction,
    TransactionEntry,
    TransactionLog,
    User,
)


class GroupTestCase(unittest.TestCase):
    def setUp(self):
        self.users = [
            User(username="alice"),
            User(username="bob"),
            User(username="darth"),
        ]
        for user in self.users:
            user.save()

        self.group = Group(name="Group 1", slug="group1")
        self.group.save()

        self.accounts = [
            # Normal user account
            Account(
                name="Account 1",
                slug="account1",
                group=self.group,
                owner=self.users[0],
            ),
            # Normal user account
            Account(
                name="Account 2",
                slug="account2",
                group=self.group,
                owner=self.users[1],
            ),
            # Inactive user account
            Account(
                name="Account 3",
                slug="account3",
                group=self.group,
                owner=self.users[2],
                active=False,
            ),
            # Group account
            Account(
                name="Account 4",
                slug="account4",
                group=self.group,
                type=Account.ASSET_ACCOUNT,
                group_account=True,
            ),
            # Inactive group account
            Account(
                name="Account 5",
                slug="account5",
                group=self.group,
                type=Account.ASSET_ACCOUNT,
                active=False,
                group_account=True,
            ),
            # Bank account
            self.group.roleaccount_set.get(
                role=RoleAccount.BANK_ACCOUNT
            ).account,
            # Cash account
            self.group.roleaccount_set.get(
                role=RoleAccount.CASH_ACCOUNT
            ).account,
        ]
        for account in self.accounts:
            account.save()

        self.transactions = {
            "Pen": Transaction(group=self.group),
            "Com": Transaction(group=self.group),
            "Rej": Transaction(group=self.group),
        }
        for transaction in self.transactions.values():
            transaction.save()
            transaction.entry_set.create(account=self.accounts[0], credit=100)
            transaction.entry_set.create(account=self.accounts[1], debit=100)
            transaction.set_pending(user=self.users[0])

        self.transactions["Undef"] = Transaction(group=self.group)
        self.transactions["Undef"].save()

        self.transactions["Com"].set_committed(user=self.users[1])
        self.transactions["Rej"].set_rejected(user=self.users[1])

    def tearDown(self):
        for transaction in self.transactions.values():
            transaction.delete()
        for account in self.accounts:
            account.delete()
        self.group.delete()
        for user in self.users:
            user.delete()

    def testUnicode(self):
        """Checks that __unicode__() returns group name"""

        assert self.group.name == self.group.__unicode__()

    def testAbsoluteUrl(self):
        """Checks that get_absolute_url() contains group slug"""

        assert self.group.slug in self.group.get_absolute_url()

    def testEmptySlugRaisesError(self):
        """Checks that saving a group without a slug results in a ValueError"""

        self.group.slug = ""
        with pytest.raises(ValueError):
            self.group.save()

    def testGetAccountNumberDisplay(self):
        """Check that account numbers are formated correctly."""

        self.group.account_number = "12345678901"
        assert "1234.56.78901" == self.group.get_account_number_display()

    def testUserAccountSet(self):
        """Checks that get_user_account_set returns all user accounts"""

        set = self.group.get_user_account_set()
        assert set.count() == 3
        assert self.accounts[0] in set
        assert self.accounts[1] in set
        assert self.accounts[2] in set
        assert self.accounts[3] not in set
        assert self.accounts[4] not in set
        assert self.accounts[5] not in set
        assert self.accounts[6] not in set

    def testGroupAccountSet(self):
        """Checks that get_group_account_set returns all group accounts"""

        set = self.group.get_group_account_set()
        assert set.count() == 4
        assert self.accounts[0] not in set
        assert self.accounts[1] not in set
        assert self.accounts[2] not in set
        assert self.accounts[3] in set
        assert self.accounts[4] in set
        assert self.accounts[5] in set
        assert self.accounts[6] in set

    # --- Transaction set tests
    # Please keep in sync with Account's set tests

    def testTransactionSet(self):
        """Checks that transaction_set returns all transactions that is not
        rejected"""

        set = self.group.transaction_set
        assert set.count() == 2
        assert self.transactions["Pen"] in set
        assert self.transactions["Com"] in set
        assert self.transactions["Rej"] not in set

    def testTransactionSetWithRejected(self):
        """Checks that transaction_set_with_rejected returns all
        transactions"""

        set = self.group.transaction_set_with_rejected
        assert set.count() == 3
        assert self.transactions["Pen"] in set
        assert self.transactions["Com"] in set
        assert self.transactions["Rej"] in set

    def testPendingTransactionSet(self):
        """Checks that pending_transaction_set returns all pending
        transactions"""

        set = self.group.pending_transaction_set
        assert set.count() == 1
        assert self.transactions["Pen"] in set
        assert self.transactions["Com"] not in set
        assert self.transactions["Rej"] not in set

    def testCommittedTransactionSet(self):
        """Checks that committed_transaction_set returns all committed
        transactions that are not rejected"""

        set = self.group.committed_transaction_set
        assert set.count() == 1
        assert self.transactions["Pen"] not in set
        assert self.transactions["Com"] in set
        assert self.transactions["Rej"] not in set

    def testRejectedTransactionSet(self):
        """Checks that rejected_transaction_set returns all rejected
        transactions"""

        set = self.group.rejected_transaction_set
        assert set.count() == 1
        assert self.transactions["Pen"] not in set
        assert self.transactions["Com"] not in set
        assert self.transactions["Rej"] in set


class AccountTestCase(unittest.TestCase):
    def setUp(self):
        self.users = [
            User(username="alice"),
            User(username="bob"),
            User(username="darth"),
        ]
        for user in self.users:
            user.save()

        self.group = Group(name="Group 1", slug="group1")
        self.group.save()

        self.accounts = [
            # Normal user account
            Account(
                name="Account 1",
                slug="account1",
                group=self.group,
                owner=self.users[0],
            ),
            # Normal user account
            Account(
                name="Account 2",
                slug="account2",
                group=self.group,
                owner=self.users[1],
            ),
            # Inactive user account
            Account(
                name="Account 3",
                slug="account3",
                group=self.group,
                owner=self.users[2],
                active=False,
            ),
            # Group account
            Account(
                name="Account 4",
                slug="account4",
                group=self.group,
                type=Account.ASSET_ACCOUNT,
            ),
            # Inactive group account
            Account(
                name="Account 5",
                slug="account5",
                group=self.group,
                type=Account.ASSET_ACCOUNT,
                active=False,
            ),
            # Bank account
            self.group.roleaccount_set.get(
                role=RoleAccount.BANK_ACCOUNT
            ).account,
            # Cash account
            self.group.roleaccount_set.get(
                role=RoleAccount.CASH_ACCOUNT
            ).account,
        ]
        for account in self.accounts:
            account.save()
        self.account = self.accounts[0]

        self.transactions = {
            "Pen": Transaction(group=self.group),
            "Com": Transaction(group=self.group),
            "Rej": Transaction(group=self.group),
        }
        values = {"Pen": 150, "Com": 200, "Rej": 100}
        for state, transaction in self.transactions.items():
            transaction.save()
            transaction.entry_set.create(
                account=self.accounts[0], credit=values[state]
            )
            transaction.entry_set.create(
                account=self.accounts[1], debit=values[state]
            )
            transaction.set_pending(user=self.users[0])

        self.transactions["Undef"] = Transaction(group=self.group)
        self.transactions["Undef"].save()

        self.transactions["Com"].set_committed(user=self.users[2])
        self.transactions["Rej"].set_rejected(user=self.users[2])

    def tearDown(self):
        for transaction in self.transactions.values():
            transaction.delete()
        for account in self.accounts:
            account.delete()
        self.group.delete()
        for user in self.users:
            user.delete()

    def testUnicode(self):
        """Checks that __unicode__() contains account and group name"""

        result = self.account.__unicode__()
        assert self.account.group.name in result
        assert self.account.name in result

    def testAbsoluteUrl(self):
        """Checks that get_absolute_url() contains account and group slug"""

        result = self.account.get_absolute_url()
        assert self.account.group.slug in result
        assert self.account.slug in result

    def testEmptySlugRaisesError(self):
        """Checks that saving an account without a slug results in a
        ValueError"""

        self.account.slug = ""
        with pytest.raises(ValueError):
            self.account.save()

    def testBalance(self):
        """Checks that account balance is correct"""

        # TODO: Add more transactions at different days and check balance
        # inbetween using date kwarg

        account1 = self.accounts[0]
        account2 = self.accounts[1]

        # User account after credit of 100
        assert int(account1.balance()) == (-200)
        # User account after debit of 100
        assert int(account2.balance()) == 200

        account1 = Account.objects.get(id=account1.id)
        account2 = Account.objects.get(id=account2.id)

        # User account after credit of 200
        assert int(account1.confirmed_balance_sql) == (-200)
        # User account after debit of 200
        assert int(account2.confirmed_balance_sql) == 200

        # User account after credit of 350
        assert int(account1.future_balance_sql) == (-350)
        # User account after debit of 350
        assert int(account2.future_balance_sql) == 350

    # --- Transaction set tests
    # Please keep in sync with Group's set tests

    def testTransactionSet(self):
        """Checks that transaction_set returns all transactions that are not
        rejected"""

        set = self.account.transaction_set
        assert set.count() == 2
        assert self.transactions["Pen"] in set
        assert self.transactions["Com"] in set
        assert self.transactions["Rej"] not in set

    def testTransactionSetWithRejected(self):
        """Checks that transaction_set_with_rejected returns all
        transactions"""

        set = self.account.transaction_set_with_rejected
        assert set.count() == 3
        assert self.transactions["Pen"] in set
        assert self.transactions["Com"] in set
        assert self.transactions["Rej"] in set

    def testPendingTransactionSet(self):
        """Checks that pending_transaction_set returns all pending
        transactions"""

        set = self.account.pending_transaction_set
        assert set.count() == 1
        assert self.transactions["Pen"] in set
        assert self.transactions["Com"] not in set
        assert self.transactions["Rej"] not in set

    def testCommittedTransactionSet(self):
        """Checks that committed_transaction_set returns all committed
        transactions that are not rejected"""

        set = self.account.committed_transaction_set
        assert set.count() == 1
        assert self.transactions["Pen"] not in set
        assert self.transactions["Com"] in set
        assert self.transactions["Rej"] not in set

    def testRejectedTransactionSet(self):
        """Checks that rejected_transaction_set returns all rejected
        transactions"""

        set = self.account.rejected_transaction_set
        assert set.count() == 1
        assert self.transactions["Pen"] not in set
        assert self.transactions["Com"] not in set
        assert self.transactions["Rej"] in set


class TransactionTestCase(unittest.TestCase):
    def setUp(self):
        self.user = User(username="alice")
        self.user.save()

        self.group = Group(name="Group 1", slug="group1")
        self.group.save()

        self.accounts = [
            Account(name="Account 1", slug="account1", group=self.group),
            Account(name="Account 2", slug="account2", group=self.group),
            Account(name="Account 3", slug="account3", group=self.group),
        ]
        for account in self.accounts:
            account.save()

        self.before = datetime.datetime.now()

        self.transaction = Transaction(group=self.group)
        self.transaction.save()
        self.transaction.entry_set.create(account=self.accounts[0], debit=100)
        self.transaction.entry_set.create(account=self.accounts[1], credit=100)

        self.transaction.set_pending(user=self.user)

        self.after = datetime.datetime.now()

    def tearDown(self):
        self.transaction.delete()
        for account in self.accounts:
            account.delete()
        self.group.delete()
        self.user.delete()

    def testEmptyTransaction(self):
        """Checks that empty transactions are accepted"""

        transaction = Transaction(group=self.group)
        transaction.save()
        transaction.delete()

    def testEqualDebitAndCreditAmount(self):
        """Checks that transaction only accept sum(debit)==sum(credit)"""

        transaction = Transaction(group=self.group)
        transaction.save()

        transaction.entry_set.create(account=self.accounts[1], debit=200)
        transaction.entry_set.create(account=self.accounts[0], credit=100)

        with pytest.raises(InvalidTransaction):
            transaction.set_pending(user=self.user)

        transaction.delete()

    def testAccountOnlyOnceInTransaction(self):
        """Checks that multiple credit accounts are allowed in a transaction"""

        transaction = Transaction(group=self.group)
        transaction.save()

        TransactionEntry.objects.create(
            account=self.accounts[0], debit=200, transaction=transaction
        )
        TransactionEntry.objects.create(
            account=self.accounts[1], credit=100, transaction=transaction
        )
        TransactionEntry.objects.create(
            account=self.accounts[2], credit=100, transaction=transaction
        )

        transaction.delete()

    def testPendingLogEntry(self):
        """Checks that a pending log entry is created"""

        transaction = self.transaction

        assert transaction.is_pending() is True
        assert transaction.log_set.count() == 1
        assert (
            transaction.log_set.filter(type=Transaction.PENDING_STATE).count()
            == 1
        )

        pending = transaction.log_set.filter(type=Transaction.PENDING_STATE)[
            0
        ].timestamp

        assert pending > self.before
        assert pending < self.after

    def testCommittedLogEntry(self):
        """Checks that a committed log entry is created"""

        transaction = self.transaction

        before = datetime.datetime.now()
        transaction.set_committed(user=self.user)
        after = datetime.datetime.now()

        assert transaction.is_committed() is True
        assert transaction.log_set.count() == 2
        assert (
            transaction.log_set.filter(type=Transaction.COMMITTED_STATE).count()
            == 1
        )

        committed = transaction.log_set.filter(
            type=Transaction.COMMITTED_STATE
        )[0].timestamp

        assert committed > before
        assert committed < after

    def testRejectLogEntry(self):
        """Checks that pending transaction can be rejected"""

        transaction = self.transaction
        assert transaction.is_pending() is True

        before = datetime.datetime.now()
        transaction.set_rejected(message="Reason for rejecting", user=self.user)
        after = datetime.datetime.now()

        assert transaction.is_rejected() is True
        assert transaction.log_set.count() == 2
        assert (
            transaction.log_set.filter(type=Transaction.REJECTED_STATE).count()
            == 1
        )

        rejected = transaction.log_set.filter(type=Transaction.REJECTED_STATE)[
            0
        ].timestamp
        assert rejected > before
        assert rejected < after

    def testRejectCommitedTransaction(self):
        """Tests that rejecting committed transaction fails"""

        transaction = self.transaction
        transaction.set_committed(user=self.user)

        with pytest.raises(InvalidTransaction):
            transaction.set_rejected(
                message="Reason for rejecting", user=self.user
            )


class LogTestCase(unittest.TestCase):
    def setUp(self):
        self.user = User(username="alice")
        self.user.save()

        self.group = Group(name="Group 1", slug="group1")
        self.group.save()

        self.transaction = Transaction(group=self.group)
        self.transaction.set_pending(user=self.user)

    def tearDown(self):
        self.transaction.delete()
        self.group.delete()
        self.user.delete()

    def testLogEntryUniqePerType(self):
        """Checks that only one log entry of each type is allowed (except for
        pending)
        """

        for key, value in Transaction.TRANSACTION_STATE:
            log1 = TransactionLog(
                type=key, transaction=self.transaction, user=self.user
            )
            log2 = TransactionLog(
                type=key, transaction=self.transaction, user=self.user
            )
            if key != Transaction.PENDING_STATE:
                log1.save()
                with pytest.raises(InvalidTransactionLog):
                    log2.save()

    def testLogEntryModify(self):
        """Checks that modifying log entry raises error"""

        log_entry = self.transaction.log_set.filter(
            type=Transaction.PENDING_STATE
        )[0]

        with pytest.raises(InvalidTransactionLog):
            log_entry.save()

        for key, value in Transaction.TRANSACTION_STATE:
            log1 = TransactionLog(
                type=key, transaction=self.transaction, user=self.user
            )

            if key != Transaction.PENDING_STATE:
                log1.save()
                with pytest.raises(InvalidTransactionLog):
                    log1.save()


class EntryTestCase(unittest.TestCase):
    def setUp(self):
        self.user = User(username="alice")
        self.user.save()

        self.group = Group(name="group1", slug="group1")
        self.group.save()

        self.account = Account(
            name="account1", slug="account1", group=self.group
        )
        self.account.save()

        self.transaction = Transaction(group=self.group)
        self.transaction.save()

        self.entry = self.transaction.entry_set.create(
            account=self.account, debit=100, credit=100
        )

    def tearDown(self):
        self.transaction.delete()
        self.account.delete()
        self.group.delete()
        self.user.delete()

    def testDebitAndCreditInSameEntry(self):
        """Checks that setting both debit and credit does not fail"""

        self.entry.debit = 100
        self.entry.credit = 100
        self.entry.save()

    def testNegativeCredit(self):
        """Checks that inputing av negative credit raises an error"""

        self.entry.credit = -100
        with pytest.raises(InvalidTransactionEntry):
            self.entry.save()

    def testNegativeDebit(self):
        """Checks that inputing av negative debit  raises an error"""

        self.entry.debit = -100
        with pytest.raises(InvalidTransactionEntry):
            self.entry.save()

    def testDebitAndCreditSetToZero(self):
        """Checks that setting both debit and credit to zero raises error"""

        self.entry.debit = 0
        self.entry.credit = 0
        with pytest.raises(InvalidTransactionEntry):
            self.entry.save()


class SettlementTestCase(unittest.TestCase):
    # FIXME: Test all settlement properties

    def setUp(self):
        pass

    def breakDown(self):
        pass
