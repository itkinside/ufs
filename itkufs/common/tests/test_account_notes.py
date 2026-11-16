from typing import Any

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from itkufs.accounting.models import Account, Group

NOTE = (
    "Rarely checks mail, contact by SMS if necessary. "
    "- Kari Nordmann, 2026-11-16"
)


@pytest.fixture(autouse=True)
def no_balance_history(monkeypatch: pytest.MonkeyPatch) -> None:
    # The balance history query is PostgreSQL-only; tests run on SQLite.
    monkeypatch.setattr(Account, "get_balance_history_set", lambda self: [])


@pytest.fixture
def group() -> Group:
    return Group.objects.create(name="Group", slug="group")


@pytest.fixture
def admin(group: Group) -> User:
    user = User.objects.create(username="admin")
    group.admins.add(user)
    return user


@pytest.fixture
def member() -> User:
    return User.objects.create(username="member")


@pytest.fixture
def account(group: Group, member: User) -> Account:
    return Account.objects.create(
        name="Member", slug="member", group=group, owner=member
    )


@pytest.fixture
def account_with_note(account: Account) -> Account:
    account.admin_note = NOTE
    account.save()
    return account


def log_in(client: Client, user: User) -> None:
    client.force_login(user)


def account_url(view: str, account: Account) -> str:
    kwargs = {"group": account.group.slug, "account": account.slug}
    return reverse(view, kwargs=kwargs)


def open_account_page(client: Client, account: Account) -> str:
    response = client.get(account_url("account-summary", account))
    assert response.status_code == 200
    return response.content.decode()


def save_note(client: Client, account: Account, note: str) -> None:
    data = {
        "name": account.name,
        "type": account.type,
        "owner": account.owner.username,
        "active": "on",
        "admin_note": note,
    }
    response = client.post(account_url("edit-account", account), data)
    assert response.status_code == 302


def fetch_account_list(client: Client, group: Group) -> list[dict[str, Any]]:
    url = reverse("account-list", kwargs={"group": group.slug})
    response = client.get(url)
    assert response.status_code == 200
    return list(response.json().values())


def find_account(
    accounts: list[dict[str, Any]], account: Account
) -> dict[str, Any]:
    return next(a for a in accounts if a["id"] == account.id)


@pytest.mark.parametrize(
    "viewer, sees_note", [("admin", True), ("member", False)]
)
def test_only_group_admins_see_the_note_on_the_account_page(
    client: Client,
    request: pytest.FixtureRequest,
    account_with_note: Account,
    viewer: str,
    sees_note: bool,
) -> None:
    log_in(client, request.getfixturevalue(viewer))

    page = open_account_page(client, account_with_note)

    assert (NOTE in page) == sees_note


def test_group_admin_can_write_a_note(
    client: Client, admin: User, account: Account
) -> None:
    log_in(client, admin)

    save_note(client, account, NOTE)

    assert NOTE in open_account_page(client, account)


@pytest.mark.parametrize("viewer", ["admin", "member"])
def test_account_list_api_leaves_out_the_note(
    client: Client,
    request: pytest.FixtureRequest,
    account_with_note: Account,
    viewer: str,
) -> None:
    log_in(client, request.getfixturevalue(viewer))

    accounts = fetch_account_list(client, account_with_note.group)

    assert "admin_note" not in find_account(accounts, account_with_note)
