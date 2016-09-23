"""Can we download user information?"""

from datetime import date, datetime, timedelta

import pytest

import mal_scraper


class TestDiscovery(object):
    """Test discovery of usernames"""

    DISCOVERY_LINK = 'http://myanimelist.net/users.php'

    def test_discovery(self, mock_requests):
        """Can we discover usernames?"""
        mock_requests.always_mock(self.DISCOVERY_LINK, 'users_discovery')

        users = mal_scraper.discover_users()
        assert len(users) == 20
        assert users == {
            'WitcherEnvy', 'TrollTama', 'Kumatetsu_Rei82', 'Dragh', 'Tom_West',
            'MrNoname7890', 'Aaaavis002', 'nguyenthugiang', 'mrtnlm', 'Kaxkk',
            '9broken_angeL', 'AnimeFreak2205', 'TMZ', 'Oxenia', 'justunknown',
            '0ldboy', 'alkodrak', 'Derin', 'Insufance', 'fatalbert357',
        }

    def test_discovery_garbled_page(self, mock_requests):
        """Do we return a failure on bad pages?"""
        mock_requests.always_mock(self.DISCOVERY_LINK, 'garbled_user_discovery_page')
        users = mal_scraper.discover_users()
        assert users == set()

    def test_discovery_failed_page(self, mock_requests):
        """Do we return a failure on failed pages?"""
        mock_requests.always_mock(self.DISCOVERY_LINK, 'garbled_user_discovery_page', status=500)
        users = mal_scraper.discover_users()
        assert users is None

    def test_discovery_from_other_pages(self, mock_requests):
        """Do we automatically discover usernames from other pages?"""
        pytest.skip()  # Should this test go here?


class TestUserStats(object):
    """Test retrieving basic stats information."""

    TEST_USER = 'SparkleBunnies'  # Sorry SparkleBunniesm, 'twas a random selection...
    TEST_USER_PAGE = 'http://myanimelist.net/profile/' + TEST_USER

    def test_user_stats(self, mock_requests):
        """Do we retrieve the right stats about a user?"""
        # Always mock this because the user will change it himself
        mock_requests.always_mock(self.TEST_USER_PAGE, 'user_test_page')

        meta, info = mal_scraper.get_user_stats(self.TEST_USER)

        # Fuzzy match datetime
        retrieval = meta['scraper_retrieved_at']
        assert datetime.utcnow() - retrieval < timedelta(seconds=30)

        assert meta == {
            'success': True,
            'scraper_retrieved_at': retrieval,  # UTC Datetime
            'username': self.TEST_USER,
        }

        assert info == {
            'name': self.TEST_USER,
            'joined': date(year=2014, month=1, day=6),
            'last_online': date.today(),  # Special 'Now'
            'num_anime_watched': 22,
            'num_anime_completed': 125,
            'num_anime_on_hold': 3,
            'num_anime_dropped': 1,
            'num_anime_plan_to_watch': 13,
        }
