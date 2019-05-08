import pytest

from pyramid.testing import DummyRequest, testConfig
from pyramid.testing import Registry

from .common import BaseTest, dummy_request

from twitcher.store import tokenstore_factory, servicestore_factory
from twitcher.datatype import Service
from twitcher.utils import expires_at
from twitcher.owssecurity import OWSSecurity
from twitcher.owsexceptions import OWSAccessForbidden


class OWSSecurityTestCase(BaseTest):
    def setUp(self):
        super(OWSSecurityTestCase, self).setUp()
        self.init_database()

        request = dummy_request(dbsession=self.session)
        token_store = tokenstore_factory(request)
        service_store = servicestore_factory(request)

        self.security = OWSSecurity(tokenstore=token_store, servicestore=service_store)

    def test_get_token_by_param(self):
        params = dict(request="Execute", service="WPS", access_token="abcdef")
        request = DummyRequest(params=params)
        token = self.security.get_token_param(request)
        assert token == "abcdef"

    def test_get_token_by_path(self):
        params = dict(request="Execute", service="WPS")
        request = DummyRequest(params=params, path="/ows/proxy/emu/12345")
        token = self.security.get_token_param(request)
        assert token == "12345"

    def test_get_token_by_header(self):
        params = dict(request="Execute", service="WPS")
        headers = {'Access-Token': '54321'}
        request = DummyRequest(params=params, headers=headers)
        token = self.security.get_token_param(request)
        assert token == "54321"

    def test_check_request(self):
        params = dict(request="Execute", service="WPS", version="1.0.0", token="cdefg")
        request = DummyRequest(params=params, path='/ows/proxy/emu')
        request.registry = Registry()
        request.registry.settings = {'twitcher.ows_prox_protected_path': '/ows'}
        self.security.check_request(request)

    def test_check_request_invalid(self):
        params = dict(request="Execute", service="WPS", version="1.0.0", token="xyz")
        request = DummyRequest(params=params, path='/ows/proxy/emu')
        request.registry = Registry()
        request.registry.settings = {'twitcher.ows_prox_protected_path': '/ows'}
        with pytest.raises(OWSAccessForbidden):
            self.security.check_request(request)

    def test_check_request_allowed_caps(self):
        params = dict(request="GetCapabilities", service="WPS", version="1.0.0")
        request = DummyRequest(params=params, path='/ows/proxy/emu')
        request.registry = Registry()
        request.registry.settings = {'twitcher.ows_prox_protected_path': '/ows'}
        self.security.check_request(request)

    def test_check_request_allowed_describeprocess(self):
        params = dict(request="DescribeProcess", service="WPS", version="1.0.0")
        request = DummyRequest(params=params, path='/ows/proxy/emu')
        request.registry = Registry()
        request.registry.settings = {'twitcher.ows_prox_protected_path': '/ows'}
        self.security.check_request(request)

    def test_check_request_public_access(self):
        self.security.store.save_service(Service(
            url='http://nowhere/wps', name='test_wps', public=True))
        params = dict(request="Execute", service="WPS", version="1.0.0", token="cdefg")
        request = DummyRequest(params=params, path='/ows/proxy/emu')
        request.registry = Registry()
        request.registry.settings = {'twitcher.ows_prox_protected_path': '/ows'}
        self.security.check_request(request)
