"""Can we download user information?"""

from datetime import date, datetime, timedelta

import pytest
import requests

import mal_scraper


class TestDiscovery(object):
    """Test discovery of usernames."""

    DISCOVERY_LINK = 'http://myanimelist.net/users.php'

    # TODO: Test Cache
    # TODO: Test fall-back

    def test_web_discovery(self, mock_requests):
        """Can we discover usernames?"""
        mock_requests.always_mock(self.DISCOVERY_LINK, 'users_discovery')

        users = mal_scraper.discover_users(use_cache=False, use_web=True)
        assert len(users) == 20
        assert users == {
            'WitcherEnvy', 'TrollTama', 'Kumatetsu_Rei82', 'Dragh', 'Tom_West',
            'MrNoname7890', 'Aaaavis002', 'nguyenthugiang', 'mrtnlm', 'Kaxkk',
            '9broken_angeL', 'AnimeFreak2205', 'TMZ', 'Oxenia', 'justunknown',
            '0ldboy', 'alkodrak', 'Derin', 'Insufance', 'fatalbert357',
        }

    def test_web_discovery_on_garbled_page(self, mock_requests):
        """Do we return a failure on bad pages?"""
        mock_requests.always_mock(self.DISCOVERY_LINK, 'garbled_user_discovery_page')
        users = mal_scraper.discover_users(use_cache=False, use_web=True)
        assert users == set()

    def test_web_discovery_on_failed_page(self, mock_requests):
        """Do we return a failure on failed pages?"""
        mock_requests.always_mock(self.DISCOVERY_LINK, 'garbled_user_discovery_page', status=500)
        with pytest.raises(requests.exceptions.HTTPError):
            mal_scraper.discover_users(use_cache=False, use_web=True)


