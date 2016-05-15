import os
import urllib.request
from base64 import b64encode, b64decode

import pytest
import responses


class ResponsesWrapper:
    """Mock ALL requests more easily using saved files when use_live.

    You can pass fake in instead which will ALWAYS use the fake response.
    """
    RESPONSES_DIR = os.path.join(os.path.dirname(__file__), 'responses')

    def __init__(self, rsps, use_live):
        self.rsps = rsps
        self.use_live = use_live  # Use live unless we are faking

    def add(self, url, method='get', fake=None):
        assert method == 'get', 'TODO: Implement other methods.'
        filename = self._encode(method, url)
        filepath = os.path.join(self.RESPONSES_DIR, filename)

        pass_method = {
            'get': responses.GET
        }[method]

        if fake:
            # Always mock the response whether it is live or not
            self.rsps.add(pass_method, url, body=fake)
        elif os.path.isfile(filepath):  # pragma: no cover
            # Only mock the response if we are not using live
            # Otherwise allow a live request to be made
            if not self.use_live:
                with open(filepath, 'rb') as fin:
                    body = fin.read()
                self.rsps.add(pass_method, url, body=body)
            else:
                # To avoid an error let's make the request and add it in as mocked
                with urllib.request.urlopen(url) as nin:
                    self.rsps.add(pass_method, url, body=nin.read())
        else:  # pragma: no cover
            # Produce a file to mock this request (needs to be checked manually)
            todo_filename = 'TODO_' + filename
            todo_filepath = os.path.join(self.RESPONSES_DIR, todo_filename)
            with urllib.request.urlopen(url) as nin,\
                    open(todo_filepath, 'wb') as fout:
                fout.write(nin.read())
            print('Response Mocked:', method, url)
            print('File in responses tests directory: ', todo_filename)
            print('Look at it and rename it by removing "TODO_".')
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
