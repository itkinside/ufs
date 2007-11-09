import unittest
from itkufs.accounting.models import *

class GroupTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def testDefaultGroup(self):
        pass

    # ...

class AccountTestCase(unittest.TestCase):
    def setUp(self):
        self.group   = Group(name='Group', slug='group')
        self.default = Account(name='Default', slug='default')

    def testDefaultAccount(self):
        default = self.default

        self.assertEquals(default.name,'Default')
        self.assertEquals(default.ignore_block_limit, False)
        self.assertEquals(default.type, 'Li')
        self.assertEquals(default.owner, None)
        self.assertEquals(default.active, True)

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
