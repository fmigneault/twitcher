from twitcher.swagger.views import swagger_json_view, swagger_ui_view
from twitcher.utils import get_settings
from pyramid.settings import asbool
import logging
logger = logging.getLogger(__name__)


def includeme(config):
    from twitcher.swagger import schemas as s
    settings = get_settings(config)
    if asbool(settings.get('twitcher.restapi', True)):
        logger.info('Adding Twitcher Swagger documentation ...')
        config.registry.settings["handle_exceptions"] = False  # avoid cornice conflicting views
        config.include('cornice')
        config.include('cornice_swagger')
        config.include('pyramid_mako')
        config.add_route(**s.service_swagger_route_info(s.swagger_json_service, settings))
        config.add_route(**s.service_swagger_route_info(s.swagger_ui_service, settings))
        config.add_view(swagger_json_view, route_name=s.swagger_json_service.name,
                        request_method='GET', renderer='json')
        config.add_view(swagger_ui_view, route_name=s.swagger_ui_service.name,
                        request_method='GET', renderer='templates/swagger_ui.mako')
