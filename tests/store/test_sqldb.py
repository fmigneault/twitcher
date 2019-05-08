"""
Based on unitests in https://github.com/wndhydrnt/python-oauth2/tree/master/oauth2/test
"""

import pytest
from .. common import DBTest

from twitcher.utils import expires_at
from twitcher.store.sqldb import SQLDBTokenStore, SQLDBServiceStore


class SQLDBTokenStoreTestCase(DBTest):
    def setUp(self):
        super(SQLDBTokenStoreTestCase, self).setUp()
        self.init_database()

        from twitcher.models import AccessToken

        model = AccessToken(token="abcdef", expires_at=expires_at(hours=1))
        self.session.add(model)

    def test_fetch_by_token(self):
        pass

    def test_save_token(self):
        pass


class SQLDBServiceStoreTestCase(DBTest):
    def setUp(self):
        super(SQLDBServiceStoreTestCase, self).setUp()
        self.init_database()

        from twitcher.models import Service

        model = Service(
            name="loving_flamingo",
            url="http://somewhere.over.the/ocean",
            type="wps",
            # public=False,
            auth='token',
            # verify=True,
            purl="http://purl/wps")
        self.session.add(model)

    def test_fetch_by_name(self):
        pass

    def test_save_service_default(self):
        pass

    def test_save_service_with_special_name(self):
        pass

    def test_save_service_public(self):
        pass
