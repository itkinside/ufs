import unittest

from itkufs.accounting.views import *

class UserViewsTestCase(unittest.TestCase):
    """Test the views as an unprivileged user"""

    def setUp(self):
        pass

    def testLoginUser(self):
        """FIXME: Write docstring"""
        # FIXME: Implement test
        self.fail('Test not implemented')

    def testGroupList(self):
        """FIXME: Write docstring"""
        # FIXME: Implement test
        self.fail('Test not implemented')

    def testAccountSummary(self):
        """FIXME: Write docstring"""
        # FIXME: Implement test
        self.fail('Test not implemented')

    def testTransfer(self):
        """FIXME: Write docstring"""
        # FIXME: Implement test
        self.fail('Test not implemented')

    def testStaticPage(self):
        """FIXME: Write docstring"""
        # FIXME: Implement test
        self.fail('Test not implemented')

class AdminViewsTestCase(unittest.TestCase):
    """Test the views as a group admin"""

    def setUp(self):
        pass

    def testGroupSummary(self):
        """FIXME: Write docstring"""
        # FIXME: Implement test
        self.fail('Test not implemented')

    def testAccountSummary(self):
        """FIXME: Write docstring"""
        # FIXME: Implement test
        self.fail('Test not implemented')

    def testTransfer(self):
        """FIXME: Write docstring"""
        # FIXME: Implement test
        self.fail('Test not implemented')

    def testApprove(self):
        """FIXME: Write docstring"""
        # FIXME: Implement test
        self.fail('Test not implemented')

    def testAlterGroup(self): # FIXME: Rename view to edit_group?
        """FIXME: Write docstring"""
        # FIXME: Implement test
        self.fail('Test not implemented')

    def testAlterAccount(self): # FIXME: Rename view to edit_account?
        """FIXME: Write docstring"""
        # FIXME: Implement test
        self.fail('Test not implemented')

