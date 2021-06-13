import csv
import time

import click
import pandas as pd
from jinja2 import Template
from slack_sdk.errors import SlackApiError

from .utils import die, load_csv
from .client import client, list_channels


def create_or_update_channel(channels, channel_name, topic=None, purpose=None, dry_run=False, is_private=False, join=True):
	action = 'Found'
	channel = next((c for c in channels if c['name'] == channel_name), None)
	if not channel:
		action = 'Created'
		if is_private:
			action += ' private'
		try:
			if dry_run:
				channel = {
					'name': channel_name,
					'id': 'C3D404E10ED',
					'purpose': {'value': ''},
					'topic': {'value': ''},
				}
			else:
				response = client.conversations_create(name=channel_name, is_private=is_private)
				channel = response['channel']
		except SlackApiError as e:
			die(f"Error creating conversation: {e}")
	if join:
		if dry_run:
			print(f"Join {channel_name}")
		else:
			client.conversations_join(channel=channel['id'])
	if purpose and channel['purpose']['value'] != purpose:
		print(f"Update {channel_name} purpose to {purpose}")
		if not dry_run:
			client.conversations_setPurpose(channel=channel['id'], purpose=purpose)
	if topic and channel['topic']['value'] != topic:
		print(f"Update {channel_name} topic to {topic}")
		if not dry_run:
			client.conversations_setTopic(channel=channel['id'], topic=topic)
	return channel, action


@click.command()
@click.argument('csv_path', default='channels.csv', type=click.File())
@click.argument('output_csv', default='channel-ids.csv', type=click.Path())
@click.option('--limit', type=int)
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--join/--no-join', default=True)
@click.option('--private/--public', default=False)
def create_channels_from_csv(csv_path, output_csv, dry_run, private, join, limit):
  channels = list_channels()
  if csv_path.name.endswith('.url'):
    csv_path = csv_path.read()
  channels_df = load_csv(csv_path, limit=limit, required_headers=['Name'])

  for _, row in channels_df.iterrows():
    channel_name = row['Name']
    _, action = create_or_update_channel(
      channels, channel_name,
      purpose=row.get('Purpose', None),
      topic=row.get('Topic', None),
      dry_run=dry_run,
      is_private=private,
			join=join)
    print(f"{action} {channel_name}")

  write_channels_csv(output_csv)

@click.command()
@click.argument('csv_output', default='channel-ids.csv', type=click.Path())
def write_csv(csv_output):
  write_channels_csv(csv_output)


def write_channels_csv(csv_output):
  rows = []
  for channel in list_channels():
    rows.append(
      {
        'Name': channel['name'],
        'Id': channel['id'],
        'Topic': channel['topic']['value'],
        'Purpose': channel['purpose']['value'],
        'Members': channel['num_members'],
        'Archived': channel['is_archived'],
      })

  df = pd.DataFrame(rows)
  df.sort_values(by=['Name'], inplace=True)
  with open(csv_output, 'w') as f:
    f.write(df.to_csv(index=False))
  print(f"Wrote channel information to {csv_output}")


@click.command()
@click.argument('csv_path', default='channels.csv', type=click.File())
@click.argument('template_path', type=click.File())
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--limit', type=int)
@click.option('--pin/--no-pin', default=False)
def post_messages(csv_path, template_path, dry_run, limit, pin):
  if csv_path.name.endswith('.url'):
    csv_path = csv_path.read()
  channels_df = pd.read_csv(csv_path)
  if 'Name' not in channels_df.columns:
    die("CSV file requires a Name column")
  channels_df.rename(columns = {k: k.replace(' ', '_') for k in channels_df.columns}, inplace = True)
  if limit:
    channels_df.drop(channels_df.index[limit:], inplace=True)

  template = Template(template_path.read())
  channels = list_channels()
  
  for _, row in channels_df.iterrows():
    channel = next((c for c in channels if c['name'] == row.Name), None)
    if not channel:
      die(f"No channel named {row.Name}")
    text = template.render(row)
    if dry_run:
      print(f"Post to {channel['name']}:")
      print(text)
    else:
      response = client.chat_postMessage(channel=channel['id'], text=text, mrkdwn=True)
      print(f"Posted to {channel['name']}")
      if pin:
        client.pins_add(channel=channel['id'], timestamp=response['ts'])


@click.command()
@click.argument('to_pin', default='to_pin.csv')
@click.argument('pin_lookup_path', default='pin_lookup.csv')
@click.option('--dry-run/--no-dry-run', default=False)
def set_pins(to_pin, pin_lookup_path, dry_run):
  pin_lookup = {}

  with open(pin_lookup_path, 'r', encoding='utf-8') as f:
    dr = csv.DictReader(f)
    for row in dr:
      pin_lookup[row['channel']] = row['ts']
  
  with open(to_pin, 'r', encoding='utf-8') as f:
    dr = csv.DictReader(f)
    for row in dr:
      channel = row['channel']
      message = row['message']
      if channel not in pin_lookup:
        # pin not created
        print('Posting to', channel, '...')
        if not dry_run:
          response = client.chat_postMessage(channel=channel, text=message, mrkdwn=True)
          ts = response['ts']
          pin_lookup[channel] = ts
          print('Pinning...')
          client.pins_add(channel=channel, timestamp=ts)
      else:
        ts = pin_lookup[channel]
        print('Editting', channel, ts, '...')
        if not dry_run:
          response = client.chat_update(channel=channel, ts=ts, text=message, mrkdwn=True)
      time.sleep(.2) # to prevent rate limiting

  print('Updating', pin_lookup_path, '...')
  with open(pin_lookup_path, 'w', encoding='utf-8', newline='') as f:
    c = csv.writer(f)
    c.writerow(['channel', 'ts'])
    c.writerows([*pin_lookup.items()])
  print('ok')


