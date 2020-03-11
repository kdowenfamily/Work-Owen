#!/usr/bin/python

import logging, os
from copy import deepcopy
from transaction import Transaction
from transaction_template import Transaction_Template
from buckets import Buckets

logging.basicConfig(filename="savings.log",
        format="[%(asctime)s] [%(levelname)-7s] [%(filename)s:%(lineno)d] %(message)s",
        level=logging.DEBUG)
log = logging.getLogger(__name__)

# An initial transaction, based on a start date and a total amount in the savings account.
# Average all the current paychecks, and give each bucket the percentage allotted by those paychecks.
class Start_Transaction(Transaction):
    def __init__(self, source_account="", start_date="1/1/2015", amount=0.00, pay_ts=Transaction.masterPaychecks):
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
        super(Start_Transaction, self).__init__(source_account=source_account, xact_data=my_data, buckets=pay_ts[0].buckets)

        # for all master bucket lists, multiply the values by the 'per-year' number in the transaction
        blists = []
        for mptt in pay_ts:
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
            bkt.weight = bkt.total.as_float() / list_total.as_float()   # store the percentage
            bkt.total = round(amount.as_float() * bkt.weight)           # derive the *real* total from the amount given

        # reconcile the buckets with the initial total
        self.reconcile_total()


if __name__ == "__main__":
    bkts = Buckets.from_file(Buckets.BUCKETS_FILE)

    from usd import USD
    paycheck_templs = [Transaction_Template(os.path.dirname(__file__) + "/transfers/dan.json")]
    tr1 = Start_Transaction(source_account="checking", start_date="11/12/2001", amount=USD(100.00), pay_ts=paycheck_templs)
    bkts += tr1.buckets
    print "\n\nStart Transaction:\n"
    print tr1.show()
    print "\nTransaction Breakdown:\n"
    print tr1.buckets.show()
    print "\nBucket Breakdown:\n"
    print bkts.show()
