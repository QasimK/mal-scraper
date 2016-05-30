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
        A tuple of two dicts (retrieval information, anime information).
        The retrieval information will include the keys:
            success (bool): Was *all* the information was retrieved?
                (Some keys from anime information may be missing otherwise.)
            scraper_retrieved_at (datetime): When the request was completed.
            id_ref (int): id_ref of this anime.
        The anime information will include the keys:
            See tests/mal_scraper/test_anime.py::test_download_first
    """
    url = get_url_from_id_ref(id_ref)
    response = requester.get(url)
    if not response.ok:
        logging.error('Unable to retrieve anime ({0.status_code}):\n{0.text}'.format(response))
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    success, info = _process_soup(soup)

    if not success:
        logger.warn('Failed to properly process the page "%s".', url)

    retrieval_info = {
        'success': success,
        'scraper_retrieved_at': datetime.utcnow(),
        'id_ref': id_ref,
    }

    return (retrieval_info, info)


def get_url_from_id_ref(id_ref):
    return 'http://myanimelist.net/anime/{:d}'.format(id_ref)


class ParseError(Exception):
    """The given tag could not be parsed properly"""

    def __init__(self, tag, error):
        super().__init__((tag, error))
        self.tag = tag
        self.error = error
        logger.warn('Error processing tag "%s": %s.', self.tag, self.error)

    def __repr__(self):  # pragma: no cover
        return 'ParseError(tag="{0.tag}", error="{0.error}")'.format(self)

    def __str__(self):  # pragma: no cover
        return 'Tag "{0.tag}" could not be parsed because: {0.error}.'.format(self)


class MissingTagError(ParseError):
    """The tag is missing from the soup/webpage."""

    def __init__(self, tag):
        super().__init__(tag, 'Missing from soup/webpage')


def _process_soup(soup):
    """Return (success?, metadata) from a soup of HTML.

    Returns:
        (success?, metadata) where success is only if there were zero errors.
    """
    retrieve = {
        'name': _get_name,
        'name_english': _get_english_name,
        'format': _get_format,
        'episodes': _get_episodes,
        'airing_status': _get_airing_status,
        'airing_started': _get_start_date,
        'airing_finished': _get_end_date,
        'airing_premiere': _get_airing_premiere,
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
        raise MissingTagError('aired')

    aired_text = pretag.next_sibling.strip()
    start_text = aired_text.split(' to ')[0]

    try:
        start_date = _convert_to_date(start_text)
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
        end_date = _convert_to_date(end_text)
    except ValueError:  # pragma: no cover
        # MAL probably changed their website
        raise ParseError('airing end date', 'Cannot process text "%s"' % end_text)

    return end_date


def _get_airing_premiere(soup):
    pretag = soup.find('span', string='Premiered:')
    if not pretag:
        raise MissingTagError('premiered')

    season, year = pretag.find_next('a').string.lower().split(' ')

    if season == 'fall':
        season = 'autumn'
    elif season not in ('spring', 'summer', 'autumn', 'winter'):  # pragma: no cover
        # MAL probably changed their website
        raise ParseError('premiered', 'Unable to identify season "%s"' % season)

    try:
        year = int(year)
    except (ValueError, TypeError):  # pragma: no cover
        # MAL probably changed their website
        raise ParseError('premiered', 'Unable to identify year "%s"' % year)

    return (year, season)
