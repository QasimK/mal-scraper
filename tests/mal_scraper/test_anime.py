"""Can we download anime metadata?"""

from datetime import datetime, timedelta

import mal_scraper


def test_download_first(mock_requests):
    """Can we retrieve the first show ever?"""
    mock_requests.add('http://myanimelist.net/anime/1')
    info = mal_scraper.retrieve_anime(1)

    # Fuzzy match datetime
    retrieval = info['scraper_retrieved_at']
    assert datetime.utcnow() - retrieval < timedelta(seconds=30)

    assert info == {
        'scraper_retrieved_at': retrieval,
        'id_ref': 1,
        'name': 'Cowboy Bebop',
        'name_english': 'Cowboy Bebop',
        'format': mal_scraper.Format.tv,
        # 'episodes': 26,  # None means unknown
        # 'airing_status': mal_scraper.AiringStatus.finished,
        # 'airing_started': datetime(year=1998, month=4, day=3),
        # 'airing_finished': datetime(year=1999, month=4, day=24),
        # 'airing_premiere': (2016, 'spring'),
        # 'age_rating': mal_scraper.AgeRating.restricted,
        # 'mal_score': 0,
        # 'mal_rank': 0,
        # 'mal_popularity': 0,
        # 'mal_members': 0,
        # 'mal_favourites': 0,
    }


def test_download_first_fail(mock_requests):
    """Do we get None if the page was bad??"""
    mock_requests.add('http://myanimelist.net/anime/1', fake='bla')
    assert mal_scraper.retrieve_anime(1) is None
