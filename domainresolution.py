import clearbit
import json
import os
import pandas as pd
import configparser
import requests
import nltk
import tldextract

api_url_base = 'https://company.clearbit.com/v1/'
api_url_base2 = 'https://autocomplete.clearbit.com/v1/'
url = 'https://scrapeulous.com/api'

source_file = 'raw-eu-unis.csv'
out_file = 'domainresolution.csv'
colname = "a"

df = pd.read_csv(source_file)
# df = df[:15]
# df = df.loc[df['c'] == 'ch']

if os.getenv('CLEARBIT_TOKEN'):
    clearbit.key = os.getenv('CLEARBIT_TOKEN')
else:
    config = configparser.ConfigParser()
    config.read('secrets')
    clearbit.key = config['clearbit']['key']
    scrapelous = config['scrapelous']['api']

headers = {'Content-Type': 'application/json',
           'Authorization': 'Bearer {0}'.format(clearbit.key)}


def lookupname(name):
    payload = {
        "API_KEY": scrapelous,
        "function": "https://raw.githubusercontent.com/NikolaiT/scrapeulous/master/google_scraper.js",
        "items": [name]
    }
    response = requests.post(url, data=json.dumps(payload))
    if response.status_code == 200:
        results = json.loads(response.content.decode('utf-8'))
        try:
            domain = results[0]['result'][0]['results'][0]['link']
            tldr = tldextract.extract(domain)
            domain = tldr.domain+'.'+tldr.suffix
            return domain
        except:
            return None
    else:
        return None

def nouns(name):
    tokens = nltk.word_tokenize(name)
    stopwords = ['Virgin', 'Care', 'Nuffield', 'Health', 'Ltd.', 'Co.', '(UK)', 'UK', 'Limited', 'Assurance', 'Society', 'Ltd', 'plc', 'Co', 
                 'Financial', 'Company', 'Branch', 'Group', 'London', 'Corporation', 'PLC', 'FS', 'Plc']
    tokens = [word for word in tokens if word not in stopwords]
    tags = nltk.pos_tag(tokens)
    nouns = [word for word,pos in tags if (pos == 'NNP' or pos == 'JJ' or pos == 'NN')]
    nouns = ' '.join(nouns)
    return nouns


def get_fdomain(name):
    # based on https://clearbit.com/docs?shell#name-to-domain-api
    api_url = '{}companies/suggest?query={}'.format(api_url_base2, name)
    response = requests.get(api_url, headers=headers)
    print(json.loads(response.content.decode('utf-8')))
    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))
    else:
        return None


def get_domain(name):
    # based on https://clearbit.com/docs?shell#name-to-domain-api
    # could also use hunter.domain_search(company='Instragram', limit=5, emails_type='personal')
    # but not as precise...
    # https://github.com/VonStruddle/PyHunter
    api_url = '{}domains/find?name={}'.format(api_url_base, name)
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))
    else:
        return None

for index, row in df.iterrows():
    # TODO: only process Authorised firms for banking
    print('..........')
    print("processing {}".format(row[colname]))
    # nounname = str(nouns(row[colname]))
    # print("nouns are: {}".format(nounname))

    # lets first try full name and if that doesn't resolve
    # then we try the nouns in the name
    # could also use:
    # name = clearbit.NameToDomain.find(name=row[colname])
    name = get_domain(row[colname])
    if name is None:
        # try with google's first result
        name = lookupname(row[colname])
        # name = get_domain(nounname)
        if name is None:
            # specific for a hospitals csv
        #     if row['Website']:
        #         tldr = tldextract.extract(str(row['Website']))
        #         domain = tldr.domain+'.'+tldr.suffix
        #         df.loc[index,'domain'] = domain
        #         df.loc[index,'nounname'] = nounname
        #     else:
            df.loc[index,'domain'] = "none"
            # df.loc[index,'nounname'] = nounname
        else:
            df.loc[index,'domain'] = name
            # df.loc[index,'nounname'] = nounname
            print("found via google: {}".format(name))

    else:
        df.loc[index,'domain'] = name['domain']
        # df.loc[index,'nounname'] = nounname
        print("found: {}".format(name['domain']))
        # record = df.loc[index, :]
        # record = pd.DataFrame(record)
        # record = record.transpose()
        # record.to_csv('list.csv', mode='a', header=False)
        # del record

df.to_csv(out_file)