import unittest
from datetime import datetime

from itkufs.accounting.models import *

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
        pass

    def testAccountWithOwner(self):
        pass

    def testDisabledAccount(self):
        pass

    def testAccountBalance(self):
        pass

class TransactionlTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def testSimpleTransaction(self):
        pass

    def testTransActionWithManyDebitEntries(self):
        pass

    def testTransActionWithManyCreditEntries(self):
        pass

    def testTransactionLog(self):
        pass

    # ...
