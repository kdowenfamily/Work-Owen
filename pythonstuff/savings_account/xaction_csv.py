#!/usr/bin/python

import csv, json, re, logging
from dateutil.parser import parse
from buckets import Buckets
from bucket import Bucket

logging.basicConfig(filename="savings.log",
        format="[%(asctime)s] [%(levelname)-7s] [%(filename)s:%(lineno)d] %(message)s",
        level=logging.DEBUG)
log = logging.getLogger(__name__)

# A list of transactions from a CSV file.
class XactionCsv(object):
    def __init__(self, in_file="", start="1/1/1970", end="1/1/2500"):
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
        boring = ['', 'Scheduled', 'Split']
        useful = []
        GRAND_TOTAL_COL = 3 # this is the column where the grand total lives in the "Running Total" row
        BALANCE_COL = 7 # this is the column where the balance lives in the "Balance" row

        if not in_file:
            return useful

        with open(in_file, 'rb') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if in_data and not ("Running Total" in row):
                    head_pos = 0
                    goodies = {}
                    for header in headers:
                        if (not (header in boring)) and (len(row) > head_pos):
                            goodies[header] = row[head_pos]
                        head_pos += 1
                    if goodies and goodies["Date"]:
                        useful.append(goodies)
        
                if 'Date' in row:
                    in_data = True
                    headers = row
                elif ("Running Total" in row):
                    self.grand_total = Bucket.string2float(row[GRAND_TOTAL_COL])
                elif ("Balance:" in row):
                    if self.end_balance:
                        # This is past the last row, with the earliest transaction.
                        # Take the last row and make an implicit "start" transaction.
                        # TODO - this is a kludge
                        start_bal = Bucket.string2float(useful[-1]["Balance"])
                        start_amt = Bucket.string2float(useful[-1]["Amount"])
                        self.start_balance = start_bal - start_amt
                        self.start_date = useful[-1]["Date"]
                    else:
                        self.end_balance = Bucket.string2float(row[BALANCE_COL])

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
                    row[rkey] = Bucket.string2float(row[rkey])

            # prepare the data for creating a transaction
            if "Running Total" in row.keys():
                # this is a savings-account sheet (custom-made)
                xact_data['Amount'] = float(row.pop('Total'))
                xact_data['Memo/Notes'] = row.pop('Transaction')
                xact_data['Date'] = row.pop('Date')
                xact_data['Running Total'] = row.pop('Running Total')
                bkts = []
                for rkey in row.keys():
                    bkts.append({"title":rkey, "total":row[rkey]})
                xact_data['buckets'] = bkts
            else:
                # this is a CSV from Quicken
                if not (('Tags' in row.keys()) and ("Savings" not in row['Tags'])):
                    # avoid rows where: there are tags, and "Savings" isn't one of them
                    xact_data = row

            # create the transaction
            if xact_data and self._in_range(xact_data['Date']):
                xactions.append(xact_data)

        return xactions

    def _in_range(self, offered_date):
        start = parse(self.start_range)
        end = parse(self.end_range)
        date = parse(offered_date)
        return (start <= date) and (date <= end)


    def _verify(self):
        ret = 0.0
        bckts = Buckets.from_file(Buckets.BUCKETS_FILE) # re-initialize

        for xact in self.raw_transactions:
            ret += xact['Amount']
            bckts += Buckets(xact['buckets'])

        print "Expected %.2f, got %.2f from totals" % (self.grand_total, ret)
        print "Expected %.2f, got %.2f from buckets" % (self.grand_total, bckts.total)
        print str(len(self.raw_transactions)) + " total transactions\n"

    def __str__(self):
        ret = ""
        for xaction in sorted(self.raw_transactions, key=lambda k: k['Date']):
            ret += str(xaction) + "\n"
        return ret

if __name__ == "__main__":
    X_FILES = [
            "data/private/cc-demo.csv",
            "data/private/cc-export-2018-12-26.csv",
            "data/private/savings.csv",
            "data/private/spending2012.csv",
            "data/private/spending2016.csv",
            "data/private/sp2.csv",
            "data/private/savings-xactions-export-2018-12-30.csv"
            ]

    csv = XactionCsv(in_file=X_FILES[4])
    print
    print "Input file is " + X_FILES[4] + "\n"
    with open("/tmp/xaction.csv", 'w') as f:
        f.write(str(csv))
    print "Output file is /tmp/xaction.csv\n"
    csv._verify()
