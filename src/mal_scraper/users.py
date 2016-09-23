"""Retrieve information about a user.

This is really tricky to scrape from MAL because we cannot reference users by ID.
We must use a user-discovery process which has limitations (see discover_users).

TODO: User discovery from all other pages gets dumped here waiting for discover_users
to be called.

Possible alternative:
- http://graph.anime.plus/
"""

import logging
import re
from datetime import date, datetime
from functools import partial

from bs4 import BeautifulSoup

from .anime import MissingTagError, ParseError, _convert_to_date
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


def get_user_stats(username, requester=request_passthrough):
    """Return statistics about a particular user.

    Args:
        username (string): The username identifier of the MAL user.
        requester (Optional(requests-like)): HTTP request maker
            This allows us to control/limit/mock requests.

    Returns:
        None if we failed to retrieve the page, otherwise a tuple of two dicts
        (retrieval information, profile information).

        The retrieval information will include the keys:
            success (bool): Was *all* the information was retrieved?
                (Some keys from profile information may be missing otherwise.)
            scraper_retrieved_at (datetime): When the request was completed.
            username (int): username of this user used for retrieval.
        The profile information will include the keys:
            See tests/mal_scraper/test_users.py::TestUserStats::test_user_stats
    """
    url = get_profile_url_from_username(username)
    logging.debug('Retrieving profile for "%s" from "%s"', username, url)

    response = requester.get(url)
    if not response.ok:
        logging.error('Unable to retrieve profile ({0.status_code}):\n{0.text}'.format(response))
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    success, info = _process_profile_soup(soup)

    if not success:
        logger.warn('Failed to properly process the page "%s".', url)

    retrieval_info = {
        'success': success,
        'scraper_retrieved_at': datetime.utcnow(),
        'username': username,
    }

    return (retrieval_info, info)


def get_profile_url_from_username(username):
    return 'http://myanimelist.net/profile/{:s}'.format(username)


def _process_discovery_soup(soup):
    """Return a set of username strings."""
    users = soup.find_all('a', href=lambda link: link and link.startswith('/profile/'))
    if not users:
        logging.warn('No users found on the user discovery page.')

    stripped_links = set(user['href'][len('/profile/'):] for user in users)
    return stripped_links


def _process_profile_soup(soup):
    """Return (success?, metadata) from a soup of HTML.

    Returns:
        (success?, metadata) where success is only if there were zero errors.
    """
    retrieve = {
        'name': _get_name,
        'last_online': _get_last_online,
        'joined': _get_joined,
        'num_anime_watched': _get_num_anime_watched,
        'num_anime_completed': _get_num_anime_completed,
        'num_anime_on_hold': _get_num_anime_on_hold,
        'num_anime_dropped': _get_num_anime_dropped,
        'num_anime_plan_to_watch': _get_num_anime_plan_to_watch,
    }

    retrieved = {}
    failed_tags = []
    for tag, func in retrieve.items():
        try:
            result = func(soup)
        except ParseError:
            logger.warn('Error processing tag "%s".', tag)
            failed_tags.append(tag)
        else:
            retrieved[tag] = result

    success = not bool(failed_tags)
    if not success:
        logger.warn('Failed to process tags: %s', failed_tags)

    return (success, retrieved)


def _get_name(soup):
    tag = soup.find('span', string=re.compile(r"'s Profile$"))
    if not tag:
        raise MissingTagError('name')

    text = tag.string.strip()[:-len("'s Profile")]
    return text


def _get_last_online(soup):
    online_title_tag = soup.find('span', class_='user-status-title', string='Last Online')
    if not online_title_tag:
        raise MissingTagError('lastonline:title')

    last_online_tag = online_title_tag.next_sibling
    if not last_online_tag:
        raise MissingTagError('lastonline:date')

    text = last_online_tag.string.strip()
    if text == 'Now':
        return date.today()

    return _convert_to_date(text)  # Jan 6, 2014


def _get_joined(soup):
    joined_title_tag = soup.find('span', class_='user-status-title', string='Joined')
    if not joined_title_tag:
        raise MissingTagError('joined:title')

    joined_date_tag = joined_title_tag.next_sibling
    if not joined_date_tag:
        raise MissingTagError('joined:date')

    text = joined_date_tag.string.strip()
    date = _convert_to_date(text)  # Jan 6, 2014
    return date


def _get_num_anime_stats(soup, classname):
    """Get stats from the stats table. tag is just the class selector."""
    tag_name = 'num_anime_' + classname

    pretag = soup.find(class_='stats-status').find('a', class_=classname)
    if not pretag:
        raise MissingTagError(tag_name + ':title')

    num_text = pretag.next_sibling.string.strip()

    try:
        num = int(num_text)
    except (TypeError, ValueError):  # pragma: no cover
        # MAL probably changed their website
        raise ParseError(tag_name, 'Unable to convert text "%s" to int' % num_text)

    return num


_get_num_anime_watched = partial(_get_num_anime_stats, classname='watching')
_get_num_anime_completed = partial(_get_num_anime_stats, classname='completed')
_get_num_anime_on_hold = partial(_get_num_anime_stats, classname='on-hold')
_get_num_anime_dropped = partial(_get_num_anime_stats, classname='dropped')
_get_num_anime_plan_to_watch = partial(_get_num_anime_stats, classname='plantowatch')
