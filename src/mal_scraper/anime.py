import logging
from datetime import datetime

from bs4 import BeautifulSoup

from .consts import AiringStatus, Format, Retrieved, Season
from .exceptions import MissingTagError, ParseError
from .mal_utils import get_date
from .requester import request_passthrough


logger = logging.getLogger(__name__)

# Future interface?
# def retrieve_iterative(id_refs, concurrency=10, requester='request_limiter'):
#     # id_refs = int or Iterable[int]
#     pass


def retrieve_anime(id_ref=1, requester=request_passthrough):
    """mal_scraper.retrieve_anime(id_ref=1, requester)

    Return the information for a particular show.

    This will raise exceptions unless we properly and fully retrieve and process
    the web-page.

    Args:
        id_ref (int, optional): Internal show identifier.
        requester (requests-like, optional): HTTP request maker
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
                    'airing_started': datetime,
                    'airing_finished': datetime, or None when MAL does not know,
                    'airing_premiere': tuple(Year (int), Season (mal_scraper.Season)),
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
                meta, data = mal_scraper.retrieve_anime(next_anime)
            except mal_scraper.ParseError as err:
                logger.error('Investigate page %s with error %d', err.url, err.code)
            except Network and Request Errors:
                pass  # TODO docs, retry etc.
            else:
                mycode.save_data(data, when=meta['when'])

            next_anime = meta['id_ref'] + 1

    .. py:sig:: mal_scrape.retrieve_anime(id_ref=1, requester)
    """
    url = get_url_from_id_ref(id_ref)

    response = requester.get(url)
    response.raise_for_status()  # May raise

    soup = BeautifulSoup(response.content, 'html.parser')
    data = retrieve_anime_from_soup(soup)  # May raise

    meta = {
        'when': datetime.utcnow(),
        'id_ref': id_ref,
    }

    return Retrieved(meta, data)


def get_url_from_id_ref(id_ref):
    return 'http://myanimelist.net/anime/{:d}'.format(id_ref)


def retrieve_anime_from_soup(soup):
    """Return the anime information from a soup of HTML.

    Args:
        soup (Soup): BeatifulSoup object

    Returns:
        A data dictionary::

            {
                'name': str,
                'name_english': str,
                'format': mal_scraper.Format,
                'episodes': int,
                'airing_status': TODO,
                'airing_started': TODO,
                'airing_finished': TODO,
                'airing_premiere': TODO,
            }

    Raises:
        ParseError: If any component of the page could not be processed
            or was unexpected.
    """
    process = {
        'name': _get_name,
        'name_english': _get_english_name,
        'format': _get_format,
        'episodes': _get_episodes,
        'airing_status': _get_airing_status,
        'airing_started': _get_start_date,
        'airing_finished': _get_end_date,
        'airing_premiere': _get_airing_premiere,
    }

    data = {}
    for tag, func in process.items():
        try:
            result = func(soup)
        except ParseError as err:
            logger.debug('Failed to process tag %s', tag)
            err.specify_tag(tag)
            raise

        data[tag] = result

    return data


def _get_name(soup):
    tag = soup.find('span', itemprop='name')
    if not tag:
        raise MissingTagError('name')

    text = tag.string
    return text


def _get_english_name(soup):
    pretag = soup.find('span', string='English:')
    if not pretag:
        raise MissingTagError('english name')

    text = pretag.next_sibling.strip()
    return text


def _get_format(soup):
    pretag = soup.find('span', string='Type:')
    if not pretag:
        raise MissingTagError('type')

    text = pretag.find_next('a').string.strip().upper()
    format_ = {
        'TV': Format.tv
    }.get(text, None)

    if not format_:  # pragma: no cover
        # Either we missed a format, or MAL changed the webpage
        raise ParseError('type', 'Unknown format for the text "{}"'.format(text))

    return format_


def _get_episodes(soup):
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
        raise ParseError('episodes', 'Unable to convert text "%s" to int' % episodes_text)

    return episodes_number


def _get_airing_status(soup):
    pretag = soup.find('span', string='Status:')
    if not pretag:
        raise MissingTagError('status')

    status_text = pretag.next_sibling.strip().lower()
    status = {
        'finished airing': AiringStatus.finished,
        'currently airing': AiringStatus.ongoing,
    }.get(status_text, None)

    if not status:  # pragma: no cover
        # MAL probably changed the website
        raise ParseError('status', 'Unable to identify text "%s"' % status_text)

    return status


def _get_start_date(soup):
    pretag = soup.find('span', string='Aired:')
    if not pretag:
        raise MissingTagError('aired')

    aired_text = pretag.next_sibling.strip()
    start_text = aired_text.split(' to ')[0]

    try:
        start_date = get_date(start_text)
    except ValueError:  # pragma: no cover
        # MAL probably changed their website
        raise ParseError('airing start date', 'Cannot process text "%s"' % start_text)

    return start_date


def _get_end_date(soup):
    pretag = soup.find('span', string='Aired:')
    if not pretag:
        raise MissingTagError('aired')

    aired_text = pretag.next_sibling.strip()
    end_text = aired_text.split(' to ')[1]

    if end_text == '?':
        return None

    try:
        end_date = get_date(end_text)
    except ValueError:  # pragma: no cover
        # MAL probably changed their website
        raise ParseError('airing end date', 'Cannot process text "%s"' % end_text)

    return end_date


def _get_airing_premiere(soup):
    pretag = soup.find('span', string='Premiered:')
    if not pretag:
        raise MissingTagError('premiered')

    season, year = pretag.find_next('a').string.lower().split(' ')

    season = Season.mal_to_enum(season)
    if season is None:
        # MAL probably changed their website
        raise ParseError('premiered', 'Unable to identify season "%s"' % season)

    try:
        year = int(year)
    except (ValueError, TypeError):  # pragma: no cover
        # MAL probably changed their website
        raise ParseError('premiered', 'Unable to identify year "%s"' % year)

    return (year, season)
