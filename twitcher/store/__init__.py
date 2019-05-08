"""
Factories to create storage backends.
"""

# Interfaces
from twitcher.store.base import AccessTokenStore

# Factories
from twitcher.db import mongodb as _mongodb
from twitcher.store.mongodb import MongodbTokenStore, MongodbServiceStore
from twitcher.store.memory import MemoryTokenStore, MemoryServiceStore
from twitcher.store.sqldb import SQLDBTokenStore, SQLDBServiceStore


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


def servicestore_factory(request, database=None):
    """
    Creates a service store with the interface of :class:`twitcher.store.ServiceStore`.
    By default the mongodb implementation will be used.

    :return: An instance of :class:`twitcher.store.ServiceStore`.
    """
    database = database or 'sqldb'
    if database == 'mongodb':
        db = _mongodb(request.registry)
        store = MongodbServiceStore(collection=db.services)
    if database == 'sqldb':
        store = SQLDBServiceStore(request)
    else:
        store = MemoryServiceStore()
    return store
