import factory
from factory.django import DjangoModelFactory
import datetime

from itkufs.accounting.models import (
    Group,
    Account,
    Transaction,
    TransactionEntry,
)


class GroupFactory(DjangoModelFactory):
    class Meta:
        model = Group

    name = factory.Sequence(lambda n: f"Group {n}")
    slug = factory.Sequence(lambda n: f"group-{n}")


class UserAccountFactory(DjangoModelFactory):
    class Meta:
        model = Account

    @factory.lazy_attribute
    def short_name(self):
        return self.name.split()[0]

    name = factory.Faker("name")
    slug = factory.Sequence(lambda n: f"user-{n}")
    group = factory.SubFactory(GroupFactory)
    type = Account.LIABILITY_ACCOUNT
    active = factory.Faker("pybool")
    group_account = False


class GroupAccountFactory(DjangoModelFactory):
    class Meta:
        model = Account

    short_name = factory.Sequence(lambda n: f"Account {n}")

    @factory.lazy_attribute
    def name(self):
        active = "active" if self.active else "inactive"
        type = self.type
        return f"{self.short_name} ({type} / {active})"

    slug = factory.Sequence(lambda n: f"group-account-{n}")
    group = factory.SubFactory(GroupFactory)
    group_account = True


class TransactionFactory(DjangoModelFactory):
    class Meta:
        model = Transaction

    state = Transaction.PENDING_STATE
    date = factory.Faker(
        "date_between_dates",
        date_start=datetime.date(2008, 1, 1),
        date_end=datetime.date(2023, 1, 1),
    )


class TransactionEntryFactory(DjangoModelFactory):
    class Meta:
        model = TransactionEntry
