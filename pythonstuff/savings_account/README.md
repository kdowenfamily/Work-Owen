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

### buckets.json

The divisions in the account.  This is a list of dictionaries with this format: 

```json
  {
    "title": "",
    "weight": n,
    "order": n,
    "tags": [""*]
  }
```

### accounts.json

A list of valid accounts:

```json
  {
    "name": "",
    "type": "Savings|Checking|CC"
  }
```

### transfers/<foo>.json

One transfer pattern with a date, payer, payee, and
  a list of dictionaries with this format:

```json
  {
    "title": "", # a bucket title
    "total": n
  }
```

  Examples:
  - Dan's paycheck: how it is divided
  - Kathy's paycheck

### spending.csv

This is the final output of the program, and the first input on a later run.

The bucketized state of the savings account
  - one transaction per line: date\_time, peer account, amount of change in each bucket

## Input Files From Quicken

### savings\_export.csv

From Quicken, a list of transactions in and out of the savings account

```csv
  ,"Scheduled","Split","Date","Payee","Category","Amount","Balance"
```

### cc\_export.csv

From Quicken, a list of transactions in and out of one credit card

```csv
  ,"Scheduled","Split","Date","Payee","Category","Tags","Amount","Memo/Notes"
```

# Bug and Enhancement List

## To Do

- comments in the CSV
- manual division of credit-card transfers into individual CC transactions (big)

## Done

- Losing old buckets that later morphed into new names
- For credit-card reports, do not ask unless it is tagged for Savings
- Allow multiple titles per bucket
- Support old paycheck splits

