import clearbit
import json
import os
import pandas as pd
import configparser
import requests
import tldextract
from serpapi.google_search_results import GoogleSearchResults

api_url_base = 'https://company.clearbit.com/v1/'
api_url_base2 = 'https://autocomplete.clearbit.com/v1/'

source_file = '/Users/bernino/dev/contactcleaner/banks/raw-banks.csv'
out_file = 'domainresolution.csv'
colname = "Firm"

df = pd.read_csv(source_file)
# df = df[:5]

if os.getenv('CLEARBIT_TOKEN'):
    clearbit.key = os.getenv('CLEARBIT_TOKEN')
else:
    config = configparser.ConfigParser()
    config.read('secrets')
    clearbit.key = config['clearbit']['key']
    GoogleSearchResults.SERP_API_KEY = ['serp']['api']

headers = {'Content-Type': 'application/json',
           'Authorization': 'Bearer {0}'.format(clearbit.key)}


def googlesearch(name):
    client = GoogleSearchResults({"q": name})
    # client = GoogleSearchResults({"q": "coffee", "location": "Austin,Texas"})
    result = client.get_json()
    domain = result['organic_results'][0]['link']
    tldr = tldextract.extract(domain)
    domain = tldr.domain+'.'+tldr.suffix
    return str(domain)


def get_domain(name):
    # based on https://clearbit.com/docs?shell#name-to-domain-api
    # could also use hunter.domain_search(company='Instragram', limit=5, emails_type='personal')
    # but not as precise...
    # https://github.com/VonStruddle/PyHunter
    api_url = '{}domains/find?name={}'.format(api_url_base, name)
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        name = json.loads(response.content.decode('utf-8'))
        return name['domain']
    else:
        return None


for index, row in df.iterrows():
    orgname = row[colname]
    print('..........')
    print("processing {}".format(orgname))

    # try with google's first result
    name = googlesearch(orgname)
    print('result: {}'.format(name))

    if name is None:
        name = get_domain(orgname)
        if name is None:
            df.loc[index,'domain'] = "none"
        else:
            df.loc[index,'domain'] = name
            print("found via clearbit: {}".format(name))

    else:
        df.loc[index,'domain'] = name
        print("found via google: {}".format(name))
    record = df.loc[index, :]
    record = pd.DataFrame(record)
    record = record.transpose()
    record.to_csv('list.csv', mode='a', header=False)
    del record

df.to_csv(out_file)