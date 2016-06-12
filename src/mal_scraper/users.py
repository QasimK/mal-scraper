"""Retrieve information about a user.

This is really tricky to scrape from MAL because we cannot reference users by ID.
We must use a user-discovery process which has limitations (see discover_users).

TODO: User discovery from all other pages gets dumped here waiting for discover_users
to be called.

Possible alternative:
- http://graph.anime.plus/
"""

import logging

from bs4 import BeautifulSoup

from .requester import request_passthrough

logger = logging.getLogger(__name__)


def discover_users(requester=request_passthrough):
    """Return a set of user_refs.

    You should call this **many** times, it will probably return different users.
    Limitations: This is currently biased towards recently active users.

    Args:
        requester (Optional(requests-like)): HTTP request maker.
            This allows us to control/limit/mock requests.

    Returns:
        A set of strings of usernames which can each be used with retrieve_user,
        or None in case of a non-recoverable error (the error is logged).
    """
    response = requester.get('http://myanimelist.net/users.php')
    if not response.ok:
        logging.error('Unable to retrieve user list ({0.status_code}):\n{0.text}'.format(response))
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    users = _process_discovery_soup(soup)

    return users


def _process_discovery_soup(soup):
    """Return a set of username strings."""
    users = soup.find_all('a', href=lambda link: link and link.startswith('/profile/'))
    if not users:
        logging.warn('No users found on the user discovery page.')

    stripped_links = set(user['href'][len('/profile/'):] for user in users)
    return stripped_links
