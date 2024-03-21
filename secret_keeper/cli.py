import argparse
import cmd
import os
import sys
from dataclasses import dataclass
from typing import Dict

from dotenv import dotenv_values
from tabulate import tabulate

from secret_keeper.api import GitHubAPI


def stop_for_invalid_api():
    print("Github API is not configured well.")
    print(
        "Please ensure env[GITHUB_PERSONAL_ACCESS_TOKEN] is a valid token for secrets read/write access."
    )
    sys.exit(1)


def create_api():
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if token is None:
        stop_for_invalid_api()

    return GitHubAPI(token)


@dataclass(frozen=True)
class Args:
    api: GitHubAPI
    owner: str
    repo: str
    config: Dict


class GitHubSecretKeeperShell(cmd.Cmd):
    intro = 'Welcome to the "GitHub secret keeper" shell.\nType help or ? to list commands.\n'
    prompt = "gsk> "

    def __init__(self, args: Args):
        super().__init__()
        self.args = args
        self.secrets = None
        self.refresh_remote_secrets(args)

    def refresh_remote_secrets(self, args):
        self.secrets = args.api.list_secrets(args.owner, args.repo)

    def do_status(self, line):
        """Show status of secret keeper"""
        self.refresh_remote_secrets(self.args)
        table = self.create_status()
        print(tabulate(table, headers="keys"))
        print()

    def do_update(self, line):
        """Update secret from the local environment file"""
        if line not in self.args.config:
            print(f"There is no secret[{line}], give up to update.")
            return

        if line in self.secrets.keys():
            answer = input(
                f"The secret[{line}] has been set on the remote, would you like to update it? (yes/no) "
            )
            if answer.lower() == "yes":
                args = self.args
                result = args.api.update_secret(
                    args.owner, args.repo, line, args.config[line]
                )
                print(f"Update success: {result}")
        else:
            args = self.args
            result = args.api.update_secret(
                args.owner, args.repo, line, args.config[line]
            )
            print(f"Update success: {result}")
        print()

    def do_delete(self, line: str):
        """Delete secret on the remote"""
        if line in self.secrets.keys():
            answer = input(
                f"Would you like to remove the secret[{line}] on the GitHub secrets? (yes/no) "
            )
            if answer.lower() == "yes":
                args = self.args
                result = args.api.delete_secret(args.owner, args.repo, line)
                print(f"Delete success: {result}")
            else:
                print("Give up to delete.")
        else:
            print("Give up to delete.")
        print()

    def complete_delete(self, *args):
        names = sorted(list(self.secrets.keys()))

        prefix, line, begin, end = args
        if prefix.strip():
            return [x for x in names if x.lower().startswith(prefix.lower())]

        return names

    def complete_update(self, *args):
        names = sorted(list(self.args.config.keys()))

        prefix, line, begin, end = args
        if prefix.strip():
            return [x for x in names if x.lower().startswith(prefix.lower())]

        return names

    def create_status(self):
        all_names = sorted(
            list(set(list(self.secrets.keys()) + list(self.args.config.keys())))
        )
        table = []

        for name in all_names:
            entry = dict(Name=name)
            if name in self.secrets.keys() and name in self.args.config.keys():
                entry["Status"] = "both"
            if name not in self.secrets.keys() and name in self.args.config.keys():
                entry["Status"] = "local"
            if name in self.secrets.keys() and name not in self.args.config.keys():
                entry["Status"] = "remote"

            table.append(entry)
        return table

    def emptyline(self):
        pass

    def do_EOF(self, line):
        """
        Quits the shell
        """
        return True


def build_args(repo: str, envfile: str) -> Args:
    segments = repo.strip().split("/")
    if not repo or len(segments) != 2:
        print("Invalid repository format.")
        print("please set up the repository in OWNER/REPO format.")
        print()
        sys.exit(1)
    owner, repo_name = segments

    if not os.path.exists(envfile):
        print(f"The specified environment file '{envfile}' does not exist.")
        sys.exit(1)
    config = dotenv_values(".env")

    api = create_api()
    return Args(owner=owner, repo=repo_name, config=config, api=api)


def update_secret(args: Args, secret: str):
    print(
        f"Updating secret '{secret}' for repository '{args.owner}/{args.repo}' using environment file."
    )
    if secret not in args.config:
        print(f"There is no {secret} in the environment file.")
        sys.exit(1)
    else:
        args.api.update_secret(args.owner, args.repo, secret, args.config[secret])

    print("Update complete.")


def interactive_shell(args: Args):
    GitHubSecretKeeperShell(args).cmdloop()


def main():
    parser = argparse.ArgumentParser(
        description="Update GitHub action secrets or enter an interactive shell."
    )
    parser.add_argument("--repo", type=str, help="Repository in the format owner/repo")
    parser.add_argument("--envfile", type=str, help="Path to the environment file")
    parser.add_argument("--update", type=str, help="The secret to update", nargs="?")

    args = parser.parse_args()

    if args.update:
        if not all([args.repo, args.envfile]):
            parser.error("--repo and --envfile are required when using --update")
        update_secret(build_args(args.repo, args.envfile), args.update)
    elif not all([args.repo, args.envfile]):
        parser.error("--repo and --envfile are required for interactive shell")
    else:
        interactive_shell(build_args(args.repo, args.envfile))


if __name__ == "__main__":
    main()
