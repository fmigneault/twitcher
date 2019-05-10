from twitcher.__meta__ import __version__ as twitcher_version
from twitcher.adapter import get_adapter_factory
from twitcher.db import get_database_type
from twitcher.formats import CONTENT_TYPE_APP_JSON
from twitcher.utils import get_settings, get_header
from twitcher.restapi import schemas as s
from twitcher.restapi.colander_one_of import CustomTypeConversionDispatcher
from twitcher.restapi.utils import restapi_base_url, restapi_base_path
from twitcher.owsexceptions import OWSException
from twitcher.owsproxy import owsproxy_base_url
from cornice_swagger import CorniceSwagger
from cornice.service import get_services
from pyramid.authentication import IAuthenticationPolicy, Authenticated
from pyramid.httpexceptions import HTTPUnauthorized, HTTPForbidden, HTTPNotFound, HTTPMethodNotAllowed, HTTPServerError
from pyramid.exceptions import PredicateMismatch
from pyramid.renderers import render_to_response
from pyramid.settings import asbool
from urllib.parse import urlparse
from typing import TYPE_CHECKING
import logging
import os
if TYPE_CHECKING:
    from twitcher.typedefs import JSON
    from typing import AnyStr, Optional
    from pyramid.request import Request
    from pyramid.response import Response
    from pyramid.httpexceptions import HTTPException
LOGGER = logging.getLogger(__name__)


@s.api_frontpage_service.get(tags=[s.TagAPI], renderer='json',
                             schema=s.FrontpageEndpoint(), response_schemas=s.get_api_frontpage_responses)
def api_frontpage(request):
    # type: (Request) -> JSON
    """Frontpage of Twitcher REST API."""

    settings = get_settings(request)
    twitcher_db = get_database_type(settings)
    twitcher_api = asbool(settings.get('twitcher.restapi'))
    twitcher_api_url = restapi_base_url(settings) if twitcher_api else None
    twitcher_api_doc = twitcher_api_url + s.api_swagger_ui_uri if twitcher_api else None
    twitcher_proxy = asbool(settings.get('twitcher.ows_proxy'))
    twitcher_proxy_url = owsproxy_base_url(settings) if twitcher_proxy else None
    twitcher_adapter = get_adapter_factory(settings)

    return {
        'message': 'Twitcher Information',
        'adapter': twitcher_adapter.describe_adapter(),
        'database': twitcher_db,
        'parameters': [
            {'name': 'api',
             'enabled': twitcher_api,
             'url': twitcher_api_url,
             'doc': twitcher_api_doc},
            {'name': 'proxy',
             'enabled': twitcher_proxy,
             'url': twitcher_proxy_url},
        ]
    }


@s.api_versions_service.get(tags=[s.TagAPI], renderer='json',
                            schema=s.VersionsEndpoint(), response_schemas=s.get_api_versions_responses)
def api_versions(request):
    # type: (Request) -> JSON
    """Twitcher versions information."""
    from twitcher.adapter import get_adapter_factory
    adapter_info = get_adapter_factory(request.registry.settings).describe_adapter()
    adapter_info['type'] = 'adapter'
    twitcher_info = {'name': 'Twitcher', 'version': twitcher_version, 'type': 'api'}
    return {'versions': [twitcher_info, adapter_info]}


@s.api_swagger_json_service.get(tags=[s.TagAPI], renderer='json',
                                schema=s.SwaggerJSONEndpoint(), response_schemas=s.get_api_swagger_json_responses)
def api_swagger_json(request, use_docstring_summary=True):
    # type: (Request, bool) -> JSON
    """Twitcher REST API schema generation in JSON format."""
    CorniceSwagger.type_converter = CustomTypeConversionDispatcher
    swagger = CorniceSwagger(get_services())
    # function docstrings are used to create the route's summary in Swagger-UI
    swagger.summary_docstrings = use_docstring_summary
    swagger_base_spec = {'schemes': [request.scheme]}

    # obtain 'server' host and api-base-path, which doesn't correspond necessarily to the app's host and path
    # ex: 'server' adds '/twitcher' with proxy redirect before API routes
    twitcher_server_url = os.getenv('TWITCHER_URL')
    LOGGER.debug("Request URL:  {}".format(request.url))
    LOGGER.debug("TWITCHER_URL: {}".format(twitcher_server_url))
    if twitcher_server_url:
        twitcher_parsed_url = urlparse(twitcher_server_url)
        swagger_base_spec['host'] = twitcher_parsed_url.netloc
        swagger_base_path = twitcher_parsed_url.path
    else:
        swagger_base_spec['host'] = request.host
        swagger_base_path = s.api_frontpage_uri
    swagger.swagger = swagger_base_spec
    return swagger.generate(title=s.API_TITLE, version=twitcher_version, base_path=swagger_base_path)


