from django.conf import settings


def debug(request):
    """
    Returns context variables helpful for debugging

    Stolen from django.core.context_processors.py, but modified to accept
    superusers as well as internal IPs

    """

    context_extras = {}
    if (settings.DEBUG
        and (request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS
            or request.user.is_superuser)):
        context_extras['debug'] = True
        from django.db import connection
        context_extras['sql_queries'] = connection.queries
    return context_extras
