#!/usr/bin/python

import logging
from copy import deepcopy
from transaction import Transaction
from buckets import Buckets

logging.basicConfig(filename="savings.log",
        format="[%(asctime)s] [%(levelname)-7s] [%(filename)s:%(lineno)d] %(message)s",
        level=logging.DEBUG)
log = logging.getLogger(__name__)

# An initial transaction, based on a start date and a total amount in the savings account.
# Average all the current paychecks, and give each bucket the percentage allotted by those paychecks.
class Start_Transaction(Transaction):
    def __init__(self, source_account="", start_date="1/1/2015", amount=0.00):
        # cobble together a dictionary
        my_data = {
                    "Date": start_date,
                    "Amount": amount,
                    "Payee": "",
                    "Tags": "",
                    "Category": "",
                    "Memo/Notes": "Restart budget",
                    "buckets": {}
                }

        # initialize this like a normal transaction, buckets already done
        super(Start_Transaction, self).__init__(source_account=source_account, xact_data=my_data)

        # for all master bucket lists, multiply the values by the 'per-year' number in the transaction
        blists = []
        for mptt in Transaction.masterPaychecks:
            bkts = deepcopy(mptt.buckets)   # make a copy of the bucket list
            for bkt in bkts.contents:
                bkt.total *= mptt.per_year
            blists.append(bkts)

        # sum up the bucket lists into our empty one
        self.buckets = self.buckets.dupe()  # empty out our list with an empty dupe
        for bl in blists:
            self.buckets += bl

        # for each bucket, get the percentage of the current total, store it in 'weight' property
        list_total = self.buckets.total     # this is a yearly total, from the sum of a year's paychecks
        for bkt in self.buckets.contents:
            bkt.weight = bkt.total / list_total         # store the percentage
            bkt.total = round(bkt.weight * amount)      # derive the *real* total from the amount given

        # reconcile the buckets with the initial total
        self.reconcile_total()


if __name__ == "__main__":
    bkts = Buckets.from_file(Buckets.BUCKETS_FILE)

    tr1 = Start_Transaction(source_account="checking", start_date="11/12/2001", amount=32134.64)
    bkts += tr1.buckets
    print "\n\nStart Transaction:\n"
    print tr1
    print "\nTransaction Breakdown:\n"
    print tr1.buckets.show()
    print "\nBucket Breakdown:\n"
    print bkts.show()
