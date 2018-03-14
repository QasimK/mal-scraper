"""Discover user_ids (automatically)."""

import logging
import re

from .requester import request_passthrough

logger = logging.getLogger(__name__)


def discover_users(requester=request_passthrough, use_cache=True, use_web=None):
    """Return a set of user_ids usable by other user related library calls.

    By default we will attempt to return any in our cache - clearing the cache
    in the process. If there are no users in the cache, we will attempt to
    find some on MAL but these will be biased towards recently active users.

    The cache is built up by discovering users from all of the other web-pages
    retrieved from other API calls as you make those calls.

    Args:
        requester (requests-like, optional): HTTP request maker.
            This allows us to control/limit/mock requests.
        use_cache (bool, optional): Ignore the cache that we have built up over time?
            True (default): Pretend the cache is empty (and do not clear it).
            False: Get and clear the cache.
        use_web (bool, optional): Control whether to fall back to scraping.
            None (default) to make a network call only if the cache is empty.
            False to never make a network call.
            True to always make a network call.

    Returns:
        A set of user_ids which are strings.

    Raises:
        Network and Request Errors: See Requests library.

    Examples:

        Get user_ids discovered from earlier uses of the library::

            animes = mal_scraper.get_anime()
            users_probably_from_cache = mal_scraper.discover_users()

        Get user_ids if there are any in the cache, but don't bother to make
        a network call just to find some::

            users_from_cache = mal_scraper.discover_users(use_web=False)

        Discover some users from the web, ignoring the cache::

            users_from_web = mal_scraper.discover_users(use_cache=False)
    """
    # TODO: Dependency injection for user store
    # TODO: Test this method
    discovered_users = set()

    if use_cache:
        discovered_users |= default_user_store.get_and_clear_cache()

    # Force use web, or fall-back to web if the cache is empty
    if use_web or (use_web is None and not discovered_users):
        response = requester.get(get_url_for_user_discovery())
        response.raise_for_status()  # May raise
        discovered_users |= set(discover_users_from_html(response.text))

    return discovered_users


def get_url_for_user_discovery():
    """Return the URL to the profile discovery page."""
    # Use HTTPS to avoid auto-redirect from HTTP (except for tests)
    from .__init__ import _FORCE_HTTP  # noqa
    protocol = 'http' if _FORCE_HTTP else 'https'
    return '{}://myanimelist.net/users.php'.format(protocol)


_username_regex = re.compile(
    r"href=[\"'](https?\://myanimelist\.net)?/profile/(?P<username>\w+)[\w/]*[\"']",
    re.ASCII | re.DOTALL | re.IGNORECASE,
)


def discover_users_from_html(html):
    """Generate usernames from the given HTML (usernames may be duplicated)

    Args:
        html (str): HTML to hunt through

    Yields:
        user_id (string)

    Test strings::

        <a href="/profile/TheLlama">
        <a href="https://myanimelist.net/profile/TheLlama">
        <a href="/profile/TheLlama/reviews">All reviews</a>
    """
    return (m.group('username') for m in _username_regex.finditer(html))


class UserStore:
    """Cache the dynamic discovery of users."""

    def __init__(self):
        self.cache = set()

    def store_users_from_html(self, html):
        """Store the users discovered in the cache from the given HTML text."""
        self.cache |= set(discover_users_from_html(html))

    def get_and_clear_cache(self):
        cache, self.cache = self.cache, set()
        return cache


default_user_store = UserStore()
