"""
Usage: ./manage.py sendmail -g GROUP
"""

import sys
import logging
from optparse import make_option

from django.conf import settings
from django.utils.translation import ugettext_lazy as _, activate, get_language
from django.core.management.base import BaseCommand
from django.core.mail import send_mass_mail

from itkufs.accounting.models import Account, Group

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-g', '--group', dest='group_slug',
            help='Group to send emails to'),
        make_option('-y', '--yes',
            action='store_const', const=1, dest='yes', default=0,
            help='Do not ask for confirmation'),
        make_option('-d', '--debug',
            action='store_const', const=1, dest='debug', default=0,
            help='Don\'t send any emails, just print them'),
        make_option('-l', '--lang', dest='lang', default='en',
            help='Language to use for emails'),
    )

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

        logging.basicConfig()
        self.logger = logging.getLogger('itkufs.accounting.sendmail')

    def handle(self, *args, **options):
        if not options['group_slug']:
            sys.exit(__doc__)

        self._set_language(options['lang'])

        group = self._get_group(options['group_slug'])
        accounts = self._get_accounts(group)
        emails = self._build_emails(accounts)

        if not options['yes'] and not options['debug']:
            answer = raw_input(u"Send emails y/N ".encode('utf-8'))

            if answer.lower() != 'y':
                print "Canceled sending"
                sys.exit(0)

        if emails:
            if options['debug']:
                self._print_debug(emails)
            else:
                send_mass_mail(emails)

    def _set_language(self, lang):
        activate(lang)

    def _get_group(self, group_slug):
        try:
            return Group.objects.get(slug=group_slug)
        except Group.DoesNotExist:
            self.logger.error(u'Group "%s" does not exist', group_slug)
            sys.exit(1)

    def _get_accounts(self, group):
        accounts = group.account_set.filter(active=True, owner__isnull=False)
        return accounts.select_related('group', 'owner')

    def _build_emails(self, accounts):
        emails = []

        for account in accounts:
            if account.is_blocked():
                emails.append(self._send_blocked_mail(account))
            elif account.needs_warning():
                emails.append(self._send_warning_mail(account))

        return emails

    def _send_warning_mail(self, account):
        subject = WARNING_SUBJECT % {'group': account.group}
        message = WARNING_MESSAGE % {'balance': account.user_balance(), 'limit': account.group.warn_limit}
        message += SIGNATURE

        return (subject, message, FROM_EMAIL, [account.owner.email])

    def _send_blocked_mail(self, account):
        subject = BLOCK_SUBJECT % {'group': account.group}
        message = BLOCK_MESSAGE % {'balance': account.user_balance(), 'limit': account.group.block_limit}
        message += SIGNATURE

        return (subject, message, FROM_EMAIL, [account.owner.email])

    def _print_debug(self, emails):
        for subject, message, from_email, to_email in emails:
            print "From: %s" % from_email
            print "To: %s" % ';'.join(to_email)
            print "Subject: %s" % subject
            print ""
            print message
            print "="*80

FROM_EMAIL = 'ufs-web@samfundet.no'

WARNING_SUBJECT = _('Warning limit passed in %(group)s')
WARNING_MESSAGE = _('''Your current account balance of %(balance).2f, is below the _warning limit_ %(limit).2f

To fix this either deposit more money or contact one of the group
administrators.
''')

BLOCK_SUBJECT = _('Block limit passed in %(group)s')
BLOCK_MESSAGE = _('''Your current account balance of %(balance).2f, is below the _block limit_ %(limit).2f

To fix this either deposit more money or contact one of the group
administrators.
''')

SIGNATURE = '\n-- \nuFS - http://ufs.samfundet.no/'
