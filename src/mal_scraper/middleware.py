# Core
# Archive.org-Redirect [when, requested-url, actual-url]
# Rate-limiter (max_rate=2/s, num_429_retries=2?)
# Auto-Retry [500, 502, 503, 504, 408] (num_times=2) [404-once]
# User-discover

# Request.meta object?

import logging
import time
from collections import OrderedDict
from datetime import datetime
from functools import reduce

import requests
from requests.adapters import HTTPAdapter
# TODO: urllib3 import change: http://docs.python-requests.org/en/master/community/updates/#id14
from requests.packages import urllib3

logger = logging.getLogger(__name__)


class Middleware:
    """Allow the middleware to wrap the next one."""

    def __init__(self):
        self.next_middleware = None

    def __call__(self, next_middleware):
        self.next_middleware = next_middleware
        return self


class ArchiveDotOrgRedirect(Middleware):
    """TODO: This.

    Modify response.scraper_meta with::

        {
            'when':  (datetime) Date when archive.org scraped the page,
        }
    """

    def get(self, url, *args, **kwargs):
        archive_url = self.convert_to_archive_url(url)
        meta, response = self.next_middleware.get(archive_url, *args, **kwargs)
        meta['when'] = 'todo'  # TODO
        return meta, response

    @staticmethod
    def convert_to_archive_url(url):
        return url  # TODO


class AutoRetry(Middleware):
    """Retry requests upon particular HTTP responses with constant back-off."""

    def __init__(self, *args, http_codes=None, retries=2, backoff_secs=30, **kwargs):
        super().__init__(*args, **kwargs)
        self.http_codes = http_codes or []
        self.retries = retries
        self.backoff_secs = backoff_secs

    def get(self, *args, **kwargs):
        return self.get_with_retry(self.retries, args, kwargs)

    def get_with_retry(self, retries_left, args, kwargs):
        meta, response = self.next_middleware.get(*args, **kwargs)
        if response.status_code in self.http_codes and retries_left:
            # Failure, and we can retry, so ignore that response and retry
            logger.warning(
                'Request failed with HTTP Code "%d". Sleeping for %.1f seconds...',
                response.status_code, self.backoff_secs
            )
            time.sleep(self.backoff_secs)
            return self.get_with_retry(retries_left - 1, args, kwargs)
        else:
            # Return success, or we cannot retry so return the failure
            return meta, response


class RateLimiter(Middleware):
    """Rate limit requests, with exponential back-off in-case of 429."""

    def __init__(self, *args, rate='1/s', retries_429=2, **kwargs):
        super().__init__(*args, **kwargs)
        if not rate.endswith('/s'):
            raise RuntimeError('Rate only supports n/s syntax.')
        self.min_secs = 1 / float(rate[:-2])
        self.sleep_secs = self.min_secs
        self.retries_429 = retries_429
        self.last_request_at = time.monotonic()

    def get(self, *args, **kwargs):
        return self.get_with_429_retry(self.retries_429, args, kwargs)

    def get_with_429_retry(self, retries_left, args, kwargs):
        sleep_secs = max(0, self.last_request_at + self.sleep_secs - time.monotonic())
        logger.debug('Rate limit: Sleeping for %.1f seconds...', sleep_secs)
        time.sleep(sleep_secs)

        self.last_request_at = time.monotonic()
        meta, response = self.next_middleware.get(*args, **kwargs)
        if response.status_code == 429 and retries_left:
            logger.warning('Request failed with HTTP code "429".')
            self.sleep_secs *= 2  # Exponential back-off
            return self.get_with_429_retry(retries_left - 1, args, kwargs)
        else:
            self.sleep_secs = max(self.min_secs, self.sleep_secs / 2)
            return meta, response


class RequestsWrapper:
    """Last in the middleware chain, providing a requests-like interface.

    This supports only GET as that is all we need.

    This will automatically retry on DNS lookups, socket connections and
    connection time-outs.

    """

    def __init__(self, retry_info):
        super().__init__()
        retry = urllib3.util.retry.Retry(**retry_info)
        adaptor = HTTPAdapter(max_retries=retry)
        self.session = requests.Session()
        self.session.mount('http://', adaptor)
        self.session.mount('https://', adaptor)

    def get(self, *args, **kwargs):
        """Return (meta, response)."""
        meta = dict(when=datetime.utcnow())
        # timeout = (connection timeout, read timeout)
        response = self.session.get(*args, timeout=7, verify=True, **kwargs)
        return meta, response


# Dict allows accessing the default_requester's middlewares.
default_middleware = OrderedDict([
    # TODO: Move user discovery into a middleware
    # 'mal_user_discovery': MALUserDiscovery(),

    # Be a gooder citizen
    # ('archive_org', ArchiveDotOrgRedirect()),

    # Be a good citizen (every 2.5 seconds)
    ('rate_limit', RateLimiter(rate='0.4/s', retries_429=2)),

    # Establish the middleware chain
    # https://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html#urllib3.util.retry.Retry
    ('core', RequestsWrapper(dict(
        total=5,
        connect=3,
        read=3,
        redirect=1,
        # status=3,  # Doesn't work
        # 404: Sometimes MAL returns 404 when it really isn't one!
        status_forcelist=[500, 502, 503, 504, 408, 413, 404],
        # Exponential back-off (seconds) 1=> 0, 2, 4, 8, ...
        backoff_factor=2,
    ))),
])
default_requester = reduce(lambda a, f: f(a), reversed(default_middleware.values()))
default_requester = requests
