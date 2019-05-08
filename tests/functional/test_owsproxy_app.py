import pytest
import webtest

from .. common import BaseTest, dummy_request, WPS_TEST_SERVICE

from twitcher.store import ServiceStore
from twitcher.datatype import Service


class OWSProxyAppTest(BaseTest):

    def setUp(self):
        super(OWSProxyAppTest, self).setUp()
        self.init_database()

        service_store = ServiceStore(
            dummy_request(dbsession=self.session))
        service_store.save_service(Service(name='wps', url=WPS_TEST_SERVICE))

        self.config.include('twitcher.owsproxy')
        self.config.include('twitcher.tweens')
        self.app = webtest.TestApp(self.config.make_wsgi_app())

    @pytest.mark.skip(reason="no way of currently testing this")
    @pytest.mark.online
    def test_getcaps(self):
        resp = self.app.get('/ows/proxy/wps?service=wps&request=getcapabilities')
        assert resp.status_code == 200
        assert resp.content_type == 'text/xml'
        resp.mustcontain('</wps:Capabilities>')

    @pytest.mark.skip(reason="no way of currently testing this")
    @pytest.mark.online
    def test_describeprocess(self):
        resp = self.app.get(
            '/ows/proxy/wps?service=wps&request=describeprocess&version=1.0.0&identifier=dummyprocess')
        assert resp.status_code == 200
        assert resp.content_type == 'text/xml'
        resp.mustcontain('</wps:ProcessDescriptions>')

    @pytest.mark.skip(reason="no way of currently testing this")
    @pytest.mark.online
    def test_execute_not_allowed(self):
        resp = self.app.get('/ows/proxy/wps?service=wps&request=execute&version=1.0.0&identifier=dummyprocess')
        assert resp.status_code == 200
        assert resp.content_type == 'text/xml'
        print(resp.body)
        resp.mustcontain('<Exception exceptionCode="NoApplicableCode" locator="AccessForbidden">')
