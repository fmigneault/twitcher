"""
Read or write data from database.
"""

from twitcher.exceptions import AccessTokenNotFound, ServiceNotFound
from twitcher import namesgenerator
from twitcher.utils import baseurl
from twitcher import datatype
from twitcher import models


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

    def delete_token(self, token):
        """
        Deletes an access token from the store using its token string to identify it.

        :param token: A token string.
        """
        query = self.request.dbsession.query(models.AccessToken)
        one = query.filter(models.AccessToken.token == token).first()
        if not one:
            raise AccessTokenNotFound
        self.request.dbsession.delete(one)

    def fetch_by_token(self, token):
        """
        Fetches an access token from the store using its token string to
        identify it.

        :param token: A token string.
        :return: An instance of :class:`twitcher.datatype.AccessToken`.
        """
        query = self.request.dbsession.query(models.AccessToken)
        one = query.filter(models.AccessToken.token == token).first()
        if not one:
            raise AccessTokenNotFound
        return datatype.AccessToken.from_model(one)

    def clear_tokens(self):
        """
        Removes all tokens.
        """
        self.request.dbsession.query(models.AccessToken).delete()


class ServiceStore(object):
    """
    Stores OWS services.
    """
    def __init__(self, request):
        self.request = request

    def save_service(self, service, overwrite=True):
        """
        Stores an OWS service in database.

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

    def delete_service(self, name):
        """
        Removes service identified by name.
        """
        query = self.request.dbsession.query(models.Service)
        one = query.filter(models.Service.name == name).first()
        if not one:
            raise ServiceNotFound
        self.request.dbsession.delete(one)

    def list_services(self):
        """
        Lists all services.

        :return: A list with instances of :class:`twitcher.datatype.Service`.
        """
        services = self.request.dbsession.query(models.Service).all()
        return [datatype.Service.from_model(service) for service in services]

    def fetch_by_name(self, name):
        """
        Get service for given service ``name``.

        :param name: A service name string.
        :return: An instance of :class:`twitcher.datatype.Service`.
        """
        query = self.request.dbsession.query(models.Service)
        one = query.filter(models.Service.name == name).first()
        if not one:
            raise ServiceNotFound
        return datatype.Service.from_model(one)

    def fetch_by_url(self, url):
        """
        Get a service for given ``url``.

        :param url: A URL string.
        :return: An instance of :class:`twitcher.datatype.Service`.
        """
        query = self.request.dbsession.query(models.Service)
        one = query.filter(models.Service.url == url).first()
        if not one:
            raise ServiceNotFound
        return datatype.Service.from_model(one)

    def clear_services(self):
        """
        Removes all services.
        """
        self.request.dbsession.query(models.Service).delete()
