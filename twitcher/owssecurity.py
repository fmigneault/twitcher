import tempfile

from twitcher.exceptions import AccessTokenNotFound, ServiceNotFound
from twitcher.owsexceptions import OWSAccessForbidden, OWSInvalidParameterValue
from twitcher.store import AccessTokenStore, ServiceStore
from twitcher import datatype
from twitcher.utils import path_elements, parse_service_name
from twitcher.owsrequest import OWSRequest
from twitcher.esgf import fetch_certificate, ESGF_CREDENTIALS

import logging
LOGGER = logging.getLogger("TWITCHER")


def owssecurity_factory(request):
    return OWSSecurity(AccessTokenStore(request), ServiceStore(request))


def verify_cert(request):
    if not request.headers.get('X-Ssl-Client-Verify', '') == 'SUCCESS':
        raise OWSAccessForbidden("A valid X.509 client certificate is needed.")


class OWSSecurity(object):

    def __init__(self, tokenstore, servicestore):
        self.tokenstore = tokenstore
        self.servicestore = servicestore

    def get_token_param(self, request):
        token = None
        if 'token' in request.params:
            token = request.params['token']   # in params
        elif 'access_token' in request.params:
            token = request.params['access_token']   # in params
        elif 'Access-Token' in request.headers:
            token = request.headers['Access-Token']  # in header
        else:  # in path
            elements = path_elements(request.path)
            if len(elements) > 1:  # there is always /ows/
                token = elements[-1]   # last path element
        return token

    def verify_access(self, request, service):
        # TODO: public service access handling is confusing.
        try:
            if service.auth == 'cert':
                verify_cert(request)
            else:  # token
                self._verify_access_token(request)
        except OWSAccessForbidden:
            if not service.public:
                raise

    def _verify_access_token(self, request):
        try:
            # try to get access_token ... if no access restrictions then don't complain.
            token = self.get_token_param(request)
            access_token = self.tokenstore.fetch_by_token(token)
            if access_token.is_expired():
                raise OWSAccessForbidden("Access token is expired.")
        except AccessTokenNotFound:
            raise OWSAccessForbidden("Access token is required to access this service.")

    def check_request(self, request):
        protected_path = request.registry.settings.get('twitcher.ows_proxy_protected_path ', '/ows')
        if request.path.startswith(protected_path):
            # TODO: refactor this code
            try:
                service_name = parse_service_name(request.path, protected_path)
                service = self.servicestore.fetch_by_name(service_name)
                if service.public is True:
                    LOGGER.warning('public access for service %s', service_name)
            except ServiceNotFound:
                # TODO: why not raising an exception?
                service = datatype.Service(name=service_name, url='unregistered', public=False, auth='token')
                LOGGER.warning("Service not registered.")
            ows_request = OWSRequest(request)
            if not ows_request.service_allowed():
                raise OWSInvalidParameterValue(
                    "service %s not supported" % ows_request.service, value="service")
            if not ows_request.public_access():
                self.verify_access(request, service)
