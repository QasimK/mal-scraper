"""Can we download user information?"""

from datetime import date, datetime, timedelta

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


class TestUserStats(object):
    """Test retrieving basic stats information."""

    PROFILE_URL = 'http://myanimelist.net/profile/'

    TEST_USER = 'SparkleBunnies'  # Sorry SparkleBunniesm, 'twas a random selection...
    TEST_USER_PAGE = PROFILE_URL + TEST_USER

    TEST_LAST_ONLINE_MINS_USER = 'Sakana-san'
    TEST_LAST_ONLINE_MINS_PAGE = PROFILE_URL + TEST_LAST_ONLINE_MINS_USER

    TEST_LAST_ONLINE_HOURS_USER = 'Lucedrom'
    TEST_LAST_ONLINE_HOURS_PAGE = PROFILE_URL + TEST_LAST_ONLINE_HOURS_USER

    def test_detect_bad_download(self, mock_requests):
        """Do we get success failure if the bad is bad?"""
        mock_requests.always_mock(self.TEST_USER_PAGE, 'garbled_user_page')
        assert not mal_scraper.get_user_stats(self.TEST_USER)[0]['success']

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
            'num_anime_watching': 22,
            'num_anime_completed': 125,
            'num_anime_on_hold': 3,
            'num_anime_dropped': 1,
            'num_anime_plan_to_watch': 13,
        }

    def test_user_last_online_minutes(self, mock_requests):
        mock_requests.always_mock(self.TEST_LAST_ONLINE_MINS_PAGE, 'user_last_online_mins')

        _, info = mal_scraper.get_user_stats(self.TEST_LAST_ONLINE_MINS_USER)
        last_online = info['last_online']
        assert (datetime.utcnow() - timedelta(minutes=21)) - last_online < timedelta(minutes=1)

    def test_user_last_online_hours(self, mock_requests):
        mock_requests.always_mock(self.TEST_LAST_ONLINE_HOURS_PAGE, 'user_last_online_hours')

        _, info = mal_scraper.get_user_stats(self.TEST_LAST_ONLINE_HOURS_USER)
        last_online = info['last_online']
        assert (datetime.utcnow() - timedelta(hours=1)) - last_online < timedelta(minutes=1)


class TestUserAnimeList(object):
    """Test retrieving basic stats information."""

    LIST_URL = 'http://myanimelist.net/animelist/{username}/load.json?offset={offset:d}&status=7'

    TEST_FORBIDDEN_USERNAME = 'SparkleBunnies'
    TEST_FORBIDDEN_PAGE = LIST_URL.format(username=TEST_FORBIDDEN_USERNAME, offset=0)

    TEST_USER_SMALL_NAME = 'Littoface'  # ~100 anime
    TEST_USER_SMALL_PAGE = LIST_URL.format(username=TEST_USER_SMALL_NAME, offset=0)
    TEST_USER_SMALL_END_PAGE = LIST_URL.format(username=TEST_USER_SMALL_NAME, offset=158)

    TEST_USER_LOTS_NAME = 'Vindstot'  # 5k anime...
    TEST_USER_LOTS_LIST_PAGE = LIST_URL.format(username=TEST_USER_LOTS_NAME, offset=0)

    def test_forbidden_access(self, mock_requests):
        """"""
        mock_requests.always_mock(self.TEST_FORBIDDEN_PAGE, 'user_anime_list_forbidden', status=400)

        assert None is mal_scraper.get_user_anime_list(self.TEST_FORBIDDEN_USERNAME)

    def test_download_one_page_anime(self, mock_requests):
        """"""
        mock_requests.always_mock(self.TEST_USER_SMALL_PAGE, 'user_anime_list_small')
        mock_requests.always_mock(self.TEST_USER_SMALL_END_PAGE, 'user_anime_list_end')

        anime = mal_scraper.get_user_anime_list(self.TEST_USER_SMALL_NAME)
        assert len(anime) == 158
        assert anime[0] == {
            'name': 'Danshi Koukousei no Nichijou',
            'id_ref': 11843,
            'consumption_status': mal_scraper.ConsumptionStatus.consuming,
            'is_rewatch': False,
            'score': 0,
            'start_date': None,
            'progress': 9,
            'finished_date': None,
        }
