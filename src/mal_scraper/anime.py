import itertools
import logging

from bs4 import BeautifulSoup
from requests.exceptions import RetryError

from .consts import AgeRating, AiringStatus, Format, Retrieved, Season
from .exceptions import MissingTagError, ParseError, RequestError
from .mal_utils import get_date
from .middleware import default_requester
from .user_discovery import default_user_store

logger = logging.getLogger(__name__)


def get_anime(id_ref=1, requester=default_requester):
    """Return the information for a particular show.

    You can simply enumerate through id_refs.

    This will raise exceptions unless we properly and fully retrieve and process
    the web-page.

    TODO: Genres https://myanimelist.net/info.php?go=genre
    # Broadcast? Producers? Licensors? Studios? Source? Duration?


    Args:
        id_ref (int, optional): Internal show identifier.
        requester (requests-like, optional): HTTP request maker.
            This allows us to control/limit/mock requests.

    Returns:
        :class:`.Retrieved`: with the attributes `meta` and `data`.

        `data`::

            {
                'name': str,
                'name_english': str,
                'format': mal_scraper.Format,
                'episodes': int, or None when MAL does not know,
                'airing_status': mal_scraper.AiringStatus,
                'airing_started': date, or None when MAL does not know,
                'airing_finished': date, or None when MAL does not know,
                'airing_premiere': tuple(Year (int), Season (mal_scraper.Season))
                    or None (for films, OVAs, specials, ONAs, music, or
                    if MAL does not know),
                'mal_age_rating': mal_scraper.AgeRating,
                'mal_score': float, or None when not yet aired/MAL does not know,
                'mal_scored_by': int (number of people),
                'mal_rank': int, or None when not yet aired/some R rated anime,
                'mal_popularity': int,
                'mal_members': int,
                'mal_favourites': int,
            }

        See also :class:`.Format`, :class:`.AiringStatus`, :class:`.Season`.

    Raises:
        Network and Request Errors: See Requests library.
        .ParseError: Upon processing the web-page including anything that does
            not meet expectations.

    Examples:

        Retrieve the first anime and get the next anime to retrieve::

            next_anime = 1

            try:
                meta, data = mal_scraper.get_anime(next_anime)
            except mal_scraper.ParseError as err:
                logger.error('Investigate page %s with error %d', err.url, err.code)
            except NetworkandRequestErrors:  # Pseudo-code (TODO: These docs)
                pass  # Retry?
            else:
                mycode.save_data(data, when=meta['when'])

            next_anime = meta['id_ref'] + 1
    """
    url = get_url_from_id_ref(id_ref)
    logger.debug('Retrieving anime "%s" from "%s"', id_ref, url)

    try:
        meta, response = requester.get(url)
    except RetryError as err:
        if ' 404 ' in str(err):  # Hack: 404 check
            msg = 'Anime #%d does not exist.' % id_ref
            raise RequestError(RequestError.Code.does_not_exist, msg)

        raise  # Will raise unknown retry error

    # TODO: Catch 404 HTTPError too in case not-retry

    response.raise_for_status()  # May raise

    # Dynamic user discovery
    default_user_store.store_users_from_html(response.text)

    soup = BeautifulSoup(response.content, 'html.parser')
    data = get_anime_from_soup(soup)  # May raise

    meta = {
        'when': meta['when'],
        'id_ref': id_ref,
        'response': response,
    }

    return Retrieved(meta, data)


def get_url_from_id_ref(id_ref):
    # Use HTTPS to avoid auto-redirect from HTTP (except for tests)
    from .__init__ import FORCE_HTTP
    protocol = 'http' if FORCE_HTTP else 'https'
    return '{}://myanimelist.net/anime/{:d}'.format(protocol, id_ref)


