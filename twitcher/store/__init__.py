"""
Factories to create storage backends.
"""

from twitcher.store.base import AccessTokenStore
from twitcher.store.sqldb import SQLDBTokenStore, SQLDBServiceStore


def tokenstore_factory(request):
    """
    Creates a token store with the interface of :class:`twitcher.store.AccessTokenStore`.

    :return: An instance of :class:`twitcher.store.AccessTokenStore`.
    """
    return SQLDBTokenStore(request)


def servicestore_factory(request):
    """
    Creates a service store with the interface of :class:`twitcher.store.ServiceStore`.

    :return: An instance of :class:`twitcher.store.ServiceStore`.
    """
    return SQLDBServiceStore(request)
