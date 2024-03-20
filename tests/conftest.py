import os

import pytest

from secret_keeper.api import GitHubAPI


@pytest.fixture(autouse=True)
def enable_fake_downloader():
    os.environ["FAKE_DOWNLOADER"] = "true"
    yield
    del os.environ["FAKE_DOWNLOADER"]


@pytest.fixture()
def api():
    token = os.environ.get('GITHUB_PERSONAL_ACCESS_TOKEN')
    assert token is not None
    return GitHubAPI(token)
