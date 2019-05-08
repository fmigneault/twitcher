"""
Testing the Twitcher API.
"""
import pytest

from .common import DBTest, dummy_request

from twitcher.store import tokenstore_factory, servicestore_factory
from twitcher.api import TokenManager, Registry
from twitcher.tokengenerator import UuidTokenGenerator


class TokenManagerTest(DBTest):

    def setUp(self):
        super(TokenManagerTest, self).setUp()
        self.init_database()

        token_store = tokenstore_factory(
            dummy_request(dbsession=self.session))
        self.tokenmgr = TokenManager(
            tokengenerator=UuidTokenGenerator(),
            tokenstore=token_store
        )

    def test_generate_token_and_revoke_it(self):
        # gentoken
        resp = self.tokenmgr.generate_token()
        assert 'access_token' in resp
        assert 'expires_at' in resp
        # revoke
        resp = self.tokenmgr.revoke_token(resp['access_token'])
        assert resp is True
        # revoke all
        resp = self.tokenmgr.revoke_all_tokens()
        assert resp is True

    def test_generate_token_with_data(self):
        # gentoken
        resp = self.tokenmgr.generate_token(valid_in_hours=1, data={'esgf_token': 'abcdef'})
        assert 'access_token' in resp
        assert 'expires_at' in resp
        # check data
        access_token = self.tokenmgr.store.fetch_by_token(resp['access_token'])
        assert access_token.data == {'esgf_token': 'abcdef'}


class RegistryTest(DBTest):

    def setUp(self):
        super(RegistryTest, self).setUp()
        self.init_database()

        service_store = servicestore_factory(
            dummy_request(dbsession=self.session))

        self.reg = Registry(servicestore=service_store)

    def test_register_service_and_unregister_it(self):
        service = {'url': 'http://localhost/wps', 'name': 'test_emu',
                   'type': 'wps', 'public': False, 'auth': 'token', 'verify': True,
                   'purl': 'http://myservice/wps'}
        # register
        resp = self.reg.register_service(
            service['url'],
            service,
            False)
        assert resp == service

        # get by name
        resp = self.reg.get_service_by_name(service['name'])
        assert resp == service

        # list
        resp = self.reg.list_services()
        assert resp == [service]

        # unregister
        resp = self.reg.unregister_service(service['name'])
        assert resp is True

        # clear
        resp = self.reg.clear_services()
        assert resp is True
