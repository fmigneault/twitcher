"""
Twitcher OWS Proxy Configuration values.

This file can safely be overridden to provide your own configuration.
"""

from twitcher import formats as f

# TODO: configure allowed content-types
allowed_content_types = [
    f.CONTENT_TYPE_APP_XML,
    f.CONTENT_TYPE_TEXT_XML,
    f.CONTENT_TYPE_TEXT_XML_ISO,
    "application/vnd.ogc.se_xml",            # OGC Service Exception
    "application/vnd.ogc.se+xml",            # OGC Service Exception
    # "application/vnd.ogc.success+xml",      # OGC Success (SLD Put)
    "application/vnd.ogc.wms_xml",           # WMS Capabilities
    # "application/vnd.ogc.gml",              # GML
    # "application/vnd.ogc.sld+xml",          # SLD
    "application/vnd.google-earth.kml+xml",  # KML
    "application/vnd.google-earth.kmz",
    f.CONTENT_TYPE_IMG_PNG,
    f.CONTENT_TYPE_IMG_PNG + ";mode=32bit",
    f.CONTENT_TYPE_IMG_GIF,
    f.CONTENT_TYPE_IMG_JPEG,
    f.CONTENT_TYPE_APP_JSON,
    f.CONTENT_TYPE_APP_JSON_ISO,
]
"""
Allowed Content-Types that are used to validate the returned response content.

If the response's 'Content-Type' header does not match one of the allowed values,
:class:`twitcher.owsexceptions.OWSAccessUnauthorized` (ie: HTTP 401) is raised.
"""

# TODO: configure allowed hosts
allowed_hosts = [
    # list allowed hosts here (no port limiting)
    # "localhost",
]
"""
Allowed Host that are used to validate the incoming request host location.

If the response's 'Host' header does not match one of the allowed values,
:class:`twitcher.owsexceptions.OWSAccessUnauthorized` (ie: HTTP 401) is raised.

If no value is provided, validation is not executed.
"""

