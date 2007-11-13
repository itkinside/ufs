import unittest
from datetime import datetime

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
        """Check that payed_transaction_set only contains payed and related transactions"""
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

        self.transaction = Transaction(entries=[
            {'account': self.accounts[0], 'debit': 100},
            {'account': self.accounts[1], 'credit': 100},
        ])

        self.transaction.save()

    def tearDown(self):
        Transaction.objects.all().delete()
        Account.objects.all().delete()
        Group.objects.all().delete()

    def testEmptyTransaction(self):
        """Check that transaction fails when no accounts are given"""

        t = Transaction(entries=({'debit': 100}, {'credit': 100}))
        self.assertRaises(InvalidTransaction, t.save)

    def testNullAmountTransaction(self):
        """Check that transaction fail when debit and credit are not given"""

        t = Transaction(entries=[
            {'account': self.accounts[0]},
            {'account': self.accounts[1]},
        ])
        self.assertRaises(InvalidTransaction, t.save)

    def testDebitAndCreditAmmountEquall(self):
        """Check that transaction only accept sum(debit)==sum(credit)"""

        transaction = Transaction(entries=[
            {'account': self.accounts[0], 'debit': 100},
            {'account': self.accounts[1], 'credit': 200},
        ])
        self.assertRaises(InvalidTransaction, transaction.save)

    def testAccountOnlyOnceInTransaction(self):
        """Check that debit accounts are only present once per transaction"""

        transaction = Transaction(entries=[
            {'account': self.accounts[1], 'debit': 200},
            {'account': self.accounts[0], 'credit': 100},
            {'account': self.accounts[1], 'credit': 100},
        ])
        self.assertRaises(InvalidTransaction, transaction.save)

    def testRegisteredLogEntry(self):
        """Check that a registered log entry is created"""

        transaction = self.transaction

        self.assertEqual(transaction.is_registered(), True)
        self.assertEqual(transaction.log_set.count(), 1)
        self.assertEqual(transaction.log_set.filter(type='Reg').count(), 1)
        #FIXME test time

    def testPayedLogEntry(self):
        """Check creation of payed log entry"""

        transaction = self.transaction
        transaction.set_payed()

        self.assertEqual(transaction.is_registered(), True)
        self.assertEqual(transaction.is_payed(), True)
        self.assertEqual(transaction.log_set.count(), 2)
        self.assertEqual(transaction.log_set.filter(type='Pay').count(), 1)
        #FIXME test time

    def testRejectLogEntry(self):
        """Check that registered transaction can be rejected"""

        transaction = self.transaction
        transaction.reject('Reason for rejecting')

        self.assertEqual(transaction.is_registered(), True)
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
        """Check that we can set a payed transaction as recieved"""

        transaction = self.transaction
        transaction.set_payed()
        transaction.set_recieved()

        self.assertEqual(transaction.is_registered(), True)
        self.assertEqual(transaction.is_payed(), True)
        self.assertEqual(transaction.is_received(), True)
        self.assertEqual(transaction.log_set.count(), 3)
        self.assertEqual(transaction.log_set.filter(type='Rec').count(), 1)


    def testRejectRecievedTransaction(self):
        """Test that rejecting recieved transaction fails"""
        transaction = self.transaction
        transaction.set_payed()
        transaction.set_recieved()

        self.assertRaises(InvalidTransaction, transaction.reject, 'Reason for rejecting')

    def testRecieveNotPayedTransaction(self):
        """Check that recieving a transaction that is not payed fails"""
        transaction = self.transaction

        self.assertRaises(InvalidTransaction, transaction.set_recieved)

    def testLogEntryUniqePerType(self):
        """Check that we can only have one log entry of each type"""
        #FIXME this should be a logentry test not a transaction test
        pass


    def testLogEntryModify(self):
        """Test that modifying log entry raises error"""
        #FIXME this should be a logentry test not a transaction test
        pass

    def testSimpleTransaction(self):
        """Baseline test to check transactions"""
        debit_account = Account.objects.get(id=1)
        credit_account = Account.objects.get(id=2)

        t = Transaction(entries=[{'debit': 100, 'account': debit_account},
                        {'credit': 100, 'account': credit_account}])

        entries = t.entry_set.all()
        debit = 0
        credit = 0
        for e in entries:
            if e.credit > 0:
                credit += e.credit
                self.assertEqual(credit_account, e.account)
            elif e.debit > 0:
                debit  += e.debit
                self.assertEqual(debit_account, e.account)
            else:
                self.fail('TransactionEntry with without valid credit or debit')

        self.assertEqual(credit, debit)
