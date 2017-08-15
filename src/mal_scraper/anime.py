import itertools
import requests
import re
from datetime import datetime

from bs4 import BeautifulSoup

from .consts import Retrieved
from .exceptions import MissingTagError, ParseError
from .requester import request_passthrough


_SEASONS_ = ["Spring", "Summer", "Fall", "Winter"]
_FORMATS_ = ['TV', 'Movie', 'OVA', 'ONA', 'Special', 'Music', 'Unknown']
_STATUS_ = ['Finished Airing', 'Not yet aired', 'Currently Airing']
_RATINGS_ = ['None', 'G', 'PG', 'PG-13', 'R - 17+', 'R+', 'Rx']


# _SOURCES_ = ['Manga', '4-koma manga', 'Web manga', 'Visual Novel',
#             'Light novel', 'Original', 'Novel', 'Game', 'Other', 'Unknown', 'Picture book']

def get_anime(ani_id, requester=request_passthrough):

    url = "https://myanimelist.net/anime/" + str(ani_id) + "/a/characters"
    response = requester.get(url)

    try:
        response.raise_for_status()  # May raise

        soup = BeautifulSoup(response.content, 'html.parser')
        data = get_anime_from_soup(soup)  # May raise
        data['id'] = str(ani_id)
        meta = {
            'when': datetime.utcnow(),
            'response': response,
        }
        return Retrieved(meta, data)

    except requests.HTTPError:
        print('error ', url, response.status_code)
        if int(response.status_code) < 400:
            raise RuntimeError('Error {}, this should not happen'.format(response.status_code))
        pass
    except ParseError:
        print("Tag not found.")
        pass

    return [{}, {}]


def get_anime_from_soup(soup):
    process = [
        ('name', _get_name),
        ('name_japanese', _get_japanese_name),
        ('name_english', _get_english_name),
        ('format', _get_format),
        ('episodes', _get_episodes),
        ('airing_status', _get_airing_status),
        ('airing_started', _get_start_date),
        ('airing_finished', _get_end_date),
        ('airing_premiere', _get_airing_premiere),
        ('producers', _get_producers),
        ('licensors', _get_licensors),
        ('studios', _get_studios),
        ('source', _get_source),
        ('genres', _get_genres),
        ('duration', _get_duration),
        ('mal_age_rating', _get_mal_age_rating),
        ('mal_score', _get_mal_score),
        ('mal_scored_by', _get_mal_scored_by),
        ('mal_rank', _get_mal_rank),
        ('mal_popularity', _get_mal_popularity),
        ('mal_members', _get_mal_members),
        ('mal_favourites', _get_mal_favourites),

        ('char_voice', _get_char_voice),
        ('anime_staff', _get_staff)
    ]

    data = {}
    for tag, func in process:
        try:
            result = func(soup)
        except TypeError:
            result = func(soup, data)
        except ParseError as err:
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


def _get_japanese_name(soup):
    pretag = soup.find('span', string='Japanese:')

    if not pretag:
        return ''

    text = pretag.next_sibling.strip()
    return text


def _get_english_name(soup):
    pretag = soup.find('span', string='English:')

    # This is not always present (https://myanimelist.net/anime/15)
    if not pretag:
        return ''

    text = pretag.next_sibling.strip()
    return text


def _get_source(soup):
    pretag = soup.find('span', string='Source:')

    if not pretag:
        return ''

    text = pretag.next_sibling.strip()
    return text


def _get_duration(soup):
    pretag = soup.find('span', string='Duration:')

    if not pretag:
        return ''

    text = pretag.next_sibling.strip()
    return text


def _get_format(soup):
    pretag = soup.find('span', string='Type:')
    if not pretag:
        raise MissingTagError('type')

    for text in itertools.islice(pretag.next_siblings, 3):
        text = text.string.strip()
        if text:
            break

    else:
        text = None
    format_ = text

    return format_


def _get_iter_tags(soup, tag):
    pretag = soup.find('span', string=tag)
    if not pretag:
        raise MissingTagError(tag.split(':')[0])

    arr = []
    for a_tag in pretag.parent.contents:
        b = a_tag.string.split(',')[0].strip()
        if b != '\n' and b != ' ' and b != '' and b != tag:
            arr.append(b)

    return arr


def _get_producers(soup):
    search = 'Producers:'
    return _get_iter_tags(soup, search)


def _get_licensors(soup):
    search = 'Licensors:'
    return _get_iter_tags(soup, search)


def _get_studios(soup):
    search = 'Studios:'
    return _get_iter_tags(soup, search)


def _get_genres(soup):
    search = 'Genres:'
    return _get_iter_tags(soup, search)


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
        raise ParseError('Unable to convert text {} to int'.format(episodes_text))

    return episodes_number


def _get_airing_status(soup):
    pretag = soup.find('span', string='Status:')
    if not pretag:
        raise MissingTagError('status')

    status = pretag.next_sibling.string.strip()

    return status


def _get_start_date(soup):
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
        raise ParseError('Unable to identify date from {}'.format(start_text))

    return start_date


def _get_end_date(soup):
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
        raise ParseError('Unable to identify date from {}'.format(end_text))

    return end_date


