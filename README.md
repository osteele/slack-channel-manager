# Slack Channel Creator

## Install

On the [Slack app management page](https://api.slack.com/apps), create a Slack application with these scopes: channels:read, channels:write, groups:read, groups:write, im:read, mpim:read. Install it in the workspace. Set `SLACK_OAUTH_TOKEN` to the User OAuth Token.

Run this in the terminal. (This is not necessary on repl.it.)

```
pip install poetry
```

## Usage

### Creating Channels

Create a CSV file named `channels.csv` with a column named "Name", and optional columns "Topic" and "Purpose".

In the Terminal or Shell, run:

```
poetry install
poetry run create_channels
```

The IDs of created channels (and all other channels) are written to `channel-ids.csv`.

### Listing Channel IDs

Run `poetry run write_csv` to create `channel-ids.csv` (without reading `channels.csv`).

The ids in this column can be used as direct link URLs to the channels. For example, if the workspace is named `example-space` and a channel has an id `C3D404E10ED`, this id can be used in the URL for a direct link `https://example-space.slack.com/archives/C3D404E10ED`.