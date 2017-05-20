"""Retrieve information about a user.

Users are identified as `user_id` which are username strings.

This is really tricky to scrape from MAL because we cannot enumerate users.
We must use a user-discovery process which has limitations (see discover_users).

TODO: User discovery from all other pages gets dumped here waiting for discover_users
to be called.

Possible alternative:
- http://graph.anime.plus/
"""

import logging
from datetime import datetime
from functools import partial

from bs4 import BeautifulSoup

from .consts import ConsumptionStatus, Retrieved
from .exceptions import MissingTagError, ParseError, RequestError
from .mal_utils import get_date, get_datetime
from .middleware import default_requester
from .user_discovery import default_user_store

from requests.exceptions import RetryError

logger = logging.getLogger(__name__)
user_cache = set()  # Global store of discovered users


def get_user_stats(user_id, requester=default_requester):
    """Return statistics about a particular user.

    # TODO: Return Gender Male/Female
    # TODO: Return Birthday "Nov", "Jan 27, 1997"
    # TODO: Return Location "England"
    # e.g. https://myanimelist.net/profile/Sakana-san

    Args:
        user_id (string): The username identifier of the MAL user.
        requester (requests-like, optional): HTTP request maker.
            This allows us to control/limit/mock requests.

    Returns:
        :class:`.Retrieved`: with the attributes `meta` and `data`.

        `data`::

            {
                'name': (str) user_id/username,
                'last_online': (datetime),
                'joined': (datetime),
                'num_anime_watching': (int),
                'num_anime_completed': (int),
                'num_anime_on_hold': (int),
                'num_anime_dropped': (int),
                'num_anime_plan_to_watch': (int),
            }

    Raises:
        requests.exceptions.RequestException: See Requests library.
        .RetryError: When the auto-retry fails.
        .RequestError: :code:`RequestError.Code.does_not_exist` if the user_id is
            invalid (i.e. the username does not exist).
            See :class:`.RequestError.Code`.
        .ParseError: Upon processing the web-page including anything that does
            not meet expectations.
    """
    url = get_profile_url_for_user(user_id)
    logger.debug('Retrieving profile for "%s" from "%s"', user_id, url)

    try:
        meta, response = requester.get(url)
    except RetryError as err:
        if ' 404 ' in str(err):  # Hack: 404 check
            msg = 'User "%s" does not exist' % user_id
            raise RequestError(RequestError.Code.does_not_exist, msg)

        raise  # Will raise unknown retry error

    # TODO: Catch 404 HTTPError too in case not-retry

    response.raise_for_status()  # May raise

    # Auto user_id discovery
    default_user_store.store_users_from_html(response.text)

    soup = BeautifulSoup(response.content, 'html.parser')
    data = get_user_stats_from_soup(soup)  # May raise

    meta = {
        'when': meta['when'],
        'user_id': user_id,
        'response': response,
    }

    return Retrieved(meta, data)


def get_user_anime_list(user_id, requester=default_requester):
    """Return the anime listed by the user on their profile.

    This will make multiple network requests (possibly > 10).

    TODO: Return Meta

    Args:
        user_id (str): The user identifier (i.e. the username).
        requester (requests-like, optional): HTTP request maker.
            This allows us to control/limit/mock requests.

    Returns:
        A list of anime-info where each anime-info is the following dict::

            {
                'name': (string) name of the anime,
                'id_ref': (id_ref) can be used with mal_scraper.get_anime,
                'consumption_status': (mal_scraper.ConsumptionStatus),
                'is_rewatch': (bool),
                'score': (int) 0-10,
                'progress': (int) 0+ number of episodes watched,
                'tags': (set of strings) user tags,

                The following tags have been removed for now:
                'start_date': (date, or None) may be missing,
                'finish_date': (date, or None) may be missing or not finished,
            }

        See also :class:`.ConsumptionStatus`.

    Raises:
        Network and Request Errors: See Requests library.
        .RequestError: :code:`RequestError.Code.forbidden` if the user's info is
            private, or :code:`RequestError.Code.does_not_exist` if the user_id is
            invalid. See :class:`.RequestError.Code`.
        .ParseError: Upon processing the web-page including anything that does
            not meet expectations.
    """
    anime = []
    has_more_anime = True
    while has_more_anime:
        url = get_anime_list_url_for_user(user_id, len(anime))
        meta, response = requester.get(url)
        if not response.ok:  # Raise an exception
            if response.status_code in (400, 401):
                msg = 'Access to user "%s"\'s anime list is forbidden' % user_id
                raise RequestError(RequestError.Code.forbidden, msg)
            elif response.status_code == 404:
                msg = 'User "%s" does not exist' % user_id
                raise RequestError(RequestError.Code.does_not_exist, msg)

            response.raise_for_status()  # Will raise

        additional_anime = get_user_anime_list_from_json(response.json())
        if additional_anime:
            anime.extend(additional_anime)
        else:
            has_more_anime = False

    return anime


# --- URLs ---


def get_profile_url_for_user(user_id):
    """Return the URL of the user's profile page.

    Args:
        user_id (string): Username

    Returns:
        url (str)
    """
    # Use HTTPS to avoid auto-redirect from HTTP (except for tests)
    from .__init__ import FORCE_HTTP  # noqa
    protocol = 'http' if FORCE_HTTP else 'https'
    return '{}://myanimelist.net/profile/{:s}'.format(protocol, user_id)


