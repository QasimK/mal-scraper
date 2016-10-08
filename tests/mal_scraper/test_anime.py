"""Can we download anime metadata?"""

from datetime import date, datetime, timedelta

import mal_scraper


def test_download_first(mock_requests):
    """Can we retrieve the first show ever?"""
    mock_requests.optional_mock('http://myanimelist.net/anime/1')
    meta, info = mal_scraper.retrieve_anime(1)

    # Fuzzy match datetime
    retrieval = meta['scraper_retrieved_at']
    assert datetime.utcnow() - retrieval < timedelta(seconds=30)

    assert meta == {
        'success': True,
        'scraper_retrieved_at': retrieval,  # UTC Datetime
        'id_ref': 1,
    }

    assert info == {
        'name': 'Cowboy Bebop',
        'name_english': 'Cowboy Bebop',
        'format': mal_scraper.Format.tv,
        'episodes': 26,  # None means unknown
        'airing_status': mal_scraper.AiringStatus.finished,
        'airing_started': date(year=1998, month=4, day=3),  # None means unknown
        'airing_finished': date(year=1999, month=4, day=24),  # None means unknown
        'airing_premiere': (1998, 'spring'),
        # 'age_rating': mal_scraper.AgeRating.restricted,
        # 'mal_score': 0,
        # 'mal_rank': 0,
        # 'mal_popularity': 0,
        # 'mal_members': 0,
        # 'mal_favourites': 0,
    }


def test_download_first_fail(mock_requests):
    """Do we get a failed success if the page was bad?"""
    mock_requests.always_mock(
        'http://myanimelist.net/anime/1',
        'garbled_anime_page',
    )
    assert not mal_scraper.retrieve_anime(1)[0]['success']


def test_parsing_unknown_episodes(mock_requests):
    """Do we return None for an unknown number of episodes?"""
    mock_requests.always_mock(
        'http://myanimelist.net/anime/32105',
        'unknown_episodes',
    )

    assert mal_scraper.retrieve_anime(32105)[1]['episodes'] is None


def test_parsing_unknown_end_date(mock_requests):
    mock_requests.always_mock(
        'http://myanimelist.net/anime/32105',
        'unknown_end_date',
    )

    assert mal_scraper.retrieve_anime(32105)[1]['airing_finished'] is None
