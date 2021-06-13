import click
import pandas as pd

from .utils import load_csv
from .client import client, get_conversation_members, get_user_list, list_channels

@click.command()
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--channel_limit', type=int)
@click.argument('member_channels_csv', type=click.File())
def add_channel_members(member_channels_csv, channel_limit, dry_run):
  df = load_csv(member_channels_csv, limit=channel_limit, required_headers=['Member'])
  if 'Email' not in df.columns:
    df['Email'] = df.Member.str.extract(r'<(.+?)(?: \(i was registered.*)?>')
  missing_emails = df[pd.isnull(df.Email)]
  if len(missing_emails):
    print(f"Skipping {len(missing_emails)} users with missing emails: {', '.join(missing_emails.Member)}")
    df.drop(df.index[pd.isnull(df.Email)], inplace=True)

  channel_names = [cn for cn in df.columns if cn not in ['Member', 'Email']]
  channels = list_channels()
  channels = [c for cn in channel_names for c in channels if c['name'] == cn]
  if len(channels) < len(channel_names):
    print("Missing channels:", ', '.join(cn for cn in channel_names if cn not in {c['name'] for c in channels}))
  # channels_by_name = {c['name']: c for c in channels}

  users_by_email = {u['profile']['email']: u
    for u in get_user_list()
    if u['profile'].get('email', None)}
  users_by_id = {u['id']: u
    for u in users_by_email.values()}

  print(f"The workspace has {len(users_by_email)} members with email addresses.")
  print(f"{len(users_by_email)} invitees are in Slack.")

  unregistered_invitees = {e for e in df.Email if e not in users_by_email}
  if unregistered_invitees:
    print('. Participants who are not in Slack:', ', '.join(unregistered_invitees))

  # uxf = [
  #   dict(
  #     username=u['name'],
  #     email=u['profile'].get('email', None),
  #     userid=u['id'],
  #     fullname=u['profile']['real_name'],
  #     displayname=u['profile']['display_name'],
  #    ) for u in get_user_list()]
  # dfx = pd.DataFrame(uxf)
  # print(uxf)
  # dfx.sort_values(by=['Name'], inplace=True)
  # with open('members.csv', 'w') as f:
  #   f.write(dfx.to_csv(index=False))

  channel_invitations = []

  for channel in channels:
    # print(f"{channel['name']}:")
    current_member_ids = get_conversation_members(channel['id'])
    current_member_emails = {users_by_id[uid]['profile']['email'] for uid in current_member_ids if uid in users_by_id}
    invited_member_emails = set(df[df[channel['name']].str.lower() == 'y'].Email)
    # print(df[channel['name']].str.lower() == 'y')

    # unregistered_invitees = {u for u in invited_member_emails if u not in users_by_email}
    # if unregistered_invitees:
    #   print('. Participants who are not in Slack:', ' '.join(unregistered_invitees))

    # print('. Current channel members who are not in the spreadsheet', current_member_emails - invited_member_emails)

    could_invite = invited_member_emails - current_member_emails - unregistered_invitees
    if could_invite:
      # print('. Slack members who are not in the channel:', ' '.join(could_invite))
      channel_invitations.append({
        'channel': channel,
        'emails': could_invite
      })

  if channel_invitations:
    print("Invitations:")
    for ci in channel_invitations:
      channel = ci['channel']
      emails = ci['emails']
      print(f"Inviting to {channel['name']}: {', '.join(emails)}")
      if not dry_run:
        client.conversations_invite(channel=channel['id'], users=','.join(users_by_email[u]['id'] for u in emails))
