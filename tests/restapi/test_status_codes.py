import pytest
import unittest
# use 'Web' prefix to avoid pytest to pick up these classes and throw warnings
from webtest import TestApp as WebTestApp
from twitcher.restapi.schemas import (
    api_frontpage_uri,
    api_swagger_ui_uri,
    api_swagger_json_uri,
    api_versions_uri,
)
from twitcher.formats import CONTENT_TYPE_APP_JSON
from tests.utils import setup_config_with_mongodb, get_test_twitcher_config
from twitcher import main
from pyramid import testing

public_routes = [
    api_frontpage_uri,
    api_swagger_ui_uri,
    api_swagger_json_uri,
    api_versions_uri,
]
unauthorized_routes = [

]
forbidden_routes = [

]
not_found_routes = [
    '/not-found',
    '/services/not-found',
]
method_not_allowed_routes = [

]
not_acceptable_routes = [

]


@pytest.mark.mongo
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

    def setUp(self):
        config = testing.setUp()
        config = get_test_twitcher_config(config)
        config = setup_config_with_mongodb(config)
        self.app = main({}, **config.registry.settings)
        self.testapp = WebTestApp(self.app)

    def execute_test_status(self, code, routes):
        for uri in routes:
            resp = self.testapp.get(uri, expect_errors=True, headers=self.headers)
            assert code == resp.status_code, 'route {} did not return {}'.format(uri, code)

    @pytest.mark.skipif(not public_routes, reason="not routes defined")
    def test_200(self):
        self.execute_test_status(200, public_routes)

    @pytest.mark.skipif(not public_routes, reason="not routes defined")
    def test_401(self):
        self.execute_test_status(401, unauthorized_routes)

    @pytest.mark.skipif(not public_routes, reason="not routes defined")
    def test_403(self):
        self.execute_test_status(403, forbidden_routes)

    @pytest.mark.skipif(not public_routes, reason="not routes defined")
    def test_404(self):
        self.execute_test_status(404, not_found_routes)

    @pytest.mark.skipif(not public_routes, reason="not routes defined")
    def test_405(self):
        self.execute_test_status(405, method_not_allowed_routes)

    @pytest.mark.skipif(not public_routes, reason="not routes defined")
    def test_406(self):
        self.execute_test_status(406, not_acceptable_routes)