@s.api_swagger_ui_service.get(tags=[s.TagAPI],
                              schema=s.SwaggerUIEndpoint(), response_schemas=s.get_api_swagger_ui_responses)
def api_swagger_ui(request):
    """Twitcher REST API swagger-ui schema documentation (this page)."""
    json_path = restapi_base_path(request.registry.settings) + s.api_swagger_json_uri
    json_path = json_path.lstrip('/')   # if path starts by '/', swagger-ui doesn't find it on remote
    data_mako = {'api_title': s.API_TITLE, 'api_swagger_json_path': json_path}
    return render_to_response('templates/swagger_ui.mako', data_mako, request=request)


def ows_json_format(function):
    """Decorator that adds additional detail in the response's JSON body if this is the returned content-type."""
    def format_response_details(response, request):
        # type: (Response, Request) -> HTTPException
        http_response = function(request)
        http_headers = get_header("Content-Type", http_response.headers) or []
        req_headers = get_header("Accept", request.headers) or []
        if any([CONTENT_TYPE_APP_JSON in http_headers, CONTENT_TYPE_APP_JSON in req_headers]):
            body = OWSException.json_formatter(http_response.status, response.message or "",
                                               http_response.title, request.environ)
            body["detail"] = get_request_info(request)
            http_response._json = body
        if http_response.status_code != response.status_code:
            raise http_response  # re-raise if code was fixed
        return http_response
    return format_response_details


@ows_json_format
def not_found_or_method_not_allowed(request):
    """
    Overrides the default is HTTPNotFound [404] by appropriate HTTPMethodNotAllowed [405] when applicable.

    Not found response can correspond to underlying process operation not finding a required item, or a completely
    unknown route (path did not match any existing API definition).
    Method not allowed is more specific to the case where the path matches an existing API route, but the specific
    request method (GET, POST, etc.) is not allowed on this path.

    Without this fix, both situations return [404] regardless.
    """
    # noinspection PyProtectedMember
    if isinstance(request.exception, PredicateMismatch) and request.method not in request.exception._safe_methods:
        http_err = HTTPMethodNotAllowed
        http_msg = ""  # auto-generated by HTTPMethodNotAllowed
    else:
        http_err = HTTPNotFound
        http_msg = str(request.exception)
    return http_err(http_msg)


@ows_json_format
def unauthorized_or_forbidden(request):
    """
    Overrides the default is HTTPForbidden [403] by appropriate HTTPUnauthorized [401] when applicable.

    Unauthorized response is for restricted user access according to credentials and/or authorization headers.
    Forbidden response is for operation refused by the underlying process operations.

    Without this fix, both situations return [403] regardless.

    .. seealso::
        http://www.restapitutorial.com/httpstatuscodes.html
    """
    authn_policy = request.registry.queryUtility(IAuthenticationPolicy)
    if authn_policy:
        principals = authn_policy.effective_principals(request)
        if Authenticated not in principals:
            return HTTPUnauthorized("Unauthorized access to this resource.")
    return HTTPForbidden("Forbidden operation under this resource.")


def get_request_info(request, detail=None):
    # type: (Request, Optional[AnyStr]) -> JSON
    """Provided additional response details based on the request and execution stack on failure."""
    content = {u'route': str(request.upath_info), u'url': str(request.url), u'method': request.method}
    if isinstance(detail, str):
        content.update({"detail": detail})
    if hasattr(request, "exception"):
        # handle error raised simply by checking for 'json' property in python 3 when body is invalid
        has_json = False
        try:
            has_json = hasattr(request.exception, "json")
        except ValueError:  # decode error
            pass
        if has_json and isinstance(request.exception.json, dict):
            content.update(request.exception.json)
        elif isinstance(request.exception, HTTPServerError) and hasattr(request.exception, "message"):
            content.update({u"exception": str(request.exception.message)})
    elif hasattr(request, "matchdict"):
        if request.matchdict is not None and request.matchdict != "":
            content.update(request.matchdict)
    return content
