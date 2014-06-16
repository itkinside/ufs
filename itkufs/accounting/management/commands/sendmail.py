"""
Usage: ./manage.py sendmail -g GROUP
"""

import sys
import logging
from optparse import make_option

from django.utils.translation import ugettext_lazy as _, activate
from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage, SMTPConnection

from itkufs.accounting.models import Group


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '-g', '--group', dest='group_slug',
            help='Group to send emails to'),
        make_option(
            '-y', '--yes',
            action='store_const', const=1, dest='yes', default=0,
            help='Do not ask for confirmation'),
        make_option(
            '-d', '--debug',
            action='store_const', const=1, dest='debug', default=0,
            help='Don\'t send any emails, just print them'),
        make_option(
            '-l', '--lang', dest='lang', default='en',
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
                connection = SMTPConnection()
                connection.send_messages(emails)

    def _set_language(self, lang):
        activate(lang)

    def _get_group(self, group_slug):
        try:
            return Group.objects.get(slug=group_slug)
        except Group.DoesNotExist:
            self.logger.error(u'Group "%s" does not exist', group_slug)
            sys.exit(1)

    def _get_accounts(self, group):
        accounts = group.account_set.filter(owner__isnull=False)
        return accounts.select_related('group', 'owner')

    def _build_emails(self, accounts):
        emails = []

        for account in accounts:
            if not account.owner.email:
                self.logger.warning(
                    u'Skipping account %s as it has no email set.', account)
            elif account.is_blocked():
                emails.append(self._send_blocked_mail(account))
            elif account.needs_warning():
                emails.append(self._send_warning_mail(account))

        return emails

    def _send_warning_mail(self, account):
        to_email = account.owner.email
        subject = WARNING_SUBJECT % {'group': account.group}
        message = WARNING_MESSAGE % {
            'balance': account.normal_balance(),
            'limit': account.group.warn_limit,
        }
        message += SIGNATURE

        group_email = account.group.email
        if group_email:
            headers = {'CC': group_email,
                       'Reply-To': group_email}
        else:
            headers = {}

        return EmailMessage(
            subject, message, FROM_EMAIL, [to_email], headers=headers)

    def _send_blocked_mail(self, account):
        to_email = account.owner.email
        subject = BLOCK_SUBJECT % {'group': account.group}
        message = BLOCK_MESSAGE % {
            'balance': account.normal_balance(),
            'limit': account.group.block_limit,
        }
        message += SIGNATURE

        group_email = account.group.email
        if group_email:
            headers = {'CC': group_email,
                       'Reply-To': group_email}
        else:
            headers = {}

        return EmailMessage(
            subject, message, FROM_EMAIL, [to_email], headers=headers)

    def _print_debug(self, emails):
        for email in emails:
            print "From: %s" % email.from_email
            print "To: %s" % ';'.join(email.to)
            print "Subject: %s" % email.subject
            print ""
            print email.body
            print "="*80

FROM_EMAIL = 'ufs-web@samfundet.no'

WARNING_SUBJECT = _('Warning limit passed in %(group)s')
WARNING_MESSAGE = _('''
Your current account balance of %(balance).2f, is below the _warning limit_
%(limit).2f.

To fix this either deposit more money or contact one of the group
administrators.
''')

BLOCK_SUBJECT = _('Block limit passed in %(group)s')
BLOCK_MESSAGE = _('''
Your current account balance of %(balance).2f, is below the _block limit_
%(limit).2f.

To fix this either deposit more money or contact one of the group
administrators.
''')

SIGNATURE = '\n-- \nuFS - http://ufs.samfundet.no/'