def get_anime_list_url_for_user(user_id, offset=0):
    """Return the url to the JSON feed for the given user.

    Args:
        user_id (str): Username
        offset (int): Feed returns paginated view, use offset to traverse

    Returns:
        url (str)
    """
    from .__init__ import FORCE_HTTP  # noqa
    protocol = 'http' if FORCE_HTTP else 'https'
    url = '{protocol}://myanimelist.net/animelist/{user_id}/load.json?offset={offset:d}&status=7'
    return url.format(protocol=protocol, user_id=user_id, offset=offset)


# --- Parse Profile Page ---


def get_user_stats_from_soup(soup):
    """Return the user stats from a soup of HTML.

    Args:
        soup (Soup): BeautifulSoup object

    Returns:
        A data dictionary::

            {
                'name': (str) user_id/username,
                'last_online': (datetime),
                'joined': (datetime),
                'num_anime_watching': (int),
                'num_anime_completed': (int),
                'num_anime_on_hold': (int),
                'num_anime_dropped': (int),
                'num_anime_plan_to_watch': (int),
            }

    TODO: RequestError.
    TODO: Test RequestError https://myanimelist.net/profile/Tuzo
    Raises:
        RequestError: does_not_exist if the user has never logged in.
        ParseError: If any component of the page could not be processed
            or was unexpected.
    """
    process = [
        ('name', _get_name),
        ('last_online', _get_last_online),
        ('joined', _get_joined),
        ('num_anime_watching', _get_num_anime_watching),
        ('num_anime_completed', _get_num_anime_completed),
        ('num_anime_on_hold', _get_num_anime_on_hold),
        ('num_anime_dropped', _get_num_anime_dropped),
        ('num_anime_plan_to_watch', _get_num_anime_plan_to_watch),
    ]

    data = {}
    for tag, func in process:
        try:
            result = func(soup)
        except ParseError as err:
            logger.debug('Failed to process tag %s', tag)
            err.specify_tag(tag)
            raise

        data[tag] = result

    if data['last_online'] is None:
        raise RequestError(RequestError.Code.does_not_exist, 'User has never logged in')

    return data


def _get_name(soup):
    tag = soup.find('h1')
    if not tag:  # pragma: no cover
        raise MissingTagError('name (outer)')

    innertag = tag.find('span')
    if not innertag:  # pragma: no cover
        raise MissingTagError('name (inner)')

    title_text = innertag.contents[0].strip()
    if not title_text.endswith("'s Profile"):
        raise ParseError('Unable to identify name on the Profile from "%s"' % title_text)

    username = title_text[:-len("'s Profile")]
    return username


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

    num_text = stat_tag.next_sibling.string.strip().replace(',', '')

    try:
        num = int(num_text)
    except (TypeError, ValueError):  # pragma: no cover
        # MAL probably changed their website
        raise ParseError(tag_name, 'Unable to convert text "%s" to int' % num_text)

    return num


_get_num_anime_watching = partial(_get_num_anime_stats, classname='watching')
_get_num_anime_completed = partial(_get_num_anime_stats, classname='completed')
_get_num_anime_on_hold = partial(_get_num_anime_stats, classname='on_hold')
_get_num_anime_dropped = partial(_get_num_anime_stats, classname='dropped')
_get_num_anime_plan_to_watch = partial(_get_num_anime_stats, classname='plan_to_watch')


# --- Parse User's Anime List Page(s) ---


def get_user_anime_list_from_json(json):
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
           "anime_image_path":"https:\/\/myanimelist.cdn-dena.com\/r\/96x136\/images\/anime\/13\/80515.jpg?s=7f9c599ca9dafb64a261bac475b44132",  # noqa
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

    Raises:
        .ParseError: Upon processing the web-page including anything that does
            not meet expectations.
    """
    anime = []
    for mal_anime in json:
        # Start date and finish date removed for now
        # try:
        #     start_date = _convert_json_date(mal_anime['start_date_string'])
        # except ParseError as err:
        #     err.specify_tag('start_date_string')
        #     raise

        # try:
        #     finish_date = _convert_json_date(mal_anime['finish_date_string'])
        # except ParseError as err:
        #     err.specify_tag('finish_date_string')
        #     raise

        tags = set(
            filter(
                bool,  # Ignore empty tags
                map(
                    str.strip,  # Splitting by ',' leaves whitespaces
                    str(mal_anime['tags']).split(','),  # Produce a list
                    # Sometimes the tag is an integer itself
                )
            )
        )

        anime.append({
            'name': mal_anime['anime_title'],
            'id_ref': int(mal_anime['anime_id']),
            'consumption_status': ConsumptionStatus.mal_code_to_enum(mal_anime['status']),
            'is_rewatch': bool(mal_anime['is_rewatching']),
            'score': int(mal_anime['score']),
            # 'start_date': start_date,
            'progress': int(mal_anime['num_watched_episodes']),
            # 'finish_date': finish_date,
            'tags': tags,
        })

    return anime


def _convert_json_date(text):
    """Return the datetime.date object from the JSON anime list date strings.

    IMPORTANT: There is a problem with determining the locale of the date.
    It varies between users and there doesn't seem to be a way to find out
    what it is (directly).

    Date Examples::

        00-00-98  # Only year is known
        12-00-98  # Year and month is known
        12-28-98  # Full date

    Returns:
        datetime, or None if there is no date.

    Raises:
        .ParseError: if the text cannot be processed.
    """
    if text is None:
        return None

    # TODO: Test
    # We must fill in the information
    # We cannot provide approximates, so say it was on the 1st :(
    text = text.replace('00-', '01-')

    try:
        # Or %d-%m-%y
        return datetime.strptime(text, '%m-%d-%y').date()
    except ValueError:  # pragma: no cover
        # It is likely that MAL has changed their format
        raise ParseError('Unable to parse the date text "%s" from an anime list' % text)
