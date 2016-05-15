from enum import Enum


class AiringStatus(Enum):
    pre_air = 'PREAIR'
    ongoing = 'ONGOING'
    finished = 'FINISHED'


class Format(Enum):
    tv = 'TV'


class AgeRating(Enum):
    restricted = 'RESTRICTED'
