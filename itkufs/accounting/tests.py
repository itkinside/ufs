import unittest
from datetime import datetime
from django.db import IntegrityError

from itkufs.accounting.models import *
from itkufs.accounting.models import NewTransaction as Transaction


# FIXME Write more tests
# FIXME Add docstrings explainging purpose of all tests

class GroupTestCase(unittest.TestCase):
    """Test the group model"""
    def setUp(self):
        pass

    def testDefaultGroup(self):
        pass

    def testPayedTransactionSet(self):
        """Checks that payed_transaction_set only contains payed and related transactions"""
        # FIXME this test _will_ break when we change transaction model

        group = Group.objects.get(id=1)
        account1 = Account.objects.get(id=1)
        account2 = Account.objects.get(id=2)

        self.assertEqual(group.payed_transaction_set().count(), 0)

        # This one should show up
        t1 = Transaction(debit_account=account1, credit_account=account2,
            amount=100, payed=datetime.now())

        # Not payed show not be in set
        t2 = Transaction(debit_account=account1, credit_account=account2,
            amount=200)

        t1.save()
        t2.save()

        transactions = group.payed_transaction_set()
        for t in transactions:
            self.assert_(t.payed is not None)
            self.assertEqual(t.amount, 100)
            self.assert_(t.credit_account.group == group
                or t.debit_account.group == group)

        t1.delete()
        t2.delete()

    # ...

class AccountTestCase(unittest.TestCase):
    def setUp(self):
        self.group   = Group(name='Account Test Group', slug='account-test-group-slug')
        self.default = Account(name='Account Test', slug='account-test-slug')

    def testDefaultAccount(self):
        default = self.default

        self.assertEqual(default.name,'Account Test')
        self.assertEqual(default.ignore_block_limit, False)
        self.assertEqual(default.type, 'Li')
        self.assertEqual(default.owner, None)
        self.assertEqual(default.active, True)

    def testAccountTypes(self):
        self.fail('Test not implemented')

    def testAccountWithOwner(self):
        self.fail('Test not implemented')

    def testDisabledAccount(self):
        self.fail('Test not implemented')

    def testAccountBalance(self):
        self.fail('Test not implemented')

