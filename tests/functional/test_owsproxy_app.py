import pytest
import webtest

from .. common import FunctionalTest, WPS_TEST_SERVICE


class OWSProxyAppTest(FunctionalTest):

    def setUp(self):
        super(OWSProxyAppTest, self).setUp()

        self.config.include('twitcher.owsproxy')
        self.config.include('twitcher.tweens')
        self.app = webtest.TestApp(self.config.make_wsgi_app())

    @pytest.mark.online
    def test_getcaps(self):
        resp = self.app.get('/ows/proxy/wps?service=wps&request=getcapabilities')
        assert resp.status_code == 200
        assert resp.content_type == 'text/xml'
        resp.mustcontain('</wps:Capabilities>')

    @pytest.mark.online
    def test_describeprocess(self):
        resp = self.app.get(
            '/ows/proxy/wps?service=wps&request=describeprocess&version=1.0.0&identifier=dummyprocess')
        assert resp.status_code == 200
        assert resp.content_type == 'text/xml'
        resp.mustcontain('</wps:ProcessDescriptions>')

    @pytest.mark.skip(reason="fix token access")
    @pytest.mark.online
    def test_execute_allowed(self):
        url = "/ows/proxy/wps?service=wps&request=execute&version=1.0.0&identifier=hello&datainputs=name=tux&access_token=ce141debe0fb4ec2836567c38e8b4592"  # noqa
        resp = self.app.get(url)
        assert resp.status_code == 200
        assert resp.content_type == 'text/xml'
        print(resp.body)
        resp.mustcontain(
            '<wps:ProcessSucceeded>PyWPS Process Say Hello finished</wps:ProcessSucceeded>')

    @pytest.mark.skip(reason="fix access forbidden")
    @pytest.mark.online
    def test_execute_not_allowed(self):
        resp = self.app.get('/ows/proxy/wps?service=wps&request=execute&version=1.0.0&identifier=dummyprocess')
        assert resp.status_code == 200
        assert resp.content_type == 'text/xml'
        print(resp.body)
        resp.mustcontain('<Exception exceptionCode="NoApplicableCode" locator="AccessForbidden">')
