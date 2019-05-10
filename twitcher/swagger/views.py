from twitcher.__meta__ import __version__ as twitcher_version
from twitcher.swagger import schemas as s
from twitcher.swagger.colander_one_of import CustomTypeConversionDispatcher
from twitcher.swagger.schemas import swagger_base_path
from cornice_swagger import CorniceSwagger
from cornice.service import get_services
from pyramid.renderers import render_to_response
from urllib.parse import urlparse
from typing import TYPE_CHECKING
import logging
import os
if TYPE_CHECKING:
    from twitcher.typedefs import JSON
    from pyramid.request import Request
LOGGER = logging.getLogger(__name__)


@s.swagger_json_service.get(tags=[s.TagAPI], renderer='json',
                            schema=s.SwaggerJSONEndpoint(), response_schemas=s.get_api_swagger_json_responses)
def swagger_json_view(request, use_docstring_summary=True):
    # type: (Request, bool) -> JSON
    """Twitcher REST API schema generation in JSON format."""
    CorniceSwagger.type_converter = CustomTypeConversionDispatcher
    swagger = CorniceSwagger(get_services())
    # function docstrings are used to create the route's summary in Swagger-UI
    swagger.summary_docstrings = use_docstring_summary
    twitcher_swagger_base_spec = {'schemes': [request.scheme]}

    # obtain 'server' host and api-base-path, which doesn't correspond necessarily to the app's host and path
    # ex: 'server' adds '/twitcher' with proxy redirect before API routes
    twitcher_server_url = os.getenv('TWITCHER_URL')
    LOGGER.debug("Request URL:  {}".format(request.url))
    LOGGER.debug("TWITCHER_URL: {}".format(twitcher_server_url))
    if twitcher_server_url:
        twitcher_parsed_url = urlparse(twitcher_server_url)
        twitcher_swagger_base_spec['host'] = twitcher_parsed_url.netloc
        twitcher_swagger_base_path = twitcher_parsed_url.path
    else:
        twitcher_swagger_base_spec['host'] = request.host
        twitcher_swagger_base_path = '/'
    swagger.swagger = twitcher_swagger_base_spec
    return swagger.generate(title=s.API_TITLE, version=twitcher_version, base_path=twitcher_swagger_base_path)


@s.swagger_ui_service.get(tags=[s.TagAPI],
                          schema=s.SwaggerUIEndpoint(), response_schemas=s.get_api_swagger_ui_responses)
def swagger_ui_view(request):
    """Twitcher REST API swagger-ui schema documentation (this page)."""
    json_path = swagger_base_path(request) + s.swagger_json_uri
    json_path = json_path.lstrip('/')   # if path starts by '/', swagger-ui doesn't find it on remote
    data_mako = {'api_title': s.API_TITLE, 'api_swagger_json_path': json_path}
    return render_to_response('templates/swagger_ui.mako', data_mako, request=request)
