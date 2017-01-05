"""
Testing the Twithcer XML-RPC interface.
"""
import pytest
import unittest
import webtest
import pyramid.testing

from twitcher._compat import PY2
from twitcher._compat import xmlrpclib

from twitcher.tests.functional.common import setup_with_mongodb
from twitcher.tests. functional.common import setup_mongodb_tokenstore
from twitcher.tests.functional.common import setup_mongodb_servicestore


class XMLRPCInterfaceAppTest(unittest.TestCase):

    def setUp(self):
        config = setup_with_mongodb()
        self.token = setup_mongodb_tokenstore(config)
        setup_mongodb_servicestore(config)
        config.include('twitcher.rpcinterface')
        self.app = webtest.TestApp(config.make_wsgi_app())

    def tearDown(self):
        pyramid.testing.tearDown()

    def _callFUT(self, method, params):
        if PY2:
            xml = xmlrpclib.dumps(params, methodname=method)
        else:
            xml = xmlrpclib.dumps(params, methodname=method).encode('utf-8')
        #print xml
        resp = self.app.post('/RPC2', content_type='text/xml', params=xml)
        assert resp.status_int == 200
        assert resp.content_type == 'text/xml'
        #print resp.body
        return xmlrpclib.loads(resp.body)[0][0]

    @pytest.mark.online
    def test_generate_token_and_revoke_it(self):
        # gentoken
        resp = self._callFUT('generate_token', (1, {}))
        assert 'access_token' in resp
        assert 'expires_at' in resp
        # revoke
        resp = self._callFUT('revoke_token', (resp['access_token'],))
        assert resp is True

    @pytest.mark.online
    def test_register_service_and_unregister_it(self):
        # register
        resp = self._callFUT('register_service', (
            'http://localhost/wps',
            'test_emu',
            'wps',
            False,
            False,
            False))
        assert resp == {'url': 'http://localhost/wps', 'name': 'test_emu',
                        'type': 'wps', 'public': False, 'c4i': False}
        # unregister
        resp = self._callFUT('unregister_service', ('test_emu',))
        assert resp is True
