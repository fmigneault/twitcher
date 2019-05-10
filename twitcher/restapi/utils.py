from twitcher.formats import CONTENT_TYPE_APP_JSON
from twitcher.owsexceptions import OWSException
from twitcher.utils import get_twitcher_url, get_settings, get_header
from pyramid.httpexceptions import HTTPServerError
from pyramid.settings import asbool
from typing import TYPE_CHECKING
import logging
if TYPE_CHECKING:
    from twitcher.typedefs import AnySettingsContainer  # noqa: F401
    from typing import AnyStr, Optional                 # noqa: F401
    from pyramid.request import Request                 # noqa: F401
    from pyramid.response import Response               # noqa: F401
    from pyramid.httpexceptions import HTTPException    # noqa: F401
LOGGER = logging.getLogger("TWITCHER")


def restapi_enabled(container):
    # type: (AnySettingsContainer) -> bool
    settings = get_settings(container)
    return asbool(settings.get('twitcher.restapi', True))


def restapi_base_path(container):
    # type: (AnySettingsContainer) -> AnyStr
    settings = get_settings(container)
    return settings.get('twitcher.restapi_path', '').rstrip('/').strip()


def restapi_base_url(container):
    # type: (AnySettingsContainer) -> AnyStr
    twitcher_url = get_twitcher_url(container)
    restapi_path = restapi_base_path(container)
    return twitcher_url + restapi_path


def get_cookie_headers(headers):
    try:
        return dict(Cookie=headers['Cookie'])
    except KeyError:  # No cookie
        return {}


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
