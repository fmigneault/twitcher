"""
OWSExceptions are based on pyramid.httpexceptions.

See also: https://github.com/geopython/pywps/blob/master/pywps/exceptions.py
"""
from twitcher.formats import (
    CONTENT_TYPE_ANY,
    CONTENT_TYPE_TEXT_ANY,
    CONTENT_TYPE_APP_JSON,
    CONTENT_TYPE_TEXT_XML,
    CONTENT_TYPE_APP_XML
)
from twitcher.utils import clean_json_text_body
from twitcher.warning import MissingParameterWarning, UnsupportedOperationWarning
from zope.interface import implementer
from webob import html_escape as _html_escape
from webob.acceptparse import create_accept_header, AcceptNoHeader, AcceptValidHeader, AcceptInvalidHeader
from pyramid.interfaces import IExceptionResponse
from pyramid.httpexceptions import (
    HTTPException,
    HTTPOk,
    HTTPBadRequest,
    HTTPUnauthorized,
    HTTPNotFound,
    HTTPMethodNotAllowed,
    HTTPNotAcceptable,
    HTTPInternalServerError,
    HTTPNotImplemented,
)
from pyramid.response import Response
from pyramid.compat import text_type
from string import Template
from typing import TYPE_CHECKING
import warnings
import json
if TYPE_CHECKING:
    from twitcher.typedefs import SettingsType  # noqa: F401
    from typing import AnyStr, Dict, Union      # noqa: F401


@implementer(IExceptionResponse)
class OWSException(Response, Exception):

    code = "NoApplicableCode"
    value = None
    locator = "NoApplicableCode"
    explanation = "Unknown Error"
    status_code = 500

    page_template = Template('''\
<?xml version="1.0" encoding="utf-8"?>
<ExceptionReport version="1.0.0"
    xmlns="http://www.opengis.net/ows/1.1"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.opengis.net/ows/1.1 http://schemas.opengis.net/ows/1.1.0/owsExceptionReport.xsd">
    <Exception exceptionCode="${code}" locator="${locator}">
        <ExceptionText>${message}</ExceptionText>
    </Exception>
</ExceptionReport>''')

    def __init__(self, detail=None, value=None, **kw):
        for arg in [detail, value]:
            if isinstance(arg, dict):
                for k, v in arg.items():
                    kw.setdefault(k, v)
        status = kw.pop("status", "{} {}".format(self.status_code, self.explanation))
        if isinstance(status, type) and issubclass(status, HTTPException):
            status = status().status
        elif isinstance(status, str):
            try:
                self._code_from_status(status)
            except Exception:
                raise ValueError("status specified as string must be of format '<code> <title>'")
        elif isinstance(status, HTTPException):
            status = status.status
        elif not status:
            status = HTTPOk().status
        Response.__init__(self, status=status, **kw)
        Exception.__init__(self, detail)
        self.status_code = self._code_from_status(status)
        self.status = status
        # get specified 'message' and use it if it is valid, otherwise use the 'default' explanation
        if isinstance(detail, tuple) and len(detail) and len(detail[0]):
            detail = detail[0]
        self.message = detail or self.explanation
        if value:
            self.locator = value

    def __str__(self, skip_body=False):
        return self.message

    @staticmethod
    def _code_from_status(status):
        # type: (AnyStr) -> int
        return int(status.split()[0])

    # noinspection PyUnusedLocal
    @staticmethod
    def json_formatter(status, body, title, environ):
        # type: (AnyStr, AnyStr, AnyStr, SettingsType) -> Dict[AnyStr, Union[AnyStr, int]]
        body = clean_json_text_body(body)
        return {"description": body, "code": OWSException._code_from_status(status), "status": status, "title": title}

    def prepare(self, environ):
        if not self.body:
            accept_value = environ.get("HTTP_ACCEPT", None)
            accept = create_accept_header(accept_value)

            if isinstance(accept, AcceptNoHeader) or (isinstance(accept, AcceptValidHeader)
                                                      and accept_value in [CONTENT_TYPE_ANY, CONTENT_TYPE_TEXT_ANY]):
                accept = create_accept_header(CONTENT_TYPE_TEXT_XML)
            elif isinstance(accept, AcceptInvalidHeader):
                raise OWSNotAcceptable("Invalid header not recognized.", value=str(accept_value))

            # Attempt to match xml or json, if those don't match, we will fall through to defaulting to xml
            match = accept.best_match([CONTENT_TYPE_TEXT_XML, CONTENT_TYPE_APP_XML, CONTENT_TYPE_APP_JSON])

            if match == CONTENT_TYPE_APP_JSON:
                self.content_type = CONTENT_TYPE_APP_JSON

                # json exception response should not have status 200
                if self.status_code == HTTPOk.code:
                    self.status = HTTPInternalServerError.code

                class JsonPageTemplate(object):
                    def __init__(self, excobj):
                        self.excobj = excobj

                    # noinspection PyUnusedLocal
                    def substitute(self, code, locator, message):
                        return json.dumps(self.excobj.json_formatter(
                            status=self.excobj.status, body=message, title=None, environ=environ))

                page_template = JsonPageTemplate(self)

            elif match in [CONTENT_TYPE_APP_XML, CONTENT_TYPE_TEXT_XML]:
                self.content_type = CONTENT_TYPE_TEXT_XML
                page_template = self.page_template

            else:
                raise OWSNotAcceptable("Invalid header is not supported.", value=str(accept_value))

            args = {
                "code": _html_escape(self.code),
                "locator": _html_escape(self.locator),
                "message": _html_escape(self.message or ""),
            }
            page = page_template.substitute(**args)
            if isinstance(page, text_type):
                page = page.encode(self.charset if self.charset else "UTF-8")
            self.app_iter = [page]
            self.body = page

    @property
    def wsgi_response(self):
        # bw compat only
        return self

    exception = wsgi_response  # bw compat only

    def __call__(self, environ, start_response):
        # differences from webob.exc.WSGIHTTPException
        #
        # - does not try to deal with HEAD requests
        #
        # - does not manufacture a new response object when generating
        #   the default response
        #
        self.prepare(environ)
        return Response.__call__(self, environ, start_response)


