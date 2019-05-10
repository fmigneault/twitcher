"""
Factories to create storage backends.
"""

from twitcher.db import mongodb as _mongodb, get_database_type
from twitcher.store.mongodb import MongodbTokenStore
from twitcher.store.memory import MemoryTokenStore
from twitcher.store.mongodb import MongodbServiceStore
from twitcher.store.memory import MemoryServiceStore
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from twitcher.store.base import AccessTokenStore, ServiceStore
    from twitcher.typedefs import AnySettingsContainer


def tokenstore_factory(container):
    # type: (AnySettingsContainer) -> AccessTokenStore
    """
    Creates a token store with the interface of :class:`twitcher.store.AccessTokenStore`.
    By default the mongodb implementation will be used.

    :param container: Container from which configuration settings can be extracted.
    :return: An instance of :class:`twitcher.store.AccessTokenStore`.
    """
    database = get_database_type(container)
    if database == 'mongodb':
        db = _mongodb(container)
        store = MongodbTokenStore(db.tokens)
    else:
        store = MemoryTokenStore()
    return store


def servicestore_factory(container):
    # type: (AnySettingsContainer) -> ServiceStore
    """
    Creates a service store with the interface of :class:`twitcher.store.ServiceStore`.
    By default the mongodb implementation will be used.

    :param container: Container from which configuration settings can be extracted.
    :return: An instance of :class:`twitcher.store.ServiceStore`.
    """
    database = get_database_type(container)
    if database == 'mongodb':
        db = _mongodb(container)
        store = MongodbServiceStore(collection=db.services)
    else:
        store = MemoryServiceStore()
    return store
