import unittest

from itkufs.common.utils import *

class VerifyAccountNumberTestCase(unittest.TestCase):

    def testValidAccount(self):
        self.assertTrue(verify_account_number('12345678903'))
        self.assertTrue(verify_account_number('1234 56 78903'))
        self.assertTrue(verify_account_number('1234.56.78903'))
        self.assertTrue(verify_account_number('1234-56-78903'))
        self.assertTrue(verify_account_number(' 12345678903 '))
        self.assertTrue(verify_account_number(' 1234 56 78903 '))
        self.assertTrue(verify_account_number(' 1234.56.78903 '))
        self.assertTrue(verify_account_number(' 1234-56-78903 '))

    def testShortAccounts(self):
        self.assertFalse(verify_account_number('123456789'))
        self.assertFalse(verify_account_number('1234567890'))

    def testInvalidCheckDigits(self):
        self.assertFalse(verify_account_number('12345678900'))
        self.assertFalse(verify_account_number('12345678901'))
        self.assertFalse(verify_account_number('12345678902'))
        self.assertFalse(verify_account_number('12345678904'))
        self.assertFalse(verify_account_number('12345678905'))
        self.assertFalse(verify_account_number('12345678906'))
        self.assertFalse(verify_account_number('12345678907'))
        self.assertFalse(verify_account_number('12345678908'))
        self.assertFalse(verify_account_number('12345678909'))

    def testInvalidCheckDigitsWithSpacers(self):
        self.assertFalse(verify_account_number('1234 56 78901'))
        self.assertFalse(verify_account_number('1234.56.78901'))
        self.assertFalse(verify_account_number(' 12345678901 '))

    def testInvalidStringInAccount(self):
        self.assertFalse(verify_account_number('1234a5678903'))
        self.assertFalse(verify_account_number('1234%5678903'))
