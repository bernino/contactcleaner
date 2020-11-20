import configparser
import sys
import os
import requests
import pandas as pd
from pyhunter import PyHunter
from pandas import json_normalize
import validators


if os.getenv('HUNTER_API_KEY'):
    HUNTER_API_KEY = os.getenv('HUNTER_API_KEY')
elif os.path.isfile('secrets'):
    config = configparser.ConfigParser()
    config.read('secrets')
    HUNTER_API_KEY = config['pyhunter']['api']
else:
    HUNTER_API_KEY = False


def main():
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    skip_to_row = False

    if not os.path.isfile(input_file):
        print("Input file doesn't exist. Exiting.")
        sys.exit(1)

    if os.path.isfile(output_file) and not skip_to_row:
        print("Output file ({}) exists already. Exiting.".format(output_file))
        sys.exit(1)

    if len(sys.argv) > 3:
        skip_to_row = int(sys.argv[3])

    if not HUNTER_API_KEY:
        print("Hunter API Key missing. Exiting.")
        sys.exit(1)

    hunter = PyHunter(HUNTER_API_KEY)
    df = pd.read_csv(input_file)
    full_df = df

    if skip_to_row:
        full_df = df
        df = df[skip_to_row:]

    normalised2 = pd.DataFrame()

    # Just in case there are duplicate domains we don't want to API call twice
    df = df.drop_duplicates(subset=['Domain'])

    for index, row in df.iterrows():
        domain = row['Domain']
        # validators.domain does exactly that - nifty little tool
        # also we only want to lookup unique domains
        if validators.domain(domain) and domain != 'wikipedia.org' and domain != '4icu.org':
            print("Processing {} ({}/{})".format(domain, index, len(full_df)-1))

            # Had to remove limit=100 as it broke the client
            try:
                results = hunter.domain_search(domain, emails_type='personal')
            except requests.exceptions.HTTPError as e:
                print("Received error: {}".format(e))
                break

            normalised = json_normalize(results['emails'])
            normalised['org'] = row['Firm']
            normalised.to_csv(output_file, mode='a', header=False, encoding='utf-8')
            normalised2 = normalised2.append(normalised, sort=True)

    normalised2.to_csv(output_file)

if __name__ == "__main__":
    main()
