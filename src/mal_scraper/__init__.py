__version__ = "0.3.0"

# Import Public API
from .anime import get_anime  # noqa
from .consts import AgeRating, AiringStatus, ConsumptionStatus, Format, Season  # noqa
from .exceptions import ParseError  # noqa
from .users import (  # noqa
    discover_users, discover_users_from_html, get_user_anime_list, get_user_stats
)

# Don't use this
FORCE_HTTP = False