class OWSAccessUnauthorized(OWSException):
    locator = "AccessUnauthorized"
    explanation = "Access to this service is unauthorized."

    def __init__(self, *args, **kwargs):
        kwargs["status"] = HTTPUnauthorized
        super(OWSAccessUnauthorized, self).__init__(*args, **kwargs)


OWSAccessForbidden = OWSAccessUnauthorized  # backward compatibility


class OWSNotFound(OWSException):
    locator = "NotFound"
    explanation = "This resource does not exist."

    def __init__(self, *args, **kwargs):
        kwargs["status"] = HTTPNotFound
        super(OWSNotFound, self).__init__(*args, **kwargs)


class OWSNotAcceptable(OWSException):
    locator = "NotAcceptable"
    explanation = "Accept header not supported."

    def __init__(self, *args, **kwargs):
        kwargs["status"] = HTTPNotAcceptable
        super(OWSNotAcceptable, self).__init__(*args, **kwargs)


class OWSBadRequest(OWSException):
    """WPS Bad Request Exception"""
    code = "AccessFailed"
    locator = ""
    explanation = "Invalid request parameters or definition."

    def __init__(self, *args, **kwargs):
        kwargs["status"] = HTTPBadRequest
        super(OWSBadRequest, self).__init__(*args, **kwargs)


OWSAccessFailed = OWSBadRequest  # backward compatibility


class OWSNoApplicableBase(OWSException):
    """WPS Exception for not applicable code (invalid route, method, etc.)"""
    code = "NoApplicableCode"
    locator = ""
    explanation = "Operation is not applicable."

    def __init__(self, *args, **kwargs):
        warnings.warn(self.message, UnsupportedOperationWarning)


class OWSNoApplicableCode(OWSNoApplicableBase):
    """WPS Bad Request Exception"""
    def __init__(self, *args, **kwargs):
        kwargs["status"] = HTTPBadRequest
        super(OWSNoApplicableCode, self).__init__(*args, **kwargs)


class OWSNoApplicableMethod(OWSNoApplicableBase):
    """WPS Method Not Allowed Exception"""
    def __init__(self, *args, **kwargs):
        kwargs["status"] = HTTPMethodNotAllowed
        super(OWSNoApplicableMethod, self).__init__(*args, **kwargs)


class OWSMissingParameterValue(OWSException):
    """MissingParameterValue WPS Exception"""
    code = "MissingParameterValue"
    locator = ""
    explanation = "Parameter value is missing."

    def __init__(self, *args, **kwargs):
        kwargs["status"] = HTTPBadRequest
        super(OWSMissingParameterValue, self).__init__(*args, **kwargs)
        warnings.warn(self.message, MissingParameterWarning)


class OWSInvalidParameterValue(OWSException):
    """InvalidParameterValue WPS Exception"""
    code = "InvalidParameterValue"
    locator = ""
    explanation = "Parameter value is not valid."

    def __init__(self, *args, **kwargs):
        kwargs["status"] = HTTPBadRequest
        super(OWSInvalidParameterValue, self).__init__(*args, **kwargs)
        warnings.warn(self.message, UnsupportedOperationWarning)


class OWSNotApplicable(OWSException):
    code = "NotApplicable"
    locator = ""
    explanation = "Operation generated a server error."

    def __init__(self, *args, **kwargs):
        kwargs["status"] = HTTPInternalServerError
        super(OWSNotApplicable, self).__init__(*args, **kwargs)


class OWSNotImplemented(OWSException):
    code = "NotImplemented"
    locator = ""
    explanation = "Operation is not implemented."

    def __init__(self, *args, **kwargs):
        kwargs["status"] = HTTPNotImplemented
        super(OWSNotImplemented, self).__init__(*args, **kwargs)
        warnings.warn(self.message, UnsupportedOperationWarning)


OWS_EXCEPTION_CODE_MAP = {
    401: OWSAccessUnauthorized,
    403: OWSAccessForbidden,
    404: OWSNotFound,
    405: OWSNoApplicableMethod,
    406: OWSNotAcceptable,
    # TODO: routes that require an AccessToken when it is not provided show return:
    #   407 Proxy Authentication Required
    #   https://www.restapitutorial.com/httpstatuscodes.html
    500: OWSNotApplicable,
    501: OWSNotImplemented,
}
