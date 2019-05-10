"""
This module should contain any and every definitions in use to build the swagger UI,
so that one can update the swagger without touching any other files after the initial integration
"""

from cornice import Service as SwaggerService
from colander import drop, MappingSchema, SequenceSchema, String, Boolean, OneOf    # don't import SchemaNode
from twitcher.swagger.colander_defaults import SchemaNodeDefault as SchemaNode      # replace colander's implementation
from twitcher.adapter import TWITCHER_ADAPTER_DEFAULT
from twitcher.formats import CONTENT_TYPE_APP_JSON, CONTENT_TYPE_APP_XML, CONTENT_TYPE_TEXT_XML, CONTENT_TYPE_TEXT_HTML
from twitcher.restapi.utils import restapi_base_path
from twitcher.utils import get_settings
from twitcher import __meta__
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from twitcher.typedefs import AnySettingsContainer
    from typing import AnyStr, Dict

FORMAT_URL = "url"

API_TITLE = 'Twitcher REST API'
API_INFO = {
    "description": __meta__.__description__,
    "contact": {
        "name": __meta__.__author__,
        "email": __meta__.__email__,
        "url": __meta__.__repository__,
    }
}


#################################################################
# Utility methods
#################################################################

def swagger_base_path(container):
    # type: (AnySettingsContainer) -> AnyStr
    settings = get_settings(container)
    return settings.get('twitcher.swagger_path', '/doc')


def service_swagger_route_info(service_api, container):
    # type: (SwaggerService, AnySettingsContainer) -> Dict[AnyStr, AnyStr]
    return {'name': service_api.name,
            'pattern': '{base}{path}'.format(base=swagger_base_path(container), path=service_api.path)}


def service_restapi_route_info(service_api, container):
    # type: (SwaggerService, AnySettingsContainer) -> Dict[AnyStr, AnyStr]
    return {'name': service_api.name,
            'pattern': '{base}{path}'.format(base=restapi_base_path(container), path=service_api.path)}


#########################################################################
# API endpoints (without corresponding 'base' paths)
#########################################################################

swagger_ui_uri = '/'
swagger_json_uri = '/json'

restapi_frontpage_uri = '/'
restapi_versions_uri = '/versions'

restapi_service_var = 'service_name'
restapi_service_var_key = '{' + restapi_service_var + '}'
restapi_services_uri = '/services'
restapi_service_uri = '/services/' + restapi_service_var_key

#########################################################
# API tags
#########################################################

TagAPI = 'API'
TagServices = 'Services'

###############################################################################
# These "services" are wrappers that allow Cornice to generate the JSON API
###############################################################################

swagger_ui_service = SwaggerService(name='api_swagger_ui', path=swagger_ui_uri)
swagger_json_service = SwaggerService(name='api_swagger_json', path=swagger_json_uri)

restapi_frontpage_service = SwaggerService(name='api_frontpage', path=restapi_frontpage_uri)
restapi_versions_service = SwaggerService(name='api_versions', path=restapi_versions_uri)
restapi_services_service = SwaggerService(name='services', path=restapi_services_uri)
restapi_service_service = SwaggerService(name='service', path=restapi_service_uri)

#########################################################
# Path parameter definitions
#########################################################

service_name_param = SchemaNode(String(), description='Service name identifier')


#########################################################
# Generic schemas
#########################################################


class JsonHeader(MappingSchema):
    content_type = SchemaNode(String(), example=CONTENT_TYPE_APP_JSON, default=CONTENT_TYPE_APP_JSON)
    content_type.name = 'Content-Type'


class HtmlHeader(MappingSchema):
    content_type = SchemaNode(String(), example=CONTENT_TYPE_TEXT_HTML, default=CONTENT_TYPE_TEXT_HTML)
    content_type.name = 'Content-Type'


class XmlHeader(MappingSchema):
    content_type = SchemaNode(String(), example=CONTENT_TYPE_TEXT_XML, default=CONTENT_TYPE_TEXT_XML)
    content_type.name = 'Content-Type'


class AcceptHeader(MappingSchema):
    Accept = SchemaNode(String(), missing=drop, default=CONTENT_TYPE_APP_JSON, validator=OneOf([
        CONTENT_TYPE_APP_JSON,
        CONTENT_TYPE_APP_XML,
        CONTENT_TYPE_TEXT_XML,
        CONTENT_TYPE_TEXT_HTML,
    ]))


#########################################################
# These classes define each of the endpoints parameters
#########################################################


class FrontpageEndpoint(MappingSchema):
    header = AcceptHeader()


class VersionsEndpoint(MappingSchema):
    header = AcceptHeader()


class SwaggerJSONEndpoint(MappingSchema):
    header = AcceptHeader()


class SwaggerUIEndpoint(MappingSchema):
    pass


class ServiceEndpoint(MappingSchema):
    header = AcceptHeader()
    service_name = service_name_param


##################################################################
# These classes define schemas for requests that feature a body
##################################################################

AuthValues = ["auth", "token"]


class CreateServiceRequestBody(MappingSchema):
    name = SchemaNode(String(), description="Service name (identifier).")
    type = SchemaNode(String(), description="Service type.", missing=drop, default="WPS")
    url = SchemaNode(String(), description="Private URL of the service.", format=FORMAT_URL)
    purl = SchemaNode(String(), description="Public URL of the service.", format=FORMAT_URL, missing=drop)
    public = SchemaNode(Boolean(), missing=drop, default=False,
                        description="Public status of the service.")
    verify = SchemaNode(Boolean(), missing=drop, default=True,
                        description="SSL verification status for request to service.")
    auth = SchemaNode(String(), description="Authentication method.", missing=drop, default="token",
                      validator=OneOf(AuthValues))