def _get_airing_premiere(soup, data):
    pretag = soup.find('span', string='Premiered:')
    if not pretag:
        # Film: https://myanimelist.net/anime/5
        # OVA: https://myanimelist.net/anime/44
        # ONA: https://myanimelist.net/anime/574
        # Missing Special
        # Music: https://myanimelist.net/anime/3642
        # Unknown: https://myanimelist.net/anime/33352
        skip = (_FORMATS_[1], _FORMATS_[2], _FORMATS_[3], _FORMATS_[4], _FORMATS_[5], _FORMATS_[6])
        if data['format'] in skip:
            return None
        else:
            raise MissingTagError('premiered')

    # '?': https://myanimelist.net/anime/3624
    if pretag.next_sibling.string.strip() == '?':
        return None

    season, year = pretag.find_next('a').string.split(' ')

    if season not in _SEASONS_:
        # MAL probably changed their website
        raise ParseError('Unable to identify season from {}'.format(season))

    try:
        year = int(year)
    except (ValueError, TypeError):  # pragma: no cover
        # MAL probably changed their website
        raise ParseError('Unable to identify year from {}'.format(year))

    return [year, season]


def _get_mal_age_rating(soup):
    pretag = soup.find('span', string='Rating:')
    if not pretag:
        raise MissingTagError('Rating')

    full_text = pretag.next_sibling.strip()
    rating_text = full_text.split('(')[0]
    if not rating_text.startswith('R - 17+'):
        rating_text = rating_text.split(' - ')[0]  # A little hacky for PG-13

    rating = rating_text.strip()
    if rating not in _RATINGS_:
        raise ParseError('Unable to identify age rating from {} part of {}'.format(rating_text, full_text))

    return rating


def _get_mal_score(soup):
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
        raise ParseError('Unable to identify rating from {}'.format(rating_text))


def _get_mal_scored_by(soup):
    pretag = soup.find('span', string='Score:')
    if not pretag:
        raise MissingTagError('Score')

    count_text = pretag.find_next_siblings('span')[1].string.strip().replace(',', '')
    try:
        return int(count_text)
    except ValueError:
        raise ParseError('Unable to identify #people scoring from {}'.format(count_text))


def _get_mal_rank(soup):
    pretag = soup.find('span', string='Ranked:')
    if not pretag:
        raise MissingTagError('Ranked')

    full_text = pretag.next_sibling.strip()
    # Not aired yet and some R+ anime are excluded
    # excluded_age_ratings = (
    #     _RATINGS_[0], _RATINGS_[4], _RATINGS_[5], _RATINGS_[6]
    # )
    if full_text == 'N/A':
        return None

    number_value = full_text.replace(',', '').replace('#', '')
    try:
        return int(number_value)
    except ValueError:
        raise ParseError('Unable to identify rank {}'.format(full_text))


def _get_mal_popularity(soup):
    pretag = soup.find('span', string='Popularity:')
    if not pretag:
        raise MissingTagError('Popularity')

    full_text = pretag.next_sibling.strip()
    number_value = full_text.replace(',', '').replace('#', '')
    try:
        return int(number_value)
    except ValueError:
        raise ParseError('Unable to identify popularity {}'.format(full_text))


def _get_mal_members(soup):
    pretag = soup.find('span', string='Members:')
    if not pretag:
        raise MissingTagError('Members')

    full_text = pretag.next_sibling.strip()
    number_value = full_text.replace(',', '')
    try:
        return int(number_value)
    except ValueError:
        raise ParseError('Unable to identify #members {}'.format(full_text))


def _get_mal_favourites(soup):
    pretag = soup.find('span', string='Favorites:')
    if not pretag:
        raise MissingTagError('Favorites')

    full_text = pretag.next_sibling.strip()
    number_value = full_text.replace(',', '')
    try:
        return int(number_value)
    except ValueError:
        raise ParseError('Unable to identify #favourites {}'.format(full_text))


def _get_char_voice(soup):
    a = soup.find_all(href=re.compile("go=characters"))[0].parent.parent
    x = soup.find_all(href=re.compile("t=staff"))[0].parent.parent
    e = []
    _next = a.next_sibling
    while _next != x:
        w = []
        try:
            for q in _next.tr.find_all('small'):
                try:
                    w.append([q.parent.parent.a.get('href').split('/')[4], q.parent.parent.a.string.strip(),
                              q.string.strip()])
                except:
                    pass
            e.append(w)
        except:
            pass
        try:
            _next = _next.next_sibling
        except:
            break

    return e


def _get_staff(soup):
    a = soup.find_all(href=re.compile("t=staff"))[0].parent.parent
    e = []
    for i in a.next_siblings:
        try:
            for q in i.tr.find_all('small'):
                try:
                    e.append([q.parent.parent.a.get('href').split('/')[4], q.parent.parent.a.string.strip(),
                              q.string.strip()])
                except:
                    pass
        except:
            pass

    return e


def get_date(_str):
    try:
        s = datetime.strptime(_str, '%b %d, %Y')
        return [s.year, s.month, s.day]
    except:
        pass

    try:
        s = datetime.strptime(_str, '%b, %Y')
        return [s.year, s.month, None]
    except:
        pass

    try:
        s = datetime.strptime(_str, '%Y')
        return [s.year, None, None]
    except:
        pass

    return [None, None, None]
