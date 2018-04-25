"""Can we download anime metadata?"""

from datetime import date, datetime, timedelta

import pytest

import mal_scraper


def test_get_anime_successful(mock_requests):
    """Can we retrieve the first show ever?"""
    mock_requests.optional_mock('http://myanimelist.net/anime/1')
    meta, info = mal_scraper.get_anime(1)

    # Fuzzy match datetime
    assert datetime.utcnow() - meta['when'] < timedelta(seconds=30)

    # Assert meta contained by ...
    assert meta.items() >= {
        'id_ref': 1,
    }.items()

    assert info == {
        'name': 'Cowboy Bebop',
        'name_english': 'Cowboy Bebop',
        'format': mal_scraper.Format.tv,
        'episodes': 26,  # None means unknown,
        'genre': ['Action', 'Adventure', 'Comedy', 'Drama', 'Sci-Fi', 'Space']
        'airing_status': mal_scraper.AiringStatus.finished,
        'airing_started': date(year=1998, month=4, day=3),
        'airing_finished': date(year=1999, month=4, day=24),
        'airing_premiere': (1998, mal_scraper.Season.spring),
        'mal_age_rating': mal_scraper.AgeRating.mal_r1,
        'mal_score': 8.83,
        'mal_scored_by': 232183,
        'mal_rank': 22,
        'mal_popularity': 31,
        'mal_members': 415050,
        'mal_favourites': 26287,
    }


def test_parsing_a_bad_page_raises_an_error(mock_requests):
    mock_requests.always_mock(
        'http://myanimelist.net/anime/1',
        'garbled_anime_page',
    )
    with pytest.raises(mal_scraper.ParseError):
        mal_scraper.get_anime(1)


def test_parsing_name_english_that_is_missing(mock_requests):
    mock_requests.optional_mock('http://myanimelist.net/anime/15')
    meta, data = mal_scraper.get_anime(15)
    assert data['name_english'] == ''


def test_parsing_episodes_that_is_unknown(mock_requests):
    """Do we return None for an unknown number of episodes?"""
    mock_requests.always_mock(
        'http://myanimelist.net/anime/32105',
        'unknown_episodes',
    )
    assert mal_scraper.get_anime(32105)[1]['episodes'] is None


def test_parsing_airing_that_is_unknown(mock_requests):
    mock_requests.always_mock('http://myanimelist.net/anime/35102', 'anime_unknown_aired')
    data = mal_scraper.get_anime(35102).data
    assert data['airing_started'] is None
    assert data['airing_finished'] is None


def test_parsing_airing_started_with_year_and_month_only(mock_requests):
    """Do we return the year and month if the day is missing?"""
    mock_requests.optional_mock('http://myanimelist.net/anime/730')
    meta, data = mal_scraper.get_anime(730)
    assert data['airing_started'] == date(1994, 4, 1)  # "Apr 1994"


def test_parsing_airing_started_with_year_only(mock_requests):
    """Do we return the year and month if the day is missing?"""
    mock_requests.optional_mock('http://myanimelist.net/anime/1190')
    meta, data = mal_scraper.get_anime(1190)
    assert data['airing_started'] == date(2003, 1, 1)  # "2003"


def test_parsing_end_date_that_is_unknown(mock_requests):
    mock_requests.always_mock(
        'http://myanimelist.net/anime/32105',
        'unknown_end_date',
    )
    assert mal_scraper.get_anime(32105)[1]['airing_finished'] is None


def test_parsing_airing_started_without_end_date(mock_requests):
    mock_requests.optional_mock('http://myanimelist.net/anime/5')
    meta, data = mal_scraper.get_anime(5)
    assert data['airing_started'] == date(2001, 9, 1)
    assert data['airing_finished'] is None


@pytest.mark.parametrize('id_ref', [
    5,  # Film
    44,  # OVA
    574,  # ONA
    3624,  # '?'
    3642,  # Music
])
def test_parsing_missing_premiere(mock_requests, id_ref):
    mock_requests.optional_mock('http://myanimelist.net/anime/%d' % id_ref)
    assert mal_scraper.get_anime(id_ref).data['airing_premiere'] is None


def test_user_discovery_on_anime_page(mock_requests):
    mock_requests.optional_mock('http://myanimelist.net/anime/1')
    meta = mal_scraper.get_anime(1).meta
    html = meta['response'].text

    usernames = list(mal_scraper.user_discovery.discover_users_from_html(html))
    assert usernames == [
        'TheLlama', 'TheLlama', 'TheLlama', 'TheLlama', 'Polyphemus',
        'Polyphemus', 'Polyphemus', 'Polyphemus', 'DeusAnima', 'DeusAnima',
        'DeusAnima', 'DeusAnima', 'TheCriticsClub', 'TheCriticsClub',
        'TheCriticsClub', 'TheCriticsClub', 'ElectricSlime', 'Mana', 'Scribbly',
        'Legg91', 'Metty', 'Darius', 'tokaicentral85', 'Ai_Sakura',
    ]
