import mal_scraper


def test_import_mal_scraper():
    """Can we import mal_scraper"""
    assert mal_scraper
    assert mal_scraper.__version__.split('.') == ['0', '3', '0']


class TestAutomaticUserDicoveryIntegration:
    """Can we discover users as we download pages?"""
    pass  # TODO
