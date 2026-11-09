import re
import unittest

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from itkufs.accounting.models import Account, Group


class UserViewsTestCase(unittest.TestCase):
    """Tests the views as an unprivileged user"""

    # FIXME: Add missing view tests

    def setUp(self):
        pass

    # Account views

    @unittest.skip("test missing")
    def testAccountSummary(self):
        """FIXME: Write docstring"""
        # FIXME: Implement test
        self.fail("Test not implemented")

    # Group views

    @unittest.skip("test missing")
    def testGroupSummary(self):
        """FIXME: Write docstring"""
        # FIXME: Implement test
        self.fail("Test not implemented")

    # Transaction views

    @unittest.skip("test missing")
    def testTransfer(self):
        """FIXME: Write docstring"""
        # FIXME: Implement test
        self.fail("Test not implemented")


class AdminViewsTestCase(unittest.TestCase):
    """Tests the views as a group admin"""

    # FIXME: Add missing view tests

    def setUp(self):
        pass

    # Account views

    @unittest.skip("test missing")
    def testAccountSummary(self):
        """FIXME: Write docstring"""
        # FIXME: Implement test
        self.fail("Test not implemented")

    @unittest.skip("test missing")
    def testEditAccount(self):
        """FIXME: Write docstring"""
        # FIXME: Implement test
        self.fail("Test not implemented")

    # Group views

    @unittest.skip("test missing")
    def testGroupSummary(self):
        """FIXME: Write docstring"""
        # FIXME: Implement test
        self.fail("Test not implemented")

    @unittest.skip("test missing")
    def testEditGroup(self):
        """FIXME: Write docstring"""
        # FIXME: Implement test
        self.fail("Test not implemented")

    # Transaction views

    @unittest.skip("test missing")
    def testApprove(self):
        """FIXME: Write docstring"""
        # FIXME: Implement test
        self.fail("Test not implemented")


@pytest.fixture
def account():
    group = Group.objects.create(name="Group", slug="group")
    return Account.objects.create(name="Account", slug="account", group=group)


@pytest.fixture
def group_admin(client, account):
    user = User.objects.create(username="admin")
    account.group.admins.add(user)
    client.force_login(user)
    return client


def open_account_page(client, view, account):
    kwargs = {"group": account.group.slug, "account": account.slug}
    response = client.get(reverse(view, kwargs=kwargs))
    assert response.status_code == 200
    return response


def page_header(response):
    header = re.search(r"<h2>(.*?)</h2>", response.content.decode(), re.S)
    assert header, "page has no <h2> header"
    return header[1]


@pytest.mark.parametrize(
    "transfer_type, title",
    [
        ("deposit", "Deposit to account"),
        ("withdraw", "Withdrawal from account"),
        ("transfer", "Transfer from account"),
    ],
)
def test_group_admin_sees_transfer_page_title(
    group_admin, account, transfer_type, title
):
    response = open_account_page(
        group_admin, f"account-{transfer_type}", account
    )
    assert title in page_header(response)
