from twitcher.restapi import api
from twitcher.restapi.utils import restapi_enabled
from twitcher.utils import get_settings
import logging
logger = logging.getLogger(__name__)


def includeme(config):
    from twitcher.swagger import schemas as s
    settings = get_settings(config)
    if restapi_enabled(settings):
        logger.info('Adding REST API ...')
        config.registry.settings["handle_exceptions"] = False  # avoid cornice conflicting views
        config.include('cornice')
        config.include('cornice_swagger')
        config.include('pyramid_mako')
        config.include('twitcher.restapi.services')
        config.add_route(**s.service_restapi_route_info(s.restapi_frontpage_service, settings))
        config.add_route(**s.service_restapi_route_info(s.swagger_json_service, settings))
        config.add_route(**s.service_restapi_route_info(s.swagger_ui_service, settings))
        config.add_route(**s.service_restapi_route_info(s.restapi_versions_service, settings))
        config.add_view(api.frontpage_view, route_name=s.restapi_frontpage_service.name,
                        request_method='GET', renderer='json')
        config.add_view(api.versions_view, route_name=s.restapi_versions_service.name,
                        request_method='GET', renderer='json')
        config.add_notfound_view(api.not_found_or_method_not_allowed_view)
        config.add_forbidden_view(api.unauthorized_or_forbidden_view)
