# Slack Channel Creator

## Installation

1. On the [Slack app management page](https://api.slack.com/apps), create a
   Slack application with these scopes: `channels:read`, `channels:write`,
   `groups:read`, `groups:write`, `im:read`, `mpim:read`. Install the
   application in the workspace.

2. Set the `SLACK_OAUTH_TOKEN` environment variable to the value of the User
   OAuth Token from the Slack app management page. (In repl.it, use the Secrets
   icon in the sidebar for this.)

3. [Install Poetry](http://python-poetry.org/docs/). (This is not necessary on repl.it.)

## Usage

You can also run the channel creation and bulk messaging commands with
`--dry-run`, in order to preview the actions without executing them.

### Creating Channels

1. Create a CSV file named `channels.csv` with a column named "Name", and
   optional columns "Topic" and "Purpose". See the files in `examples` for an
   example.

2. In the Terminal or Shell, run:

  ```sh
  poetry install --no-root
  poetry run create_channels
  ```

The IDs of created channels (and all other channels) are written to
`channel-ids.csv`. See the documentation for “Listing Channel IDs", below, for
additional documentation about this file.

### Listing Channel IDs

Run to write a list of all a workspace's public channels to `channel-ids.csv`.

```sh
poetry install --no-root
poetry run write_csv
```

This file has columns "Name", "Id", "Topic", "Purpose", and "Archived".

The ids in this column can be used as direct link URLs to the channels. For
example, if the workspace is named `example-space` and a channel has an id
`C3D404E10ED`, this id can be used in the URL for a direct link:
`https://example-space.slack.com/archives/C3D404E10ED`.

### Bulk Message Posting

This feature sends a parameterized message to each channel that is listed in a
CSV file. The CSV file should contain at least a Name column, that lists the
names of Slack channels. It may contain other columns, that are used in the
template text. See the files in `examples` for an example.

```sh
poetry install --no-root
poetry run send_template_messages channels.csv template.jinja
```

The template file uses the [Jinja template
format](https://jinja.palletsprojects.com/en/3.0.x/templates/). Template
variables refer to cells in the CSV file, except that the spaces in the column
names are replaced by underscores. For example, if the CSV contains a column
named `Zoom URL`, the template may refer to it as `{{ Zoom_URL }}`. See
`template-example.jinja` for an example.

Messages are posted as [Markdown](https://www.markdownguide.org/tools/slack/).

## License

MIT
