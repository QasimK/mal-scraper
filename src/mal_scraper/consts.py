"""All constants/enumerations available directly from `mal_scraper.x`"""

from collections import namedtuple
from enum import Enum


Retrieved = namedtuple('Retrieved', ['meta', 'data'])
"""When successfully retrieving from a web-page

.. py:attribute:: meta

    A dict of metadata::

        {
            'id_ref': (object) ID of the media depending on the context,
            'when': (datetime) Our best guess on the date of this information,
        }

.. py:attribute:: data

    A dict of data varying on the media.
"""


class ConsumptionStatus(Enum):
    """A person's status on a media item, e.g. are they currently watching it?"""
    consuming = 'CONSUMING'
    completed = 'COMPLETED'
    on_hold = 'ONHOLD'
    dropped = 'DROPPED'
    backlog = 'BACKLOG'


class AiringStatus(Enum):
    """The airing status of a media item."""
    pre_air = 'PREAIR'
    ongoing = 'ONGOING'
    finished = 'FINISHED'


class Format(Enum):
    """The media format of a media item."""
    tv = 'TV'


class AgeRating(Enum):
    """The age rating of a media item."""
    restricted = 'RESTRICTED'
