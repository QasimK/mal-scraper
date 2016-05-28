import logging
from datetime import datetime

from bs4 import BeautifulSoup

from .consts import Format
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
        logger.warn('Failed to process page "%s".', url)

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

    if not format_:
        logger.warn('Unknown format for text "%s".', text)

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
    except (ValueError, TypeError):
        logger.warn('Unable to convert episodes text "%s" to int.', episodes_text)
        return None

    return episodes_number
