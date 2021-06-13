import sys

import pandas as pd

def die(message):
	print(message, file=sys.stderr)
	sys.exit(1)


def load_csv(file_or_url, limit=None, required_headers=[]):
  if file_or_url.name.endswith('.url'):
    file_or_url = file_or_url.read()
  df = pd.read_csv(file_or_url)
  missing_headers = [h for h in required_headers if h not in df.columns]
  if missing_headers:
    die(f"The following required headers were not found in {file_or_url}: {' '.join(missing_headers)}")
  if limit:
    df.drop(df.index[limit:], inplace=True)
  return df
