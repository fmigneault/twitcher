"""
The owsproxy is based on `papyrus_ogcproxy <https://github.com/elemoine/papyrus_ogcproxy>`_

See also: https://github.com/nive/outpost/blob/master/outpost/proxy.py
"""

from twitcher.formats import (
    CONTENT_TYPE_APP_JSON,
    CONTENT_TYPE_APP_JSON_ISO,
    CONTENT_TYPE_APP_XML,
    CONTENT_TYPE_TEXT_XML,
    CONTENT_TYPE_TEXT_XML_ISO,
    CONTENT_TYPE_TEXT_HTML,
    CONTENT_TYPE_TEXT_PLAIN,
)
from twitcher.owsproxyconfig import allowed_hosts, allowed_content_types
from twitcher.owsexceptions import OWSBadRequest, OWSAccessUnauthorized, OWSNotFound, OWSException
from twitcher.utils import replace_caps_url, replace_text_url, get_twitcher_url, get_settings
from twitcher.store import servicestore_factory
from urllib.parse import urlparse, urlencode
from pyramid.httpexceptions import HTTPException
from pyramid.settings import asbool
from pyramid.response import Response
from typing import TYPE_CHECKING
import requests
import logging
if TYPE_CHECKING:
    from twitcher.datatype import Service
    from typing import AnyStr, Optional
    from pyramid.request import Request
    from pyramid.config import Configurator
LOGGER = logging.getLogger(__name__)


# requests.models.Response defaults its chunk size to 128 bytes, which is very slow
class BufferedResponse(object):
    def __init__(self, resp):
        self.resp = resp

    def __iter__(self):
        return self.resp.iter_content(64 * 1024)


def _find_public_url(request, service):
    # type: (Request, Service) -> AnyStr
    """Returns the public URL of the service. If not configured use proxy URL."""
    if service.has_purl():
        public_url = service.purl
    else:
        public_url = request.route_url('owsproxy', service_name=service.name)
    return public_url


def _send_request(request, service, extra_path=None, request_params=None):
    # type: (Request, Service, Optional[AnyStr], Optional[AnyStr]) -> Response

    if allowed_hosts:
        host = request.host
        parsed = urlparse(host)
        if not any(h in allowed_hosts for h in [host, parsed.netloc]):
            return OWSAccessUnauthorized("Request Host is not allowed: {}".format(host))

    # TODO: fix way to build url
    url = service.url
    if extra_path:
        url += '/' + extra_path
    if request_params:
        url += '?' + request_params
    LOGGER.debug('url = %s', url)

    # forward request to target (without Host Header)
    h = dict(request.headers)
    h.pop("Host", h)
    h['Accept-Encoding'] = None

    service_type = service.type
    ssl_verify = asbool(request.registry.settings.get('twitcher.ows_proxy_ssl_verify', True))
    if service_type and (service_type.lower() != 'wps'):
        try:
            resp_iter = requests.request(method=request.method.upper(), url=url, data=request.body, headers=h,
                                         stream=True, verify=service.verify and ssl_verify)
        except Exception as e:
            return OWSAccessUnauthorized("Request failed: {}".format(e))

        # Headers meaningful only for a single transport-level connection
        hop_by_hop = ['Connection', 'Keep-Alive', 'Public', 'Proxy-Authenticate', 'Transfer-Encoding', 'Upgrade']
        return Response(app_iter=BufferedResponse(resp_iter),
                        headers={k: v for k, v in list(resp_iter.headers.items()) if k not in hop_by_hop})
    else:
        try:
            resp = requests.request(method=request.method.upper(), url=url, data=request.body, headers=h,
                                    verify=service.verify and ssl_verify)
        except Exception as e:
            return OWSAccessUnauthorized("Request failed: {}".format(e))

        if resp.ok is False:
            if 'ExceptionReport' in resp.text:
                pass
            else:
                return OWSAccessUnauthorized("Response is not ok: {}".format(resp.reason))

        # check for allowed content types
        ct = None
        # LOGGER.debug("headers=", resp.headers)
        if "Content-Type" in resp.headers:
            ct = resp.headers["Content-Type"]
            if not ct.split(";")[0] in allowed_content_types:
                msg = "Response Content-Type is not allowed: {}.".format(ct)
                LOGGER.error(msg)
                return OWSAccessUnauthorized(msg)
        else:
            # return OWSAccessFailed("Could not get content type from response.")
            LOGGER.warning("Could not get content type from response")

        # noinspection PyBroadException
        try:
            # replace urls in content by type
            if ct in [CONTENT_TYPE_APP_XML, CONTENT_TYPE_TEXT_XML, CONTENT_TYPE_TEXT_XML_ISO]:
                public_url = _find_public_url(request, service)
                # TODO: where do i need to replace urls?
                content = replace_caps_url(resp.content, public_url, service.url)
            elif ct in [CONTENT_TYPE_APP_JSON, CONTENT_TYPE_APP_JSON_ISO,
                        CONTENT_TYPE_TEXT_PLAIN, CONTENT_TYPE_TEXT_HTML]:
                public_url = _find_public_url(request, service)
                content = replace_text_url(resp.content, public_url, service.url)
            else:
                # raw content
                # TODO: is there other types to handle that should avoid leaking the private URL?
                content = resp.content
        except Exception as err:
            LOGGER.error("Error decoding content: {!r}".format(err))
            return OWSAccessUnauthorized("Could not decode content.")

        headers = {}
        if ct:
            headers["Content-Type"] = ct
        return Response(content, status=resp.status_code, headers=headers)


