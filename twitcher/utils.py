from twitcher.exceptions import ServiceNotFound
from webob.headers import ResponseHeaders, EnvironHeaders
from requests.structures import CaseInsensitiveDict
from pyramid.request import Request
from pyramid.registry import Registry
from pyramid.config import Configurator
from typing import TYPE_CHECKING
from urllib.parse import urlparse
from datetime import datetime
from lxml import etree
import pytz
import time
import logging
if TYPE_CHECKING:
    from twitcher.typedefs import AnySettingsContainer, AnyHeadersContainer, SettingsType   # noqa: F401
    from lxml.etree import _Element as xmlElement                                           # noqa: F401
    from typing import AnyStr, List, Optional                                               # noqa: F401
logger = logging.getLogger(__name__)


def get_settings(container):
    # type: (AnySettingsContainer) -> Optional[SettingsType]
    """
    Retrieves the application ``settings`` from various containers referencing to it.

    :raises TypeError: if the container type cannot be identified to retrieve settings.
    """
    if isinstance(container, (Configurator, Request)):
        container = container.registry
    if isinstance(container, Registry):
        container = container.settings
    if isinstance(container, dict):
        return container
    raise TypeError("Could not retrieve settings from container object of type [{}]".format(type(container)))


def get_header(header_name, header_container):
    # type: (AnyStr, AnyHeadersContainer) -> Optional[AnyStr]
    """
    Searches for the specified header by case/dash/underscore-insensitive ``header_name`` inside ``header_container``.
    """
    if header_container is None:
        return None
    headers = header_container
    if isinstance(headers, (ResponseHeaders, EnvironHeaders, CaseInsensitiveDict)):
        headers = dict(headers)
    if isinstance(headers, dict):
        headers = header_container.items()
    header_name = header_name.lower().replace('-', '_')
    for h, v in headers:
        if h.lower().replace('-', '_') == header_name:
            return v
    return None


def get_twitcher_url(container):
    # type: (AnySettingsContainer) -> AnyStr
    settings = get_settings(container)
    return settings.get('twitcher.url').rstrip('/').strip()


def is_valid_url(url):
    # type: (Optional[AnyStr]) -> bool
    try:
        parsed_url = urlparse(url)
        return True if all([parsed_url.scheme, ]) else False
    except Exception:
        return False


def parse_service_name(url, protected_path):
    # type: (AnyStr, AnyStr) -> AnyStr
    parsed_url = urlparse(url)
    service_name = None
    if parsed_url.path.startswith(protected_path):
        parts_without_protected_path = parsed_url.path[len(protected_path)::].strip('/').split('/')
        if 'proxy' in parts_without_protected_path:
            parts_without_protected_path.remove('proxy')
        if len(parts_without_protected_path) > 0:
            service_name = parts_without_protected_path[0]
    if not service_name:
        raise ServiceNotFound
    return service_name


def now():
    # type: () -> datetime
    return localize_datetime(datetime.utcnow())


def now_secs():
    # type: () -> int
    """
    Return the current time in seconds since the Epoch.
    """
    return int(time.time())


def expires_at(hours=1):
    # type: (Optional[int]) -> int
    return now_secs() + hours * 3600


def localize_datetime(dt, tz_name='UTC'):
    # type: (datetime, Optional[AnyStr]) -> datetime
    """
    Provide a timezone-aware object for a given datetime and timezone name.
    """
    tz_aware_dt = dt
    if dt.tzinfo is None:
        utc = pytz.timezone('UTC')
        aware = utc.localize(dt)
        timezone = pytz.timezone(tz_name)
        tz_aware_dt = aware.astimezone(timezone)
    else:
        logger.warn('tzinfo already set')
    return tz_aware_dt


def baseurl(url):
    # type: (AnyStr) -> AnyStr
    """
    return baseurl of given url
    """
    parsed_url = urlparse(url)
    if not parsed_url.netloc or parsed_url.scheme not in ("http", "https"):
        raise ValueError('bad url')
    service_url = "%s://%s%s" % (parsed_url.scheme, parsed_url.netloc, parsed_url.path.strip())
    return service_url


