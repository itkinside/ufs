import unittest
from datetime import datetime as dt

from itkufs.accounting.models import *

class GroupTestCase(unittest.TestCase):
    # FIXME: Test all group properties

    def setUp(self):
        self.user = User(username='alice')
        self.user.save()

        self.group = Group(name='Group 1', slug='group1')
        self.group.save()

        self.accounts = [
            Account(name='Account 1', slug='account1', group=self.group),
            Account(name='Account 2', slug='account2', group=self.group),
            Account(name='Account 3', slug='account3', group=self.group),
        ]
        for account in self.accounts:
            account.save()

        self.transactions = {
            'Pen': Transaction(group=self.group),
            'Com': Transaction(group=self.group),
            'Rej': Transaction(group=self.group),
        }
        for transaction in self.transactions.values():
            transaction.save()
            transaction.entry_set.add(
                TransactionEntry(account=self.accounts[0], credit=100))
            transaction.entry_set.add(
                TransactionEntry(account=self.accounts[1], debit=100))
            transaction.set_pending(user=self.user)

        self.transactions['Undef'] = Transaction(group=self.group)
        self.transactions['Undef'].save()

        self.transactions['Com'].set_committed(user=self.user)
        self.transactions['Rej'].set_rejected(user=self.user)

    def tearDown(self):
        for transaction in self.transactions.values():
            transaction.delete()
        for account in self.accounts:
            account.delete()
        self.group.delete()
        self.user.delete()

    ### Transaction set tests
    # Please keep in sync with Account's set tests
    # FIXME: Check more than count in the set tests?

    def testTransactionSet(self):
        """Checks that transaction_set returns all transactions that is not
        rejected"""

        set = self.group.transaction_set
        self.assertEqual(set.count(), 2)

    def testTransactionSetWithRejected(self):
        """Checks that transaction_set_with_rejected returns all
        transactions"""

        set = self.group.transaction_set_with_rejected
        self.assertEqual(set.count(), 3)

    def testPendingTransactionSet(self):
        """Checks that pending_transaction_set returns all pending
        transactions"""

        set = self.group.pending_transaction_set
        self.assertEqual(set.count(), 1)

    def testCommittedTransactionSet(self):
        """Checks that committed_transaction_set returns all committed
        transactions that are not rejected"""

        set = self.group.committed_transaction_set
        self.assertEqual(set.count(), 1)

    def testRejectedTransactionSet(self):
        """Checks that rejected_transaction_set returns all rejected
        transactions"""

        set = self.group.rejected_transaction_set
        self.assertEqual(set.count(), 1)

    #FIXME add user_account testcase and group account testcase!

class AccountTestCase(unittest.TestCase):
    # FIXME: Test all account properties

    def setUp(self):
        self.user = User(username='alice')
        self.user.save()

        self.group = Group(name='Group 1', slug='group1')
        self.group.save()

        self.accounts = [
            Account(name='Account 1', slug='account1', group=self.group),
            Account(name='Account 2', slug='account2', group=self.group),
            Account(name='Account 3', slug='account3', group=self.group),
        ]
        for account in self.accounts:
            account.save()
        self.account = self.accounts[0]

        self.transactions = {
            'Pen': Transaction(group=self.group),
            'Com': Transaction(group=self.group),
            'Rej': Transaction(group=self.group),
        }
        for transaction in self.transactions.values():
            transaction.save()
            transaction.entry_set.add(
                TransactionEntry(account=self.accounts[0], credit=100))
            transaction.entry_set.add(
                TransactionEntry(account=self.accounts[1], debit=100))
            transaction.set_pending(user=self.user)

        self.transactions['Undef'] = Transaction(group=self.group)
        self.transactions['Undef'].save()

        self.transactions['Com'].set_committed(user=self.user)
        self.transactions['Rej'].set_rejected(user=self.user)

    def tearDown(self):
        for transaction in self.transactions.values():
            transaction.delete()
        for account in self.accounts:
            account.delete()
        self.group.delete()
        self.user.delete()

    ### Transaction set tests
    # Please keep in sync with Group's set tests
    # FIXME: Check more than count in the set tests?

    def testTransactionSet(self):
        """Checks that transaction_set returns all transactions that are not
        rejected"""

        set = self.account.transaction_set
        self.assertEqual(set.count(), 2)

    def testTransactionSetWithRejected(self):
        """Checks that transaction_set_with_rejected returns all
        transactions"""

        set = self.account.transaction_set_with_rejected
        self.assertEqual(set.count(), 3)

    def testPendingTransactionSet(self):
        """Checks that pending_transaction_set returns all pending
        transactions"""

        set = self.account.pending_transaction_set
        self.assertEqual(set.count(), 1)

    def testCommittedTransactionSet(self):
        """Checks that committed_transaction_set returns all committed
        transactions that are not rejected"""

        set = self.account.committed_transaction_set
        self.assertEqual(set.count(), 1)

    def testRejectedTransactionSet(self):
        """Checks that rejected_transaction_set returns all rejected
        transactions"""

        set = self.account.rejected_transaction_set
        self.assertEqual(set.count(), 1)

    # FIXME test that one account per user per group is enforced

