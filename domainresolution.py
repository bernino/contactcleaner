import json
import os
import configparser
import sys
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
else:
    config = configparser.ConfigParser()
    config.read('secrets')
    serp_api_key = config['serp']['api']


def googlesearch(name, location=False):
    """
    Perform Google Search lookup.
    """
    if not location:
        client = GoogleSearch({"q": name, "api_key": serp_api_key})
    else:
        client = GoogleSearch({"q": name, "location": location, "api_key": serp_api_key})

    result = client.get_json()
    domain = result['organic_results'][0]['link']
    tldr = tldextract.extract(domain)
    return '{}.{}'.format(tldr.domain, tldr.suffix)


def get_domain_from_clearbit(name):
    """
    Based on https://clearbit.com/docs?shell#name-to-domain-api
    could also use hunter.domain_search(company='Instragram', limit=5, emails_type='personal')
    but not as precise...
    https://github.com/VonStruddle/PyHunter
    """
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
        return None


def main():
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    if not os.path.isfile(input_file):
        print("Input file doesn't exist. Exiting.")
        sys.exit(1)

    if os.path.isfile(output_file):
        print("Output file ({}) exists already. Exiting.".format(output_file))
        sys.exit(1)

    clearbit.key = CLEARBIT_TOKEN

    df = pd.read_csv(input_file)

    for index, row in df.iterrows():
        orgname = row['Firm'].title()
        location = row['Location']
        print("Processing {} ({}/{})".format(orgname, index, len(df)-1))

        # Try with google's first result
        name = googlesearch(orgname, location)
        print('result: {}'.format(name))

        if name is None and CLEARBIT_TOKEN:
            name = get_domain_from_clearbit(orgname)
            if name is None:
                df.loc[index,'Domain'] = "none"
            else:
                df.loc[index,'Domain'] = name
                print("Found via Clearbit: {}".format(name))
        else:
            df.loc[index,'Domain'] = name
            print("Found via Google: {}".format(name))
        record = df.loc[index, :]
        record = pd.DataFrame(record)
        record = record.transpose()
        record.to_csv(output_file, mode='a', header=False)
        del record

    df.to_csv(output_file)

if __name__ == "__main__":
    main()
