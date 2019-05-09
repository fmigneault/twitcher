"""
Testing the Twitcher XML-RPC interface.
"""
import pytest
import webtest

from .. common import FunctionalTest, call_FUT, WPS_TEST_SERVICE


class XMLRPCInterfaceAppTest(FunctionalTest):

    def setUp(self):
        super(XMLRPCInterfaceAppTest, self).setUp()
        self.config.include('twitcher.rpcinterface')

        self.app = webtest.TestApp(self.config.make_wsgi_app())

    @pytest.mark.skip(reason="fix db init")
    def test_generate_token_and_revoke_it(self):
        # gentoken
        resp = call_FUT(self.app, 'generate_token', (1, {}))
        assert 'access_token' in resp
        assert 'expires_at' in resp
        # revoke
        resp = call_FUT(self.app, 'revoke_token', (resp['access_token'],))
        assert resp is True
        # revoke all
        resp = call_FUT(self.app, 'revoke_all_tokens', ())
        assert resp is True

    @pytest.mark.skip(reason="fix rpc call")
    def test_register_service_and_unregister_it(self):
        service = {'url': WPS_TEST_SERVICE, 'name': 'test_wps',
                   'type': 'wps', 'public': False, 'auth': 'token',
                   'verify': True, 'purl': 'http://purl/wps'}
        # register
        resp = call_FUT(self.app, 'register_service', (
            service['url'],
            service,
            False))
        assert resp == service

        # get by name
        resp = call_FUT(self.app, 'get_service_by_name', (service['name'],))
        assert resp == service

        # get by url
        resp = call_FUT(self.app, 'get_service_by_url', (service['url'],))
        assert resp == service

        # list
        resp = call_FUT(self.app, 'list_services', ())
        assert resp == [service]

        # unregister
        resp = call_FUT(self.app, 'unregister_service', (service['name'],))
        assert resp is True

        # clear
        resp = call_FUT(self.app, 'clear_services', ())
        assert resp is True
