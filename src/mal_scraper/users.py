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
from datetime import datetime
from functools import partial

from bs4 import BeautifulSoup

from .consts import ConsumptionStatus
from .exceptions import MissingTagError, ParseError
from .mal_utils import get_date, get_datetime
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
        logging.error('Unable to retrieve user list (%d):\n%s', response.status_code, response.text)
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    users = _process_discovery_soup(soup)

    return users


# TODO: Clean this up
username_regex = re.compile(
    r"href=[\"'](https?\://myanimelist\.net)?/profile/(?P<username>\w+)[\w/]*[\"']",
    re.ASCII | re.DOTALL | re.IGNORECASE,
)


def discover_users_from_html(html):
    """Generate usernames from the given HTML (repetition is possible)

    Args:
        html (str): HTML to hunt through

    Yields:
        Usernames (string)

    Test strings::

        <a href="/profile/TheLlama">
        <a href="https://myanimelist.net/profile/TheLlama">
        <a href="/profile/TheLlama/reviews">All reviews</a>
    """
    return (m.group('username') for m in username_regex.finditer(html))


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

    retrieval_info = {
        'success': False,
        'scraper_retrieved_at': datetime.utcnow(),
        'username': username,
    }

    response = requester.get(url)
    if not response.ok:
        logging.error('Unable to retrieve profile ({0.status_code}):\n{0.text}'.format(response))
        return (retrieval_info, {})

    soup = BeautifulSoup(response.content, 'html.parser')
    success, info = _process_profile_soup(soup)

    if not success:
        logger.warn('Failed to properly process the page "%s".', url)

    retrieval_info['success'] = success

    return (retrieval_info, info)


def get_user_anime_list(username, requester=request_passthrough):
    """Return the categorised anime listed by the user.

    Args:
        username (str): The user identifier

    Returns:
        None if the download failed, the username is invalid, or the
        user has forbidden access.
        Otherwise, a list of anime where each anime is the following dict:

        {
            name: (string) name of the anime
            id_ref: (id_ref) can be used with get_anime,
            consumption_status: (ConsumptionStatus),
            is_rewatch: (bool),
            score: (int) 0-10,
            start_date: (date or None) may be missing
            progress: (int) 0+ number of episodes watched
            finished_date (date or None) may be missing or not finished
        }
    """
    anime = []
    has_more_anime = True
    while has_more_anime:
        url = get_anime_list_url_for_user(username, len(anime))
        logging.debug('Retrieving anime list from "%s"', url)

        response = requester.get(url)
        if not response.ok:
            if response.status_code == 400:
                logging.info('Access to user "%s"\'s anime list is forbidden', username)
                return None

            logging.error('Unable to get anime list ({0.status_code}):\n{0.text}'.format(response))
            return None

        additional_anime = _process_anime_list_json(response.json())
        if additional_anime:
            anime.extend(additional_anime)
        else:
            has_more_anime = False

    return anime


# --- URLs ---


def get_profile_url_from_username(username):
    # Use HTTPS to avoid auto-redirect from HTTP (except for tests)
    from .__init__ import FORCE_HTTP
    protocol = 'http' if FORCE_HTTP else 'https'
    return '{}://myanimelist.net/profile/{:s}'.format(protocol, username)


def get_anime_list_url_for_user(username, offset=0):
    """Return the url to the JSON feed for the given user:

    Args:
        username (string): User identifier
        offset (int): Feed returns paginated view, use offset to traverse

    Returns: String url
    """
    from .__init__ import FORCE_HTTP
    protocol = 'http' if FORCE_HTTP else 'https'
    url = '{protocol}://myanimelist.net/animelist/{username}/load.json?offset={offset:d}&status=7'
    return url.format(protocol=protocol, username=username, offset=offset)


# --- Dynamic User Discovery ---


def _process_discovery_soup(soup):
    """Return a set of username strings."""
    users = soup.find_all('a', href=lambda link: link and link.startswith('/profile/'))
    if not users:
        logging.error('No users found on the user discovery page.')

    stripped_links = set(user['href'][len('/profile/'):] for user in users)
    return stripped_links


# --- Parse Profile Page ---


