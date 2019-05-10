"""
Definitions of types used by tokens.
"""

from twitcher.utils import now_secs, is_valid_url
from pyramid.settings import asbool
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from twitcher.typedefs import JSON
    from typing import AnyStr


class Base(dict):
    __info__ = None

    def __str__(self):
        info = ' <{}>'.format(self.__info__) if self.__info__ else ''
        return '{}{}'.format(type(self).__name__, info)

    def __repr__(self):
        cls = type(self)
        repr_ = dict.__repr__(self)
        return '{0}.{1}({2})'.format(cls.__module__, cls.__name__, repr_)


class Service(Base):
    """
    Dictionary that contains OWS services. It always has the ``'url'`` key.
    """

    def __init__(self, *args, **kwargs):
        super(Service, self).__init__(*args, **kwargs)
        if 'url' not in self:
            raise TypeError("'url' is required")
        self.__info__ = self.name

    @property
    def url(self):
        # type: () -> AnyStr
        """Service URL."""
        return self['url']

    @property
    def name(self):
        # type: () -> AnyStr
        """Service name."""
        return self.get('name', 'unknown')

    @property
    def type(self):
        # type: () -> AnyStr
        """Service type."""
        return self.get('type', 'WPS')

    @property
    def purl(self):
        # type: () -> AnyStr
        """Service optional public URL (purl)."""
        return self.get('purl', '')

    def has_purl(self):
        # type: () -> bool
        """Return true if we have a valid public URL (purl)."""
        return is_valid_url(self.purl)

    @property
    def public(self):
        # type: () -> bool
        """Flag if service has public access."""
        # TODO: public access can be set via auth parameter.
        return self.get('public', False)

    @property
    def auth(self):
        # type: () -> AnyStr
        """Authentication method: public, token, cert."""
        return self.get('auth', 'token')

    @property
    def verify(self):
        # type: () -> bool
        """Verify ssl service certificate."""
        return asbool(self.get('verify', True))

    @property
    def params(self):
        # type: () -> JSON
        return {
            'url': self.url,
            'name': self.name,
            'type': self.type,
            'purl': self.purl,
            'public': self.public,
            'auth': self.auth,
            'verify': self.verify}


class AccessToken(Base):
    """
    Dictionary that contains access token. It always has ``'token'`` key.
    """

    def __init__(self, *args, **kwargs):
        super(AccessToken, self).__init__(*args, **kwargs)
        if 'token' not in self:
            raise TypeError("'token' is required")
        self.__info__ = self.token

    @property
    def token(self):
        # type: () -> AnyStr
        """Access token string."""
        return self['token']

    @property
    def expires_at(self):
        # type: () -> int
        return int(self.get("expires_at", 0))

    @property
    def expires_in(self):
        # type: () -> int
        """
        Returns the time until the token expires.
        :return: The remaining time until expiration in seconds or 0 if the
                 token has expired.
        """
        time_left = self.expires_at - now_secs()

        if time_left > 0:
            return time_left
        return 0

    def is_expired(self):
        # type: () -> bool
        """
        Determines if the token has expired.
        :return: `True` if the token has expired. Otherwise `False`.
        """
        if self.expires_at is None:
            return True

        if self.expires_in > 0:
            return False

        return True

    @property
    def data(self):
        # type: () -> JSON
        return self.get('data') or {}

    @property
    def params(self):
        return {'access_token': self.token, 'expires_at': self.expires_at}
