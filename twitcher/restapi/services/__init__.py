from twitcher.restapi import schemas as sd
from twitcher.restapi.services import services as s
import logging
logger = logging.getLogger('TWITCHER')


def includeme(config):
    logger.info('Adding WPS REST API services ...')
    settings = config.registry.settings
    config.add_route(**sd.service_api_route_info(sd.services_service, settings))
    config.add_route(**sd.service_api_route_info(sd.service_service, settings))
    config.add_view(s.get_services_view, route_name=sd.services_service.name, request_method='GET', renderer='json')
    config.add_view(s.add_service_view, route_name=sd.services_service.name, request_method='POST', renderer='json')
    config.add_view(s.get_service_view, route_name=sd.service_service.name, request_method='GET', renderer='json')
    config.add_view(s.remove_service_view, route_name=sd.service_service.name, request_method='DELETE', renderer='json')
