from datetime import date, datetime, timedelta

import pytest

from mal_scraper import mal_utils


class TestGetDatetime(object):

    nowish = datetime.utcnow()
    yesterdayish = nowish - timedelta(days=1)

    @pytest.mark.parametrize('text,expected_datetime', [
        ('Now', datetime.utcnow()),
        ('Oct 1, 2013 11:04 PM', datetime(year=2013, month=10, day=1, hour=23, minute=4)),
        ('Oct 1, 4:29 AM', datetime(year=nowish.year, month=10, day=1, hour=4, minute=29)),
        ('Yesterday, 9:58 AM', yesterdayish.replace(hour=9, minute=58)),
        ('4 hours ago', nowish - timedelta(hours=4)),
        ('1 hour ago', nowish - timedelta(hours=1)),
        ('12 minutes ago', nowish - timedelta(minutes=12)),
        ('1 minute ago', nowish - timedelta(minutes=1)),
        ('Now', nowish),
    ])
    def test_get_datetime(self, text, expected_datetime):
        assert (expected_datetime - mal_utils.get_datetime(text)) < timedelta(minutes=1)

        time_difference = mal_utils.get_datetime(text, self.nowish) - mal_utils.get_datetime(text)
        assert time_difference < timedelta(minutes=1)

    @pytest.mark.parametrize('text,expected_datetime', [
        ('Now', yesterdayish),
        ('Oct 1, 2013 11:04 PM', datetime(year=2013, month=9, day=30, hour=23, minute=4)),
        ('Oct 1, 4:29 AM', datetime(year=nowish.year, month=9, day=30, hour=4, minute=29)),
        ('Yesterday, 9:58 AM', yesterdayish.replace(hour=9, minute=58) - timedelta(days=1)),
        ('4 hours ago', yesterdayish - timedelta(hours=4)),
        ('1 hour ago', yesterdayish - timedelta(hours=1)),
        ('12 minutes ago', yesterdayish - timedelta(minutes=12)),
        ('1 minute ago', yesterdayish - timedelta(minutes=1)),
        ('Now', yesterdayish),
    ])
    def test_get_datetime_relative_to_yesterday(self, text, expected_datetime):
        time_difference = expected_datetime - mal_utils.get_datetime(text, self.yesterdayish)
        assert time_difference < timedelta(minutes=1)


@pytest.mark.parametrize('text,expected_date', [
    ('Apr 3, 1998', date(year=1998, month=4, day=3))
])
def test_get_date(text, expected_date):
    assert expected_date == mal_utils.get_date(text)
