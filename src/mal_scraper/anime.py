import logging
from datetime import datetime

from bs4 import BeautifulSoup

from .consts import AiringStatus, Format
from .requester import request_passthrough


logger = logging.getLogger(__name__)

# Future interface?
# def retrieve_iterative(id_refs, concurrency=10, requester='request_limiter'):
#     # id_refs = int or Iterable[int]
#     pass


def retrieve_anime(id_ref=1, requester=request_passthrough):
    """Return the metadata for a particular show. TODO.

    Args:
        id_ref (Optional(int)): Internal show identifier
        requester (Optional(requests-like)): HTTP request maker
            This allows us to control/limit/mock requests.

    Return:
        A dictionary.
        See tests/mal_scraper/test_anime.py::test_download_first for the keys.
    """
    url = get_url_from_id_ref(id_ref)
    response = requester.get(url)
    if not response.ok:
        logging.error('Unable to retrieve anime ({0.status_code}):\n{0.text}'.format(response))
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    info = _process_soup(soup)

    # Add additional meta information
    if info:
        info['scraper_retrieved_at'] = datetime.utcnow()
        info['id_ref'] = id_ref
    else:
        logger.error('Failed to process page "%s".', url)

    return info


def get_url_from_id_ref(id_ref):
    return 'http://myanimelist.net/anime/{:d}'.format(id_ref)


def _process_soup(soup):
    """Return metadata from a soup of HTML."""
    retrieved = {
        'name': _get_name(soup),
        'name_english': _get_english_name(soup),
        'format': _get_format(soup),
        'episodes': _get_episodes(soup),
        'airing_status': _get_airing_status(soup),
        'airing_started': _get_start_date(soup),
        'airing_finished': _get_end_date(soup),
        'airing_premiere': _get_airing_premiere(soup),
    }

    if not all(retrieved.values()):
        logger.warn('Failed to process given soup due a missing tag.')
        return None

    # -1 episodes should be presented as None
    if retrieved['episodes'] == -1:
        retrieved['episodes'] = None

    return retrieved


def _get_name(soup):
    tag = soup.find('span', itemprop='name')
    if not tag:
        logger.warn('No "name" tag found.')
        return None

    text = tag.string
    return text


def _get_english_name(soup):
    pretag = soup.find('span', string='English:')
    if not pretag:
        logger.warn('No "english name" tag found.')
        return None

    text = pretag.next_sibling.strip()
    return text


def _get_format(soup):
    pretag = soup.find('span', string='Type:')
    if not pretag:
        logger.warn('No "type" tag found.')
        return None

    text = pretag.find_next('a').string.strip().upper()
    format_ = {
        'TV': Format.tv
    }.get(text, None)

    if not format_:  # pragma: no cover
        # Either we missed a format, or MAL changed the webpage
        logger.warn('Unknown format for text "%s".', text)
        return None

    return format_


def _get_episodes(soup):
    pretag = soup.find('span', string='Episodes:')
    if not pretag:
        logger.warn('No "episodes" tag found.')
        return None

    episodes_text = pretag.next_sibling.strip().lower()
    if episodes_text == 'unknown':
        return -1

    try:
        episodes_number = int(episodes_text)
    except (ValueError, TypeError):  # pragma: no cover
        # MAL probably changed the webpage
        logger.warn('Unable to convert episodes text "%s" to int.', episodes_text)
        return None

    return episodes_number


def _get_airing_status(soup):
    pretag = soup.find('span', string='Status:')
    if not pretag:
        logger.warn('No "status" tag found.')
        return None

    status_text = pretag.next_sibling.strip().lower()
    status = {
        'finished airing': AiringStatus.finished,
    }.get(status_text, None)

    if not status:
        logger.warn('Unable to identify status text "%s".', status_text)
        return None

    return status


def _convert_to_date(text):
    """Convert MAL text to a datetime stamp.

    Args:
        text (str): like "Apr 3, 1998"

    Returns:
        date object or None.

    Raises:
        ValueError: if the conversion fails

    Issues:
        - This may be locale dependent
    """
    return datetime.strptime(text, '%b %d, %Y').date()


def _get_start_date(soup):
    pretag = soup.find('span', string='Aired:')
    if not pretag:
        logger.warn('No "aired" tag found.')
        return None

    aired_text = pretag.next_sibling.strip()
    start_text = aired_text.split(' to ')[0]

    try:
        start_date = _convert_to_date(start_text)
    except ValueError:
        logger.warn('Failed to get start date from text "%s".', start_text)
        return None

    return start_date


def _get_end_date(soup):
    pretag = soup.find('span', string='Aired:')
    if not pretag:
        logger.warn('No "aired" tag found.')
        return None

    aired_text = pretag.next_sibling.strip()
    end_text = aired_text.split(' to ')[1]

    try:
        end_date = _convert_to_date(end_text)
    except ValueError:
        logger.warn('Failed to get end date from text "%s".', end_text)
        return None

    return end_date


def _get_airing_premiere(soup):
    pretag = soup.find('span', string='Premiered:')
    if not pretag:
        logger.warn('No "premiered" tag found.')
        return None

    season, year = pretag.find_next('a').string.lower().split(' ')

    if season == 'fall':
        season = 'autumn'
    elif season not in ('spring', 'summer', 'winter'):
        logger.warn('Unable to identify season "%s".', season)
        return None

    try:
        year = int(year)
    except (ValueError, TypeError):
        logger.warn('Unable to identify anime year "%s".', year)

    return (year, season)
