# Contact Cleaner

## Objective

The objective of this tool is to build sales leads.

## Requirements

Before you get started, you need API keys/tokens for the following services

* [SerpApi](https://serpapi.com/) (Primary)
* [Clearbit](https://clearbit.com/) (Fallback)
* [Hunter](https://hunter.io)

## Workflow

The workflow for this tool is as follows:

* Feed a CSV file of company names to `domainresolver.py` to get a list of domain (or best guess at least) to the company
* With the list of domains, we can feed

### Domain Resolution

The input CSV file must have the following headers:

* "Firm" - The company you're looking up
* "Location" - Optional, but can help narrow down and improve the search

First we need to set our API key/tokens:
```
$ export CLEARBIT_TOKEN=YourToken
$ export SERP_API_KEY=YourApiKey
```

Next, we can look up the data:

```
$ python domainresolution.py input-file.csv output-file.csv
[...]
```

You can now inspect your new file (`output-file.csv`) and will notice that it is the same as `input-file.csv`, but with a new column called "Domain".

Do however sanity check this file manually to ensure it makes sense. You might need to delete some rows that doesn't make sense before moving on to the next step.

### Contact Hunting

With the data from the previous step, we can now start looking for contacts at these companies.


Before we begin the next step set our API key for Hunter:

```
$ export HUNTER_API_TOKEN=YourToken
```

We can now do the lookup.
```
$ python pyhunting.py input-file.csv output-file.csv
[...]
```

## Experimentals

There are a few experimental tools in the lab folder that are yet to be updated/documented.
