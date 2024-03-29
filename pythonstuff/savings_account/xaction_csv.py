#!/usr/bin/python3

import csv, re
from datetime import datetime
from buckets import Buckets
from usd import USD
from constants import log

# A list of transactions from a CSV file.
class XactionCsv(object):
    def __init__(self, in_file="", start="1970-01-01", end="2500-12-31"):
        log.info("Parsing CSV of transactions, %s." % in_file)
        self.grand_total = 0.0
        self.start_balance = 0.0
        self.end_balance = 0.0
        self.start_date = None
        self.start_range = start
        self.end_range = end

        # create a Transaction for each row
        rows = self._parse_csv(in_file)
        self.raw_transactions = self._parse_rows(rows)

        log.info("Done parsing CSV of transactions, %d transactions." % len(self.raw_transactions))

    # Find the header row and match every value to its header.
    # Return a list of [{header1 : value1}, {header2 : value2},...]
    def _parse_csv(self, in_file=""):
        in_data = False
        headers = []
        boring = ['', 'Scheduled', 'Split', '\xef\xbb\xbf'] # ignore columns with any of these headers
        useful = []
        GRAND_TOTAL_COL = 3 # this is the column where the grand total lives in the "Running Total" row
        BALANCE_COL = 7     # this is the column where the balance lives in the "Balance" row

        if not in_file:
            return useful

        with open(in_file, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                # get raw values matched up with their headers
                if in_data and not ("Running Total" in row):
                    head_pos = 0
                    goodies = {}
                    for header in headers:
                        if (not (header in boring)) and (len(row) > head_pos):
                            goodies[header] = row[head_pos]
                        head_pos += 1
                    if goodies and ("Date" in goodies.keys()) and goodies["Date"]:
                        useful.append(goodies)
        
                # make switches based on row contents
                if 'Date' in row:
                    # top row for savings.py output or exported CSV from Quicken
                    in_data = True
                    headers = row
                elif ("Running Total" in row):
                    # second row for savings.py output only - contains grand total
                    self.grand_total = USD(row[GRAND_TOTAL_COL])
                elif ("Balance:" in row):
                    # this must be an exported CSV from Quicken, last row
                    if self.end_balance:
                        # This is past the last row, with the earliest transaction.
                        # Take the last row and make an implicit "start" transaction.
                        start_bal = USD(useful[-1]["Balance"])
                        start_amt = USD(useful[-1]["Amount"])
                        self.start_balance = start_bal - start_amt
                        self.start_date = useful[-1]["Date"]
                    else:
                        self.end_balance = USD(row[BALANCE_COL])

                if 'Total Inflows:' in row:
                    in_data = False 

        return useful

    # The input rows are each a list of dicts: [{"head1" : "val1"}, {"head2": "val2"}, ...]
    # Normalize these rows.  Separate out the metadata, and put the rest of 
    # the dicts into a "buckets" sub-list.
    # Return the list of raw-transaction dictionariess.
    def _parse_rows(self, rows=[]):
        xactions = []

        for row in rows:
            xact_data = {}

            # clean the raw data
            for rkey in row.keys():
                if re.search("^[\s\,\(,\),\.\-\$\d]+$", row[rkey]):
                    row[rkey] = USD(row[rkey])

            # prepare the data for creating a transaction
            if "Running Total" in row.keys():
                # this is a savings-account sheet (custom-made)
                xact_data['Amount'] = row.pop('Total')
                xact_data['Memo/Notes'] = row.pop('Transaction')
                xact_data['Date'] = row.pop('Date')
                xact_data['Running Total'] = row.pop('Running Total')
                bkts = []
                for rkey in row.keys():
                    bkts.append({"title":rkey, "total":row[rkey]})
                xact_data['buckets'] = bkts
            else:
                # this is a CSV from Quicken
                if not (('Tags' in row.keys()) and (not re.search(r"savings", row['Tags'], re.IGNORECASE))):
                    # avoid rows where: there are tags, and "savings" isn't one of them
                    xact_data = row

            # create one raw transaction
            if xact_data and self._in_range(xact_data['Date']):
                xactions.append(xact_data)

        return xactions

    def _in_range(self, offered_date):
        start = datetime.strptime(self.start_range, "%Y-%m-%d")
        end = datetime.strptime(self.end_range, "%Y-%m-%d")
        try:
            date = datetime.strptime(offered_date, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                date = datetime.strptime(offered_date, "%m/%d/%Y")
            except ValueError:
                print(f"Warning:  Cannot parse {offered_date} - calling it '2000-01-01'.")
                date = datetime.strptime("2000-01-01", "%Y-%m-%d")
        return (start <= date) and (date <= end)


    def _verify(self):
        ret = 0.0
        bckts = Buckets.from_file(Buckets.BUCKETS_FILE) # re-initialize

        for xact in self.raw_transactions:
            ret += xact['Amount'].as_float()
            bckts += Buckets(xact['buckets'])

        print("Expected %.2f, got %.2f from totals" % (self.grand_total.as_float(), ret))
        print("Expected %.2f, got %.2f from buckets" % (self.grand_total.as_float(), bckts.total.as_float()))
        print(str(len(self.raw_transactions)) + " total transactions\n")

    def __str__(self):
        ret = ""
        for xaction in sorted(self.raw_transactions, key=lambda k: k['Date']):
            ret += str(xaction) + "\n"
        return ret

if __name__ == "__main__":
    X_FILES = [
            "data/private/cc-short.csv",
            "data/private/cc-export-2018-12-26.csv",
            "data/private/savings.csv",
            "data/private/spending2012.csv",
            "data/private/spending2016.csv",
            "data/private/savings-2020-05-08.csv",
            "data/private/savings-2020-04-02.csv"
            ]

    csv = XactionCsv(in_file=X_FILES[0])
    print()
    print("Input file is " + X_FILES[0] + "\n")
    with open("/tmp/xaction.csv", 'w') as f:
        f.write(str(csv))
    print("Output file is /tmp/xaction.csv\n")
    if 'buckets' in csv.raw_transactions[0]:
        csv._verify()
