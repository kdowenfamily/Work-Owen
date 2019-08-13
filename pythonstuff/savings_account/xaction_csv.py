#!/usr/bin/python

import csv, json, re, logging
from dateutil.parser import parse
from transaction import Transaction
from buckets import Buckets

logging.basicConfig(filename="savings.log",
                    format="[%(asctime)s] [%(levelname)-7s] %(message)s",
                    level=logging.DEBUG)

# A list of transactions from a CSV file.
class XactionCsv(object):
    def __init__(self, in_file=""):
        logging.info("Parsing CSV of transactions, %s." % in_file)

        # identify the account type
        source_account = ""
        if 'saving' in in_file:
            source_account = "savings"
        elif 'cc' in in_file:
            source_account = "credit card"

        # create a Transaction for each row
        rows = self._parse_csv(in_file)
        self.transactions = self._parse_rows(source_account, rows)

        # if this is a credit card, weed out the non-savings transactions
        if source_account == "credit card":
            self.transactions = self._prune_cc()

        logging.info("Done parsing CSV of transactions, %d transactions." % len(self.transactions))

    def _parse_csv(self, in_file=""):
        in_data = False
        headers = []
        boring = ['', 'Scheduled', 'Split']
        useful = []

        if not in_file:
            return useful

        with open(in_file) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if in_data:
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
                if 'Total Inflows:' in row:
                    in_data = False 

        return useful

    # The rows are each a dict:{"head1" : "val1", "head2": "val2", ...}
    def _parse_rows(self, source_account="", rows=[]):
        xactions = []

        for row in rows:
            xact_data = {}

            # clean the raw data
            for rkey in row.keys():
                if re.search("^[\s\,\.\-\$\d]+$", row[rkey]):
                    row[rkey] = self._string2float(row[rkey])

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
                xact_data = row
                # TODO if not tagged for savings, skip it...?

            # create the transaction
            xactions.append(Transaction(source_account=source_account, xact_data=xact_data))

        return xactions

    def _prune_cc(self):
        good_xacts = []

        for xact in self.transactions:
            if ("savings" in xact.tags) or ("Savings" in xact.tags):
                good_xacts.append(xact)
            else:
                logging.debug("Pruning %s, %f, transaction from credit card" % (xact.date_time, xact.total) )

        return good_xacts

    def _string2float(self, st):
        money = str(st)                         # incase it is already a number

        money = money.strip()                   # remove any leading/trailing space
        money = money.strip("$")                # remove any leading '$'
        money = re.sub(r',', "", money)         # no commas
        money = re.sub(r'^-$', "0", money)      # a '-' translates to 0
        return float(money)

    def __str__(self):
        ret = ""

        for xaction in sorted(self.transactions, key=lambda k: k.date_time):
            ret += str(xaction)
            '''
            bkts = xaction.buckets.find_non_zero()
            if bkts:
                btitles = []
                for bkt in bkts:
                    btitles.append(bkt.title)
                ret += " => " + ", ".join(btitles)
            '''
            ret += "\n"

        return ret

if __name__ == "__main__":
    X_FILES = ["data/private/cc-demo.csv",
           "data/private/cc-export-2018-12-26.csv",
           "data/private/savings.csv",
           "data/private/savings-xactions-export-2018-12-30.csv"]

    csv = XactionCsv(in_file=X_FILES[3])
    print
    print csv
