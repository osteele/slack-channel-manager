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
  df = load_csv(member_channels_csv)
  user_id_headers = {'Email', 'Member'}
  if not set(df.columns) & user_id_headers:
    die(f"{member_channels_csv.name} must include at least one of {' and '.join(user_id_headers)}")
  if 'Email' not in df.columns:
    df['Email'] = df.Member.str.extract(r'<(.+?)(?: \(i was registered.*)?>')

  missing_emails_df = df[pd.isnull(df.Email)]
  if len(missing_emails_df):
    print(f"Skipping {len(missing_emails_df)} users with missing emails: {', '.join(missing_emails_df.Member)}")
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
    print("These column names are not workspace channels:",
      ', '.join(cn
        for cn in channel_names
        if cn not in {c['name'] for c in channels}))
  if channel_limit:
    channels = channels[:channel_limit]

  workspace_users = get_user_list()
  users_by_email = {u['profile']['email'].lower(): u
    for u in workspace_users
    if u['profile'].get('email', None)}
  users_by_id = {u['id']: u for u in workspace_users}

  unregistered_invitee_emails = {em
    for em in df.Email
    if em.lower() not in users_by_email}

  invitee_count = len({em.lower() for em in df.Email if em})
  print(f"The workspace has {len(users_by_email)} members with email addresses.")
  print(f"{invitee_count - len(unregistered_invitee_emails)}/{invitee_count} invitees are in the workspace.")

  if unregistered_invitee_emails:
    print(f"{len(unregistered_invitee_emails)} invitees are not in the workspace:", ', '.join(unregistered_invitee_emails))

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
      print(f"Channel #{channel['name']}:")

    current_member_ids = get_conversation_members(channel['id'])
    current_member_emails = {users_by_id[uid]['profile']['email'].lower()
      for uid in current_member_ids
      if uid in users_by_id}
    invited_member_emails = set(df[df[channel['name']].str.lower() == 'y'].Email.str.lower())

    unregistered_invitee_emails = {em.lower()
      for em in invited_member_emails
      if em.lower() not in users_by_email}
    if verbose:
      if unregistered_invitee_emails:
        print('. Participants who are not in Slack:',
          ' '.join(unregistered_invitee_emails))

    if verbose:
      print('. Current channel members who are not in the spreadsheet:',
        ', '.join(current_member_emails - invited_member_emails))

    could_invite_emails = invited_member_emails - current_member_emails - unregistered_invitee_emails
    if could_invite_emails:
      if verbose:
        print('. Workspace members who are not in the channel:', ', '.join(could_invite_emails))
      channel_invitations.append({
        'channel': channel,
        'emails': could_invite_emails
      })

  if channel_invitations:
    print("Invitations:")
    for ci in channel_invitations:
      channel = ci['channel']
      emails = ci['emails']
      print(f"Inviting to #{channel['name']}: {', '.join(emails)}")
      if not dry_run:
        client.conversations_invite(
          channel=channel['id'],
          users=','.join(users_by_email[em.lower()]['id'] for em in emails))
