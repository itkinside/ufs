from datetime import datetime
import unittest

from django.db import IntegrityError

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

        self.before = datetime.now()

        self.transaction = Transaction(group=self.group)
        self.transaction.save()
        self.transaction.entry_set.add(TransactionEntry(
            account=self.accounts[0], debit=100))
        self.transaction.entry_set.add(TransactionEntry(
            account=self.accounts[1], credit=100))

        self.transaction.set_registered(user=self.user)

        self.after = datetime.now()

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
            transaction.set_registered, user=self.user)

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

    def testRegisteredLogEntry(self):
        """Checks that a registered log entry is created"""

        transaction = self.transaction

        self.assertEqual(transaction.is_registered(), True)
        self.assertEqual(transaction.log_set.count(), 1)
        self.assertEqual(transaction.log_set.filter(type='Reg').count(), 1)

        registered = transaction.log_set.filter(type='Reg')[0].timestamp

        self.assert_(registered > self.before)
        self.assert_(registered < self.after)

    def testPayedLogEntry(self):
        """Checks creation of payed log entry"""

        transaction = self.transaction

        before = datetime.now()
        transaction.set_payed(user=self.user)
        after = datetime.now()

        self.assertEqual(transaction.is_registered(), True)
        self.assertEqual(transaction.is_payed(), True)
        self.assertEqual(transaction.log_set.count(), 2)
        self.assertEqual(transaction.log_set.filter(type='Pay').count(), 1)

        payed = transaction.log_set.filter(type='Pay')[0].timestamp
        self.assert_(payed > before)
        self.assert_(payed < after)

    def testRejectLogEntry(self):
        """Checks that registered transaction can be rejected"""

        transaction = self.transaction
        self.assertEqual(transaction.is_registered(), True)

        before = datetime.now()
        transaction.reject(message='Reason for rejecting', user=self.user)
        after = datetime.now()

        self.assertEqual(transaction.is_rejected(), True)
        self.assertEqual(transaction.log_set.count(), 2)
        self.assertEqual(transaction.log_set.filter(type='Rej').count(), 1)

        rejected = transaction.log_set.filter(type='Rej')[0].timestamp
        self.assert_(rejected > before)
        self.assert_(rejected < after)

    def testRejectPayedTransaction(self):
        """Test that rejecting payed transaction fails"""

        transaction = self.transaction
        transaction.set_payed(user=self.user)

        # FIXME: Maybe raise a different exception?
        self.assertEqual(transaction.is_registered(), True)
        self.assertEqual(transaction.is_payed(), True)
        self.assertRaises(InvalidTransaction, transaction.reject,
            'Reason for rejecting')

    def testReceivePayedTransaction(self):
        """Checks that we can set a payed transaction as received"""

        transaction = self.transaction
        transaction.set_payed(user=self.user)

        before = datetime.now()
        transaction.set_received(user=self.user)
        after = datetime.now()

        self.assertEqual(transaction.is_registered(), True)
        self.assertEqual(transaction.is_payed(), True)
        self.assertEqual(transaction.is_received(), True)
        self.assertEqual(transaction.log_set.count(), 3)
        self.assertEqual(transaction.log_set.filter(type='Rec').count(), 1)

        received = transaction.log_set.filter(type='Rec')[0].timestamp
        self.assert_(received > before)
        self.assert_(received < after)

    def testRejectReceivedTransaction(self):
        """Tests that rejecting received transaction fails"""

        transaction = self.transaction
        transaction.set_payed(user=self.user)
        transaction.set_received(user=self.user)

        self.assertRaises(InvalidTransaction, transaction.reject,
            'Reason for rejecting')

    def testReceiveNotPayedTransaction(self):
        """Checks that receiving a transaction that is not payed does not fail"""

        transaction = self.transaction

        transaction.set_received(user=self.user)

class LogTestCase(unittest.TestCase):
    def setUp(self):
        self.user = User(username='alice')
        self.user.save()

        self.group = Group(name='Group 1', slug='group1')
        self.group.save()

        self.transaction = Transaction(group=self.group)
        self.transaction.set_registered(user=self.user)

    def tearDown(self):
        self.transaction.delete()
        self.group.delete()
        self.user.delete()

    def testLogEntryUniqePerType(self):
        """Checks that only one log entry of each type is allowed"""

        for key, value in Transaction.TRANSACTION_STATE:
            log1 = TransactionLog(type=key, transaction=self.transaction,
                                  user=self.user)
            log2 = TransactionLog(type=key, transaction=self.transaction,
                                  user=self.user)
            if key != 'Reg':
                log1.save()
            self.assertRaises(InvalidTransactionLog, log2.save)

    def testLogEntryModify(self):
        """Checks that modifying log entry raises error"""
        self.assertRaises(InvalidTransactionLog,
            self.transaction.log_set.filter(type='Reg')[0].save)

        for key, value in Transaction.TRANSACTION_STATE:
            log1 = TransactionLog(type=key, transaction=self.transaction,
                                  user=self.user)

            if key != 'Reg':
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
        """Checks that setting both debit and credit will fail"""

        self.entry.debit = 100
        self.entry.credit = 100
        self.assertRaises(InvalidTransactionEntry, self.entry.save)

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
