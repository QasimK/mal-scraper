__version__ = "0.4.0"

# Import Public API
from .anime import get_anime  # noqa
from .consts import AgeRating, AiringStatus, ConsumptionStatus, Format, Season  # noqa
from .exceptions import ParseError, RequestError  # noqa
from .user_discovery import discover_users  # noqa
from .users import get_user_anime_list, get_user_stats  # noqa

# Don't use this
FORCE_HTTP = False
