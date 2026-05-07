# AGENTS.md

## Project

`daily-bcp` is a Python CLI installed as `bcp`. It reads Daily Office readings,
collects, common prayers, devotions, user library readings, Markdown notes, and
local reading history.

## Install From Repo

Use `pipx`, not system `pip`.

On macOS, if `pipx` is missing:

```sh
brew install pipx
pipx ensurepath
```

Install from GitHub:

```sh
pipx install git+https://github.com/dwhamilton/daily-bcp.git
```

If `daily-bcp` is already installed and should be refreshed from the repo:

```sh
pipx install --force git+https://github.com/dwhamilton/daily-bcp.git
```

Verify:

```sh
bcp library
bcp library --path
```

Report the installed command path, the library folder path, and whether
`sample.yaml` was seeded.

Do not use `--break-system-packages`. Do not overwrite existing notes, history,
or user library files.

## Local Development

For direct source-tree checks:

```sh
python3 -m bcp_cli library
python3 -m bcp_cli library --path
python3 -m unittest tests/test_cli.py
python3 -m py_compile bcp_cli/*.py
```

The project has no runtime Python package dependencies.

## User Data

Notes, history, and library files are user-managed data. Do not delete or
overwrite them unless the user explicitly asks.

Default notes path:

```text
${XDG_STATE_HOME:-$HOME/.local/state}/daily-bcp/notes.md
```

Default library folder:

```text
<notes folder>/library
```

The library folder can be overridden with `BCP_LIBRARY_DIR`.

## Library Samples

Bundled library samples live in:

```text
bcp_cli/data/library/
```

On first library use, missing bundled sample files are copied into the user's
library folder. Existing user files with the same names are not overwritten.

## Git And Safety

Keep commits scoped to the requested change. Before committing, run:

```sh
git status --short
python3 -m unittest tests/test_cli.py
```

Do not run destructive git commands such as `git reset --hard` or
`git checkout -- <path>` unless the user explicitly asks.
