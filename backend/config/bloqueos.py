"""Serialización local de SQLite; no sustituye los bloqueos de PostgreSQL."""
from contextlib import contextmanager
from threading import RLock
from django.db import connection

_sqlite = RLock()

@contextmanager
def escritura_serializada():
    if connection.vendor == 'sqlite':
        with _sqlite:
            yield
    else:
        yield
