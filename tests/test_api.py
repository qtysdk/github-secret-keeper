from datetime import datetime
import os

from secret_keeper.api import GitHubAPI, encrypt_secret


def test_datetime_parser(api: GitHubAPI):
    print(api.parse_datetime("2024-03-20T08:59:54Z"))
    assert api.parse_datetime("2024-03-20T08:59:54Z") == datetime.fromisoformat(
        "2024-03-20 08:59:54+00:00"
    )


def test_api_call(api: GitHubAPI):
    secrets = api.list_secrets("qtysdk", "github-secret-keeper")
    assert "PYTEST" in secrets
    assert secrets["PYTEST"].name == "PYTEST"


def test_update_secret(api: GitHubAPI):
    success = api.update_secret(
        "qtysdk", "github-secret-keeper", "PYTEST_test_update_secret", "123"
    )
    assert success
