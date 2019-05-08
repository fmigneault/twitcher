"""
Based on unitests in https://github.com/wndhydrnt/python-oauth2/tree/master/oauth2/test
"""

import pytest
from .. common import DBTest, dummy_request

from twitcher.utils import expires_at
from twitcher.store import tokenstore_factory, servicestore_factory
from twitcher.models import AccessToken, Service


class SQLDBTokenStoreTestCase(DBTest):
    def setUp(self):
        super(SQLDBTokenStoreTestCase, self).setUp()
        self.init_database()

        self.token_store = tokenstore_factory(
            dummy_request(dbsession=self.session))

    def test_fetch_by_token(self):
        pass

    def test_save_token(self):
        self.token_store.save_token(
            AccessToken(token="abc", expires_at=expires_at(hours=1)))


class SQLDBServiceStoreTestCase(DBTest):
    def setUp(self):
        super(SQLDBServiceStoreTestCase, self).setUp()
        self.init_database()

        self.service_store = servicestore_factory(
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