class ServiceSummarySchema(MappingSchema):
    """WPS service summary information."""
    name = SchemaNode(String(), description="Service name (identifier).")
    type = SchemaNode(String(), description="Service type.", default="WPS")


class ServiceDetailSchema(ServiceSummarySchema):
    """WPS service detailed information."""
    url = SchemaNode(String(), description="Private URL of the service.", format=FORMAT_URL)
    purl = SchemaNode(String(), description="Public URL of the service.", format=FORMAT_URL, missing=drop)
    public = SchemaNode(Boolean(), description="Public status of the service.")
    verify = SchemaNode(Boolean(), description="SSL verification status for request to service.")
    auth = SchemaNode(String(), description="Authentication method.", validator=OneOf(AuthValues))


class ServiceListSchema(SequenceSchema):
    service = ServiceSummarySchema()


class FrontpageParameterSchema(MappingSchema):
    name = SchemaNode(String(), example='api')
    enabled = SchemaNode(Boolean(), example=True)
    url = SchemaNode(String(), example='https://localhost:5000', missing=drop)
    doc = SchemaNode(String(), example='https://localhost:5000/api', missing=drop)


class FrontpageParameters(SequenceSchema):
    param = FrontpageParameterSchema()


class AdapterDescriptionSchema(MappingSchema):
    description = "Adapter details."
    name = SchemaNode(String(), example=TWITCHER_ADAPTER_DEFAULT, default=TWITCHER_ADAPTER_DEFAULT)
    version = SchemaNode(String(), example="1.0.0")


class FrontpageSchema(MappingSchema):
    message = SchemaNode(String(), default='Twitcher Information', example='Twitcher Information')
    adapter = AdapterDescriptionSchema()
    database = SchemaNode(String(), description="Database type loaded by setting configuration.")
    parameters = FrontpageParameters()


class SwaggerJSONSpecSchema(MappingSchema):
    pass


class SwaggerUISpecSchema(MappingSchema):
    pass


class VersionsSpecSchema(MappingSchema):
    name = SchemaNode(String(), description="Identification name of the current item.", example='default')
    type = SchemaNode(String(), description="Identification type of the current item.", example='adapter')
    version = SchemaNode(String(), description="Version of the current item.", example='0.3.0')


class VersionsList(SequenceSchema):
    item = VersionsSpecSchema()


class VersionsSchema(MappingSchema):
    versions = VersionsList()


#################################
# Service Processes schemas
#################################


class GetServices(MappingSchema):
    header = AcceptHeader()


class PostService(MappingSchema):
    header = AcceptHeader()
    body = CreateServiceRequestBody()


#################################
# Responses schemas
#################################


class ErrorJsonResponseBodySchema(MappingSchema):
    code = SchemaNode(String(), example="NoApplicableCode")
    description = SchemaNode(String(), example="Not authorized to access this resource.")


class UnauthorizedJsonResponseSchema(MappingSchema):
    header = JsonHeader()
    body = ErrorJsonResponseBodySchema()


class OkGetFrontpageSchema(MappingSchema):
    header = JsonHeader()
    body = FrontpageSchema()


class OkGetSwaggerJSONSchema(MappingSchema):
    header = JsonHeader()
    body = SwaggerJSONSpecSchema(description="Swagger JSON of Twitcher API.")


class OkGetSwaggerUISchema(MappingSchema):
    header = HtmlHeader()
    body = SwaggerUISpecSchema(description="Swagger UI of Twitcher API.")


class OkGetVersionsSchema(MappingSchema):
    header = JsonHeader()
    body = VersionsSchema()


class OkGetServicesSchema(MappingSchema):
    header = JsonHeader()
    body = ServiceListSchema()


class OkGetServiceSchema(MappingSchema):
    header = JsonHeader()
    body = ServiceDetailSchema()


class NoContentDeleteServiceSchema(MappingSchema):
    header = JsonHeader()
    body = MappingSchema(default={})


class CreatedPostService(MappingSchema):
    header = JsonHeader()
    body = ServiceSummarySchema()


get_api_frontpage_responses = {
    '200': OkGetFrontpageSchema(description='success'),
    '401': UnauthorizedJsonResponseSchema(description='unauthorized'),
}
get_api_swagger_json_responses = {
    '200': OkGetSwaggerJSONSchema(description='success'),
    '401': UnauthorizedJsonResponseSchema(description='unauthorized'),
}
get_api_swagger_ui_responses = {
    '200': OkGetSwaggerUISchema(description='success'),
    '401': UnauthorizedJsonResponseSchema(description='unauthorized'),
}
get_api_versions_responses = {
    '200': OkGetVersionsSchema(description='success'),
    '401': UnauthorizedJsonResponseSchema(description='unauthorized'),
}
get_all_services_responses = {
    '200': OkGetServicesSchema(description='success'),
    '401': UnauthorizedJsonResponseSchema(description='unauthorized'),
}
get_one_service_responses = {
    '200': OkGetServiceSchema(description='success'),
    '401': UnauthorizedJsonResponseSchema(description='unauthorized'),
}
delete_service_responses = {
    '204': NoContentDeleteServiceSchema(description='success'),
    '401': UnauthorizedJsonResponseSchema(description='unauthorized'),
}
post_service_responses = {
    '201': CreatedPostService(description='success'),
    '401': UnauthorizedJsonResponseSchema(description='unauthorized'),
}
