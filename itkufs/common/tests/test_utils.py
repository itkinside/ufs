import unittest

from itkufs.common.utils import verify_account_number


class VerifyAccountNumberTestCase(unittest.TestCase):
    def testValidAccount(self):
        assert verify_account_number("12345678903")
        assert verify_account_number("1234 56 78903")
        assert verify_account_number("1234.56.78903")
        assert verify_account_number("1234-56-78903")
        assert verify_account_number(" 12345678903 ")
        assert verify_account_number(" 1234 56 78903 ")
        assert verify_account_number(" 1234.56.78903 ")
        assert verify_account_number(" 1234-56-78903 ")

    def testShortAccounts(self):
        assert not verify_account_number("123456789")
        assert not verify_account_number("1234567890")

    def testInvalidCheckDigits(self):
        assert not verify_account_number("12345678900")
        assert not verify_account_number("12345678901")
        assert not verify_account_number("12345678902")
        assert not verify_account_number("12345678904")
        assert not verify_account_number("12345678905")
        assert not verify_account_number("12345678906")
        assert not verify_account_number("12345678907")
        assert not verify_account_number("12345678908")
        assert not verify_account_number("12345678909")

    def testInvalidCheckDigitsWithSpacers(self):
        assert not verify_account_number("1234 56 78901")
        assert not verify_account_number("1234.56.78901")
        assert not verify_account_number(" 12345678901 ")

    def testInvalidStringInAccount(self):
        assert not verify_account_number("1234a5678903")
        assert not verify_account_number("1234%5678903")
