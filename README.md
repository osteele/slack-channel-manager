# Slack Channel Creator

## Installation

1. On the [Slack app management page](https://api.slack.com/apps), create a Slack application with these scopes: `channels:read`, `channels:write`, `groups:read`, `groups:write`, `im:read`, `mpim:read`. Install the application in the workspace.

2. Set the `SLACK_OAUTH_TOKEN` environment variable to the value of the User OAuth Token from the Slack app management page. (In repl.it, use the Secrets icon in the sidebar for this.)

3. [Install Poetry](http://python-poetry.org/docs/). (This is not necessary on repl.it.)

## Usage

### Creating Channels

1. Create a CSV file named `channels.csv` with a column named "Name", and optional columns "Topic" and "Purpose".

2. In the Terminal or Shell, run:

  ```sh
  poetry install --no-root
  poetry run create_channels
  ```

The IDs of created channels (and all other channels) are written to `channel-ids.csv`.
See the documentation for “Listing Channel IDs", below, for additional documentation about this file.

### Listing Channel IDs

Run  to write a list of all a workspace's public channels to `channel-ids.csv`.

```sh
poetry install --no-root
poetry run write_csv
```

This file has columns "Name", "Id", "Topic", "Purpose", and "Archived".

The ids in this column can be used as direct link URLs to the channels. For example, if the workspace is named `example-space` and a channel has an id `C3D404E10ED`, this id can be used in the URL for a direct link: `https://example-space.slack.com/archives/C3D404E10ED`.
