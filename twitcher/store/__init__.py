"""
Factories to create storage backends.
"""

# Interfaces
from twitcher.store.base import AccessTokenStore

# Factories
from twitcher.db import mongodb as _mongodb
from twitcher.store.mongodb import MongodbTokenStore
from twitcher.store.memory import MemoryTokenStore
from twitcher.store.sqldb import SQLDBTokenStore


def tokenstore_factory(request, database=None):
    """
    Creates a token store with the interface of :class:`twitcher.store.AccessTokenStore`.
    By default the mongodb implementation will be used.

    :param database: A string with the store implementation name: "mongodb" or "memory".
    :return: An instance of :class:`twitcher.store.AccessTokenStore`.
    """
    database = database or 'sqldb'
    if database == 'mongodb':
        db = _mongodb(request.registry)
        store = MongodbTokenStore(db.tokens)
    if database == 'sqldb':
        store = SQLDBTokenStore(request)
    else:
        store = MemoryTokenStore()
    return store


from twitcher.store.mongodb import MongodbServiceStore
from twitcher.store.memory import MemoryServiceStore


def servicestore_factory(registry, database=None):
    """
    Creates a service store with the interface of :class:`twitcher.store.ServiceStore`.
    By default the mongodb implementation will be used.

    :return: An instance of :class:`twitcher.store.ServiceStore`.
    """
    database = database or 'mongodb'
    if database == 'mongodb':
        db = _mongodb(registry)
        store = MongodbServiceStore(collection=db.services)
    else:
        store = MemoryServiceStore()
    return store
