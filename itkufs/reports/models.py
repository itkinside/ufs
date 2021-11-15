import random

from django.db import models
from django.utils.translation import ugettext_lazy as _

from itkufs.accounting.models import Group, Account
from itkufs.common.utils import callsign_sorted


class ListManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .extra(
                select={
                    "listcolumn_count": """
                    SELECT COUNT(*)
                    FROM reports_listcolumn
                    WHERE reports_listcolumn.list_id = reports_list.id
                    """,
                    "listcolumn_width": """
                    SELECT SUM(reports_listcolumn.width)
                    FROM reports_listcolumn
                    WHERE reports_listcolumn.list_id = reports_list.id
                    """,
                }
            )
        )


class List(models.Model):
    objects = ListManager()

    LANDSCAPE = "L"
    PORTRAIT = "P"
    ORIENTATION_CHOICES = (("L", _("Landscape")), ("P", _("Portrait")))

    ALPHABETICAL_SORT_ORDER = "Al"
    CALLSIGN_SORT_ORDER = "Ca"
    CONSUMPTION_SORT_ORDER = "Co"
    RANDOM_SORT_ORDER = "Ra"
    LAST_30_DAYS_USAGE_SORT_ORDER = "Lt"
    SORT_ORDER_CHOICES = (
        (ALPHABETICAL_SORT_ORDER, _("Alphabetical")),
        (CALLSIGN_SORT_ORDER, _("Callsign")),
        (CONSUMPTION_SORT_ORDER, _("Total consumption")),
        (RANDOM_SORT_ORDER, _("Random")),
        (LAST_30_DAYS_USAGE_SORT_ORDER, _("Last 30 days usage")),
    )

    name = models.CharField(_("name"), max_length=200)
    slug = models.SlugField(_("slug"))
    account_width = models.PositiveSmallIntegerField(
        _("account name width"),
        help_text=_("Relative width of cell, 0 to hide"),
    )
    short_name_width = models.PositiveSmallIntegerField(
        _("short name width"), help_text=_("Relative width of cell, 0 to hide")
    )
    balance_width = models.PositiveSmallIntegerField(
        _("balance width"), help_text=_("Relative width of cell, 0 to hide")
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        verbose_name=_("group"),
        related_name="list_set",
    )

    public = models.BooleanField(
        _("Public"),
        default=False,
        help_text=_("Should this list be publicly available"),
    )

    add_active_accounts = models.BooleanField(
        _("Add active user accounts"),
        default=True,
        help_text=_("Should all active accounts be added by default"),
    )

    extra_accounts = models.ManyToManyField(Account, blank="true")

    sort_order = models.CharField(
        _("account sort order"),
        default=ALPHABETICAL_SORT_ORDER,
        max_length=2,
        choices=SORT_ORDER_CHOICES,
    )

    orientation = models.CharField(
        _("orientation"), max_length=1, choices=ORIENTATION_CHOICES
    )
    comment = models.TextField(
        _("comment"),
        blank=True,
        help_text=_("Comment shown at bottom on first page"),
    )

    double = models.BooleanField(
        default=False, help_text=_("Use two rows per account")
    )
    ignore_blocked = models.BooleanField(
        _("ignore blocked"),
        default=False,
        help_text=_("Don't exclude blocked accounts"),
    )

    class Meta:
        unique_together = (("slug", "group"),)
        verbose_name = _("list")
        verbose_name_plural = _("lists")

        ordering = ("name",)

    def __str__(self):
        return f"{self.group}: {self.name}"

    def total_width(self):
        return int(
            self.account_width + self.balance_width + self.listcolumn_width
        )

    def total_column_count(self):
        count = self.listcolumn_count + 1
        if self.balance_width:
            count += 1
        return int(count)

    def accounts(self):
        all_accounts = Account.objects.filter(active=True, group=self.group_id)
        extra_accounts = self.extra_accounts.values_list("id", flat=True)

        accounts = []
        for a in all_accounts:
            if self.add_active_accounts and a.is_user_account():
                accounts.append(a)
            elif a.id in extra_accounts:
                accounts.append(a)

        if self.sort_order == self.CALLSIGN_SORT_ORDER:
            return callsign_sorted(accounts)
        elif self.sort_order == self.RANDOM_SORT_ORDER:
            random.shuffle(accounts)
            return accounts
        elif self.sort_order == self.CONSUMPTION_SORT_ORDER:
            return sorted(accounts, key=lambda a: a.total_used(), reverse=True)
        elif self.sort_order == self.LAST_30_DAYS_USAGE_SORT_ORDER:
            return sorted(
                accounts, key=lambda a: a.last_30_days_usage(), reverse=True
            )
        else:
            return sorted(accounts, key=lambda a: a.name.lower())


class ListColumn(models.Model):
    name = models.CharField(_("name"), max_length=200)
    width = models.PositiveSmallIntegerField(_("width"))
    list = models.ForeignKey(
        List,
        on_delete=models.CASCADE,
        verbose_name=_("list"),
        related_name="column_set",
    )

    class Meta:
        ordering = ["id"]
        # unique_together = (('name', 'list'),)
        verbose_name = _("list item")
        verbose_name_plural = _("list items")

    def __str__(self):
        return f"{self.list.group}: {self.list}, {self.name}"
