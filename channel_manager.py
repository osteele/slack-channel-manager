import os
import sys
import pandas as pd
from pathlib import Path

import click
from jinja2 import Template

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def die(message):
	print(message, file=sys.stderr)
	sys.exit(1)

try:
  SLACK_OAUTH_TOKEN = os.environ["SLACK_OAUTH_TOKEN"]
except KeyError:
  die("Error: SLACK_OAUTH_TOKEN is not defined. See the README for installation instructions.")

client = WebClient(token=SLACK_OAUTH_TOKEN)

def list_channels():
	channels = []
	next_cursor = None
	while True:
		response = client.conversations_list(limit=1000, cursor=next_cursor)
		channels += response['channels']
		next_cursor = response['response_metadata']['next_cursor']
		if not next_cursor:
			break
	return channels


def find_or_create_channel(channels, channel_name, topic=None, purpose=None, dry_run=False):
	action = 'Found'
	channel = next((c for c in channels if c['name'] == channel_name), None)
	if not channel:
		action = 'Created'
		try:
			if dry_run:
				return {'name': channel_name, 'id': '12345'}, action
			response = client.conversations_create(name=channel_name)
			channel = response['channel']
		except SlackApiError as e:
			die(f"Error creating conversation: {e}")
	# print(channel)
	client.conversations_join(channel=channel['id'])
	if purpose and channel['purpose']['value'] != purpose:
		print(f"Update {channel['name']} purpose to {purpose}")
		client.conversations_setPurpose(channel=channel['id'], purpose=purpose)
	if topic and channel['topic']['value'] != topic:
		print(f"Update {channel['name']} topic to {topic}")
		client.conversations_setTopic(channel=channel['id'], topic=topic)
	return channel, action

@click.command()
@click.argument('csv_path', default='channels.csv', type=click.File())
@click.argument('output_csv', default='channel-ids.csv', type=click.Path())
@click.option('--dry-run/--no-dry-run', default=False)
def create_channels_from_csv(csv_path, output_csv, dry_run = False):
  channels = list_channels()
  channels_df = pd.read_csv(csv_path)
  if 'Name' not in channels_df.columns:
    die("CSV file requires a Name column")

  for _, row in channels_df.iterrows():
    channel_name = row['Name']
    channel, action = find_or_create_channel(
      channels, channel_name,
      purpose=row.get('Purpose', None),
      topic=row.get('Topic', None),
      dry_run=dry_run)
    print(f"{action} {channel_name}")

  write_channels_csv(output_csv)

@click.command()
@click.argument('csv_output', default='channel-ids.csv', type=click.Path())
def write_csv(csv_output):
  write_channels_csv(csv_output)

def write_channels_csv(csv_output):
  channel_ids_df = pd.DataFrame([], columns=['Name', 'Id', 'Topic', 'Purpose', 'Members', 'Archived'])
  for channel in list_channels():
    channel_ids_df = channel_ids_df.append(
        {
					'Name': channel['name'],
					'Id': channel['id'],
					'Archived': channel['is_archived'],
					'Topic': channel['topic']['value'],
					'Members': channel['num_members'],
					'Purpose': channel['purpose']['value'],
        }, ignore_index=True)

  channel_ids_df.sort_values(by=['Name'], inplace=True)
  with open(csv_output, 'w') as f:
    f.write(channel_ids_df.to_csv(index=False))

  print(f"Wrote channel information to {csv_output}")

@click.command()
@click.argument('csv_path', default='channels.csv', type=click.File())
@click.argument('template_path', type=click.File())
@click.option('--dry-run/--no-dry-run', default=False)
def send_template_messages(csv_path, template_path, dry_run = False):
  template = Template(template_path.read())
  channels_df = pd.read_csv(csv_path)
  channels_df.rename(columns = {k: k.replace(' ', '_') for k in channels_df.columns}, inplace = True)
  channels = list_channels()
  for _, row in channels_df.iterrows():
    channel = next(c for c in channels if c['name'] == row.Name)
    text = template.render(row)
    if dry_run:
      print(f"Post to {channel['name']}:")
      print(text)
    else:
      client.chat_postMessage(channel=channel['id'], text=text)
      print(f"Posted to {channel['name']}")
