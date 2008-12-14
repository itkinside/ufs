#! /usr/bin/env python
"""
Usage: ./bin/create-ufs-user.py GROUP USERNAME

To create uFS users and accounts for all Samfundet users with primary group
"ark", run the following in your shell, where 230 is the group ID of "ark":

for u in `getent passwd | awk -F: '$4=="230" { print $1 }'`; do
    ./bin/create-ufs-user.py ark $u;
done
"""

# Setup Django environment
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')
from django.core.management import setup_environ
from itkufs import settings as itkufs_settings
setup_environ(itkufs_settings)

# Normal imports
from pwd import getpwnam
from django.conf import settings
from django.contrib.auth.models import User
from itkufs.accounting.models import Group, Account

if len(sys.argv) != 3:
    sys.exit(__doc__)

group_slug = sys.argv[1]
username = sys.argv[2]
name = getpwnam(username)[4].split(',')[0]

if not raw_input('Add %s (%s)? y/N ' % (username, name)).lower() == 'y':
    print 'Skipping "%s"' % username
else:
    try:
        group = Group.objects.get(slug=group_slug)
    except Group.DoesNotExist:
        sys.exit('Group "%s" does not exist' % group_slug)
    user, user_created = User.objects.get_or_create(
	username=username, email='%s@%s' % (username, settings.MAIL_DOMAIN))
    account, account_created = Account.objects.get_or_create(
	group=group, owner=user,
        defaults={
            'name': name,
            'short_name': username,
            'type': Account.LIABILITY_ACCOUNT,
            'slug': username,
        })

    if user_created:
        print 'User "%s" created' % user
    else:
        print 'User "%s" already exists' % user

    if account_created:
        print 'Account "%s" of user "%s" created' % (account, user)
    else:
        print 'Account "%s" of user "%s" already exists' % (account, user)
