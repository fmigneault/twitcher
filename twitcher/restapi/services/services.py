from twitcher.restapi import schemas as s
from twitcher.adapter import servicestore_factory
from twitcher.datatype import Service
from twitcher.exceptions import ServiceNotFound
from twitcher.owsexceptions import OWSMissingParameterValue, OWSNotImplemented
from pyramid.httpexceptions import HTTPOk, HTTPCreated, HTTPNotFound, HTTPNoContent
import logging
logger = logging.getLogger('TWITCHER')


def get_service(request):
    """
    Get the service specified by request parameter from the adapter's service store.
    """
    store = servicestore_factory(request.registry)
    service_id = request.matchdict.get(s.service_var)
    try:
        service = store.fetch_by_name(service_id, request=request)
    except ServiceNotFound:
        raise HTTPNotFound("Service '{}' cannot be found.".format(service_id))
    return service, store


@s.services_service.get(tags=[s.TagServices], renderer='json',
                        schema=s.GetServices(), response_schemas=s.get_all_services_responses)
def get_services_view(request):
    """
    Lists registered services.
    """
    store = servicestore_factory(request.registry)
    services = [{"name": svc.name, "type": svc.type} for svc in store.list_services(request=request)]
    return HTTPOk(json=services)


@s.services_service.post(tags=[s.TagServices], renderer='json',
                         schema=s.PostService(), response_schemas=s.post_service_responses)
def add_service_view(request):
    """
    Add a service.
    """
    valid_fields = Service(url='dummy').params.keys()
    fields = {f: v for f, v in request.json.items() if f in valid_fields}
    store = servicestore_factory(request.registry)
    try:
        new_service = Service(**fields)
    except TypeError as e:
        raise OWSMissingParameterValue("Missing json parameter '{!s}'.".format(e))
    try:
        saved_service = store.save_service(new_service, request=request)
        return HTTPCreated(json={"name": saved_service.name, "type": saved_service.type})
    except NotImplementedError:
        raise OWSNotImplemented("Add service not supported.", value=new_service)


@s.service_service.delete(tags=[s.TagServices], renderer='json',
                          schema=s.ServiceEndpoint(), response_schemas=s.delete_service_responses)
def remove_service_view(request):
    """
    Remove a service.
    """
    service, store = get_service(request)
    try:
        store.delete_service(service.name, request=request)
    except NotImplementedError:
        raise OWSNotImplemented("Delete service not supported.")

    return HTTPNoContent(json={})


@s.service_service.get(tags=[s.TagServices], renderer='json',
                       schema=s.ServiceEndpoint(), response_schemas=s.get_one_service_responses)
def get_service_view(request):
    """
    Get a service description.
    """
    service, store = get_service(request)
    service_params = service.params
    service_params.pop('url')   # TODO: provide it if valid AccessToken ?
    return HTTPOk(json=service_params)