def get_anime_from_soup(soup):
    """Return the anime information from a soup of HTML.

    Args:
        soup (Soup): BeautifulSoup object

    Returns:
        A data dictionary::

            {
                'name': str,
                'name_english': str,
                'format': mal_scraper.Format,
                'episodes': int, or None when MAL does not know,
                'airing_status': mal_scraper.AiringStatus,
                'airing_started': date, or None when MAL does not know,
                'airing_finished': date, or None when MAL does not know,
                'airing_premiere': tuple(Year (int), Season (mal_scraper.Season))
                    or None (for films, OVAs, specials, ONAs, music, unknown, or
                    if MAL does not know),
                'mal_age_rating': mal_scraper.AgeRating,
                'mal_score': float, or None when not yet aired/MAL does not know,
                'mal_scored_by': int (number of people),
                'mal_rank': int, or None when not yet aired/some R rated anime,
                'mal_popularity': int,
                'mal_members': int,
                'mal_favourites': int,
            }

    Raises:
        ParseError: If any component of the page could not be processed
            or was unexpected.
    """
    process = [
        ('name', _get_name),
        ('name_english', _get_english_name),
        ('format', _get_format),
        ('episodes', _get_episodes),
        ('airing_status', _get_airing_status),
        ('airing_started', _get_start_date),
        ('airing_finished', _get_end_date),
        ('airing_premiere', _get_airing_premiere),
        ('mal_age_rating', _get_mal_age_rating),
        ('mal_score', _get_mal_score),
        ('mal_scored_by', _get_mal_scored_by),
        ('mal_rank', _get_mal_rank),
        ('mal_popularity', _get_mal_popularity),
        ('mal_members', _get_mal_members),
        ('mal_favourites', _get_mal_favourites),
    ]

    data = {}
    for tag, func in process:
        try:
            result = func(soup, data)
        except ParseError as err:
            logger.debug('Failed to process tag %s', tag)
            err.specify_tag(tag)
            raise

        data[tag] = result

    return data


def _get_name(soup, data=None):
    tag = soup.find('span', itemprop='name')
    if not tag:
        raise MissingTagError('name')

    text = tag.string
    return text


def _get_english_name(soup, data=None):
    pretag = soup.find('span', string='English:')

    # This is not always present (https://myanimelist.net/anime/15)
    if not pretag:
        return ''

    text = pretag.next_sibling.strip()
    return text


def _get_format(soup, data=None):
    pretag = soup.find('span', string='Type:')
    if not pretag:
        raise MissingTagError('type')

    for text in itertools.islice(pretag.next_siblings, 3):
        text = text.string.strip()
        if text:
            break
    else:
        text = None

    format_ = Format.mal_to_enum(text)
    if not format_:  # pragma: no cover
        # Either we missed a format, or MAL changed the webpage
        raise ParseError('Unable to identify format from "{}"'.format(text))

    return format_


def _get_episodes(soup, data=None):
    pretag = soup.find('span', string='Episodes:')
    if not pretag:
        raise MissingTagError('episodes')

    episodes_text = pretag.next_sibling.strip().lower()
    if episodes_text == 'unknown':
        return None

    try:
        episodes_number = int(episodes_text)
    except (ValueError, TypeError):  # pragma: no cover
        # MAL probably changed the webpage
        raise ParseError('Unable to convert text "%s" to int' % episodes_text)

    return episodes_number


def _get_airing_status(soup, data=None):
    pretag = soup.find('span', string='Status:')
    if not pretag:
        raise MissingTagError('status')

    status_text = pretag.next_sibling
    status = AiringStatus.mal_to_enum(status_text)

    if not status:  # pragma: no cover
        # MAL probably changed the website
        raise ParseError('Unable to identify airing status from "%s"' % status_text)

    return status


def _get_start_date(soup, data=None):
    pretag = soup.find('span', string='Aired:')
    if not pretag:
        raise MissingTagError('aired')

    aired_text = pretag.next_sibling.strip().lower()
    if aired_text == 'not available':
        return None

    start_text = aired_text.split(' to ')[0]

    try:
        start_date = get_date(start_text)
    except ValueError:  # pragma: no cover
        # MAL probably changed their website
        raise ParseError('Unable to identify date from "%s"' % start_text)

    return start_date


def _get_end_date(soup, data=None):
    pretag = soup.find('span', string='Aired:')
    if not pretag:
        raise MissingTagError('aired')

    aired_text = pretag.next_sibling.strip()
    date_range_text = aired_text.split(' to ')

    # Not all Aired tags have a date range (https://myanimelist.net/anime/5)
    try:
        end_text = date_range_text[1]
    except IndexError:
        return None

    if end_text == '?':
        return None

    try:
        end_date = get_date(end_text)
    except ValueError:  # pragma: no cover
        # MAL probably changed their website
        raise ParseError('Unable to identify date from "%s"' % end_text)

    return end_date