def path_elements(path):
    # type: (AnyStr) -> List[AnyStr]
    elements = [el.strip() for el in path.split('/')]
    elements = [el for el in elements if len(el) > 0]
    return elements


def lxml_strip_ns(tree):
    # type: (xmlElement) -> None
    for node in tree.iter():
        try:
            has_namespace = node.tag.startswith('{')
        except AttributeError:
            continue  # node.tag is not a string (node is a comment or similar)
        if has_namespace:
            node.tag = node.tag.split('}', 1)[1]


def replace_text_url(text, public_url, private_url=None):
    # type: (AnyStr, AnyStr, Optional[AnyStr]) -> AnyStr
    """Replaces any ``private_url`` by ``public_url`` from a text string or bytes response content."""
    if isinstance(text, bytes):
        text = text.decode('utf-8', 'ignore')
    return text.replace(private_url, public_url)


def replace_caps_url(xml, public_url, private_url=None):
    # type: (AnyStr, AnyStr, Optional[AnyStr]) -> AnyStr
    """Replaces any ``private_url`` by ``public_url`` from a XML WPS/WMS GetCapabilities response content."""
    ns = {
        'ows': 'http://www.opengis.net/ows/1.1',
        'xlink': 'http://www.w3.org/1999/xlink'}
    doc = etree.fromstring(xml)
    # wms 1.1.1 onlineResource
    if 'WMT_MS_Capabilities' in doc.tag:
        logger.debug("replace proxy urls in wms 1.1.1")
        for element in doc.findall('.//OnlineResource[@xlink:href]', namespaces=ns):
            parsed_url = urlparse(element.get('{http://www.w3.org/1999/xlink}href'))
            new_url = public_url
            if parsed_url.query:
                new_url += '?' + parsed_url.query
            element.set('{http://www.w3.org/1999/xlink}href', new_url)
        xml = etree.tostring(doc)
    # wms 1.3.0 onlineResource
    elif 'WMS_Capabilities' in doc.tag:
        logger.debug("replace proxy urls in wms 1.3.0")
        for element in doc.findall('.//{http://www.opengis.net/wms}OnlineResource[@xlink:href]', namespaces=ns):
            parsed_url = urlparse(element.get('{http://www.w3.org/1999/xlink}href'))
            new_url = public_url
            if parsed_url.query:
                new_url += '?' + parsed_url.query
            element.set('{http://www.w3.org/1999/xlink}href', new_url)
        xml = etree.tostring(doc)
    # wps operations
    elif 'Capabilities' in doc.tag:
        for element in doc.findall('ows:OperationsMetadata//*[@xlink:href]', namespaces=ns):
            element.set('{http://www.w3.org/1999/xlink}href', public_url)
        xml = etree.tostring(doc)
    elif private_url:
        xml = replace_text_url(xml, public_url, private_url)
    return xml


def clean_json_text_body(body):
    # type: (AnyStr) -> AnyStr
    """
    Cleans a textual body field of superfluous characters to provide a better human-readable text in a JSON response.
    """
    # cleanup various escape characters and u'' stings
    replaces = [(',\n', ', '), ('\\n', ' '), (' \n', ' '), ('\"', '\''), ('\\', ''),
                ('u\'', '\''), ('u\"', '\''), ('\'\'', '\''), ('  ', ' ')]
    replaces_from = [r[0] for r in replaces]
    while any(rf in body for rf in replaces_from):
        for _from, _to in replaces:
            body = body.replace(_from, _to)

    body_parts = [p.strip() for p in body.split('\n') if p != '']               # remove new line and extra spaces
    body_parts = [p + '.' if not p.endswith('.') else p for p in body_parts]    # add terminating dot per sentence
    body_parts = [p[0].upper() + p[1:] for p in body_parts if len(p)]           # capitalize first word
    body_parts = ' '.join(p for p in body_parts if p)
    return body_parts
