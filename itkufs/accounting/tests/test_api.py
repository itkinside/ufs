import pytest
from django.contrib.auth.models import User
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from itkufs.accounting.models import Account, Group


@pytest.fixture
def group():
    return Group.objects.create(name="Group", slug="group", block_limit=0)


@pytest.fixture
def group_admin(client, group):
    user = User.objects.create(username="admin")
    group.admins.add(user)
    client.force_login(user)
    return client


def add_user_accounts(group, count):
    for _ in range(count):
        n = Account.objects.count()
        Account.objects.create(name=f"User {n}", slug=f"user-{n}", group=group)


def count_queries_for_account_list(client, group):
    url = reverse("account-list", kwargs={"group": group.slug})
    with CaptureQueriesContext(connection) as queries:
        response = client.get(url)
    assert response.status_code == 200
    return len(queries)


def test_account_list_queries_do_not_grow_with_accounts(group_admin, group):
    add_user_accounts(group, 1)
    queries_for_one_account = count_queries_for_account_list(group_admin, group)

    add_user_accounts(group, 10)

    assert (
        count_queries_for_account_list(group_admin, group)
        == queries_for_one_account
    )
