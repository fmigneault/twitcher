"""
Utility methods for various TestCase setup operations.
"""
from twitcher.tokengenerator import tokengenerator_factory
from twitcher.adapter import TWITCHER_ADAPTER_DEFAULT, servicestore_factory, tokenstore_factory
from twitcher.datatype import Service
from twitcher.utils import get_settings
from twitcher.exceptions import ServiceNotFound
from twitcher.warning import MissingParameterWarning, UnsupportedOperationWarning
from configparser import ConfigParser
from pyramid import testing
from pyramid.response import Response
from webtest import TestApp
from typing import TYPE_CHECKING
import warnings
import mock
import os
if TYPE_CHECKING:
    from twitcher.store.mongodb import MongodbServiceStore
    from twitcher.datatype import AccessToken
    from twitcher.typedefs import AnySettingsContainer, SettingsType
    from typing import Any, AnyStr, Dict, Optional
    from pyramid.config import Configurator
    from pyramid.registry import Registry


def ignore_wps_warnings(test_case):
    """Decorator that eliminates WPS related warnings during test execution logging."""
    def do_test(self, *args, **kwargs):
        with warnings.catch_warnings():
            for warn in [MissingParameterWarning, UnsupportedOperationWarning]:
                for msg in ["Parameter 'request*", "Parameter 'service*"]:
                    warnings.filterwarnings(action="ignore", message=msg, category=warn)
            test_case(self, *args, **kwargs)
    return do_test


def get_settings_from_config_ini(config_ini_path=None, ini_section_name='app:main'):
    # type: (Optional[AnyStr], Optional[AnyStr]) -> SettingsType
    parser = ConfigParser()
    parser.read([config_ini_path or get_default_config_ini_path()])
    settings = dict(parser.items(ini_section_name))
    return settings


def get_default_config_ini_path():
    # type: () -> AnyStr
    return os.path.expanduser('~/birdhouse/etc/twitcher/twitcher.ini')


def setup_config_from_settings(container=None):
    # type: (Optional[AnySettingsContainer]) -> Configurator
    settings = get_settings(container) if container else {}
    config = testing.setUp(settings=settings)
    return config


def setup_config_from_ini(config_ini_file_path=None):
    # type: (Optional[AnyStr]) -> Configurator
    config_ini_file_path = config_ini_file_path or get_default_config_ini_path()
    settings = get_settings_from_config_ini(config_ini_file_path, 'app:main')
    config = testing.setUp(settings=settings)
    return config


def setup_config_with_mongodb(container=None):
    # type: (Optional[AnySettingsContainer]) -> Configurator
    settings = get_settings(container) if container else {}
    settings.update({
        'mongodb.host': '127.0.0.1',
        'mongodb.port': '27027',
        'mongodb.db_name': 'twitcher_test'
    })
    config = testing.setUp(settings=settings)
    return config


def setup_mongodb_tokenstore(container):
    # type: (AnySettingsContainer) -> AccessToken
    """
    Setup store using mongodb and get a token from it.
    Database Will be enforced if not configured properly.
    """
    store = tokenstore_factory(container)
    generator = tokengenerator_factory(container)
    store.clear_tokens()
    access_token = generator.create_access_token()
    store.save_token(access_token)
    return access_token.token


def setup_mongodb_servicestore(container):
    # type: (AnySettingsContainer) -> MongodbServiceStore
    """Setup store using mongodb, will be enforced if not configured properly."""
    config = setup_config_with_mongodb(container)
    store = servicestore_factory(config)  # type: MongodbServiceStore
    store.clear_services()
    return store


class DummyMongo(object):
    pass


# TODO:
#   we should remove all 'MemoryStore' and generic 'Store' implementations to use similar mock method
#   this way we make sure that we evaluate real application code (except the specific mock) and don't
#   introduce variations directly in the code only for testing purposes
def mock_mongodb(test_case):
    """
    Decorator that mocks the call to :func:`twitcher.db.mongodb` with minimal properties to allow non-breaking
    code execution when no actual connection is required.
    (ie: avoids errors during configuration loading and class instantiations)
    """
    def call_mongodb(*call_args, **call_kwargs):
        return DummyMongo()

    def do_test(self, *args, **kwargs):
        with mock.patch('twitcher.db.mongodb', side_effect=call_mongodb):
            test_case(self, *args, **kwargs)
    return do_test


def get_test_twitcher_config(config=None, settings_override=None):
    # type: (Optional[Configurator], Optional[SettingsType]) -> Configurator
    if not config:
        # default db required if none specified by config
        config = setup_config_from_settings()
    if 'twitcher.adapter' not in config.registry.settings:
        config.registry.settings['twitcher.adapter'] = TWITCHER_ADAPTER_DEFAULT
    config.registry.settings['twitcher.url'] = "https://localhost"
    config.registry.settings['twitcher.rpcinterface'] = False
    if settings_override:
        config.registry.settings.update(settings_override)
    # create the test application
    config.include('twitcher.restapi')
    config.include('twitcher.rpcinterface')
    config.include('twitcher.tweens')
    return config


