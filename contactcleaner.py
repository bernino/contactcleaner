import clearbit
import json
import os
import pandas as pd
import configparser

if os.getenv('CLEARBIT_TOKEN'):
    clearbit.key = os.getenv('CLEARBIT_TOKEN')
else:
    config = configparser.ConfigParser()
    config.read('secrets')
    clearbit.key = config['clearbit']['key']

# TODO: MongoDB
# client = pymongo.MongoClient("mongodb+srv://bernino:<password>@cluster0-nvy1s.mongodb.net/test?retryWrites=true&w=majority")
# db = client.test

df = pd.read_csv('list.csv')

# let's be polite and run a small set while we develop
# also we can max do 1000 per month
contacts = df.copy()
contacts = contacts[:250]

if not os.path.exists('json-dumps'):
    os.makedirs('json-dumps')


# in case we don't understand the data structure
# print(contacts)

for index, row in contacts.iterrows():
    lookup = {}
    # TODO: Email ETL
    # There should be ETL on email first...
    # and validation of email is valid
    # https://www.scottbrady91.com/Email-Verification/Python-Email-Verification-Script
    # or a service like: https://www.datavalidation.com/api/
    if row['email'] is None:
        pass
    else:
        email = row['email']

    print("Processing row {} with email {}".format(index, email))

    try:
        if "gmail" not in email and "hotmail" not in email:
            lookup = clearbit.Enrichment.find(email=email, stream=True)
        else:
            print("gmail or hotmail... not checking with API")
    except Exception as e:
        print(e)

    try:
        contacts.loc[index,'firstname'] = lookup['person']['name']['givenName']
        contacts.loc[index,'lastname'] = lookup['person']['name']['familyName']
    except:
        print("error 0")

    try:
        contacts.loc[index,'description'] = lookup['company']['description']
    except:
        print("error 3")

    try:
        contacts.loc[index,'segment'] = lookup['company']['category']['industry']
    except:
        print("error 1")

    try:
        contacts.loc[index,'naics'] = lookup['company']['category']['naicsCode']
    except:
        print("error 2")

    try:
        if lookup['company']['twitter']['handle'] is not None:
            contacts.loc[index,'twitter'] = "https://twitter.com/"+str(lookup['company']['twitter']['handle'])
    except:
        print("error 4")

    try:
        contacts.loc[index,'company_name'] = lookup['company']['name']
    except:
        print("error 5")

    # attention: record is a DF series and not a df so its transposed
    # transpose the created record and write sequentially
    # even if there's an iops penalty on writing sequentially
    # we rather do that than risk all stuff to be processed an error crash and no write
    record = contacts.loc[index, :]
    record = pd.DataFrame(record)
    record = record.transpose()
    record.to_csv('cleanlist.csv', mode='a', header=False)
    del record

    # in case we want to explore all data available
    # print(json.dumps(lookup, sort_keys=True, indent=4))

    # Dump all JSON data to files for future reference
    # this should better be done into a MongoDB
    try:
        jsonfile = "json-dumps/data"+str(index)+".json"
        with open(jsonfile, 'w') as outfile:
            json.dump(lookup, outfile, sort_keys=True, indent=4)
    except Exception as e:
        print(e)

    del lookup
