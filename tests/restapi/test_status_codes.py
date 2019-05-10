import pytest
import unittest
# use 'Web' prefix to avoid pytest to pick up these classes and throw warnings
from webtest import TestApp as WebTestApp
from twitcher.swagger import schemas as s
from twitcher.formats import CONTENT_TYPE_APP_JSON
from twitcher.warning import UnsupportedOperationWarning
from tests.utils import setup_config_with_mongodb, get_test_twitcher_config, mock_mongodb, ignore_warnings
from twitcher import main
from pyramid import testing

public_routes = [
    s.restapi_frontpage_uri,
    s.swagger_ui_uri,
    s.swagger_json_uri,
    s.restapi_versions_uri,
    s.restapi_services_uri,
]
unauthorized_routes = [

]
forbidden_routes = [

]
not_found_routes = [
    '/not-found',           # invalid route
    '/services/not-found',  # valid route, but invalid service
]
method_not_allowed_routes = [

]
not_acceptable_routes = [

]


class StatusCodeTestCase(unittest.TestCase):
    """
    Verify that the twitcher app returns correct status codes for common cases, such as:

        - unauthorized/forbidden (difference between blocked by unauthenticated and operation not allowed respectively)
        - not found/method not allowed (difference between route non-existing and invalid request method [get,post,...])
        - unauthorized/method not allowed (difference between authentication and invalid method regardless of auth)
        - resource added
        - ok
    """

    headers = {'accept': CONTENT_TYPE_APP_JSON}

    @mock_mongodb
    def setUp(self):
        config = testing.setUp()
        config = get_test_twitcher_config(config)
        config = setup_config_with_mongodb(config)
        self.app = main({}, **config.registry.settings)
        self.testapp = WebTestApp(self.app)

    @mock_mongodb
    def execute_test_status(self, code, routes):
        for uri in routes:
            resp = self.testapp.get(uri, expect_errors=True, headers=self.headers)
            assert code == resp.status_code, 'route {} did not return {}'.format(uri, code)

    @pytest.mark.skipif(not public_routes, reason="not routes defined")
    def test_200(self):
        self.execute_test_status(200, public_routes)

    @pytest.mark.skipif(not unauthorized_routes, reason="not routes defined")
    def test_401(self):
        self.execute_test_status(401, unauthorized_routes)

    @pytest.mark.skipif(not forbidden_routes, reason="not routes defined")
    def test_403(self):
        self.execute_test_status(403, forbidden_routes)

    @pytest.mark.skipif(not not_found_routes, reason="not routes defined")
    @ignore_warnings(warning_types=UnsupportedOperationWarning)
    def test_404(self):
        self.execute_test_status(404, not_found_routes)

    @pytest.mark.skipif(not method_not_allowed_routes, reason="not routes defined")
    def test_405(self):
        self.execute_test_status(405, method_not_allowed_routes)

    @pytest.mark.skipif(not not_acceptable_routes, reason="not routes defined")
    def test_406(self):
        self.execute_test_status(406, not_acceptable_routes)
