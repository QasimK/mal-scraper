import os
import urllib.request
from base64 import b64encode

import pytest
import responses


class ResponsesWrapper:
    """Mock ALL requests more easily using saved files when use_live.

    You can ALWAYS mock a request if there is no safe live page to use.

    AUTO_DIR is used for optional_mock because it is like a cache.
    MANUAL_DIR is used to always_mock because you are deliberately saving this.
    """
    TODO_DIR = os.path.join(os.path.dirname(__file__), '0_todo_responses')
    AUTO_DIR = os.path.join(os.path.dirname(__file__), 'auto_responses')
    MANUAL_DIR = os.path.join(os.path.dirname(__file__), 'manual_responses')

    def __init__(self, rsps, use_live):
        self.rsps = rsps
        self.use_live = use_live  # Use live unless we are faking

    def optional_mock(self, url):
        """Add an automatic mock for a URL, this can be disabled if desired."""
        filename = self._encode('get', url)
        filepath = os.path.join(self.AUTO_DIR, filename)

        if os.path.isfile(filepath):
            # Mock the response unless we are using live
            if not self.use_live:  # pragma: no cover
                with open(filepath, 'rb') as fin:
                    body = fin.read()
            else:  # pragma: no cover
                # Make the request manually, avoiding requests which is mocked.
                with urllib.request.urlopen(url) as nin:
                    body = nin.read()

            self.rsps.add(responses.GET, url, body=body, match_querystring=True)
        else:  # pragma: no cover
            # Produce a file to mock this request (needs to be checked manually)
            self._save_url(url, filename)

    def always_mock(self, url, filename, status=200):
        """Always mock this response, never test against the live url.

        Args:
            url (str): The URL to mock.
            filename (str): The file inside self.MANUAL_DIR to use.
        """
        filepath = os.path.join(self.MANUAL_DIR, filename)
        if os.path.isfile(filepath):
            with open(filepath, 'rb') as fin:
                self.rsps.add(
                    responses.GET,
                    url,
                    body=fin.read(),
                    status=status,
                    match_querystring=True
                )
        else:  # pragma: no cover
            # Produce a file to mock this request (needs to be checked manually)
            self._save_url(url, filename)

    def _save_url(self, url, filename):  # pragma: no cover
        os.makedirs(self.TODO_DIR, exist_ok=True)
        todo_filepath = os.path.join(self.TODO_DIR, filename)

        try:
            nin_ = urllib.request.urlopen(url)
        except urllib.error.HTTPError as error:
            nin_ = error

        with nin_ as nin, open(todo_filepath, 'wb') as fout:
            fout.write(nin.read())

        print('Response Mocked:', url)
        print('File in TODO responses directory:', filename)
        print('If you want to edit the file, move it into manual responses and use always_mock.')
        print('Otherwise, move it into the auto responses folder.')
        assert False, 'Look at stdout because a response was mocked for you.'

    @staticmethod
    def _encode(method, url):
        """Return a base64 string from a string."""
        # Decode: b64decode(b64.encode('utf-8')).decode('utf-8').split(':+:')
        return b64encode((method + ':+:' + url).encode('utf-8')).decode('utf-8')


@pytest.yield_fixture(autouse=True)
def mock_requests(request):
    """Mock all requests unless the LIVE_RESPONSES environ has been set."""
    use_live = bool(os.environ.get('LIVE_RESPONSES', False))
    with responses.RequestsMock(assert_all_requests_are_fired=True) as rsps:
        yield ResponsesWrapper(rsps, use_live)