def _process_profile_soup(soup):
    """Return (success?, metadata) from a soup of HTML.

    Returns:
        (success?, metadata) where success is only if there were zero errors.
    """
    retrieve = {
        'name': _get_name,
        'last_online': _get_last_online,
        'joined': _get_joined,
        'num_anime_watching': _get_num_anime_watching,
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
            logger.error('Error processing tag "%s".', tag)
            failed_tags.append(tag)
        else:
            retrieved[tag] = result

    success = not bool(failed_tags)
    if not success:
        logger.error('Failed to process tags: %s', failed_tags)

    return (success, retrieved)


def _get_name(soup):
    tag = soup.find('span', string=re.compile(r"'s Profile$"))
    if not tag:  # pragma: no cover
        # MAL probably changed their website
        raise MissingTagError('name')

    text = tag.string.strip()[:-len("'s Profile")]
    return text


def _get_last_online(soup):
    online_title_tag = soup.find('span', class_='user-status-title', string='Last Online')
    if not online_title_tag:
        raise MissingTagError('lastonline:title')

    last_online_tag = online_title_tag.next_sibling
    if not last_online_tag:  # pragma: no cover
        # MAL probably changed their website
        raise MissingTagError('lastonline:date')

    text = last_online_tag.string.strip()
    return get_datetime(text)


def _get_joined(soup):
    joined_title_tag = soup.find('span', class_='user-status-title', string='Joined')
    if not joined_title_tag:
        raise MissingTagError('joined:title')

    joined_date_tag = joined_title_tag.next_sibling
    if not joined_date_tag:  # pragma: no cover
        # MAL probably changed their website
        raise MissingTagError('joined:date')

    text = joined_date_tag.string.strip()
    return get_date(text)  # Jan 6, 2014


def _get_num_anime_stats(soup, classname):
    """Get stats from the stats table. tag is just the class selector."""
    tag_name = 'num_anime_' + classname

    stats_table_tag = soup.find(class_='stats-status')
    if not stats_table_tag:  # pragma: no cover
        # MAL probably changed their website
        raise MissingTagError(tag_name + ':table')

    stat_tag = stats_table_tag.find('a', class_=classname)
    if not stat_tag:  # pragma: no cover
        # MAL probably changed their website
        raise MissingTagError(tag_name + ':title')

    num_text = stat_tag.next_sibling.string.strip()

    try:
        num = int(num_text)
    except (TypeError, ValueError):  # pragma: no cover
        # MAL probably changed their website
        raise ParseError(tag_name, 'Unable to convert text "%s" to int' % num_text)

    return num


_get_num_anime_watching = partial(_get_num_anime_stats, classname='watching')
_get_num_anime_completed = partial(_get_num_anime_stats, classname='completed')
_get_num_anime_on_hold = partial(_get_num_anime_stats, classname='on-hold')
_get_num_anime_dropped = partial(_get_num_anime_stats, classname='dropped')
_get_num_anime_plan_to_watch = partial(_get_num_anime_stats, classname='plantowatch')


# --- Parse User's Anime List Page(s) ---


def _process_anime_list_json(json):
    """Return a list of anime as described by get_user_anime_list.

    Implementation notes:

        The JSON is a list of objects like

        {
           "status":1,
           "score":0,
           "tags":"",
           "is_rewatching":0,
           "num_watched_episodes":1,
           "anime_title":"91 Days",
           "anime_num_episodes":12,
           "anime_airing_status":1,
           "anime_id":32998,
           "anime_studios":null,
           "anime_licensors":null,
           "anime_season":null,
           "has_episode_video":true,
           "has_promotion_video":true,
           "has_video":true,
           "video_url":"\/anime\/32998\/91_Days\/video",
           "anime_url":"\/anime\/32998\/91_Days",
           "anime_image_path":"https:\/\/myanimelist.cdn-dena.com\/r\/96x136\/images\/anime\/13\/80515.jpg?s=7f9c599ca9dafb64a261bac475b44132",
           "is_added_to_list":false,
           "anime_media_type_string":"TV",
           "anime_mpaa_rating_string":"R",
           "start_date_string":null,
           "finish_date_string":null,
           "anime_start_date_string":"22-03-15",
           "anime_end_date_string":"01-10-16",
           "days_string":null,
           "storage_string":"",
           "priority_string":"Low"
        }
    """
    anime = []
    for mal_anime in json:
        anime.append({
            'name': mal_anime['anime_title'],
            'id_ref': int(mal_anime['anime_id']),
            'consumption_status': _convert_status_code_to_const(mal_anime['status']),
            'is_rewatch': bool(mal_anime['is_rewatching']),
            'score': int(mal_anime['score']),
            'progress': int(mal_anime['num_watched_episodes']),
            'start_date': _convert_json_date(mal_anime['start_date_string']),
            'finished_date': _convert_json_date(mal_anime['finish_date_string']),
        })

    return anime


def _convert_json_date(text):
    """Return the datetime.date object from the JSON anime list date strings.

    Return None if date is a placeholder, or the information is missing.
    """
    if text is None or text.startswith('00-00-'):
        return None

    try:
        return datetime.strptime(text, '%d-%m-%y').date()
    except ValueError:  # pragma: no cover
        # It is likely that MAL has changed their format
        logging.error('Unable to parse the date text "%s" from an anime list', text)
        return None


def _convert_status_code_to_const(code):
    return {
        1: ConsumptionStatus.consuming,
        2: ConsumptionStatus.completed,
        3: ConsumptionStatus.on_hold,
        4: ConsumptionStatus.dropped,
        6: ConsumptionStatus.backlog,
    }[code]
