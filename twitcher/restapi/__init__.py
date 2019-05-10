from twitcher.restapi.api import api_frontpage, api_swagger_json, api_swagger_ui, api_versions
from twitcher.utils import get_settings
from pyramid.settings import asbool
import logging
logger = logging.getLogger(__name__)


def includeme(config):
    from twitcher.restapi import schemas as s
    settings = get_settings(config)
    if asbool(settings.get('twitcher.restapi', True)):
        logger.info('Adding WPS REST API ...')
        config.registry.settings["handle_exceptions"] = False  # avoid cornice conflicting views
        config.include('cornice')
        config.include('cornice_swagger')
        config.include('pyramid_mako')
        config.include('twitcher.restapi.services')
        config.add_route(**s.service_api_route_info(s.api_frontpage_service, settings))
        config.add_route(**s.service_api_route_info(s.api_swagger_json_service, settings))
        config.add_route(**s.service_api_route_info(s.api_swagger_ui_service, settings))
        config.add_route(**s.service_api_route_info(s.api_versions_service, settings))
        config.add_view(api_frontpage, route_name=s.api_frontpage_service.name,
                        request_method='GET', renderer='json')
        config.add_view(api_swagger_json, route_name=s.api_swagger_json_service.name,
                        request_method='GET', renderer='json')
        config.add_view(api_swagger_ui, route_name=s.api_swagger_ui_service.name,
                        request_method='GET', renderer='templates/swagger_ui.mako')
        config.add_view(api_versions, route_name=s.api_versions_service.name,
                        request_method='GET', renderer='json')
        config.add_notfound_view(api.not_found_or_method_not_allowed)
        config.add_forbidden_view(api.unauthorized_or_forbidden)
