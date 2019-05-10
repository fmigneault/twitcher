from twitcher.owsexceptions import OWSException, OWSNoApplicableCode, OWSNotImplemented, OWS_EXCEPTION_CODE_MAP
from twitcher.adapter import get_adapter_factory
from twitcher.utils import get_settings
from pyramid.settings import asbool
from pyramid.tweens import EXCVIEW
from pyramid.httpexceptions import HTTPException, HTTPInternalServerError


import logging
logger = logging.getLogger(__name__)


def includeme(config):
    settings = get_settings(config)

    # INGRESS (Request) ====> OWSResponse ====> EXCVIEW ====> (if-enabled) OWSSecurity ====> APP
    # <-------------------|<------------------|-----------|------------------------------|<--[OK]
    # <-------------------|<------------------|-----------|<---[on OWS security error]   |   n/a
    # <-------------------|<--(convert OWS)<--|----[code/exec HTTP/OWS/Python Exception anywhere]
    if asbool(settings.get('twitcher.ows_security', True)):
        logger.info('Add OWS security tween')
        config.add_tween(OWS_SECURITY, under=EXCVIEW)
    logger.info('Add OWS response tween')
    config.add_tween(OWS_RESPONSE, over=EXCVIEW)


# noinspection PyUnusedLocal
def ows_response_tween_factory(handler, registry):
    """
    A tween factory which produces a tween which transforms generic Python Exception and HTTPException
    into corresponding specific OWSException.

    It also adds JSON output format handling for cases where it was requested.
    """
    def _fmt_msg(err_1, err_2):
        return "\n  " \
            "Raised exception:   [{!r}]\n  " \
            "Returned exception: [{!r}]".format(err_1, err_2)

    def ows_response_tween(request):
        try:
            response = handler(request)
            if 200 <= response.status_code < 400:
                return response
            raise response
        except HTTPException as err:
            logger.debug("http exception -> ows exception response.")
            i_err = err
            ows_err = OWS_EXCEPTION_CODE_MAP.get(err.status_code)
            if ows_err:
                o_err = ows_err(detail=str(err))
            else:
                raise NotImplementedError("OWS response not implemented for exception: [{!r}]".format(err))
        except OWSException as err:
            logger.debug("direct ows exception response")
            i_err = o_err = err
        except NotImplementedError as err:
            logger.debug('not implemented error -> ows exception response')
            i_err = err
            o_err = OWSNotImplemented(str(err))
        except Exception as err:
            logger.debug("unhandled {!s} exception -> ows exception response".format(type(err).__name__))
            i_err = err
            o_err = OWSException(detail=str(err), status=HTTPInternalServerError)
        logger.exception(_fmt_msg(i_err, o_err))
        return o_err

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
            return err
        except HTTPException as err:
            logger.exception("security http failure.")
            return err  # let ows request tween handle it
        except Exception as err:
            logger.exception("unknown error")
            return OWSNoApplicableCode("{}".format(err))

    return ows_security_tween


OWS_RESPONSE = 'twitcher.tweens.ows_response_tween_factory'
OWS_SECURITY = 'twitcher.tweens.ows_security_tween_factory'