def owsproxy_base_path(settings):
    return settings.get('twitcher.ows_proxy_protected_path', '/ows').rstrip('/').strip()


def owsproxy_base_url(settings):
    twitcher_url = get_twitcher_url(settings)
    owsproxy_path = owsproxy_base_path(settings)
    return twitcher_url + owsproxy_path


def owsproxy_view(request):
    service_name = request.matchdict.get('service_name')
    extra_path = request.matchdict.get('extra_path')
    try:
        if not service_name:
            raise OWSBadRequest("Request failed: no service specified.")
        store = servicestore_factory(request)
        service = store.fetch_by_name(service_name)
    except (OWSException, HTTPException) as ex:
        # TODO: Store impl should raise appropriate exception like not authorized
        return ex
    except Exception as err:
        return OWSNotFound("Could not find service {0} : {1}.".format(service_name, err))
    else:
        return _send_request(request, service, extra_path, request_params=request.query_string)


def owsproxy_delegate_view(request):
    """
    Delegates owsproxy request to external twitcher service.
    """
    url = owsproxy_base_url(request.registry.settings)
    if request.matchdict.get('service_name'):
        url += '/' + request.matchdict.get('service_name')
        if request.matchdict.get('access_token'):
            url += '/' + request.matchdict.get('service_name')
    url += '?' + urlencode(request.params)
    LOGGER.debug("delegate to owsproxy: %s", url)
    # forward request to target (without Host Header)
    # h = dict(request.headers)
    # h.pop("Host", h)
    resp = requests.request(method=request.method.upper(), url=url, data=request.body,
                            headers=request.headers, verify=False)
    return Response(resp.content, status=resp.status_code, headers=resp.headers)


def includeme(config):
    from twitcher.adapter import get_adapter_factory
    get_adapter_factory(config).owsproxy_config(config)


def owsproxy_defaultconfig(config):
    # type: (Configurator) -> None
    settings = get_settings(config)
    if asbool(settings.get('twitcher.ows_proxy', True)):
        protected_path = owsproxy_base_path(settings)
        LOGGER.debug('Twitcher {}/proxy enabled.'.format(protected_path))

        config.add_route('owsproxy', protected_path + '/proxy/{service_name}')
        config.add_route('owsproxy_extra', protected_path + '/proxy/{service_name}/{extra_path:.*}')
        config.add_route('owsproxy_secured', protected_path + '/proxy/{service_name}/{access_token}')

        # use delegation mode?
        if asbool(settings.get('twitcher.ows_proxy_delegate', False)):
            LOGGER.debug('Twitcher {}/proxy delegation mode enabled.'.format(protected_path))
            config.add_view(owsproxy_delegate_view, route_name='owsproxy')
            config.add_view(owsproxy_delegate_view, route_name='owsproxy_secured')
        else:
            config.include('twitcher.config')
            # include mongodb
            # config.include('twitcher.db')
            config.add_view(owsproxy_view, route_name='owsproxy')
            config.add_view(owsproxy_view, route_name='owsproxy_secured')
            config.add_view(owsproxy_view, route_name='owsproxy_extra')
