import os
import logging
import sys
from time import time
import pandas as pd

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

input_csv_path = 'channels.csv'
output_csv_path = 'channel-ids.csv'

#logging.basicConfig(level=logging.DEBUG)

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


def find_or_create_channel(channel_name, topic=None, purpose=None):
	action = 'Found'
	channel = next((c for c in channels if c['name'] == channel_name), None)
	if not channel:
		action = 'Created'
		try:
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


channels = list_channels()

# name: test-channel
# id: C)248EG11HR
# invitation: https://join.slack.com/share/zt-rd66bdz7-Y5_XAbK2I34hSu7wBsMC4w

channels_pd = pd.read_csv(input_csv_path)
if 'Name' not in channels_pd.columns:
	print("CSV file requires a Name column")
	sys.exit(1)

channel_ids_df = pd.DataFrame([], columns=['Name', 'ID'])

for _, row in channels_pd.iterrows():
	channel_name = row['Name']
	channel, action = find_or_create_channel(channel_name,
	                                         purpose=row.get('Purpose'),
	                                         topic=row.get('Topic'))
	channel_ids_df = channel_ids_df.append(
	    {
	        'Name': channel_name,
	        'ID': channel['id']
	    }, ignore_index=True)
	print(f"{action} {channel_name}")

with open(output_csv_path, 'w') as f:
	f.write(channel_ids_df.to_csv(index=False))

print(f"Wrote channel ids to {output_csv_path}")
