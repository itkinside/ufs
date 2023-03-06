import random
import logging
from typing import List
from tqdm import tqdm
from django.db import transaction
from django.core.management.base import BaseCommand
from django.core.management.color import color_style
from itkufs.accounting.models import (
    Group,
    Account,
    Transaction,
    TransactionEntry,
)

from itkufs.common.management.factories import (
    GroupFactory,
    UserAccountFactory,
    GroupAccountFactory,
    TransactionFactory,
    TransactionEntryFactory,
)


class Command(BaseCommand):
    help = "Generate fake data for testing the application"

    def add_arguments(self, parser):
        parser.add_argument(
            "--groups",
            type=int,
            default=2,
            help="How many groups will be created",
        )
        parser.add_argument(
            "--users",
            type=int,
            default=250,
            help="How many users will be created per group",
        )
        parser.add_argument(
            "--group-accounts",
            type=int,
            default=50,
            help="How many group accounts will be created per group",
        )
        parser.add_argument(
            "--transactions",
            type=int,
            default=100,
            help="How many transactions will be created per group",
        )
        parser.add_argument(
            "--entries",
            type=int,
            default=25,
            help="How many entries will be created per transaction",
        )

    def __init__(self):
        self.log = self._setup_logging()
        self.style = color_style()

    def _setup_logging(self):
        CONSOLE_LOG_FORMAT = "%(levelname)-8s %(message)s"
        logging.basicConfig(format=CONSOLE_LOG_FORMAT, level=logging.INFO)
        return logging.getLogger("createfakedata")

    @transaction.atomic
    def create_user_accounts(self, group: Group, count: int):
        # Create a distribution of active and inactive accounts
        active = random.choices(
            population=[True, False], weights=[0.5, 0.5], k=count
        )

        user_accounts: List["Account"] = []
        for _ in tqdm(range(count)):
            user = UserAccountFactory(group=group, active=active.pop())
            user_accounts.append(user)
        return user_accounts

    @transaction.atomic
    def create_group_accounts(self, group: Group, count: int):
        # Create a distribution of active and inactive accounts
        states = random.choices(
            population=[True, False], weights=[0.8, 0.2], k=count
        )
        types = random.choices(
            population=[
                Account.LIABILITY_ACCOUNT,
                Account.ASSET_ACCOUNT,
                Account.EQUITY_ACCOUNT,
                Account.INCOME_ACCOUNT,
                Account.EXPENSE_ACCOUNT,
            ],
            k=count,
        )

        # Randomly create accounts of different types
        group_accounts: List["Account"] = []
        for _ in tqdm(range(count)):
            account = GroupAccountFactory(
                group=group, type=types.pop(), active=states.pop()
            )
            group_accounts.append(account)

        return group_accounts

    @transaction.atomic
    def create_transactions(self, group: Group, count: int):
        transactions: List["Transaction"] = []
        for _ in tqdm(range(count)):
            transaction = TransactionFactory(group=group)
            transactions.append(transaction)

        return transactions

    def fill_transactions(
        self,
        transactions: List["Transaction"],
        group_accounts: List["Account"],
        user_accounts: List["Account"],
        entry_count: int,
    ):
        # Split the transactions in two groups
        MID = int(len(transactions) / 2)
        pbar = tqdm(total=len(transactions), desc="Creating transaction data")

        # Create transactions which debit one group account
        for t in transactions[:MID]:
            group_account = random.choice(group_accounts)
            self.create_transaction_entries(
                t,
                entry_count,
                group_account,
                user_accounts,
                debit_group=True,
            )
            self.finalize_transaction(t)
            pbar.update(1)

        # Create transactions which credit one group account
        for t in transactions[MID:]:
            group_account = random.choice(group_accounts)
            self.create_transaction_entries(
                t,
                entry_count,
                group_account,
                user_accounts,
                debit_group=False,
            )
            self.finalize_transaction(t)
            pbar.update(1)
        pbar.close()

    def finalize_transaction(self, transaction: Transaction):
        transaction.state = random.choices(
            population=[
                Transaction.PENDING_STATE,
                Transaction.COMMITTED_STATE,
                Transaction.REJECTED_STATE,
            ],
            weights=[0.05, 0.85, 0.1],
            k=1,
        )[0]
        transaction.save()

    @transaction.atomic
    def create_transaction_entries(
        self,
        transaction: Transaction,
        count: int,
        group_account: Account,
        user_accounts: List["Account"],
        debit_group=True,
    ):
        """
        Create transaction entries for a transaction.
        Debits or credits a group account and randomly credits or debits user accounts.
        """
        total = 0
        users = random.sample(population=user_accounts, k=count - 1)

        # Create entries for user accounts
        for user_account in users:
            amount = random.randint(1, 5000)
            debit = amount if not debit_group else 0
            credit = amount if debit_group else 0

            TransactionEntryFactory(
                transaction=transaction,
                account=user_account,
                debit=debit,
                credit=credit,
            )
            total += amount

        # Create the matching entry for the group account
        debit = total if debit_group else 0
        credit = total if not debit_group else 0
        TransactionEntryFactory(
            transaction=transaction,
            account=group_account,
            debit=debit,
            credit=credit,
        )

    def handle(self, *args, **options):
        # Ratios for the number of objects to create
        GROUP_COUNT = options["groups"]
        USERS_PER_GROUP = options["users"]
        GROUP_ACCOUNTS_PER_GROUP = (
            options["group_accounts"] - 2
        )  # 2 accounts are created by default
        TRANSACTIONS_PER_GROUP = options["transactions"]
        ENTRIES_PER_TRANSACTION = options["entries"]

        self.log.info("Before adding fake data, existing data will be deleted.")
        if input("Delete existing data? (y/n) ").lower() == "y":
            self.log.info("Deleting old data...")
            models = [Group, Account, Transaction, TransactionEntry]
            for m in models:
                m.objects.all().delete()
        else:
            self.log.info("Aborting...")
            return

        self.log.info("Generating new data...")

        # Create groups
        for _ in tqdm(range(GROUP_COUNT)):
            GroupFactory()

        for group in Group.objects.all():
            self.log.info(f"Creating data for group '{group.name}'...")

            self.log.info("Creating user accounts...")
            self.create_user_accounts(group, USERS_PER_GROUP)
            user_accounts = list(
                Account.objects.filter(group=group, group_account=False)
            )

            self.log.info("Creating group accounts...")
            self.create_group_accounts(group, GROUP_ACCOUNTS_PER_GROUP)
            group_accounts = list(
                Account.objects.filter(group=group, group_account=True)
            )

            self.log.info("Creating transactions...")
            self.create_transactions(group, TRANSACTIONS_PER_GROUP)
            transactions = Transaction.objects.filter(group=group)

            # Pick a subset of users and group accounts for transactions
            # This is to ensure some accounts are left empty/unused
            user_count = int(USERS_PER_GROUP * 0.8)
            included_users = random.sample(
                population=user_accounts, k=user_count
            )

            group_account_count = int(GROUP_ACCOUNTS_PER_GROUP * 0.8)
            included_group_accounts = random.sample(
                population=group_accounts, k=group_account_count
            )

            self.log.info("Filling transactions with entries...")
            self.fill_transactions(
                transactions,
                included_group_accounts,
                included_users,
                ENTRIES_PER_TRANSACTION,
            )

        group_count = Group.objects.count()
        group_account_count = Account.objects.filter(group_account=True).count()
        user_count = Account.objects.filter(group_account=False).count()
        transaction_count = Transaction.objects.count()
        entry_count = TransactionEntry.objects.count()
        self.log.info("Finished generating fake data! There are now:")
        self.log.info(f"    {group_count} groups")
        self.log.info(f"    {group_account_count} group accounts")
        self.log.info(f"    {user_count} user accounts")
        self.log.info(f"    {transaction_count} transactions")
        self.log.info(f"    {entry_count} transaction entries")
