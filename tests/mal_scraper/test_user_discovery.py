import mal_scraper


class TestAutomaticUserDicoveryIntegrationTest:
    """Can we discover users as we download pages?"""

    def test_user_discovery_from_anime_pages(self, mock_requests):
        # TODO: Use DI to not have to mock tests like this
        mal_scraper.discover_users(use_web=False)  # Empty cache
        mock_requests.optional_mock('http://myanimelist.net/anime/1')

        mal_scraper.get_anime(1)  # Populate cache

        assert mal_scraper.discover_users(use_web=False) == {
            'TheLlama', 'Polyphemus', 'DeusAnima', 'TheCriticsClub',
            'ElectricSlime', 'Mana', 'Scribbly', 'Legg91',
            'Metty', 'Darius', 'tokaicentral85', 'Ai_Sakura',
        }

    def test_user_discovery_from_user_profile_pages(self, mock_requests):
        mal_scraper.discover_users(use_web=False)  # Empty cache
        mock_requests.always_mock('http://myanimelist.net/profile/SparkleBunnies', 'user_test_page')

        mal_scraper.get_user_stats('SparkleBunnies')  # Populate cache

        assert mal_scraper.discover_users(use_web=False) == {
            'Kyle', 'Wrath', 'Cigarette', 'Skye12', 'Vacuous',
            'Subpyro', 'Roth', 'FallingUmbrella', 'HaXXspetten', 'lemoncup',
            'SparkleBunnies', 'Star_Slayer', 'Exmortus420', 'TimeToRepent', 'DatRandomDude',
            'Nekonaut', 'Exo_x', 'Turnip', 'Solos', 'Funky',
            'Mooncake', 'okies', 'Kyrex', 'Phraze', 'Senpaoi',
        }
