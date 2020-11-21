import os
import configparser
import sys
import json
import argparse
from time import sleep
import clearbit
import pandas as pd
import requests
import tldextract
from serpapi import GoogleSearch

if os.getenv('CLEARBIT_TOKEN'):
    CLEARBIT_TOKEN = os.getenv('CLEARBIT_TOKEN')
elif os.path.isfile('secrets'):
    config = configparser.ConfigParser()
    config.read('secrets')
    CLEARBIT_TOKEN = config['clearbit']['key']
else:
    CLEARBIT_TOKEN = False

if os.getenv('SERP_API_KEY'):
    serp_api_key = os.getenv('SERP_API_KEY')
    serp_api_fast = bool(os.getenv('SERP_API_FAST', False))
else:
    config = configparser.ConfigParser()
    config.read('secrets')
    serp_api_key = config['serp']['api']


def googlesearch(name, location=False):
    """
    Perform Google Search lookup.
    """

    # The base plan for SerpAPI is rate limited to 1k calls per hour.
    # We intentionally slow this down to avoid hitting the rate limit.
    if not serp_api_fast:
        sleep(2.5)

    if not location:
        client = GoogleSearch({"q": name, "api_key": serp_api_key})
    else:
        client = GoogleSearch({"q": name, "location": location, "api_key": serp_api_key})

    result = client.get_json()
    try:
        domain = result['organic_results'][0]['link']
        tldr = tldextract.extract(domain)
        return '{}.{}'.format(tldr.domain, tldr.suffix)
    except KeyError:
        print("Unable to lookup record from SerpAPI.")
    return


def get_domain_from_clearbit(name):
    """
    Based on https://clearbit.com/docs?shell#name-to-domain-api
    could also use hunter.domain_search(company='Instragram', limit=5, emails_type='personal')
    but not as precise...
    https://github.com/VonStruddle/PyHunter
    """
    clearbit.key = CLEARBIT_TOKEN
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {0}'.format(clearbit.key)
    }
    api_url = '{}domains/find?name={}'.format('https://company.clearbit.com/v1/', name)
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        name = json.loads(response.content.decode('utf-8'))
        return name['domain']
    else:
        return


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
    tally = len(df)

    if args.start_row != 0:
        print("Starting on row {}".format(args.start_row + 1))
        df = df[args.start_row +1 :]

    if args.end_row != 0:
        print("Will stop on row {}".format(args.end_row + 1))
        df = df[:args.end_row + 1]


    for index, row in df.iterrows():
        # Let's make sure we have nice and formatted company namnes
        row['Firm'] = row['Firm'].title()

        orgname = row['Firm']
        location = row['Location']
        print("Processing {} ({}/{})".format(orgname, index, tally-1))

        # Try with google's first result
        name = googlesearch(orgname, location)

        if name:
            df.loc[index,'Domain'] = name
            print("Found via Google: {}".format(name))
        elif not name and CLEARBIT_TOKEN:
            name = get_domain_from_clearbit(orgname)
            if not name:
                df.loc[index,'Domain'] = "none"
            else:
                df.loc[index,'Domain'] = name
                print("Found via Clearbit: {}".format(name))
        else:
            print("Unable to find record in Google lookup.")
            print("Assuming rate limiting. Sleeping for 30s.")
            sleep(30)

        record = df.loc[index, :]
        record = pd.DataFrame(record)
        record = record.transpose()
        record.to_csv(args.output_file, mode='a', header=False)

if __name__ == "__main__":
    main()
