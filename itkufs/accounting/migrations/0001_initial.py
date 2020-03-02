from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Account",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("name", models.CharField(max_length=100, verbose_name="name")),
                (
                    "short_name",
                    models.CharField(
                        max_length=100, verbose_name="short name", blank=True
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        help_text="A shortname used in URLs etc.",
                        verbose_name="slug",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        default=b"Li",
                        max_length=2,
                        verbose_name="type",
                        choices=[
                            (b"As", "Asset"),
                            (b"Li", "Liability"),
                            (b"Eq", "Equity"),
                            (b"In", "Income"),
                            (b"Ex", "Expense"),
                        ],
                    ),
                ),
                (
                    "active",
                    models.BooleanField(default=True, verbose_name="active"),
                ),
                (
                    "ignore_block_limit",
                    models.BooleanField(
                        default=False,
                        help_text="Never block account automatically",
                        verbose_name="ignore block limit",
                    ),
                ),
                (
                    "blocked",
                    models.BooleanField(
                        default=False,
                        help_text="Block account manually",
                        verbose_name="blocked",
                    ),
                ),
                (
                    "group_account",
                    models.BooleanField(
                        default=False,
                        help_text="Does this account belong to the group?",
                        verbose_name="group account",
                    ),
                ),
            ],
            options={
                "ordering": ("group", "name"),
                "verbose_name": "account",
                "verbose_name_plural": "accounts",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Group",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("name", models.CharField(max_length=100, verbose_name="name")),
                (
                    "slug",
                    models.SlugField(
                        help_text="A shortname used in URLs.",
                        unique=True,
                        verbose_name="slug",
                    ),
                ),
                (
                    "warn_limit",
                    models.IntegerField(
                        help_text="Warn user of low balance at this limit, leave blank for no limit.",
                        null=True,
                        verbose_name="warn limit",
                        blank=True,
                    ),
                ),
                (
                    "block_limit",
                    models.IntegerField(
                        help_text="Limit for blacklisting user, leave blank for no limit.",
                        null=True,
                        verbose_name="block limit",
                        blank=True,
                    ),
                ),
                (
                    "logo",
                    models.ImageField(
                        help_text="A small image that will be added to lists.",
                        upload_to=b"logos",
                        blank=True,
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        help_text="Contact address for group.",
                        max_length=75,
                        blank=True,
                    ),
                ),
                (
                    "account_number",
                    models.CharField(
                        help_text="Bank account for group.",
                        max_length=11,
                        blank=True,
                    ),
                ),
                (
                    "admins",
                    models.ManyToManyField(
                        to=settings.AUTH_USER_MODEL,
                        null=True,
                        verbose_name="admins",
                        blank=True,
                    ),
                ),
            ],
            options={
                "ordering": ("name",),
                "verbose_name": "group",
                "verbose_name_plural": "groups",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="RoleAccount",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        max_length=4,
                        verbose_name="role",
                        choices=[
                            (b"Bank", "Bank account"),
                            (b"Cash", "Cash account"),
                            (b"Sale", "Sale account"),
                        ],
                    ),
                ),
                (
                    "account",
                    models.ForeignKey(
                        verbose_name="account",
                        to="accounting.Account",
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        verbose_name="group",
                        to="accounting.Group",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "ordering": ("group", "role"),
                "verbose_name": "role account",
                "verbose_name_plural": "role accounts",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Settlement",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("date", models.DateField(verbose_name="date")),
                (
                    "comment",
                    models.CharField(
                        max_length=200, verbose_name="comment", blank=True
                    ),
                ),
                (
                    "closed",
                    models.BooleanField(
                        default=False,
                        help_text="Mark as closed when done adding transactions to the settlement.",
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        verbose_name="group",
                        to="accounting.Group",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "ordering": ("-date",),
                "verbose_name": "settlement",
                "verbose_name_plural": "settlements",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Transaction",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "date",
                    models.DateField(
                        help_text="May be used for date of the transaction if not today.",
                        verbose_name="date",
                    ),
                ),
                (
                    "last_modified",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Last modified"
                    ),
                ),
                (
                    "state",
                    models.CharField(
                        blank=True,
                        max_length=3,
                        verbose_name="state",
                        choices=[
                            (b"Pen", "Pending"),
                            (b"Com", "Committed"),
                            (b"Rej", "Rejected"),
                        ],
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        related_name="real_transaction_set",
                        verbose_name="group",
                        to="accounting.Group",
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "settlement",
                    models.ForeignKey(
                        verbose_name="settlement",
                        blank=True,
                        to="accounting.Settlement",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "ordering": ("-last_modified",),
                "verbose_name": "transaction",
                "verbose_name_plural": "transactions",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TransactionEntry",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "debit",
                    models.DecimalField(
                        default=0,
                        verbose_name="debit amount",
                        max_digits=10,
                        decimal_places=2,
                    ),
                ),
                (
                    "credit",
                    models.DecimalField(
                        default=0,
                        verbose_name="credit amount",
                        max_digits=10,
                        decimal_places=2,
                    ),
                ),
                (
                    "account",
                    models.ForeignKey(
                        verbose_name="account",
                        to="accounting.Account",
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "transaction",
                    models.ForeignKey(
                        related_name="entry_set",
                        verbose_name="transaction",
                        to="accounting.Transaction",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "ordering": ("credit", "debit"),
                "verbose_name": "transaction entry",
                "verbose_name_plural": "transaction entries",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TransactionLog",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        max_length=3,
                        verbose_name="type",
                        choices=[
                            (b"Pen", "Pending"),
                            (b"Com", "Committed"),
                            (b"Rej", "Rejected"),
                        ],
                    ),
                ),
                (
                    "timestamp",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="timestamp"
                    ),
                ),
                (
                    "message",
                    models.CharField(
                        max_length=200, verbose_name="message", blank=True
                    ),
                ),
                (
                    "transaction",
                    models.ForeignKey(
                        related_name="log_set",
                        verbose_name="transaction",
                        to="accounting.Transaction",
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        verbose_name="user",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "ordering": ("timestamp",),
                "verbose_name": "transaction log entry",
                "verbose_name_plural": "transaction log entries",
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name="transactionentry",
            unique_together={("transaction", "account")},
        ),
        migrations.AddField(
            model_name="account",
            name="group",
            field=models.ForeignKey(
                verbose_name="group",
                to="accounting.Group",
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="account",
            name="owner",
            field=models.ForeignKey(
                verbose_name="owner",
                blank=True,
                to=settings.AUTH_USER_MODEL,
                null=True,
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name="account",
            unique_together={("slug", "group"), ("owner", "group")},
        ),
    ]
