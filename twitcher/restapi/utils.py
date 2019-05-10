from twitcher.utils import get_twitcher_url
import logging
LOGGER = logging.getLogger("TWITCHER")


def restapi_base_path(settings):
    restapi_path = settings.get('twitcher.restapi_path', '').rstrip('/').strip()
    return restapi_path


def restapi_base_url(settings):
    twitcher_url = get_twitcher_url(settings)
    restapi_path = restapi_base_path(settings)
    return twitcher_url + restapi_path


def get_cookie_headers(headers):
    try:
        return dict(Cookie=headers['Cookie'])
    except KeyError:  # No cookie
        return {}
