import click
import pandas as pd

from .utils import die, load_csv
from .client import client, get_conversation_members, get_user_list, list_channels

@click.command()
@click.option('--channel_limit', type=int)
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--verbose/--no-verbose', default=False)
@click.argument('member_channels_csv', type=click.File())
def add_channel_members(member_channels_csv, channel_limit, dry_run, verbose):
  # load the CSV file
  df = load_csv(member_channels_csv, limit=channel_limit)
  user_id_headers = {'Email', 'Member'}
  if not set(df.columns) & user_id_headers:
    die(f"{member_channels_csv.name} must include at least one of {' and '.join(user_id_headers)}")
  if 'Email' not in df.columns:
    df['Email'] = df.Member.str.extract(r'<(.+?)(?: \(i was registered.*)?>')

  members_without_emails = df[pd.isnull(df.Email)]
  if len(members_without_emails):
    print(f"Skipping {len(members_without_emails)} users with missing emails: {', '.join(members_without_emails.Member)}")
    df.drop(df.index[pd.isnull(df.Email)], inplace=True)

  workspace_channels = list_channels()
  channel_names = [cn
    for cn in df.columns
    if cn not in user_id_headers]
  channels = [c
    for cn in channel_names
    for c in workspace_channels
    if c['name'] == cn]
  if len(channels) < len(channel_names):
    print("Missing channels:", ', '.join(cn
      for cn in channel_names
      if cn not in {c['name'] for c in channels}))

  workspace_users = get_user_list()
  users_by_email = {u['profile']['email'].lower(): u
    for u in workspace_users
    if u['profile'].get('email', None)}
  users_by_id = {u['id']: u for u in workspace_users}

  print(f"The workspace has {len(users_by_email)} members with email addresses.")
  print(f"{len(users_by_email)} invitees are in Slack.")

  unregistered_invitee_emails = {em
    for em in df.Email
    if em.lower() not in users_by_email}
  if unregistered_invitee_emails:
    print(f"{len(unregistered_invitee_emails)} invitees are not in Slack:", ', '.join(unregistered_invitee_emails))

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
    if verbose:
      print(f"{channel['name']}:")

    current_member_ids = get_conversation_members(channel['id'])
    current_member_emails = {users_by_id[uid]['profile']['email']
      for uid in current_member_ids
      if uid in users_by_id}
    invited_member_emails = set(df[df[channel['name']].str.lower() == 'y'].Email)

    if verbose:
      unregistered_invitee_emails = {em
        for em in invited_member_emails
        if em not in users_by_email}
      if unregistered_invitee_emails:
        print('. Participants who are not in Slack:',
          ' '.join(unregistered_invitee_emails))

    if verbose:
      print('. Current channel members who are not in the spreadsheet:',
        ', '.join(current_member_emails - invited_member_emails))

    could_invite_emails = invited_member_emails - current_member_emails - unregistered_invitee_emails
    if could_invite_emails:
      if verbose:
        print('. Slack members who are not in the channel:', ', '.join(could_invite_emails))
      channel_invitations.append({
        'channel': channel,
        'emails': could_invite_emails
      })

  if channel_invitations:
    print("Invitations:")
    for ci in channel_invitations:
      channel = ci['channel']
      emails = ci['emails']
      print(f"Inviting to {channel['name']}: {', '.join(emails)}")
      if not dry_run:
        client.conversations_invite(
          channel=channel['id'],
          users=','.join(users_by_email[em.lower()]['id'] for em in emails))
