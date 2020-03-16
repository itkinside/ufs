"""
Usage: ./manage.py createuser -g GROUP -u USERNAME [-y]

Details: ./manage.py createuser -h

Example:
    To create uFS users and accounts for all Samfundet users with primary group
    "ark", run the following in your shell, where 230 is the group ID of "ark":

    for u in `getent passwd | awk -F: '$4=="230" { print $1 }'`; do
        ./manage.py createuser -g ark -u $u;
    done
"""

import logging
from optparse import make_option
from pwd import getpwnam
import sys

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.management.color import color_style

from itkufs.accounting.models import Group, Account

CONSOLE_LOG_FORMAT = "%(levelname)-8s %(message)s"


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            "-g",
            "--group",
            dest="group_slug",
            help="Group to create new account in",
        ),
        make_option(
            "-u",
            "--user",
            dest="username",
            help="User to create uFS user and account for",
        ),
        make_option(
            "-y",
            "--yes",
            action="store_const",
            const=1,
            dest="yes",
            default=0,
            help="Do not ask for confirmation",
        ),
    )

    def __init__(self):
        self.logger = self._setup_logging()
        self.style = color_style()

    def _setup_logging(self):
        logging.basicConfig(format=CONSOLE_LOG_FORMAT, level=logging.INFO)
        return logging.getLogger("createuser")

    def handle(self, *args, **options):
        if options["group_slug"] is None or options["username"] is None:
            sys.exit(__doc__)
        full_name = self._get_full_name(options["username"])
        if options["yes"] or self._get_confirmation(
            options["username"], full_name
        ):
            user = self._create_user(options["username"])
            self._create_account(options["group_slug"], user, full_name)

    def _get_full_name(self, username):
        try:
            return getpwnam(username)[4].split(",")[0]
        except (IndexError, KeyError):
            self.logger.warning(
                'Failed to extract full name for "%s"', username, exc_info=True
            )
            return username

    def _get_confirmation(self, username, full_name):
        question = f"Add {username} ({full_name})? y/N "
        answer = input(question)
        if answer.lower() == "y":
            return True
        else:
            self.logger.info('Skipping "%s"', username)
            return False

    def _create_user(self, username):
        user, created = User.objects.get_or_create(
            username=username, email=f"{username}@{settings.MAIL_DOMAIN}"
        )
        if created:
            self.logger.info('User "%s" created', user)
        else:
            self.logger.info('User "%s" already exists', user)
        return user

    def _create_account(self, group_slug, user, full_name):
        group = self._get_group(group_slug)
        account, created = Account.objects.get_or_create(
            group=group,
            owner=user,
            defaults={
                "name": full_name,
                "short_name": user.username,
                "type": Account.LIABILITY_ACCOUNT,
                "slug": user.username,
            },
        )
        if created:
            self.logger.info('Account "%s" of user "%s" created', account, user)
        else:
            self.logger.info(
                'Account "%s" of user "%s" already exists', account, user
            )
        return account

    def _get_group(self, group_slug):
        try:
            return Group.objects.get(slug=group_slug)
        except Group.DoesNotExist:
            self.logger.error('Group "%s" does not exist', group_slug)
            sys.exit(1)
