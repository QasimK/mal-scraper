import logging

logger = logging.getLogger(__name__)


class MalScraperError(Exception):
    """All exceptions raised by this library."""


class ParseError(MalScraperError):
    """The given tag could not be parsed properly"""

    def __init__(self, tag, error):
        super().__init__((tag, error))
        self.tag = tag
        self.error = error
        logger.error('Error processing tag "%s": %s.', self.tag, self.error)

    def __repr__(self):  # pragma: no cover
        return 'ParseError(tag="{0.tag}", error="{0.error}")'.format(self)

    def __str__(self):  # pragma: no cover
        return 'Tag "{0.tag}" could not be parsed because: {0.error}.'.format(self)


class MissingTagError(ParseError):
    """The tag is missing from the soup/webpage."""

    def __init__(self, tag):
        super().__init__(tag, 'Missing from soup/webpage')
