"""Utilities related to MAL."""

import re
from datetime import datetime, timedelta


last_online_minutes = re.compile(r'(?P<minutes>\d+) minutes? ago')
last_online_hours = re.compile(r'(?P<hours>\d+) hours? ago')


def get_datetime(text, relative_to=None):
    """Convert a datetime like "Oct 1, 4:29 AM"

    Timestamps that are relative "3 hours ago" can be given a base time
    in case the timestamp was generated at a different time.

    Args:
        text (str): The following examples are supported
            Oct 1, 2013 11:04 PM
            Oct 1, 4:29 AM
            Yesterday, 9:58 AM
            4 hours ago
            1 hour ago
            12 minutes ago
            1 minute ago
            Now

    Returns datetime.datetime

    Raises ValueError if the conversion fails

    Issues: Potentially locale-dependent.
    """

    relative_to = relative_to or datetime.utcnow()

    # Now
    text = text.strip()
    if text.lower() == 'now':
        return relative_to

    # x minute(s) ago
    minutes_match = last_online_minutes.match(text)
    if minutes_match is not None:
        return relative_to - timedelta(minutes=int(minutes_match.group('minutes')))

    # x hour(s) ago
    hours_match = last_online_hours.match(text)
    if hours_match is not None:
        return relative_to - timedelta(hours=int(hours_match.group('hours')))

    # Yesterday, 9:58 AM
    base = relative_to - timedelta(days=1)
    time_text = text.strip('Yesterday, ')
    try:
        time = datetime.strptime(time_text, '%I:%M %p')
    except ValueError:
        pass
    else:
        return datetime.replace(time, year=base.year, month=base.month, day=base.day)

    # Oct 1, 4:29 AM
    try:
        time = datetime.strptime(text, '%b %d, %I:%M %p')
        return datetime.replace(time, year=relative_to.year)
    except ValueError:
        pass

    # Oct 1, 2013 11:04 PM
    return datetime.strptime(text, '%b %d, %Y %I:%M %p')
