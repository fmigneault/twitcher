"""
Based on unitests in https://github.com/wndhydrnt/python-oauth2/tree/master/oauth2/test
"""

import pytest
from .common import BaseTest, dummy_request

from twitcher.utils import expires_at
from twitcher.store import AccessTokenStore, ServiceStore
from twitcher.models import AccessToken, Service


class AccessTokenStoreTestCase(BaseTest):
    def setUp(self):
        super(AccessTokenStoreTestCase, self).setUp()
        self.init_database()

        self.token_store = AccessTokenStore(
            dummy_request(dbsession=self.session))

    def test_token(self):
        self.token_store.save_token(
            AccessToken(token="abc", expires_at=expires_at(hours=1)))
        token = self.token_store.fetch_by_token(token='abc')
        assert token.token == 'abc'
        self.token_store.delete_token(token='abc')
        self.token_store.clear_tokens()


class ServiceStoreTestCase(BaseTest):
    def setUp(self):
        super(ServiceStoreTestCase, self).setUp()
        self.init_database()

        self.service_store = ServiceStore(
            dummy_request(dbsession=self.session))

    def test_fetch_by_name(self):
        pass

    def test_save_service(self):
        self.service_store.save_service(
            Service(
                name="loving_flamingo",
                url="http://somewhere.over.the/ocean",
                type="wps",
                # public=False,
                auth='token',
                # verify=True,
                purl="http://purl/wps")
        )
