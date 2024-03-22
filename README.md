## Github secret keeper

A command line tool to manage GitHub repository secrets:

* update secret from a local `.env` file
* delete the specific secret

## Demo

usage:

```sh
$ gsk
usage: gsk [-h] [--repo REPO] [--envfile ENVFILE] [--update [UPDATE]]
gsk: error: --repo and --envfile are required for interactive shell
```

See recording at asciinema:
https://asciinema.org/a/648148

## Heads Up!

This project is for learning purposes only. For real-world applications, it's important to update your secrets securely using the `gh` command.