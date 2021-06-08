# Slack Channel Creator

## Install

Create a Slack application with these scopes: channels:read, channels:write, groups:read, groups:write, im:read, mpim:read. Install it in the workspace. Set SLACK_OAUTH_TOKEN to the User OAuth Token.

Run this in the terminal. (This is not necessary on repl.it.)

```
pip install poetry
```

## Usage

Create a CSV file named channels.csv with columns Name, Topic, and Purpose.

Run `poetry run create_channels`.

The channel IDs are written to `channel-ids.csv`.