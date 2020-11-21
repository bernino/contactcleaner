import sys
import os
import argparse
import requests
import configparser
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
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "--input-file",
            help="The input CSV file. Must have the 'Firm' column (and can also have the optional 'Location' column).",
            type=str,
            default=0
    )
    parser.add_argument(
            "--output-file",
            help="The output CSV file.",
            type=str,
            default=0
    )
    parser.add_argument(
            "--start-row",
            help="The row in input file to start on",
            type=int,
            default=0
    )
    parser.add_argument(
            "--end-row",
            help="The row in input file to end on",
            type=int,
            default=0
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input_file):
        print("Input file doesn't exist. Exiting.")
        sys.exit(1)

    if os.path.isfile(args.output_file) and not (args.end_row or args.start_row):
        print("Output file ({}) exists already. Exiting.".format(args.output_file))
        sys.exit(1)

    # Make sure we can load the file
    df = pd.read_csv(args.input_file)

    if args.start_row != 0:
        print("Starting on row {}".format(args.start_row + 1))
        df = df[args.start_row + 1 :]

    if args.end_row != 0:
        print("Will stop on row {}".format(args.end_row + 1))
        df = df[:args.end_row + 1]

    if not HUNTER_API_KEY:
        print("Hunter API Key missing. Exiting.")
        sys.exit(1)

    hunter = PyHunter(HUNTER_API_KEY)
    tally = len(df)

    # Just in case there are duplicate domains we don't want to API call twice
    df = df.drop_duplicates(subset=['Domain'])

    for index, row in df.iterrows():
        domain = row['Domain']
        # validators.domain does exactly that - nifty little tool
        # also we only want to lookup unique domains
        if not validators.domain(domain) and domain != 'wikipedia.org' and domain != '4icu.org':
            print("{} is an invalid domain. Skipping.".format(domain))
            break

        print("Processing {} ({}/{})".format(domain, index - args.start_row - 1, tally-1))

        # Had to remove limit=100 as it broke the client
        try:
            results = hunter.domain_search(domain, emails_type='personal')
        except requests.exceptions.HTTPError as e:
            print("Received error: {}".format(e))
            break

        normalized = json_normalize(results['emails'])
        normalized['org'] = row['Firm']
        normalized.to_csv(
                args.output_file,
                mode='a',
                header=False,
                encoding='utf-8'
        )

if __name__ == "__main__":
    main()
