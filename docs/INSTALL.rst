µFS Microfinance System
=======================

Dependencies for production use
-------------------------------

See the ``requirements.txt`` file for all Python dependencies, in
addition, you may need:

- gettext -- for translations
- A database supported by Django, e.g. PostgreSQL
- A Python database adapter, e.g. python-psycopg2

Dependency requirements are manually encoded in ``requirements.in``. Then,
the tool ``pip-compile`` from the ``pip-tools`` package is run to resolve all
dependencies and lock them down in ``requirements.txt``, which is the file
you use when installing dependencies, both in your development environment
and in production.


Additional dependencies for development
---------------------------------------

See the ``requirements.txt`` file.


How to install
--------------

This is a rather rough guide on how to install µFS.

#. Checkout latest source from https://github.com/itkinside/ufs/

#. Get all the dependencies listed above. Some/most can be installed using
   ``pip`` and the bundled ``requirements.txt`` file::

    pip install -r requirements.txt

#. Compile translation files (.po -> .mo) using::

    python manage.py compilemessages

#. Add a ``itkufs/settings/local.py`` file which sets the ``DATABASE_*`` and
   ``SECRET_KEY`` options. You can find a template at
   ``itkufs/settings/local.py.template``.

#. Either:

   - Setup your web server. See the dir ``itkufs/wsgi/`` for an WSGI
     application setup which optionally supports using dependencies from a
     virtualenv.

   - Use Django's builtin development web server, which also use the above
     WSGI application.


How to setup
------------

After the installation is completed, do the following:

#. To create database tables and create a superuser::

    python manage.py syncdb --migrate

#. If you use Django's builtin development server, start it::

    python manage.py runserver --settings=itkufs.settings.dev

   Using the ``dev`` settings file turns off the requirement for SSL and
   turns on ``django-debug-toolbar``.

#. Go to e.g. http://127.0.0.1:8000/admin/ and log in using the newly
   created superuser.

#. Create a group, and add the superuser as admin of the group.

#. Go to e.g. http://127.0.0.1:8000/ and use µFS.

#. Profit!

Additional groups must be added from the Django admin, just like the first
one. All other operations should be possible to do from the µFS interface.


How to run tests
----------------

To run the unit tests::

    python manage.py test

To run the unit tests while measuring code coverage, run::

    coverage run --source=itkufs manage.py test

To see the code coverage reports, run::

    coverage report


How to run code linting
-----------------------

To run code linting, run::

    flake8 itkufs

Ideally, this command should not print a single warning.

..
    vim: ft=rst tw=74 ai
