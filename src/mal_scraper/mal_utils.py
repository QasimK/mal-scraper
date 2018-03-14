"""Utilities related to MAL."""

import re
from datetime import datetime, timedelta

last_online_minutes = re.compile(r'(?P<minutes>\d+) minutes? ago')
last_online_hours = re.compile(r'(?P<hours>\d+) hours? ago')


def get_datetime(text, relative_to=None):  # noqa: C901 (code complexity)
    """Convert a datetime like "Oct 1, 4:29 AM"

    Timestamps that are relative "3 hours ago" can be given a base time
    in case the timestamp was generated at a different time.

    Args:
        text (str): The following examples are supported (with varying accuracy)
            Oct 1, 2013 11:04 PM
            Oct 1, 4:29 AM
            Today, 1:22 AM
            Yesterday, 9:58 AM
            4 hours ago
            1 hour ago
            12 minutes ago
            1 minute ago
            Now
            Never

    Returns:
        datetime.datetime, or None if the text is "Never".

    Raises:
        ValueError if the conversion fails

    Issues:
        - Potentially locale-dependent.
    """
    relative_to = relative_to or datetime.utcnow()
    text = text.strip().lower()

    if text == 'never':
        return None

    # Now
    if text == 'now':
        return relative_to

    # x minute(s) ago
    minutes_match = last_online_minutes.match(text)
    if minutes_match is not None:
        return relative_to - timedelta(minutes=int(minutes_match.group('minutes')))

    # x hour(s) ago
    hours_match = last_online_hours.match(text)
    if hours_match is not None:
        return relative_to - timedelta(hours=int(hours_match.group('hours')))

    if text.startswith(('today,', 'yesterday,')):
        if text.startswith('today'):
            # Today, 1:22 AM
            base = relative_to
        elif text.startswith('yesterday'):
            # Yesterday, 9:58 AM
            base = relative_to - timedelta(days=1)
        else:
            raise RuntimeError('Invalid Branch')

        time_text = text.split(',')[1].lstrip()
        try:
            time = datetime.strptime(time_text, '%I:%M %p')
        except ValueError:
            pass
        else:
            return datetime.replace(time, year=base.year, month=base.month, day=base.day)

    # Oct 1, 4:29 AM
    try:
        time = datetime.strptime(text, '%b %d, %I:%M %p')
    except ValueError:
        pass
    else:
        return datetime.replace(time, year=relative_to.year)

    # Oct 1, 2013 11:04 PM
    return datetime.strptime(text, '%b %d, %Y %I:%M %p')


def get_date(text):
    """Return a datetime from a date like "Apr 3, 1998", or None.

    Args:
        text (str): The following examples are supported
            Apr 3, 1998
            Apr, 1994   (This will convert to 1st Apr 1994 as a best guess;
                         https://myanimelist.net/anime/730)
            2003        (This will convert to 1st Jan 2003 as a best guess;
                         https://myanimelist.net/anime/1190)

    Returns:
        datetime.date

    Raises:
        ValueError if the conversion fails

    Issues:
        This may be locale dependent
    """
    try:
        return datetime.strptime(text, '%b %d, %Y').date()
    except ValueError:
        pass

    try:
        return datetime.strptime(text, '%b, %Y').date()
    except ValueError:
        pass

    try:
        return datetime.strptime(text, '%Y').date()
    except ValueError:
        pass