class TransactionTestCase(unittest.TestCase):
    def setUp(self):
        Group.objects.all().delete()
        self.group = Group(name='group1', slug='group1')
        self.group.save()

        self.accounts = [
            Account(name='account1', slug='account1', group=self.group),
            Account(name='account2', slug='account2', group=self.group),
            Account(name='account3', slug='account3', group=self.group),
        ]
        for a in self.accounts:
            a.save()

        self.transaction = Transaction()
        self.transaction.save()
        self.transaction.entry_set.add(TransactionEntry(account= self.accounts[0], debit=100))
        self.transaction.entry_set.add(TransactionEntry(account= self.accounts[1], debit=100))


    def tearDown(self):
        Transaction.objects.all().delete()
        Account.objects.all().delete()
        Group.objects.all().delete()

    def testEmptyTransaction(self):
        """Checks that empty transactions are accepted"""
        # FIXME
        pass

    def testNullAmountTransaction(self):
        """Checks that transaction fail when debit and credit are not given"""
        # FIXME not needed as entry test should cover this
        pass

    def testEqualDebitAndCreditAmount(self):
        """Checks that transaction only accept sum(debit)==sum(credit)"""

        transaction = Transaction()
        transaction.save()

        transaction.entry_set.add(TransactionEntry(account=self.accounts[1], debit=200))
        transaction.entry_set.add(TransactionEntry(account=self.accounts[0], credit=100))
        self.assertRaises(InvalidTransaction, transaction.save)

    def testAccountOnlyOnceInTransaction(self):
        """Checks that debit accounts are only present once per transaction"""

        transaction = Transaction()
        transaction.save()

        transaction.entry_set.add(TransactionEntry(account=self.accounts[1], debit=200))
        transaction.entry_set.add(TransactionEntry(account=self.accounts[0], credit=100))

        self.assertRaises(IntegrityError, transaction.entry_set.add, TransactionEntry(account=self.accounts[1], credit=100))

    def testRegisteredLogEntry(self):
        """Checks that a registered log entry is created"""

        transaction = self.transaction

        self.assertEqual(transaction.is_registered(), True)
        self.assertEqual(transaction.log_set.count(), 1)
        self.assertEqual(transaction.log_set.filter(type='Reg').count(), 1)
        #FIXME test time

    def testPayedLogEntry(self):
        """Checks creation of payed log entry"""

        transaction = self.transaction
        transaction.set_payed()

        self.assertEqual(transaction.is_registered(), True)
        self.assertEqual(transaction.is_payed(), True)
        self.assertEqual(transaction.log_set.count(), 2)
        self.assertEqual(transaction.log_set.filter(type='Pay').count(), 1)
        #FIXME test time

    def testRejectLogEntry(self):
        """Checks that registered transaction can be rejected"""

        transaction = self.transaction
        self.assertEqual(transaction.is_registered(), True)

        transaction.reject('Reason for rejecting')

        self.assertEqual(transaction.is_rejected(), True)
        self.assertEqual(transaction.log_set.count(), 2)
        self.assertEqual(transaction.log_set.filter(type='Rej').count(), 1)
        #FIXME test time

    def testRejectPayedTransaction(self):
        """Test that rejecting payed transaction fails"""

        transaction = self.transaction
        transaction.set_payed()

        #FIXME different error type perhaps?
        self.assertEqual(transaction.is_registered(), True)
        self.assertEqual(transaction.is_payed(), True)
        self.assertRaises(InvalidTransaction, transaction.reject, 'Reason for rejecting')

    def testRecievePayedTransaction(self):
        """Checks that we can set a payed transaction as recieved"""

        transaction = self.transaction
        transaction.set_payed()
        transaction.set_recieved()

        self.assertEqual(transaction.is_registered(), True)
        self.assertEqual(transaction.is_payed(), True)
        self.assertEqual(transaction.is_received(), True)
        self.assertEqual(transaction.log_set.count(), 3)
        self.assertEqual(transaction.log_set.filter(type='Rec').count(), 1)

    def testRejectRecievedTransaction(self):
        """Tests that rejecting recieved transaction fails"""
        transaction = self.transaction
        transaction.set_payed()
        transaction.set_recieved()

        self.assertRaises(InvalidTransaction, transaction.reject, 'Reason for rejecting')

    def testRecieveNotPayedTransaction(self):
        """Checks that recieving a transaction that is not payed fails"""
        transaction = self.transaction

        self.assertRaises(InvalidTransaction, transaction.set_recieved)

    def testUserGetsPassedOnToLog(self):
        self.fail('Test not written yet')

class LogTestCase(unittest.TestCase):
    def setUp(self):
        self.transaction = Transaction()
        self.transaction.save()

    def tearDown(self):
        self.transaction.delete()

    def testLogEntryUniqePerType(self):
        """Checks that we can only have one log entry of each type"""
        for key, value in TRANSACTIONLOG_TYPE:
            log1 = TransactionLog(type=key, transaction=self.transaction)
            log2 = TransactionLog(type=key, transaction=self.transaction)

            if key != 'Reg':
                log1.save()
            self.assertRaises(IntegrityError, log2.save)


    def testLogEntryModify(self):
        """Test that modifying log entry raises error"""
        self.assertRaises(InvalidTransactionLog, self.transaction.log_set.filter(type='Reg')[0].save)

        for key, value in TRANSACTIONLOG_TYPE:
            log1 = TransactionLog(type=key, transaction=self.transaction)

            if key != 'Reg':
                log1.save()
                self.assertRaises(InvalidTransactionLog, log1.save)

class EntryTestCase(unittest.TestCase):
    def setUp(self):
        Group.objects.all().delete()
        group = Group(name='group1', slug='group1')
        group.save()

        account = Account(name='account1', slug='account1', group=group)
        account.save()

        transaction = Transaction()
        transaction.save()

        self.entry = TransactionEntry(account=account, debit=100, credit=100, transaction=transaction)


    def tearDown(self):
        Transaction.objects.all().delete()
        Account.objects.all().delete()
        Group.objects.all().delete()

    def testDebitAndCreditInSameEntry(self):
        self.entry.credit = 100
        self.entry.debit  = 100
        self.assertRaises(InvalidTransactionEntry, self.entry.save)

    def testNegativeCredit(self):
        self.entry.credit  = -100
        self.assertRaises(InvalidTransactionEntry, self.entry.save)

    def testNegativeDebit(self):
        self.entry.debit  = -100
        self.assertRaises(InvalidTransactionEntry, self.entry.save)

    def testDebitAndCreditSetToZero(self):
        self.entry.debit  = 0
        self.entry.credit = 0
        self.assertRaises(InvalidTransactionEntry, self.entry.save)
