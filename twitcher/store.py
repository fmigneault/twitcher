"""
Read or write data from database.
"""

from .exceptions import AccessTokenNotFound, ServiceNotFound
import .namesgenerator
from .utils import baseurl
import .datatype
import .models


class AccessTokenStore(object):
    """
    Stores tokens in sql database.
    """
    def __init__(self, request):
        self.request = request

    def save_token(self, access_token):
        """
        Stores an access token.
        """
        self.request.dbsession.add(models.AccessToken(
            token=access_token.token,
            expires_at=access_token.expires_at))
        return True

    def delete_token(self, token):
        """
        Deletes an access token from the store using its token string to identify it.

        :param token: A string containing the token.
        :return: None.
        """
        pass

    def fetch_by_token(self, token):
        """
        Fetches an access token from the store using its token string to
        identify it.

        :param token: A string containing the token.
        :return: An instance of :class:`twitcher.datatype.AccessToken`.
        """
        query = self.request.dbsession.query(models.AccessToken)
        one = query.filter(models.AccessToken.token == token).first()
        return datatype.AccessToken.from_model(one)

    def clear_tokens(self):
        """
        Removes all tokens from database.
        """
        pass


class ServiceStore(object):
    """
    Stores OWS services.
    """
    def __init__(self, request):
        self.request = request

    def save_service(self, service, overwrite=True):
        """
        Stores an OWS service in storage.

        :param service: An instance of :class:`twitcher.datatype.Service`.
        """
        self.request.dbsession.add(models.Service(
            name=service.name,
            url=baseurl(service.url),
            type=service.type,
            purl=service.purl,
            public=service.public,
            verify=service.verify,
            auth=service.auth))
        return True

    def delete_service(self, name):
        """
        Removes service from database.
        """
        return True

    def list_services(self):
        """
        Lists all services in database.
        """
        my_services = []
        return my_services

    def fetch_by_name(self, name):
        """
        Get service for given ``name`` from storage.

        :param token: A string containing the service name.
        :return: An instance of :class:`twitcher.datatype.Service`.
        """
        query = self.request.dbsession.query(models.Service)
        one = query.filter(models.Service.name == name).first()
        return datatype.Service.from_model(one)

    def fetch_by_url(self, url):
        """
        Get service for given ``url`` from storage.

        :param token: A string containing the service url.
        :return: An instance of :class:`twitcher.datatype.Service`.
        """
        query = self.request.dbsession.query(models.Service)
        one = query.filter(models.Service.url == url).first()
        return datatype.Service.from_model(one)

    def clear_services(self):
        """
        Removes all OWS services from storage.
        """
        return True
