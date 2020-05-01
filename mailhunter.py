#!/usr/bin/env python3

import requests
import json
import pandas as pd 
from pandas.io.json import json_normalize
import os
import configparser

source = ''
out_file = 'mailhunter.csv'
colname = 'domain'

df = pd.read_csv(source)
# df = df[:2]

if os.getenv('snov_client_id'):
    client_id = os.getenv('snov_client_id')
    client_secret = os.getenv('snov_client_secret')
else:
    config = configparser.ConfigParser()
    config.read('secrets')
    client_id = config['snov']['client_id']
    client_secret = config['snov']['client_secret']


def get_access_token():
    global client_id, client_secret
    params = {
        'grant_type':'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }

    res = requests.post('https://api.snov.io/v1/oauth/access_token', data=params)
    resText = res.text.encode('ascii','ignore')

    return json.loads(resText)['access_token']

def get_domain_search(domain):
    token = get_access_token()
    params = {'access_token':token,
            'domain':domain,
            'type': 'personal',
            'offset': 0,
            'limit': 100
    }

    res = requests.post('https://api.snov.io/v1/get-domain-emails-with-info', data=params)

    return json.loads(res.text)

normalised = pd.DataFrame()

for index, row in df.iterrows():
    domain = row[colname]
    if domain != 'none' and domain != 'nan.':
        print("processing {}".format(domain))
        emails = get_domain_search(domain)
        # print(json.dumps(emails, sort_keys=True, indent=4))
        try:
            emdf = json_normalize(emails['emails'])
            emdf['org'] = emails['companyName']
            print(emdf.head())
            normalised = normalised.append(emdf, sort=True)
        except Exception as e:
            print(e)

normalised.to_csv(out_file)
