"""
Factories to create storage backends.
"""

# Interfaces
from twitcher.store.base import AccessTokenStore

# Factories
from twitcher.store.memory import MemoryTokenStore, MemoryServiceStore
from twitcher.store.sqldb import SQLDBTokenStore, SQLDBServiceStore


def tokenstore_factory(request, database=None):
    """
    Creates a token store with the interface of :class:`twitcher.store.AccessTokenStore`.
    By default the `sqldb` implementation will be used.

    :param database: A string with the store implementation name: "sqldb" or "memory".
    :return: An instance of :class:`twitcher.store.AccessTokenStore`.
    """
    database = database or 'sqldb'
    if database == 'sqldb':
        store = SQLDBTokenStore(request)
    else:
        store = MemoryTokenStore()
    return store


def servicestore_factory(request, database=None):
    """
    Creates a service store with the interface of :class:`twitcher.store.ServiceStore`.
    By default the `sqldb` implementation will be used.

    :return: An instance of :class:`twitcher.store.ServiceStore`.
    """
    database = database or 'sqldb'
    if database == 'sqldb':
        store = SQLDBServiceStore(request)
    else:
        store = MemoryServiceStore()
    return store
