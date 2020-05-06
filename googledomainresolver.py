import json
import os
import pandas as pd
import configparser
import requests
import tldextract

# using the scrapelous API to query google
# because beautifulsoup doesn't work with google
url = 'https://scrapeulous.com/api'

source_file = 'domainresolution-all-banks.csv'
out_file = 'domainresolution.csv'
namedentity = "Firm"
domain = "domain"

df = pd.read_csv(source_file)
# small sets while testing:
# df = df[:15]

config = configparser.ConfigParser()
config.read('secrets')
scrapelous = config['scrapelous']['api']

def lookupname(name):
    payload = {
        "API_KEY": scrapelous,
        "function": "https://raw.githubusercontent.com/NikolaiT/scrapeulous/master/google_scraper.js",
        "items": [name]
    }
    # TODO: try - except?
    response = requests.post(url, data=json.dumps(payload))
    if response.status_code == 200:
        results = json.loads(response.content.decode('utf-8'))
        try:
            domain = results[0]['result'][0]['results'][0]['link']
            tldr = tldextract.extract(domain)
            domain = tldr.domain+'.'+tldr.suffix
            # TODO: perhaps rinse the domains further for wikipedia, linkedin, facebook etc.
            # and take next result in the results json?
            return domain
        except:
            return None
    else:
        return None

for index, row in df.iterrows():
    # TODO: only process Authorised firms for banking?
    name = row[namedentity]
    domainname = str(row[domain])

    print('..........')
    print("processing {}".format(name))

    if domainname == 'none':
        domainname = lookupname(name)
        if domainname is None:
            df.loc[index,'domain'] = "none"
        else:
            df.loc[index,'domain'] = domainname
            print("found via google: {}".format(domainname))

        # TODO: test if line by line writing works
        # to avoid loosing all data on conn problems
        # record = df.loc[index, :]
        # record = pd.DataFrame(record)
        # record = record.transpose()
        # record.to_csv('list.csv', mode='a', header=False)
        # del record
    else:
        pass

df.to_csv(out_file)