class TestUserStats:
    """Test retrieving basic stats information."""

    PROFILE_URL = 'http://myanimelist.net/profile/'

    TEST_USER = 'SparkleBunnies'  # Sorry SparkleBunniesm, 'twas a random selection...
    TEST_USER_PAGE = PROFILE_URL + TEST_USER

    TEST_LAST_ONLINE_NOW_USER = 'Ichigo_Shiba'
    TEST_LAST_ONLINE_NOW_PAGE = PROFILE_URL + TEST_LAST_ONLINE_NOW_USER

    TEST_LAST_ONLINE_MINS_USER = 'El_Anciano'
    TEST_LAST_ONLINE_MINS_PAGE = PROFILE_URL + TEST_LAST_ONLINE_MINS_USER

    TEST_LAST_ONLINE_HOURS_USER = 'snip-snip'
    TEST_LAST_ONLINE_HOURS_PAGE = PROFILE_URL + TEST_LAST_ONLINE_HOURS_USER

    TEST_LAST_ONLINE_YESTERDAY_USER = 'Nyanloveanimes'
    TEST_LAST_ONLINE_YESTERDAY_PAGE = PROFILE_URL + TEST_LAST_ONLINE_YESTERDAY_USER

    TEST_LAST_ONLINE_DATE_USER = 'Elizi'
    TEST_LAST_ONLINE_DATE_PAGE = PROFILE_URL + TEST_LAST_ONLINE_DATE_USER

    def test_detect_bad_download(self, mock_requests):
        mock_requests.always_mock(self.TEST_USER_PAGE, 'garbled_user_page')
        with pytest.raises(mal_scraper.ParseError):
            mal_scraper.get_user_stats(self.TEST_USER)

    def test_user_does_not_exist(self, mock_requests):
        mock_requests.always_mock(
            'http://myanimelist.net/profile/asdghiuhunircg',
            'user_does_not_exist',
            status=404,
        )

        with pytest.raises(mal_scraper.RequestError) as err:
            mal_scraper.get_user_stats('asdghiuhunircg')
        assert err.value.code == mal_scraper.RequestError.Code.does_not_exist

    def test_user_stats(self, mock_requests):
        """Do we retrieve the right stats about a user?"""
        # Always mock this because the user will change it himself
        mock_requests.always_mock(self.TEST_USER_PAGE, 'user_test_page')

        meta, data = mal_scraper.get_user_stats(self.TEST_USER)

        # Fuzzy match datetime
        assert datetime.utcnow() - meta['when'] < timedelta(seconds=30)

        # Assert meta contained by ...
        assert meta.items() >= {
            'user_id': self.TEST_USER,
        }.items()

        # Fuzzy match datetime - last online was "10 hours ago"
        last_online = data['last_online']
        assert datetime.utcnow() - last_online < timedelta(hours=11)

        assert data == {
            'name': self.TEST_USER,
            'joined': date(year=2014, month=1, day=6),
            'last_online': last_online,  # Already checked
            'num_anime_watching': 14,
            'num_anime_completed': 129,
            'num_anime_on_hold': 9,
            'num_anime_dropped': 4,
            'num_anime_plan_to_watch': 16,
        }

    def test_user_last_online_now(self, mock_requests):
        mock_requests.always_mock(self.TEST_LAST_ONLINE_NOW_PAGE, 'user_last_online_now')

        data = mal_scraper.get_user_stats(self.TEST_LAST_ONLINE_NOW_USER).data
        last_online = data['last_online']
        assert datetime.utcnow() - last_online < timedelta(seconds=10)

    def test_user_last_online_minutes(self, mock_requests):
        # 23 minutes ago
        mock_requests.always_mock(self.TEST_LAST_ONLINE_MINS_PAGE, 'user_last_online_mins')

        data = mal_scraper.get_user_stats(self.TEST_LAST_ONLINE_MINS_USER).data
        last_online = data['last_online']
        assert (datetime.utcnow() - timedelta(minutes=23)) - last_online < timedelta(minutes=1)

    def test_user_last_online_hours(self, mock_requests):
        mock_requests.always_mock(self.TEST_LAST_ONLINE_HOURS_PAGE, 'user_last_online_hours')

        data = mal_scraper.get_user_stats(self.TEST_LAST_ONLINE_HOURS_USER).data
        last_online = data['last_online']  # '6 hours ago'
        assert (datetime.utcnow() - timedelta(hours=6)) - last_online < timedelta(seconds=10)

    def test_user_last_online_yesterday(self, mock_requests):
        # Yesterday, 9:01 AM
        mock_requests.always_mock(
            self.TEST_LAST_ONLINE_YESTERDAY_PAGE,
            'user_last_online_yesterday',
        )

        data = mal_scraper.get_user_stats(self.TEST_LAST_ONLINE_YESTERDAY_USER).data
        yesterday = datetime.utcnow() - timedelta(days=1)
        expected_date = yesterday.replace(hour=9, minute=1, second=0, microsecond=0)
        assert data['last_online'] == expected_date

    def test_user_last_online_date(self, mock_requests):
        # May 4, 8:09 AM
        mock_requests.always_mock(self.TEST_LAST_ONLINE_DATE_PAGE, 'user_last_online_date')

        _, info = mal_scraper.get_user_stats(self.TEST_LAST_ONLINE_DATE_USER)
        this_year = datetime.utcnow().year
        assert datetime(year=this_year, month=5, day=4, hour=8, minute=9) == info['last_online']

    def test_user_discovery_on_user_profile_page(self, mock_requests):
        mock_requests.always_mock('http://myanimelist.net/profile/SparkleBunnies', 'user_test_page')
        meta = mal_scraper.get_user_stats('SparkleBunnies').meta
        html = meta['response'].text

        usernames = list(mal_scraper.user_discovery.discover_users_from_html(html))
        assert usernames == [
            'SparkleBunnies', 'SparkleBunnies', 'SparkleBunnies', 'SparkleBunnies', 'AkitoKazuki',
            'Exmortus420', 'ChannelOrange', 'Brandon', 'Zeally', 'Daedalus',
            'HaXXspetten', 'Kagami', 'no_good_name', 'BlackFIFA19', 'Ichigo_Shiba',
            'Ichigo_Shiba', 'Sacchie', 'Sacchie', 'Woodenspoon', 'Woodenspoon',
            'Teddy_Bear56', 'Teddy_Bear56', 'Speeku', 'Speeku', 'stonemask',
            'stonemask', 'IIDarkII', 'IIDarkII', 'ThisNameSucks', 'ThisNameSucks',
            'Z6890', 'Z6890', 'BKZekken', 'BKZekken', 'Woodenspoon',
            'Woodenspoon', 'ChannelOrange', 'ChannelOrange', 'Padgit', 'Padgit',
        ]


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

    TEST_USER_TAGS_NAME = 'reltats'
    TEST_USER_TAGS_PAGE = LIST_URL.format(username=TEST_USER_TAGS_NAME, offset=0)
    TEST_USER_TAGS_END_PAGE = LIST_URL.format(username=TEST_USER_TAGS_NAME, offset=263)

    def test_non_ok_download(self, mock_requests):
        mock_requests.always_mock(self.TEST_FORBIDDEN_PAGE, 'user_anime_list_forbidden', status=401)

        with pytest.raises(mal_scraper.RequestError) as err:
            mal_scraper.get_user_anime_list(self.TEST_FORBIDDEN_USERNAME)
        assert err.value.code == mal_scraper.RequestError.Code.forbidden

    def test_forbidden_access(self, mock_requests):
        mock_requests.always_mock(self.TEST_FORBIDDEN_PAGE, 'user_anime_list_forbidden', status=400)

        with pytest.raises(mal_scraper.RequestError) as err:
            mal_scraper.get_user_anime_list(self.TEST_FORBIDDEN_USERNAME)
        assert err.value.code == mal_scraper.RequestError.Code.forbidden

    def test_download_one_page_anime(self, mock_requests):
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
            # 'start_date': None,
            'progress': 9,
            # 'finish_date': None,
            'tags': [],
        }

    def test_user_tags(self, mock_requests):
        mock_requests.always_mock(self.TEST_USER_TAGS_PAGE, 'user_anime_list_tags')
        mock_requests.always_mock(self.TEST_USER_TAGS_END_PAGE, 'user_anime_list_tags_end')

        anime_list = mal_scraper.get_user_anime_list(self.TEST_USER_TAGS_NAME)
        assert len(anime_list) == 263
        assert anime_list[99]['tags'] == [
            'A masterpiece of failures. Yami wo Kirisaku',
            'LOAD THIS DRYER!',
        ]
