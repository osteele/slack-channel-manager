# Slack Channel Creator

## Install

Create a Slack application with these scopes: channels:read, channels:write, groups:read, groups:write, im:read, mpim:read. Install it in the workspace. Set SLACK_OAUTH_TOKEN to the User OAuth Token.

Run these in the terminal:

```
pip install slack_sdk
pip install pandas
```

## Usage

Create a CSV file named channels.csv with columns Name, Topic, and Purpose.

Run `python create_channels.py`

The channel IDs are written to channel-ids.csv.