# Overview

The savings.py program splits a savings account into configurable "buckets" for things you want, like
Vacation, New Car, and College Fund.  As input, it takes files you can save out from Quicken. You can
go through the real savings-account transactions from Quicken and decide which bucket or buckets get
those transfers.  For example:

- If you transfer in a 100 deposit from your Mom, it might go into the College Fund bucket.
- If you transferred out 1000 for a new car, that would probably come from the New Car bucket.
- If you deposit 300 dollars from a bonus, you might want to give 100 to each bucket.

At the end of a run, the program lists all the buckets and shows how much they each have.  It also
outputs a spreadsheet that you can feed to the program the next time you run it.  The spreadsheet
provides the starting point for the next run.

# Files

## Config Files

You need to write at least one JSON file, described below, to set up the buckets you want.

### data/buckets.json

The divisions in the account.  This is a list of dictionaries with this format: 

```json
[
  {
    "title": "",
    "alt_titles": [""\*]
    "weight": n,
    "order": n,
    "tags": [""\*]
  },
  {
    ...
  },
  ...
]
```

Prepare exactly one of these files to establish the buckets you want in your account.
For example:

```json
[
  {
    "title": "Home Maintenance",
    "alt_titles": [
        "Maint.",
        "Braces"
    ],
    "weight": 1,
    "order": 1,
    "tags": []
  },
  {
    "title": "College Fund",
    "alt_titles": [
      "Linsey College",
      "Molly College",
      "Liam College"
    ],
    "weight": 1,
    "order": 2,
    "tags": [
      "Education"
    ]
  },
  {
    "title": "Oil",
    "weight": 1,
    "order": 3,
    "tags": [
      "Utilities"
    ]
  }
]
```

Place this file in a "data" directory under the savings.py script.

### budgets/private/\<foo\>.json

Prepare one of these for each "regular" transfer into savings.  These are scheduled transactions
that you create in your banking app, or just regular transfers that you periodically make (assuming
the transfers are all exactly the same amount of money).

The file contains one transfer pattern with a date, title, payer, payee, and a list of dictionaries with this format:

```json
  "date": "\*",
  "title": "",
  "per_year": n,
  "payer": "",
  "payee": "",
  {
    "title": "", # a bucket title
    "total": n
  }
```

Examples of these transfers:
- Dad's scheduled transfer after each paycheck (twice per month, or 24 times per year): how it is divided
- Mom's scheduled transfer after each paycheck (once per week, or 52 times per year).

To show the contents of one of these files, along with the total, run:

```
transaction\_template.py -j budgets/private/\<foo\>.json.
```

## File From savings.py -  spending.csv

This is the final output of the program, and the first input on a later run.
It is the bucketized state of the savings account, one transaction per line:

```
Date,Transaction,Running Total,Total,\<bucket1\>,\<bucket2\>,...,\<bucketN\>
```

You do not need to make this; it is auto-generated.

## Input Files From Quicken

You get these from the Quicken program.
These files tell savings.py the details of the transactions at your bank and your credit card.

### savings\_export.csv

From Quicken, a list of transactions in and out of the savings account:

```csv
  ,"Scheduled","Split","Date","Payee","Category","Amount","Balance"
```

### cc\_export.csv

From Quicken, a list of transactions in and out of one credit card account:

```csv
  ,"Scheduled","Split","Date","Payee","Category","Tags","Amount","Memo/Notes"
```