class TransactionTestCase(unittest.TestCase):
    def setUp(self):
        self.user = User(username='alice')
        self.user.save()

        self.group = Group(name='Group 1', slug='group1')
        self.group.save()

        self.accounts = [
            Account(name='Account 1', slug='account1', group=self.group),
            Account(name='Account 2', slug='account2', group=self.group),
            Account(name='Account 3', slug='account3', group=self.group),
        ]
        for account in self.accounts:
            account.save()

        self.before = dt.now()

        self.transaction = Transaction(group=self.group)
        self.transaction.save()
        self.transaction.entry_set.add(TransactionEntry(
            account=self.accounts[0], debit=100))
        self.transaction.entry_set.add(TransactionEntry(
            account=self.accounts[1], credit=100))

        self.transaction.set_pending(user=self.user)

        self.after = dt.now()

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

        transaction.entry_set.add(TransactionEntry(
            account=self.accounts[1], debit=200))
        transaction.entry_set.add(TransactionEntry(
            account=self.accounts[0], credit=100))
        self.assertRaises(InvalidTransaction,
            transaction.set_pending, user=self.user)

        transaction.delete()

    def testAccountOnlyOnceInTransaction(self):
        """Checks that multiple credit accounts are allowed in a transaction"""

        transaction = Transaction(group=self.group)
        transaction.save()

        transaction.entry_set.add(TransactionEntry(
            account=self.accounts[0], debit=200))
        transaction.entry_set.add(TransactionEntry(
            account=self.accounts[1], credit=100))
        transaction.entry_set.add(TransactionEntry(
            account=self.accounts[2], credit=100))

        transaction.delete()

    def testPendingLogEntry(self):
        """Checks that a pending log entry is created"""

        transaction = self.transaction

        self.assertEqual(transaction.is_pending(), True)
        self.assertEqual(transaction.log_set.count(), 1)
        self.assertEqual(transaction.log_set.filter(type=Transaction.PENDING_STATE).count(), 1)

        pending = transaction.log_set.filter(type=Transaction.PENDING_STATE)[0].timestamp

        self.assert_(pending > self.before)
        self.assert_(pending < self.after)

    def testCommittedLogEntry(self):
        """Checks that a committed log entry is created"""

        transaction = self.transaction

        before = dt.now()
        transaction.set_committed(user=self.user)
        after = dt.now()

        self.assertEqual(transaction.is_committed(), True)
        self.assertEqual(transaction.log_set.count(), 2)
        self.assertEqual(transaction.log_set.filter(type=Transaction.COMMITTED_STATE).count(), 1)

        committed = transaction.log_set.filter(type=Transaction.COMMITTED_STATE)[0].timestamp

        self.assert_(committed > before)
        self.assert_(committed < after)

    def testRejectLogEntry(self):
        """Checks that pending transaction can be rejected"""

        transaction = self.transaction
        self.assertEqual(transaction.is_pending(), True)

        before = dt.now()
        transaction.set_rejected(message='Reason for rejecting', user=self.user)
        after = dt.now()

        self.assertEqual(transaction.is_rejected(), True)
        self.assertEqual(transaction.log_set.count(), 2)
        self.assertEqual(transaction.log_set.filter(type=Transaction.REJECTED_STATE).count(), 1)

        rejected = transaction.log_set.filter(type=Transaction.REJECTED_STATE)[0].timestamp
        self.assert_(rejected > before)
        self.assert_(rejected < after)

    def testRejectCommitedTransaction(self):
        """Tests that rejecting committed transaction fails"""

        transaction = self.transaction
        transaction.set_committed(user=self.user)

        self.assertRaises(InvalidTransaction, transaction.set_rejected,
            message='Reason for rejecting', user=self.user)

class LogTestCase(unittest.TestCase):
    def setUp(self):
        self.user = User(username='alice')
        self.user.save()

        self.group = Group(name='Group 1', slug='group1')
        self.group.save()

        self.transaction = Transaction(group=self.group)
        self.transaction.set_pending(user=self.user)

    def tearDown(self):
        self.transaction.delete()
        self.group.delete()
        self.user.delete()

    def testLogEntryUniqePerType(self):
        """Checks that only one log entry of each type is allowed (except for pending)"""

        for key, value in Transaction.TRANSACTION_STATE:
            log1 = TransactionLog(type=key, transaction=self.transaction,
                                  user=self.user)
            log2 = TransactionLog(type=key, transaction=self.transaction,
                                  user=self.user)
            if key != Transaction.PENDING_STATE:
                log1.save()
                self.assertRaises(InvalidTransactionLog, log2.save)

    def testLogEntryModify(self):
        """Checks that modifying log entry raises error"""
        self.assertRaises(InvalidTransactionLog,
            self.transaction.log_set.filter(type=Transaction.PENDING_STATE)[0].save)

        for key, value in Transaction.TRANSACTION_STATE:
            log1 = TransactionLog(type=key, transaction=self.transaction,
                                  user=self.user)

            if key != Transaction.PENDING_STATE:
                log1.save()
                self.assertRaises(InvalidTransactionLog, log1.save)


class EntryTestCase(unittest.TestCase):
    def setUp(self):
        self.user = User(username='alice')
        self.user.save()

        self.group = Group(name='group1', slug='group1')
        self.group.save()

        self.account = Account(name='account1', slug='account1',
            group=self.group)
        self.account.save()

        self.transaction = Transaction(group=self.group)
        self.transaction.save()

        self.entry = TransactionEntry(account=self.account,
            debit=100, credit=100, transaction=self.transaction)

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
        self.assertRaises(InvalidTransactionEntry, self.entry.save)

    def testNegativeDebit(self):
        """Checks that inputing av negative debit  raises an error"""

        self.entry.debit = -100
        self.assertRaises(InvalidTransactionEntry, self.entry.save)

    def testDebitAndCreditSetToZero(self):
        """Checks that setting both debit and credit to zero raises error"""

        self.entry.debit = 0
        self.entry.credit = 0
        self.assertRaises(InvalidTransactionEntry, self.entry.save)


class SettlementTestCase(unittest.TestCase):
    # FIXME: Test all settlement properties

    def setUp(self):
        pass

    def breakDown(self):
        pass
