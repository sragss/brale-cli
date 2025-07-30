# brale-cli
Command-line interface for [brale.xyz](https://brale.xyz).

## Installation

Install using [uv](https://docs.astral.sh/uv/):

```bash
uv add brale-cli
```

## Usage

```
Usage: brale [OPTIONS] COMMAND [ARGS]...

  Brale CLI - Interact with the Brale API from the command line.

Options:
  --account TEXT              Account ID to use (overrides default)
  --output [table|json|yaml]  Output format
  -v, --verbose               Enable verbose logging
  --help                      Show this message and exit.

Commands:
  accounts     Account management commands.
  addresses    Address management commands.
  auth         Authentication commands.
  automations  Automation management commands.
  config       Configuration management commands.
  transfers    Transfer management commands.
```
