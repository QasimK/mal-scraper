import mal_scraper


def test_import_mal_scraper():
    """Can we import mal_scraper"""
    assert mal_scraper
    assert mal_scraper.__version__.split('.') == ['0', '1', '0']


class TestAutomaticUserDicoveryIntegration(object):
    """Can we discover users as we download pages?"""
    pass  # TODO
