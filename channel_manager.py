import os
import sys
import pandas as pd

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

input_csv_path = 'channels.csv'
output_csv_path = 'channel-ids.csv'

client = WebClient(token=os.environ["SLACK_OAUTH_TOKEN"])

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
			print("Error creating conversation: {}".format(e))
			sys.exit(1)
	if purpose and channel['purpose']['value'] != purpose:
		print(f"Update {channel['name']} purpose to {purpose}")
		client.conversations_setPurpose(channel=channel['id'], purpose=purpose)
	if topic and channel['topic']['value'] != topic:
		print(f"Update {channel['name']} topic to {topic}")
		client.conversations_setTopic(channel=channel['id'], topic=topic)
	return channel, action

def create_channels_from_csv():
  dry_run = False
  channels = list_channels()

  channels_pd = pd.read_csv(input_csv_path)
  if 'Name' not in channels_pd.columns:
    print("CSV file requires a Name column")
    sys.exit(1)

  for _, row in channels_pd.iterrows():
    channel_name = row['Name']
    channel, action = find_or_create_channel(channels, channel_name,
      purpose=row.get('Purpose'),
      topic=row.get('Topic'),
      dry_run=dry_run)
    print(f"{action} {channel_name}")

  write_channels_csv()

def write_channels_csv():
  channel_ids_df = pd.DataFrame([], columns=['Name', 'Id', 'Topic', 'Purpose'])
  for channel in list_channels():
    channel_ids_df = channel_ids_df.append(
        {
            'Name': channel['name'],
            'Id': channel['id'],
            'Topic': channel['topic']['value'],
            'Purpose': channel['purpose']['value'],
        }, ignore_index=True)

  with open(output_csv_path, 'w') as f:
    f.write(channel_ids_df.to_csv(index=False))

  print(f"Wrote channel information to {output_csv_path}")
