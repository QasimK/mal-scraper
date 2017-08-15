__version__ = "0.3.0"

# Import Public API
from .anime import get_anime  # noqa
from .consts import AgeRating, AiringStatus, ConsumptionStatus, Format, Season  # noqa

# Don't use this
FORCE_HTTP = False
