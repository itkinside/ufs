µFS Microfinance System
=======================

Dependencies for production use
-------------------------------

See the ``requirements.txt`` file for all Python dependencies, in
addition, you may need:

- gettext -- for translations
- A PostgreSQL database

Dependency requirements are manually encoded in ``requirements.in``. Then,
the tool ``pip-compile`` from the ``pip-tools`` package is run to resolve all
dependencies and lock them down in ``requirements.txt``, which is the file
you use when installing dependencies, both in your development environment
and in production.


Additional dependencies for development
---------------------------------------

See the ``requirements-dev.txt`` file.


How to install
--------------

This is a rather rough guide on how to install µFS.

#. Checkout latest source from https://github.com/itkinside/ufs/

#. Install PostgreSQL development headers. On Debian::

    sudo apt install libpq-dev

#. Get all the dependencies listed above. Some/most can be installed using
   ``pip`` and the bundled requirement files. In production::

    python3 -m pip install -r requirements.txt

   Or in development::

    python3 -m pip install -r requirements-dev.txt

#. Add a ``itkufs/settings/local.py`` file which sets the ``DATABASE_*`` and
   ``SECRET_KEY`` options. You can find a template at
   ``itkufs/settings/local.py.template``.

#. Compile translation files (.po -> .mo) using::

    python3 manage.py compilemessages

#. Either:

   - In production, setup your web server to run the WSGI app at
     ``itkufs.wsgi:application``. µFS doesn't serve its static files
     (``/static/``) in production, so the web server must serve them.

   - Or, in development, use Django's builtin development web server,
     which also use the above WSGI application.


How to setup
------------

After the installation is completed, do the following:

#. To create database tables and create a superuser::

    python3 manage.py migrate

#. If you use Django's builtin development server, start it::

    python3 manage.py runserver --settings=itkufs.settings.dev

   Using the ``dev`` settings file turns off the requirement for SSL and
   turns on ``django-debug-toolbar``.

#. Go to e.g. http://127.0.0.1:8000/admin/ and log in using the newly
   created superuser.

#. Create a group, and add the superuser as admin of the group.

#. Go to e.g. http://127.0.0.1:8000/ and use µFS.

#. Profit!

Additional groups must be added from the Django admin, just like the first
one. All other operations should be possible to do from the µFS interface.


How to update
-------------

To deploy a new version in production:

#. Get the latest source::

    git pull

#. Apply new database migrations::

    python3 manage.py migrate

#. Compile translation files. The compiled ``.mo`` files are not in git, so
   changes to the ``.po`` files only take effect after this::

    python3 manage.py compilemessages

#. Make sure the web server serves the updated static files (CSS,
   JavaScript, images). If it serves them from ``STATIC_ROOT``, copy them
   there using::

    python3 manage.py collectstatic --noinput

#. Restart the WSGI app (e.g. uWSGI), so it loads the new code and
   translations.

Each step is safe to run when nothing has changed, so run all of them on
every update.


How to run tests
----------------

To run the unit tests::

    python3 -m pytest

To run the unit tests while measuring code coverage, run::

    python3 -m pytest --cov=itkufs --cov-report=term-missing


How to run code linting
-----------------------

To check formatting and run code linting, run::

    black --check itkufs
    python3 -m flake8
    mypy .

Ideally, these commands should not print a single warning.

..
    vim: ft=rst tw=74 ai
