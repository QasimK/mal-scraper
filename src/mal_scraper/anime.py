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


def retrieve_anime(id_ref, requester=request_passthrough):
    """Return the metadata for a particular show. TODO.

    id_ref: identifier that can be used in iterations
    requester: funnel requests through a request maker, this allows
    us to limit requests globally

    Return a dictionary.
    See tests/mal_scraper/test_anime.py::test_download_first for the keys.
    """
    url = get_url_from_id_ref(id_ref)
    response = requester.get(url)
    if response.status_code != 200:
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
    retrieve = {
        'name': _get_name,
        'name_english': _get_english_name,
        'format': _get_format,
    }

    retrieved = {}
    for key, value_func in retrieve.items():
        value = value_func(soup)
        if not value:
            logger.warn('Failed to process given soup due to the missing tag "%s".', key)
            return None

        retrieved[key] = value

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
