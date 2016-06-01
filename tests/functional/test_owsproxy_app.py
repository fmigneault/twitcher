import unittest
from nose.plugins.attrib import attr
from nose import SkipTest
from webtest import TestApp
from pyramid import testing
from tests.functional.common import setup_with_db, setup_tokenstore

from twitcher.registry import service_registry_factory

class OWSProxyAppTest(unittest.TestCase):

    def setUp(self):
        config = setup_with_db()
        self._setup_registry(config)
        config.include('twitcher.owsproxy')
        config.include('twitcher.tweens')
        self.app= TestApp(config.make_wsgi_app())
        
    def tearDown(self):
        testing.tearDown()

    def _setup_registry(self, config):
        registry = service_registry_factory(config.registry)
        registry.clear_services()
        # TODO: testing against ourselfs ... not so good
        url = "https://localhost:38083/ows/wps"
        registry.register_service(url=url, name="twitcher")

    @attr('online')
    def test_getcaps(self):
        raise SkipTest
        resp = self.app.get('/ows/proxy/twitcher?service=wps&request=getcapabilities')
        assert resp.status_code == 200
        assert resp.content_type == 'text/xml'
        resp.mustcontain('</wps:Capabilities>')

    @attr('online')
    def test_describeprocess(self):
        raise SkipTest
        resp = self.app.get('/ows/proxy/twitcher?service=wps&request=describeprocess&version=1.0.0&identifier=dummyprocess')
        assert resp.status_code == 200
        assert resp.content_type == 'text/xml'
        resp.mustcontain('</wps:ProcessDescriptions>')

    @attr('online')
    def test_execute_not_allowed(self):
        raise SkipTest
        resp = self.app.get('/ows/proxy/twitcher?service=wps&request=execute&version=1.0.0&identifier=dummyprocess')
        assert resp.status_code == 200
        assert resp.content_type == 'text/xml'
        print resp.body
        resp.mustcontain('<Exception exceptionCode="NoApplicableCode" locator="AccessForbidden">')

   
