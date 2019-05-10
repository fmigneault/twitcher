"""
based on `papyrus_ogcproxy <https://github.com/elemoine/papyrus_ogcproxy>`_

pyramid testing:

* http://docs.pylonsproject.org/projects/pyramid/en/latest/quick_tutorial/routing.html
"""

import unittest
import pytest

from pyramid import testing
from pyramid.testing import DummyRequest
from pyramid.response import Response

from twitcher.owsexceptions import OWSAccessUnauthorized, OWSBadRequest
from twitcher.formats import CONTENT_TYPE_APP_JSON, CONTENT_TYPE_APP_XML
from twitcher import owsproxy
from twitcher.owsproxy import owsproxy_view
from tests.utils import mock_servicestore_factory, mock_requests_response


# noinspection PyMethodMayBeStatic
class OWSProxyTests(unittest.TestCase):
    def setUp(self):
        self.allowed_hosts_original = owsproxy.allowed_hosts
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        owsproxy.allowed_hosts = self.allowed_hosts_original

    def test_badrequest_url(self):
        request = DummyRequest(scheme='http')
        response = owsproxy_view(request)
        assert isinstance(response, OWSBadRequest)

    def test_badrequest_netloc(self):
        request = DummyRequest(scheme='http', params={'url': 'http://'})
        response = owsproxy_view(request)
        assert isinstance(response, OWSBadRequest)

    @mock_servicestore_factory()
    @mock_requests_response(code=200, headers={'Content-Type': 'application/x-test'})
    def test_unauthorized_content_type(self):
        request = DummyRequest(scheme='http', matchdict={'service_name': 'test-service'})
        response = owsproxy_view(request)
        assert isinstance(response, OWSAccessUnauthorized)
        assert 'application/x-test' in response.message

    @mock_servicestore_factory(purl='http://test-public/wps', url='http://test-private:9000')
    @mock_requests_response(code=201, headers={'Content-Type': CONTENT_TYPE_APP_JSON}, content='test-content-type')
    def test_authorized_content_type(self):
        request = DummyRequest(scheme='http', matchdict={'service_name': 'test-service'})
        response = owsproxy_view(request)
        assert isinstance(response, Response), "new valid response from proxy should be returned, not the dummy one"
        # status code, content and headers should be passed down from request's response call,
        # this ensure we went through the whole function without error
        assert response.status_code == 201
        assert response.content_type == CONTENT_TYPE_APP_JSON
        assert response.text == 'test-content-type'

    @mock_servicestore_factory()
    @mock_requests_response(code=202, headers={'Content-Type': CONTENT_TYPE_APP_XML}, content='test-host')
    def test_unauthorized_host_empty_config(self):
        owsproxy.allowed_hosts = []  # empty config should not cause any filtering
        request = DummyRequest(scheme='http', matchdict={'service_name': 'test-service'})
        response = owsproxy_view(request)
        assert isinstance(response, Response), "new valid response from proxy should be returned, not the dummy one"
        # status code, content and headers should be passed down from request's response call,
        # this ensure we went through the whole function without error
        assert response.status_code == 202
        assert response.content_type == CONTENT_TYPE_APP_XML
        assert response.text == 'test-host'

    @mock_servicestore_factory()
    @mock_requests_response(code=200, headers={'Content-Type': CONTENT_TYPE_APP_XML}, content='test-host')
    def test_unauthorized_host_with_config(self):
        owsproxy.allowed_hosts = ['allowed-test-host']
        test_host = 'dummy-test'
        request = DummyRequest(scheme='http', host=test_host, matchdict={'service_name': 'test-service'})
        response = owsproxy_view(request)
        assert isinstance(response, OWSAccessUnauthorized)
        assert test_host in response.message

    @mock_servicestore_factory(purl='http://test-public/wps', url='http://test-private:9000')
    @mock_requests_response(code=200, headers={'Content-Type': CONTENT_TYPE_APP_JSON}, content='test-host')
    def test_authorized_host(self):
        test_host = 'dummy-test'
        owsproxy.allowed_hosts = [test_host]   # now a valid host, should be allowed
        request = DummyRequest(scheme='http', host=test_host, matchdict={'service_name': 'test-service'})
        response = owsproxy_view(request)
        # status code, content and headers should be passed down from request's response call,
        # this ensure we went through the whole function without error
        assert response.status_code == 200
        assert response.content_type == CONTENT_TYPE_APP_JSON
        assert response.text == 'test-host'

    @mock_servicestore_factory(purl='http://test-public/wps', url='http://test-private:9000')
    @mock_requests_response(code=200, headers={'Content-Type': CONTENT_TYPE_APP_XML},
                            content='<xml><url>http://test-private:9000</url></xml>')
    def test_unauthorized_host_empty_config(self):
        request = DummyRequest(scheme='http', matchdict={'service_name': 'test-service'})
        response = owsproxy_view(request)
        assert isinstance(response, Response), "new valid response from proxy should be returned, not the dummy one"
        # status code, content and headers should be passed down from request's response call,
        # this ensure we went through the whole function without error
        assert response.status_code == 200
        assert response.content_type == CONTENT_TYPE_APP_XML
        # private URL should have been replaced by public one
        assert 'http://test-private:9000' not in response.text
        assert 'http://test-public/wps' in response.text
