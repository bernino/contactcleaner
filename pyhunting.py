from pyhunter import PyHunter
import pandas as pd
import json
from pandas.io.json import json_normalize
import validators
import os
import configparser

if os.getenv('PYHUNTER'):
    pyhunterapikey = os.getenv('PYHUNTER')
else:
    config = configparser.ConfigParser()
    config.read('secrets')
    pyhunterapikey = config['pyhunter']['api']

hunter = PyHunter(pyhunterapikey)

source_file = 'domainresolution-all-banks-clean-no-dupes.csv'
out_file = 'pyhunterout.csv'
domains = 'domain'
organisation = 'Firm'

df = pd.read_csv(source_file)
df = df[507:]

normalised2 = pd.DataFrame()

# just in case there are duplicate domains we don't want to API call twice
df = df.drop_duplicates(subset=['domain'])

for index, row in df.iterrows():
    domain = row[domains]
    # validators.domain does exactly that - nifty little tool
    # also we only want to lookup unique domains
    if validators.domain(domain) and domain != 'wikipedia.org' and domain != '4icu.org':
        print("processing {} row {}".format(domain, index))
        try:
            results = hunter.domain_search(domain, limit=100, emails_type='personal')
        except:
            results = None

        normalised = json_normalize(results['emails'])
        normalised['org'] = row[organisation]
        normalised.to_csv('list.csv', mode='a', header=False, encoding='utf-8')
        normalised2 = normalised2.append(normalised, sort=True)

normalised2.to_csv(out_file)