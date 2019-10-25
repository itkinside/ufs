# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):
    def forwards(self, orm):

        # Adding model 'List'
        db.create_table(
            "reports_list",
            (
                (
                    "id",
                    self.gf("django.db.models.fields.AutoField")(
                        primary_key=True
                    ),
                ),
                (
                    "name",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=200
                    ),
                ),
                (
                    "slug",
                    self.gf("django.db.models.fields.SlugField")(
                        max_length=50, db_index=True
                    ),
                ),
                (
                    "account_width",
                    self.gf(
                        "django.db.models.fields.PositiveSmallIntegerField"
                    )(),
                ),
                (
                    "short_name_width",
                    self.gf(
                        "django.db.models.fields.PositiveSmallIntegerField"
                    )(),
                ),
                (
                    "balance_width",
                    self.gf(
                        "django.db.models.fields.PositiveSmallIntegerField"
                    )(),
                ),
                (
                    "group",
                    self.gf("django.db.models.fields.related.ForeignKey")(
                        related_name="list_set", to=orm["accounting.Group"]
                    ),
                ),
                (
                    "public",
                    self.gf("django.db.models.fields.BooleanField")(
                        default=False
                    ),
                ),
                (
                    "add_active_accounts",
                    self.gf("django.db.models.fields.BooleanField")(
                        default=True
                    ),
                ),
                (
                    "orientation",
                    self.gf("django.db.models.fields.CharField")(max_length=1),
                ),
                (
                    "comment",
                    self.gf("django.db.models.fields.TextField")(blank=True),
                ),
                (
                    "double",
                    self.gf("django.db.models.fields.BooleanField")(
                        default=False
                    ),
                ),
                (
                    "ignore_blocked",
                    self.gf("django.db.models.fields.BooleanField")(
                        default=False
                    ),
                ),
            ),
        )
        db.send_create_signal("reports", ["List"])

        # Adding unique constraint on 'List', fields ['slug', 'group']
        db.create_unique("reports_list", ["slug", "group_id"])

        # Adding M2M table for field extra_accounts on 'List'
        db.create_table(
            "reports_list_extra_accounts",
            (
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID", primary_key=True, auto_created=True
                    ),
                ),
                ("list", models.ForeignKey(orm["reports.list"], null=False)),
                (
                    "account",
                    models.ForeignKey(orm["accounting.account"], null=False),
                ),
            ),
        )
        db.create_unique(
            "reports_list_extra_accounts", ["list_id", "account_id"]
        )

        # Adding model 'ListColumn'
        db.create_table(
            "reports_listcolumn",
            (
                (
                    "id",
                    self.gf("django.db.models.fields.AutoField")(
                        primary_key=True
                    ),
                ),
                (
                    "name",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=200
                    ),
                ),
                (
                    "width",
                    self.gf(
                        "django.db.models.fields.PositiveSmallIntegerField"
                    )(),
                ),
                (
                    "list",
                    self.gf("django.db.models.fields.related.ForeignKey")(
                        related_name="column_set", to=orm["reports.List"]
                    ),
                ),
            ),
        )
        db.send_create_signal("reports", ["ListColumn"])

    def backwards(self, orm):

        # Removing unique constraint on 'List', fields ['slug', 'group']
        db.delete_unique("reports_list", ["slug", "group_id"])

        # Deleting model 'List'
        db.delete_table("reports_list")

        # Removing M2M table for field extra_accounts on 'List'
        db.delete_table("reports_list_extra_accounts")

        # Deleting model 'ListColumn'
        db.delete_table("reports_listcolumn")

    models = {
        "accounting.account": {
            "Meta": {
                "ordering": "('group', 'name')",
                "unique_together": "(('slug', 'group'), ('owner', 'group'))",
                "object_name": "Account",
            },
            "active": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True"},
            ),
            "blocked": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False"},
            ),
            "group": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['accounting.Group']"},
            ),
            "group_account": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False"},
            ),
            "id": (
                "django.db.models.fields.AutoField",
                [],
                {"primary_key": "True"},
            ),
            "ignore_block_limit": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False"},
            ),
            "name": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "100"},
            ),
            "owner": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['auth.User']", "null": "True", "blank": "True"},
            ),
            "short_name": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "100", "blank": "True"},
            ),
            "slug": (
                "django.db.models.fields.SlugField",
                [],
                {"max_length": "50", "db_index": "True"},
            ),
            "type": (
                "django.db.models.fields.CharField",
                [],
                {"default": "'Li'", "max_length": "2"},
            ),
        },
        "accounting.group": {
            "Meta": {"ordering": "('name',)", "object_name": "Group"},
            "admins": (
                "django.db.models.fields.related.ManyToManyField",
                [],
                {
                    "symmetrical": "False",
                    "to": "orm['auth.User']",
                    "null": "True",
                    "blank": "True",
                },
            ),
            "block_limit": (
                "django.db.models.fields.IntegerField",
                [],
                {"null": "True", "blank": "True"},
            ),
            "email": (
                "django.db.models.fields.EmailField",
                [],
                {"max_length": "75", "blank": "True"},
            ),
            "id": (
                "django.db.models.fields.AutoField",
                [],
                {"primary_key": "True"},
            ),
            "logo": (
                "django.db.models.fields.files.ImageField",
                [],
                {"max_length": "100", "blank": "True"},
            ),
            "name": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "100"},
            ),
            "slug": (
                "django.db.models.fields.SlugField",
                [],
                {"unique": "True", "max_length": "50", "db_index": "True"},
            ),
            "warn_limit": (
                "django.db.models.fields.IntegerField",
                [],
                {"null": "True", "blank": "True"},
            ),
        },
        "auth.group": {
            "Meta": {"object_name": "Group"},
            "id": (
                "django.db.models.fields.AutoField",
                [],
                {"primary_key": "True"},
            ),
            "name": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "80"},
            ),
            "permissions": (
                "django.db.models.fields.related.ManyToManyField",
                [],
                {
                    "to": "orm['auth.Permission']",
                    "symmetrical": "False",
                    "blank": "True",
                },
            ),
        },
        "auth.permission": {
            "Meta": {
                "ordering": "('content_type__app_label', 'content_type__model', 'codename')",
                "unique_together": "(('content_type', 'codename'),)",
                "object_name": "Permission",
            },
            "codename": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "100"},
            ),
            "content_type": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['contenttypes.ContentType']"},
            ),
            "id": (
                "django.db.models.fields.AutoField",
                [],
                {"primary_key": "True"},
            ),
            "name": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "50"},
            ),
        },
        "auth.user": {
            "Meta": {"object_name": "User"},
            "date_joined": (
                "django.db.models.fields.DateTimeField",
                [],
                {"default": "datetime.datetime.now"},
            ),
            "email": (
                "django.db.models.fields.EmailField",
                [],
                {"max_length": "75", "blank": "True"},
            ),
            "first_name": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "30", "blank": "True"},
            ),
            "groups": (
                "django.db.models.fields.related.ManyToManyField",
                [],
                {
                    "to": "orm['auth.Group']",
                    "symmetrical": "False",
                    "blank": "True",
                },
            ),
            "id": (
                "django.db.models.fields.AutoField",
                [],
                {"primary_key": "True"},
            ),
            "is_active": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True"},
            ),
            "is_staff": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False"},
            ),
            "is_superuser": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False"},
            ),
            "last_login": (
                "django.db.models.fields.DateTimeField",
                [],
                {"default": "datetime.datetime.now"},
            ),
            "last_name": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "30", "blank": "True"},
            ),
            "password": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "128"},
            ),
            "user_permissions": (
                "django.db.models.fields.related.ManyToManyField",
                [],
                {
                    "to": "orm['auth.Permission']",
                    "symmetrical": "False",
                    "blank": "True",
                },
            ),
            "username": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "30"},
            ),
        },
        "contenttypes.contenttype": {
            "Meta": {
                "ordering": "('name',)",
                "unique_together": "(('app_label', 'model'),)",
                "object_name": "ContentType",
                "db_table": "'django_content_type'",
            },
            "app_label": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "100"},
            ),
            "id": (
                "django.db.models.fields.AutoField",
                [],
                {"primary_key": "True"},
            ),
            "model": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "100"},
            ),
            "name": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "100"},
            ),
        },
        "reports.list": {
            "Meta": {
                "ordering": "('name',)",
                "unique_together": "(('slug', 'group'),)",
                "object_name": "List",
            },
            "account_width": (
                "django.db.models.fields.PositiveSmallIntegerField",
                [],
                {},
            ),
            "add_active_accounts": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True"},
            ),
            "balance_width": (
                "django.db.models.fields.PositiveSmallIntegerField",
                [],
                {},
            ),
            "comment": (
                "django.db.models.fields.TextField",
                [],
                {"blank": "True"},
            ),
            "double": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False"},
            ),
            "extra_accounts": (
                "django.db.models.fields.related.ManyToManyField",
                [],
                {
                    "to": "orm['accounting.Account']",
                    "symmetrical": "False",
                    "blank": "'true'",
                },
            ),
            "group": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"related_name": "'list_set'", "to": "orm['accounting.Group']"},
            ),
            "id": (
                "django.db.models.fields.AutoField",
                [],
                {"primary_key": "True"},
            ),
            "ignore_blocked": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False"},
            ),
            "name": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "200"},
            ),
            "orientation": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "1"},
            ),
            "public": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False"},
            ),
            "short_name_width": (
                "django.db.models.fields.PositiveSmallIntegerField",
                [],
                {},
            ),
            "slug": (
                "django.db.models.fields.SlugField",
                [],
                {"max_length": "50", "db_index": "True"},
            ),
        },
        "reports.listcolumn": {
            "Meta": {"ordering": "['id']", "object_name": "ListColumn"},
            "id": (
                "django.db.models.fields.AutoField",
                [],
                {"primary_key": "True"},
            ),
            "list": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"related_name": "'column_set'", "to": "orm['reports.List']"},
            ),
            "name": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "200"},
            ),
            "width": (
                "django.db.models.fields.PositiveSmallIntegerField",
                [],
                {},
            ),
        },
    }

    complete_apps = ["reports"]
