"""All constants/enumerations are available directly from `mal_scraper.x`"""

from collections import namedtuple
from enum import Enum, unique

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


@unique
class ConsumptionStatus(Enum):
    """A person's status on a media item, e.g. are they currently watching it?"""
    consuming = 'CONSUMING'
    completed = 'COMPLETED'
    on_hold = 'ONHOLD'
    dropped = 'DROPPED'
    backlog = 'BACKLOG'


@unique
class AiringStatus(Enum):
    """The airing status of a media item."""
    pre_air = 'PREAIR'
    ongoing = 'ONGOING'
    finished = 'FINISHED'


class Season(Enum):
    """The season in a year ordered as Winter, Spring, Summer, Autumn."""
    # _order_ = 'WINTER SPRING SUMMER AUTUMN'  # py3.6? The order in a year
    winter = 'WINTER'
    spring = 'SPRING'
    summer = 'SUMMER'
    autumn = fall = 'AUTUMN'

    @classmethod
    def mal_to_enum(cls, text):
        """Return the enum from the MAL string, or None."""
        return {
            'winter': cls.winter,
            'spring': cls.spring,
            'summer': cls.summer,
            'fall': cls.autumn,
        }.get(text.lower().strip())


class Format(Enum):
    """The media format of a media item."""
    tv = 'TV'
    film = movie = 'FILM'  # https://myanimelist.net/anime/5
    ova = 'OVA'  # https://myanimelist.net/anime/44
    special = 'SPECIAL'
    ona = 'ONA'  # (Original Net Animation) https://myanimelist.net/anime/574
    music = 'MUSIC'  # Seriously? https://myanimelist.net/anime/731

    @classmethod
    def mal_to_enum(cls, text):
        """Return the enum from the MAL string, or None."""
        return {
            'tv': cls.tv,
            'movie': cls.film,
            'ova': cls.ova,
            'special': cls.special,
            'ona':  cls.ona,
            'music': cls.music,
        }.get(text.lower().strip())


@unique
class AgeRating(Enum):
    """The age rating of a media item."""
    restricted = 'RESTRICTED'
