# Design

## Files

### Config Files

#### buckets.json

The divisions in the account.  This is a list of dictionaries with this format: 

{code:java}
  {
    "title": "",
    "weight": n,
    "order": n,
    "tags": [""*]
  }
{code}

#### accounts.json

A list of valid accounts:

{code:java}
  {
    "name": "",
    "type": "Savings|Checking|CC"
  }
{code}

#### transfers/<foo>.json

One transfer pattern with a date, payer, payee, and
  a list of dictionaries with this format:

{code:java}
  {
    "title": "", # a bucket title
    "total": n
  }
{code}

  Examples:
  - Dan's paycheck: how it is divided
  - Kathy's paycheck

#### savings.csv

The bucketized state of the savings account
  - one transaction per line: date_time, peer_account, amount of change in each bucket

### Input Files

#### savings_export.csv

From Quicken, a list of transactions in and out of the savings account
  ,"Scheduled","Split","Date","Payee","Category","Amount","Balance"

#### cc_export.csv

From Quicken, a list of transactions in and out of one credit card
  ,"Scheduled","Split","Date","Payee","Category","Tags","Amount","Memo/Notes"


## Classes

### Transaction_Template

Describes how to split up a transfer into savings 
  buckets.  From transfers/<foo>.json?

#### Properties
  - buckets:  Buckets list, where all buckets add up to the total. 
  - payer:  account that always pays this (could be Savings)
  - payee: account that always receives this (or this could be Savings)

#### Methods
  - __init__(): load up and parse the buckets.
      load() up the buckets from the JSON into self.buckets
      set the payer and payee from the JSON
  - load():  load JSON file into self.buckets.

### Transaction

Describes a transaction event in the account.
  This is about freezing a transaction in one moment of time, 
  and it gets listed out in order.

#### Properties
  - date_time:  when it happened
  - total:  the grand total of all buckets
  - payer:  account that always pays this
  - payee: account that always receives this
  - tag(s), maybe
  - note, maybe
  - buckets:  Buckets list, where all buckets add up to the total. 
  - total2Tr_Template: dictionary of all "known" totals to their Transaction_Template objects

#### Methods
  - __init__ (class):  find all transaction-template JSON files (in transfers/<foo>.json) and make
      a Transaction_Template object for each of them.
      Create total2Tr_Template, a map.
      foreach bucket in Savings.buckets:
        self.buckets.append(Bucket({'title', bucket.title}))
  - __init__(src_acct, csv_dict, final=False): load up and parse the transaction info, a dictionary from 
      csv_line.
      The csv_dict contains total, date_time, payer account, payee account. Load them up.
      If (final):
        Return - no need to break it down.
      If total is in the templates:
        Take the buckets/amounts from the template.
        confirm(0) that buckets/amounts are OK
      If total is unknown:
        ask() for buckets of transfer.
  - ask():  interactive loop, showing all bucket names as pick list.
      print xaction total, date, source (or Payer), dest (or Payee) 
        Either source or dest is Savings itself.
      question:  Do you have a breakdown of this xaction?
      - Y:  provide path to .csv, start and end dates
        Create Breakdown object, which parses the .csv file (a CC file, or similar),
          reads each record and makes a full Transaction(final=True) out of it.  
          The Transaction contains a full set of Buckets, with one bucket having some 
          money added or subtracted.  Also, should have a Payer or Payee.
      - N:  confirm() to start loop
  - add_bucket(bucket_name, amount, other_account): take a bucket and ask for another
      if bucket_name != "":
        add amount to that bucket, change total
      confirm()
  - confirm(total_left):
      print list of buckets, amount in each bucket (possibly all 0), total, and total left to add
      question: provide bucket number, amount, and name of Payer or Payee (peer account).
      Create Transaction with full set of Buckets, where one has some money added
        or subtracted, and the name of the Payer or Payee.
      Does total entered == total needed?
      - Y: 
        question: Is this OK?
        - Y: exit loop.
        - N: enter bucket and new amount
      - N: back to top.

### Buckets

Is a list of "buckets" in a savings account.

#### Properties
  - contents: a list of Bucket objects

#### Methods
  - __init__(buckets.json): load up Buckets from the JSON file
    Read the json file and make one Bucket object per bucket dict.
  - __str__(): print all totals in priority order, separated by commas
  - __eq__(other): compare all buckets in this.contents with other.contents.
  - __plus__(other): add all buckets in other.contents to this.contents.
                     foreach ob in other.buckets:
                       Use self._find(ob.title) to find each bucket.
                       Use self.bucket + other.bucket.
  - _find(title):  return a bucket in this list with the given title.

### Bucket

Is one "bucket" in a savings account.

#### Properties
  - total
  - title
  - weight
  - order
  - tags()

#### Methods
  - __init__(dict): take one bucket dict (from JSON file) and load up
    the properties
  - __str__(): print the total
  - change(int):  take the money amount and add it to the bucket
  - __eq__(other):  compare all properties in this with those in other.
  - __plus__(other): if this.title eq other.title:
                         this.total += other.total

### XactionCsv

Any CSV file from Quicken
  Load up from a .csv file.

#### Properties
  - source_acct (string)
  - transactions[] (list of Transaction() objects)

#### Methods
  - __init__(path2csv, buckets): read the CSV and get all its transactions
    set self.source_acct
    for each CSV line:
      make xactionDict (dictionary) out of CSV line
      Append a new Transaction(self.source_acct, xactionDict, buckets) to self.transactions[]

### Savings

Is a savings account.

#### Class Properties:
  - buckets:  a Buckets list object

#### Properties
  - total:  total of all Buckets after all transactions
  - transactions: list of Transactions in this account, sorted by date
  - snapshots: one bucket-list snapshot per transaction

#### Methods
  - __init__(path2buckets.json, path2savings.csv):
    init_buckets(path2buckets.json)
    load_sv(path2savings.csv)
  - init_buckets(path2buckets.json):  load up the buckets.json file and make all the buckets
  - load_sv(path2savings.csv): load the savings.csv file with the starting total and fill the buckets 
      with start amounts.
  - load_transactions([path2xactions+]):
      foreach path in path2xactions:
        transactions.append(XactionCsv(path, self.buckets).transactions)
        self.snapshot()
  - snapshot(): do a deepcopy of the current buckets list, with a timestamp
  - csv_out(): write out a .csv file with one snapshot of the buckets per row,
    ordered by transaction date.
  - __str__():  make a string with the start total, all buckets now, and the final total.

  - __main__():
    savings = Savings(path2buckets.json, path2savings.csv)
    savings.load_transactions(savings_export.csv, cc_export.csv)
    savings.csv_out()
    print savings
