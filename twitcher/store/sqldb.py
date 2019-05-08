"""
Read or write data from SQL database.
"""

from twitcher.store.base import AccessTokenStore
from twitcher.exceptions import AccessTokenNotFound

from twitcher.store.base import ServiceStore
from twitcher.datatype import Service
from twitcher.exceptions import ServiceNotFound
from twitcher import namesgenerator
from twitcher.utils import baseurl

from .. import models


class SQLDBTokenStore(AccessTokenStore):
    """
    Stores tokens in sql database.
    """
    def __init__(self, request):
        self.request = request

    def save_token(self, access_token):
        self.request.dbsession.add(models.AccessToken(
            token=access_token.token,
            expires_at=access_token.expires_at))
        return True

    def delete_token(self, token):
        pass

    def fetch_by_token(self, token):
        query = self.request.dbsession.query(models.AccessToken)
        one = query.filter(models.AccessToken.token == token).first()
        return one

    def clear_tokens(self):
        pass


class SQLDBServiceStore(ServiceStore):
    """
    Stores OWS services in sql database.
    """
    def __init__(self, request):
        self.request = request

    def save_service(self, service, overwrite=True):
        self.request.dbsession.add(models.Service(
            name=service.name,
            url=baseurl(service.url),
            type=service.type,
            purl=service.purl,
            # public=service.public,
            # verify=service.verify
            auth=service.auth))
        return True

    def delete_service(self, name):
        return True

    def list_services(self):
        my_services = []
        return my_services

    def fetch_by_name(self, name):
        query = self.request.dbsession.query(models.Service)
        one = query.filter(models.Service.name == name).first()
        return one

    def fetch_by_url(self, url):
        query = self.request.dbsession.query(models.Service)
        one = query.filter(models.Service.url == url).first()
        return one

    def clear_services(self):
        return True