def _get_airing_premiere(soup, data):
    pretag = soup.find('span', string='Premiered:')
    if not pretag:
        # Film: https://myanimelist.net/anime/5
        # OVA: https://myanimelist.net/anime/44
        # ONA: https://myanimelist.net/anime/574
        # TODO: Missing Special
        # Music: https://myanimelist.net/anime/3642
        # Unknown: https://myanimelist.net/anime/33352
        skip = (Format.film, Format.ova, Format.special, Format.ona, Format.music, Format.unknown)
        if data['format'] in skip:
            return None
        else:
            raise MissingTagError('premiered')

    # '?': https://myanimelist.net/anime/3624
    if pretag.next_sibling.string.strip() == '?':
        return None

    season, year = pretag.find_next('a').string.lower().split(' ')

    season = Season.mal_to_enum(season)
    if season is None:
        # MAL probably changed their website
        raise ParseError('Unable to identify season from "%s"' % season)

    try:
        year = int(year)
    except (ValueError, TypeError):  # pragma: no cover
        # MAL probably changed their website
        raise ParseError('Unable to identify year from "%s"' % year)

    return (year, season)


def _get_mal_age_rating(soup, data=None):
    pretag = soup.find('span', string='Rating:')
    if not pretag:
        raise MissingTagError('Rating')

    full_text = pretag.next_sibling.strip()
    rating_text = full_text.split('(')[0]
    if not rating_text.startswith('R - 17+'):
        rating_text = rating_text.split(' - ')[0]  # A little hacky for PG-13

    rating = AgeRating.mal_to_enum(rating_text)
    if rating is None:
        raise ParseError(
            'Unable to identify age rating from "%s" part of "%s"' % (rating_text, full_text)
        )

    return rating


def _get_mal_score(soup, data):
    pretag = soup.find('span', string='Score:')
    if not pretag:
        raise MissingTagError('Score')

    rating_text = pretag.find_next_sibling('span').string.strip()
    # Not aired yet/MAL does not know anime are excluded
    if rating_text == 'N/A':
        return None

    try:
        return float(rating_text)
    except ValueError:
        raise ParseError('Unable to identify rating from "%s"' % rating_text)


def _get_mal_scored_by(soup, data=None):
    pretag = soup.find('span', string='Score:')
    if not pretag:
        raise MissingTagError('Score')

    count_text = pretag.find_next_siblings('span')[1].string.strip().replace(',', '')
    try:
        return int(count_text)
    except ValueError:
        raise ParseError('Unable to identify #people scoring from "%s"' % count_text)


def _get_mal_rank(soup, data):
    pretag = soup.find('span', string='Ranked:')
    if not pretag:
        raise MissingTagError('Ranked')

    full_text = pretag.next_sibling.strip()
    # Not aired yet and some R+ anime are excluded
    # Apparently some PG - 13 are excluded too, and who knows what else...
    if full_text == 'N/A':
        return None

    number_value = full_text.replace(',', '').replace('#', '')
    try:
        return int(number_value)
    except ValueError:
        raise ParseError('Unable to identify rank "%s"' % full_text)


def _get_mal_popularity(soup, data=None):
    pretag = soup.find('span', string='Popularity:')
    if not pretag:
        raise MissingTagError('Popularity')

    full_text = pretag.next_sibling.strip()
    number_value = full_text.replace(',', '').replace('#', '')
    try:
        return int(number_value)
    except ValueError:
        raise ParseError('Unable to identify popularity "%s"' % full_text)


def _get_mal_members(soup, data=None):
    pretag = soup.find('span', string='Members:')
    if not pretag:
        raise MissingTagError('Members')

    full_text = pretag.next_sibling.strip()
    number_value = full_text.replace(',', '')
    try:
        return int(number_value)
    except ValueError:
        raise ParseError('Unable to identify #members "%s"' % full_text)


def _get_mal_favourites(soup, data=None):
    pretag = soup.find('span', string='Favorites:')
    if not pretag:
        raise MissingTagError('Favorites')

    full_text = pretag.next_sibling.strip()
    number_value = full_text.replace(',', '')
    try:
        return int(number_value)
    except ValueError:
        raise ParseError('Unable to identify #favourites "%s"' % full_text)
