from datetime import datetime
from django.db import IntegrityError
import unittest

from itkufs.common.models import *

class GroupTestCase(unittest.TestCase):
    # FIXME: Test all group properties
    # FIXME: Check more than count in the set tests?

    def setUp(self):
        self.user = User(username='user')
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

        Transaction.objects.all().delete()

        self.transactions = {
            'Reg': Transaction(),
            'Pay': Transaction(),
            'Rec': Transaction(),
            'Rej': Transaction(),
        }
        for transaction in self.transactions.values():
            transaction.save()
            transaction.entry_set.add(
                TransactionEntry(account=self.accounts[0], credit=100))
            transaction.entry_set.add(
                TransactionEntry(account=self.accounts[1], debit=100))
            transaction.set_registered(user=self.user)

        self.transactions['Pay'].set_payed(user=self.user)
        self.transactions['Rec'].set_payed(user=self.user)
        self.transactions['Rec'].set_received(user=self.user)
        self.transactions['Rej'].set_rejected(user=self.user)

    def tearDown(self):
        self.group.delete()
        self.user.delete()
        for transaction in self.transactions.values():
            transaction.delete()

    def testTransactionSet(self):
        """Checks that transaction_set returns all transactions that is not
        rejected"""

        set = self.group.transaction_set()
        self.assertEqual(set.count(), 3)

    def testTransactionSetWithRejected(self):
        """Checks that transaction_set_with_rejected returns all
        transactions"""

        set = self.group.transaction_set_with_rejected()
        self.assertEqual(set.count(), 4)

    def testRegisteredTransactionSet(self):
        """Checks that registered_transaction_set returns all registered
        transactions that is not rejected"""

        set = self.group.registered_transaction_set()
        self.assertEqual(set.count(), 3)

    def testPayedTransactionSet(self):
        """Checks that payed_transaction_set returns all payed
        transactions that is not rejected"""

        set = self.group.payed_transaction_set()
        self.assertEqual(set.count(), 2)

    def testNotPayedTransactionSet(self):
        """Checks that not_payed_transaction_set returns all unpayed
        transactions that is not rejected"""

        set = self.group.not_payed_transaction_set()
        self.assertEqual(set.count(), 1)

    def testReceivedTransactionSet(self):
        """Checks that received_transaction_set returns all received
        transactions that is not rejected"""

        set = self.group.received_transaction_set()
        self.assertEqual(set.count(), 1)

    def testNotReceivedTransactionSet(self):
        """Checks that not_received_transaction_set returns all transactions
        that has not been received, that is not rejected"""

        set = self.group.not_received_transaction_set()
        self.assertEqual(set.count(), 2)

    def testRejectedTransactionSet(self):
        """Checks that rejected_transaction_set returns all rejected
        transactions"""

        set = self.group.rejected_transaction_set()
        self.assertEqual(set.count(), 1)

    def testNotReceivedTransactionSet(self):
        """Checks that rejected_transaction_set returns all transactions that
        is not rejected"""

        set = self.group.not_rejected_transaction_set()
        self.assertEqual(set.count(), 3)

class AccountTestCase(unittest.TestCase):
    # FIXME: Test all account properties

    def setUp(self):
        pass

