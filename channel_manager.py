import os
import sys
import pandas as pd
from pathlib import Path

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

try:
  SLACK_OAUTH_TOKEN = os.environ["SLACK_OAUTH_TOKEN"]
except KeyError:
  print("Error: SLACK_OAUTH_TOKEN is not defined. See the README for installation instructions.", file=sys.stderr)
  sys.exit(1)

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
			print(f"Error creating conversation: {e}", file=sys.stderr)
			sys.exit(1)
	if purpose and channel['purpose']['value'] != purpose:
		print(f"Update {channel['name']} purpose to {purpose}")
		client.conversations_setPurpose(channel=channel['id'], purpose=purpose)
	if topic and channel['topic']['value'] != topic:
		print(f"Update {channel['name']} topic to {topic}")
		client.conversations_setTopic(channel=channel['id'], topic=topic)
	return channel, action

def create_channels_from_csv(input_csv_path = 'channels.csv', dry_run = False):
  if not Path(input_csv_path).exists():
    print(f"Missing file: {input_csv_path}", file=sys.stderr)
    sys.exit(1)

  channels = list_channels()

  channels_pd = pd.read_csv(input_csv_path)
  if 'Name' not in channels_pd.columns:
    print("CSV file requires a Name column", file=sys.stderr)
    sys.exit(1)

  for _, row in channels_pd.iterrows():
    channel_name = row['Name']
    channel, action = find_or_create_channel(channels, channel_name,
      purpose=row.get('Purpose', None),
      topic=row.get('Topic', None),
      dry_run=dry_run)
    print(f"{action} {channel_name}")

  write_channels_csv()

def write_channels_csv(output_csv_path = 'channel-ids.csv'):
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
  with open(output_csv_path, 'w') as f:
    f.write(channel_ids_df.to_csv(index=False))

  print(f"Wrote channel information to {output_csv_path}")
