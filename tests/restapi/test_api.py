from pyramid.httpexceptions import HTTPFound
from twitcher.swagger.schemas import (
    restapi_frontpage_uri,
    restapi_versions_uri,
    swagger_ui_uri,
    swagger_json_uri,
    swagger_json_service,
    API_TITLE,
    FrontpageSchema,
    VersionsSchema,
)
from twitcher.adapter import TWITCHER_ADAPTER_DEFAULT
from tests.utils import get_test_twitcher_app, get_test_twitcher_config, get_settings_from_testapp, mock_mongodb
import colander
import unittest
import mock
import os


class GenericApiRoutesTestCase(unittest.TestCase):

    @classmethod
    @mock_mongodb
    def setUpClass(cls):
        settings = {'twitcher.adapter': TWITCHER_ADAPTER_DEFAULT}
        config = get_test_twitcher_config()
        cls.testapp = get_test_twitcher_app(config=config, settings_override=settings)
        cls.json_app = 'application/json'
        cls.json_headers = {'Accept': cls.json_app, 'Content-Type': cls.json_app}

    def test_frontpage_format(self):
        resp = self.testapp.get(restapi_frontpage_uri, headers=self.json_headers)
        assert 200 == resp.status_code
        try:
            FrontpageSchema().deserialize(resp.json)
        except colander.Invalid as ex:
            self.fail("expected valid response format as defined in schema [{!s}]".format(ex))

    def test_version_format(self):
        resp = self.testapp.get(restapi_versions_uri, headers=self.json_headers)
        assert 200 == resp.status_code
        try:
            VersionsSchema().deserialize(resp.json)
        except colander.Invalid as ex:
            self.fail("expected valid response format as defined in schema [{!s}]".format(ex))

    def test_swagger_api_format(self):
        resp = self.testapp.get(swagger_ui_uri)
        assert 200 == resp.status_code
        assert "<title>{}</title>".format(API_TITLE) in resp.text

        resp = self.testapp.get(swagger_json_uri, headers=self.json_headers)
        assert 200 == resp.status_code
        assert 'tags' in resp.json
        assert 'info' in resp.json
        assert 'host' in resp.json
        assert 'paths' in resp.json
        assert 'swagger' in resp.json
        assert 'basePath' in resp.json


class AlternativeProxyBaseUrlApiRoutesTestCase(unittest.TestCase):

    # noinspection PyUnusedLocal
    @staticmethod
    def redirect_api_view(request):
        return HTTPFound(location=swagger_json_service.path)

    @classmethod
    @mock_mongodb
    def setUpClass(cls):
        # derived path for testing simulated server proxy pass
        cls.proxy_api_base_path = '/twitcher/rest'
        cls.proxy_api_base_name = swagger_json_service.name + '_proxy'

        # create redirect view to simulate the server proxy pass
        settings = {'twitcher.adapter': TWITCHER_ADAPTER_DEFAULT}
        config = get_test_twitcher_config(settings_override=settings)
        config.add_route(name=cls.proxy_api_base_name, path=cls.proxy_api_base_path)
        config.add_view(cls.redirect_api_view, route_name=cls.proxy_api_base_name)

        cls.testapp = get_test_twitcher_app(config)
        cls.json_app = 'application/json'
        cls.json_headers = {'Accept': cls.json_app, 'Content-Type': cls.json_app}

    def test_swagger_api_request_base_path_proxied(self):
        """
        Validates that Swagger JSON properly redefines the host/path to test live requests on Swagger UI
        when the app's URI results from a proxy pass redirect under another route.
        """
        # setup environment that would define the new twitcher location for the proxy pass
        twitcher_server_host = get_settings_from_testapp(self.testapp).get('twitcher.url')
        twitcher_server_url = twitcher_server_host + self.proxy_api_base_path
        with mock.patch.dict('os.environ', {'TWITCHER_URL': twitcher_server_url}):
            resp = self.testapp.get(self.proxy_api_base_path, headers=self.json_headers)
            resp = resp.follow()
            assert 200 == resp.status_code
            assert self.proxy_api_base_path not in resp.json['host']
            assert resp.json['basePath'] == self.proxy_api_base_path

            # validate that swagger UI still renders and has valid URL
            resp = self.testapp.get(swagger_ui_uri)
            assert 200 == resp.status_code
            assert "<title>{}</title>".format(API_TITLE) in resp.text

    def test_swagger_api_request_base_path_original(self):
        """
        Validates that Swagger JSON properly uses the original host/path to test live requests on Swagger UI
        when the app's URI results direct route access.
        """
        resp = self.testapp.get(swagger_ui_uri)
        assert 200 == resp.status_code
        assert "<title>{}</title>".format(API_TITLE) in resp.text

        # ensure that environment that would define the twitcher location is not defined for local app
        with mock.patch.dict('os.environ'):
            os.environ.pop('TWITCHER_URL', None)
            resp = self.testapp.get(self.proxy_api_base_path, headers=self.json_headers)
            resp = resp.follow()
            assert 200 == resp.status_code
            assert self.proxy_api_base_path not in resp.json['host']
            assert resp.json['basePath'] == restapi_frontpage_uri

            # validate that swagger UI still renders and has valid URL
            resp = self.testapp.get(swagger_ui_uri)
            assert 200 == resp.status_code
            assert "<title>{}</title>".format(API_TITLE) in resp.text
