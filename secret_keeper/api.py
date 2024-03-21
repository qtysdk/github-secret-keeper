from datetime import datetime, timezone
import json
from dataclasses import dataclass
from io import BytesIO
from typing import Dict, Optional
import base64

import nacl
from nacl import encoding, public

import requests


@dataclass(frozen=True)
class SecretMetadata:
    name: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PublicKey:
    key_id: str
    key: str


def encrypt_secret(public_key: str, secret_value: str) -> str:
    """
    implement ref:
    https://github.com/orgs/community/discussions/26535

    :param public_key:
    :param secret_value:
    :return:
    """
    public_key_bytes = base64.b64decode(public_key)

    public_key = nacl.public.PublicKey(public_key_bytes)
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


class GitHubAPI(object):

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.public_key: Optional[PublicKey] = None

    def headers(self):
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.access_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _get_public_key(self, owner: str, repo: str) -> PublicKey:
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
        response = requests.get(url, headers=self.headers()).content
        body = json.loads(response)
        return PublicKey(key_id=body["key_id"], key=body["key"])

    def list_secrets(self, owner: str, repo: str):
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets"
        response = requests.get(url, headers=self.headers())
        if response.status_code != 200:
            raise ValueError(
                f"GitHub API returned: \n"
                f"{response.status_code}\n{url}\n"
                f" {response.text}"
            )

        body = json.loads(response.content)
        output: Dict[str, SecretMetadata] = {}
        for secret in body.get("secrets", []):
            name = secret["name"]
            created_at = secret["created_at"]
            updated_at = secret["updated_at"]
            output[name] = SecretMetadata(
                name=name,
                created_at=GitHubAPI.parse_datetime(created_at),
                updated_at=GitHubAPI.parse_datetime(updated_at),
            )

        return output

    @classmethod
    def parse_datetime(cls, datetime_str: str) -> datetime:
        if datetime_str.endswith("Z"):
            datetime_str = datetime_str.rstrip("Z") + "+00:00"

        target = datetime.fromisoformat(datetime_str)
        target = target.replace(tzinfo=timezone.utc)
        return target

    def update_secret(self, owner: str, repo: str, secret_name: str, secret_value: str):
        if self.public_key is None:
            self.public_key = self._get_public_key(owner, repo)
        encrypted_value = encrypt_secret(self.public_key.key, secret_value)
        request_body = dict(
            key_id=self.public_key.key_id, encrypted_value=encrypted_value
        )

        url = (
            f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}"
        )
        response = requests.put(url, headers=self.headers(), json=request_body)
        return response.status_code == 201 or response.status_code == 204

    def delete_secret(self, owner: str, repo: str, secret_name: str):
        url = (
            f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}"
        )
        response = requests.delete(url, headers=self.headers())
        return response.status_code == 204
