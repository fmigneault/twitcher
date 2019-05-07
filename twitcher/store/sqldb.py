"""
Read or write data from SQL database.
"""

from twitcher.store.base import AccessTokenStore
from twitcher.exceptions import AccessTokenNotFound

from .. import models


class SQLDBTokenStore(AccessTokenStore):
    """
    Stores tokens in sqldb.
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
