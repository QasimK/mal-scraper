from enum import Enum


class ConsumptionStatus(Enum):
    consuming = 'CONSUMING'
    completed = 'COMPLETED'
    on_hold = 'ONHOLD'
    dropped = 'DROPPED'
    backlog = 'BACKLOG'


class AiringStatus(Enum):
    pre_air = 'PREAIR'
    ongoing = 'ONGOING'
    finished = 'FINISHED'


class Format(Enum):
    tv = 'TV'


class AgeRating(Enum):
    restricted = 'RESTRICTED'
