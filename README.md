# Slack Channel Creator

## Installation

1. On the [Slack app management page](https://api.slack.com/apps), create a
   Slack application with these scopes: `channels:read`, `channels:write`,
   `groups:read`, `groups:write`, `im:read`, `mpim:read`, `chat:write`, `pins:write`. Install the
   application in the workspace.

2. Set the `SLACK_OAUTH_TOKEN` environment variable to the value of the User
   OAuth Token from the Slack app management page. (In repl.it, use the Secrets
   icon in the sidebar for this.)

3. [Install Poetry](http://python-poetry.org/docs/). (This is not necessary on repl.it.)

4. Install the dependencies:

   `poetry install --no-root`

### Creating Channels

1. Create a CSV file named `channels.csv`. This file must have a column named "Name", and
   optional columns "Topic" and "Purpose". The file `examples/channel-creation.csv` is an
   example.

2. In the Terminal or Shell, run:

   ```sh
   poetry run create_channels
   ```

The IDs of created channels (and all other channels) are written to
`channel-ids.csv`. See the documentation for “Listing Channel IDs", below, for
additional documentation about this file.

The `--dry-run` option previews the channel creation actions without executing
them.

### Listing Channel IDs

Run this command to write a list of all a workspace's public channels to `channel-ids.csv`.

```sh
poetry run write_csv
```

The output file has these columns: "Name", "Id", "Topic", "Purpose", and "Archived".

The cells in the Id column can be used as direct link URLs to the channels. For
example, if the workspace is named `example-space` and a channel has an id
`C3D404E10ED`, this channel id can be used in the URL for a direct link:
`https://example-space.slack.com/archives/C3D404E10ED`.

### Bulk Message Posting

This feature sends a parameterized message to each channel that is listed in a
CSV file. The CSV file should contain at least a Name column, that lists the
names of Slack channels. It may contain other columns, that are used in the
template text. See the files in `examples` for an example.

```sh
poetry run post_messages channels.csv template.jinja
```

The template file uses the [Jinja template
format](https://jinja.palletsprojects.com/en/3.0.x/templates/). Template
variables refer to cells in the CSV file, except that the spaces in the column
names are replaced by underscores. For example, if the CSV contains a column
named `Zoom URL`, the template may refer to it as `{{ Zoom_URL }}`. See
`examples/bulk-messaging.csv`  and examples/bulk-messaging.jinja` for an example.

Messages are posted as [Markdown](https://www.markdownguide.org/tools/slack/). The template may include `*` for bullet list items, `[link](https://example.com)` for links, etc.

The `--dry-run` option previews the actions without executing them.

### Set channel pins

- input: a csv, each row being [`channel`, `message`]
- This tool focuses on *one pinned item* per channel. When you set pins with it, it creates a new pinned message for new channels, and edits the pinned message for channels that it has dealt with.

```sh
poetry run set_pins to_pin.csv
```

The `--dry-run` option previews the actions without executing them.

### Add Channel Members

```sh
poetry run add_channel_members CSV_FILE
```

CSV_FILE should be the path to a CSV file whose columns are Member, and a column for each channel name.

Member should be in the form `User Name <user@host.com>`.

The cell at the intersection of a member's row, and a channel's column, contains `y` if the member should be invited to the workspace.

## License

MIT
