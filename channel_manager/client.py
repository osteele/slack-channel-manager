import os

from slack_sdk import WebClient

from .utils import die

try:
  SLACK_OAUTH_TOKEN = os.environ["SLACK_OAUTH_TOKEN"]
except KeyError:
  die("Error: SLACK_OAUTH_TOKEN is not defined. See the README for installation instructions.")

client = WebClient(token=SLACK_OAUTH_TOKEN)


def get_conversation_members(channel_id):
  members = []
  cursor = None
  while True:
    response = client.conversations_members(channel=channel_id, cursor=cursor, limit=100)
    members += response['members']
    cursor = response['response_metadata']['next_cursor']
    if not cursor:
      break
  return set(members)


def list_channels(types='public_channel,private_channel'):
	"""Return a list of channels, following pagination."""
	channels = []
	next_cursor = None
	while True:
		response = client.conversations_list(types=types, limit=1000, cursor=next_cursor)
		channels += response['channels']
		next_cursor = response['response_metadata']['next_cursor']
		if not next_cursor:
			break
	return channels


def get_user_list():
  members = []
  cursor = None
  while True:
    response = client.users_list(cursor=cursor, limit=100)
    members += response['members']
    cursor = response['response_metadata']['next_cursor']
    if not cursor:
      break
  return members
