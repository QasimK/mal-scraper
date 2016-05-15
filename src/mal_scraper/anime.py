import logging
from datetime import datetime

from bs4 import BeautifulSoup

from .requester import request_passthrough


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

    return info


def get_url_from_id_ref(id_ref):
    return 'http://myanimelist.net/anime/{:d}'.format(id_ref)


def _process_soup(soup):
    """Return metadata from a soup of HTML."""
    name = _get_name(soup)
    english_name = _get_english_name(soup)

    if not all([name, english_name]):
        return None

    return {
        'name': name,
        'name_english': english_name,
    }


def _get_name(soup):
    tag = soup.find('span', itemprop='name')
    if not tag:
        return None

    text = tag.string
    return text


def _get_english_name(soup):
    pretag = soup.find('span', string='English:')
    if not pretag:
        return None

    text = pretag.next_sibling.strip()
    return text
