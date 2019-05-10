from twitcher.owsexceptions import OWSException, OWSNoApplicableCode, OWSNotImplemented
from twitcher.adapter import get_adapter_factory
from pyramid.settings import asbool
from pyramid.tweens import EXCVIEW, INGRESS
from pyramid.httpexceptions import HTTPException, HTTPInternalServerError


import logging
logger = logging.getLogger(__name__)


def includeme(config):
    settings = config.registry.settings

    if asbool(settings.get('twitcher.ows_security', True)):
        logger.info('Add OWS security tween')
        config.add_tween(OWS_SECURITY, under=EXCVIEW)

    # using 'INGRESS' to run `twitcher.restapi` views that fix HTTP code before OWS response,
    # using 'EXCVIEW' does the other way around
    config.add_tween(OWS_RESPONSE, under=INGRESS)


# noinspection PyUnusedLocal
def ows_response_tween_factory(handler, registry):
    """
    A tween factory which produces a tween which transforms common
    exceptions into OWS specific exceptions.
    """

    def ows_response_tween(request):
        try:
            return handler(request)
        except HTTPException as err:
            logger.debug("http exception -> ows exception response.")
            # Use the same json formatter than OWSException
            err._json_formatter = OWSException.json_formatter
            r_err = err
        except OWSException as err:
            logger.debug('direct ows exception response')
            logger.exception("Raised exception: [{!r}]\nReturned exception: {!r}".format(err, err))
            r_err = err
        except NotImplementedError as err:
            logger.debug('not implemented error -> ows exception response')
            r_err = OWSNotImplemented(str(err))
        except Exception as err:
            logger.debug("unhandled {!s} exception -> ows exception response".format(type(err).__name__))
            r_err = OWSException(detail=str(err), status=HTTPInternalServerError)
        logger.exception("Raised exception: [{!r}]\nReturned exception: {!r}".format(err, r_err))
        return r_err

    return ows_response_tween


def ows_security_tween_factory(handler, registry):
    """
    A tween factory which produces a tween which raises an exception
    if access to OWS service is not allowed.
    """
    adapter = get_adapter_factory(registry)
    security = adapter.owssecurity_factory(registry)

    def ows_security_tween(request):
        try:
            security.check_request(request)
            return handler(request)
        except OWSException as err:
            logger.exception("security check failed.")
            # Use the same json formatter than OWSException
            err._json_formatter = OWSException.json_formatter
            return err
        except Exception as err:
            logger.exception("unknown error")
            return OWSNoApplicableCode("{}".format(err))

    return ows_security_tween


OWS_RESPONSE = 'twitcher.tweens.ows_response_tween_factory'
OWS_SECURITY = 'twitcher.tweens.ows_security_tween_factory'