def get_test_twitcher_app(config=None, settings_override=None):
    # type: (Optional[Configurator], Optional[SettingsType]) -> TestApp
    config = get_test_twitcher_config(config=config, settings_override=settings_override)
    config.scan()
    return TestApp(config.make_wsgi_app())


def get_settings_from_testapp(testapp):
    # type: (TestApp) -> Dict
    settings = {}
    if hasattr(testapp.app, 'registry'):
        settings = testapp.app.registry.settings or {}
    return settings


class Null(object):
    pass


def get_setting(env_var_name, app=None, setting_name=None):
    # type: (AnyStr, Optional[TestApp], Optional[AnyStr]) -> Any
    val = os.getenv(env_var_name, Null())
    if not isinstance(val, Null):
        return val
    if app:
        val = app.extra_environ.get(env_var_name, Null())
        if not isinstance(val, Null):
            return val
        if setting_name:
            val = app.extra_environ.get(setting_name, Null())
            if not isinstance(val, Null):
                return val
            settings = get_settings_from_testapp(app)
            if settings:
                val = settings.get(setting_name, Null())
                if not isinstance(val, Null):
                    return val
    return Null()


def init_twitcher_service(registry):
    # type: (Registry) -> None
    service_store = servicestore_factory(registry)
    service_store.save_service(Service({
        'type': '',
        'name': 'twitcher',
        'url': 'http://localhost/ows/proxy/twitcher',
        'public': True
    }))


def dummy_servicestore_factory(**kwargs):
    kwargs.setdefault('url', 'http://localhost:9000/wps')
    kwargs.setdefault('name', 'test-service')
    service = Service(**kwargs)

    class DummyServiceStore(object):
        def fetch_by_name(self, *f_args, **f_kwargs):
            name = f_kwargs.get('name', f_args[0])
            if name == service.name:
                return service
            raise ServiceNotFound("mock: service '{!s}' not found".format(name))

    return DummyServiceStore()


def mock_servicestore_factory(**mock_kwargs):
    """
    Decorator that mocks any call to :func:`twitcher.store.servicestore_factory` by overriding it with
    :func:`dummy_service_store_factory`. This dummy instance provides a :class:`twitcher.datatype.Service`
    instantiated with provided ``mock_kwargs`` (ie: service is created with provided attributes).

    The real :func:`twitcher.store.servicestore_factory` parameters during call are ignored.

    .. seealso::
        :class:`twitcher.datatype.Service` for supported attributes of the service to be generated.
    """
    def servicestore_factory_call(*call_args, **call_kwargs):
        return dummy_servicestore_factory(**mock_kwargs)

    def decorator(test_case):
        def do_test(self, *args, **kwargs):
            with mock.patch("twitcher.owsproxy.servicestore_factory", side_effect=servicestore_factory_call):
                test_case(self, *args, **kwargs)
        return do_test
    return decorator


class DummyResponse(Response):
    """
    Response returned by :func:`mock_requests_response` when corresponding mocked request function is called.
    Specified arguments are used to generated the desired response from the call.

    Provides some patches of missing definitions/attributes of :class:`Response` when not generated by a real request.
    """
    def __init__(self, *args, **kwargs):
        self._dummy_kwargs = kwargs
        super(DummyResponse, self).__init__()

        self.status_code = self._get_code()
        if 'headers' in kwargs:
            for h, v in kwargs['headers'].items():
                self.headers[h] = v

    def _get_code(self):
        return self._dummy_kwargs.get(
            'code', self._dummy_kwargs.get(
                'status', self._dummy_kwargs.get(
                    'status_code', 200)))

    def ok(self):
        return 200 >= self._get_code() < 400

    @property
    def content(self):
        return self._dummy_kwargs.get('content', '')


def mock_requests_response(mock_call="requests.request", *mock_args, **mock_kwargs):
    """
    Decorator that mocks a `request` callable (default :func:`requests.request`) and returns a :class:`DummyResponse`
    instantiated with provided ``mock_args`` and ``mock_kwargs``.

    The real `request`'s ``args`` and ``kwargs`` are ignored.

    .. seealso::
        :class:`tests.utils.DummyResponse` for supported parameters of the generated response.
    """
    def request_callable(*request_args, **request_kwargs):
        return DummyResponse(*mock_args, **mock_kwargs)

    def decorator(test_case):
        def do_test(self, *args, **kwargs):
            with mock.patch(mock_call, side_effect=request_callable):
                test_case(self, *args, **kwargs)
        return do_test
    return decorator
