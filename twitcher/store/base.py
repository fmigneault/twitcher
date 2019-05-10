"""
Store adapters to persist and retrieve data during the twitcher process or
for later use. For example an access token storage and a service registry.

This module provides base classes that can be extended to implement your own
solution specific to your needs.

The implementation is based on `python-oauth2 <http://python-oauth2.readthedocs.io/en/latest/>`_.
"""
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from twitcher.datatype import AccessToken, Service
    from pyramid.request import Request
    from typing import Optional


class AccessTokenStore(object):

    def save_token(self, access_token, request=None):
        # type: (AccessToken, Optional[Request]) -> None
        """
        Stores an access token with additional data.

        :param access_token: Access token to save.
        :param request: Request that lead to this call.
        """
        raise NotImplementedError

    def delete_token(self, token, request=None):
        # type: (AnyStr, Optional[Request]) -> None
        """
        Deletes an access token from the store using its token string to identify it.
        This invalidates both the access token and the token.

        :param token: A string containing the token.
        :param request: Request that lead to this call.
        :return: None.
        """
        raise NotImplementedError

    def fetch_by_token(self, token, request=None):
        # type: (AnyStr, Optional[Request]) -> AccessToken
        """
        Fetches an access token from the store using its token string to
        identify it.

        :param token: A string containing the token.
        :param request: Request that lead to this call.
        :return: An instance of :class:`twitcher.datatype.AccessToken`.
        """
        raise NotImplementedError

    def clear_tokens(self, request=None):
        # type: (Optional[Request]) -> None
        """
        Removes all tokens from database.

        :param request: Request that lead to this call.
        :return: None.
        """
        raise NotImplementedError


class ServiceStore(object):
    """
    Storage for OWS services.
    """

    def save_service(self, service, overwrite=True, request=None):
        # type: (Service, bool, Optional[Request]) -> Service
        """
        Stores an OWS service in storage.

        :param service: An instance of :class:`twitcher.datatype.Service`.
        :param request: Request that lead to this call.
        :returns: saved Service with updated fields as they have been stored.
        """
        raise NotImplementedError

    def delete_service(self, name, request=None):
        # type: (AnyStr, Optional[Request]) -> bool
        """
        Removes service from database.

        :param name: Name of the service to be removed.
        :param request: Request that lead to this call.
        :returns: successful operation status.
        """
        raise NotImplementedError

    def list_services(self, request=None):
        # type: (Optional[Request]) -> List[Service]
        """
        Lists all services in database.

        :param request: Request that lead to this call.
        :returns: list of services retrieved from storage.
        """
        raise NotImplementedError

    def fetch_by_name(self, name, request=None):
        # type: (AnyStr, Optional[Request]) -> Service
        """
        Get service for given ``name`` from storage.

        :param name: A string containing the service name.
        :param request: Request that lead to this call.
        :return: An instance of :class:`twitcher.datatype.Service`.
        """
        raise NotImplementedError

    def fetch_by_url(self, url, request=None):
        # type: (AnyStr, Optional[Request]) -> Service
        """
        Get service for given ``url`` from storage.

        :param url: A string containing the service url.
        :param request: Request that lead to this call.
        :return: An instance of :class:`twitcher.datatype.Service`.
        """
        raise NotImplementedError

    def clear_services(self, request=None):
        # type: (Optional[Request]) -> bool
        """
        Removes all OWS services from storage.

        :param request: Request that lead to this call.
        :returns: successful operation status.
        """
        raise NotImplementedError
