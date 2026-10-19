from django.apps import AppConfig
from django.db.backends.signals import connection_created


def enable_wal(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        cur = connection.cursor()
        cur.execute('PRAGMA journal_mode=WAL;')
        cur.execute('PRAGMA synchronous=FULL;')


class ReceptionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reception'

    def ready(self):
        connection_created.connect(enable_wal)
        from . import signals  # noqa: F401
