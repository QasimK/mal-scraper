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

    @classmethod
    def mal_code_to_enum(cls, code):
        """Return the enum from the MAL code, or None."""
        return {
            1: ConsumptionStatus.consuming,
            2: ConsumptionStatus.completed,
            3: ConsumptionStatus.on_hold,
            4: ConsumptionStatus.dropped,
            6: ConsumptionStatus.backlog,
        }.get(code)


@unique
class AiringStatus(Enum):
    """The airing status of a media item."""
    pre_air = 'PREAIR'  # e.g. https://myanimelist.net/anime/3786
    ongoing = 'ONGOING'
    finished = 'FINISHED'

    @classmethod
    def mal_to_enum(cls, text):
        return {
            'not yet aired': AiringStatus.pre_air,
            'finished airing': AiringStatus.finished,
            'currently airing': AiringStatus.ongoing,
        }.get(text.strip().lower())


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
        }.get(text.strip().lower())


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
        }.get(text.strip().lower())


@unique
class AgeRating(Enum):
    """The age rating of a media item.

    MAL Ratings are dubious.

    Reference: https://myanimelist.net/forum/?topicid=16816
    """
    mal_none = 'NONE'
    mal_g = 'ALL'
    mal_pg = 'CHILDREN'
    mal_t = 'TEEN'
    mal_r1 = 'RESTRICTEDONE'
    mal_r2 = 'RESTRICTEDTWO'
    mal_r3 = 'RESTRICTEDTHREE'

    @classmethod
    def mal_to_enum(cls, text):
        """Return the enum from the MAL string, or None."""
        return {
            'none': cls.mal_none,
            'g': cls.mal_g,
            'pg': cls.mal_pg,
            'pg-13': cls.mal_t,
            'r - 17+': cls.mal_r1,
            'r+':  cls.mal_r2,
            'rx': cls.mal_r3,
        }.get(text.strip().lower())
