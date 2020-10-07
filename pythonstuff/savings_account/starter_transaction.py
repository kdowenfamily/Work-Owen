#!/usr/bin/python

import logging, os
from copy import deepcopy
from transaction import Transaction
from transaction_template import Transaction_Template
from buckets import Buckets

logging.basicConfig(filename="/var/log/savings/savings.log",
        format="[%(asctime)s] [%(levelname)-7s] [%(filename)s:%(lineno)d] %(message)s",
        level=logging.DEBUG)
log = logging.getLogger(__name__)

# An initial transaction, based on a start date and a total amount in the savings account.
# Average all the current paychecks, and give each bucket the percentage allotted by those paychecks.
class Starter_Transaction(Transaction):
    def __init__(self, source_account="", start_date="1/1/2015", amount=0.00, paychks=Transaction.masterPaychecks):
        # a dictionary to describe this transaction
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
        super(Starter_Transaction, self).__init__(source_account=source_account, xact_data=my_data, buckets=paychks[0].buckets)
        blists = self._bucket_lists_with_per_year(paychks)
        self._replace_my_bucket_list(blists)
        self._divide_total_amongst_buckets(amount)
        self.reconcile_total()              # reconcile the buckets with the initial total

    # Take a random number of paycheck Transactions.
    # Return a new list of Bucket_Lists, copied from those paychecks, and all bucket amounts are per-year.
    def _bucket_lists_with_per_year(self, paychecks):
        blists = []
        for paychk in paychecks:
            bkts = deepcopy(paychk.buckets) # make a copy of the paycheck's bucket list
            for bkt in bkts.contents:
                bkt.total *= paychk.per_year
            blists.append(bkts)
        return blists

    # Replace this transactions bucket list with a union of the given bucket lists
    def _replace_my_bucket_list(self, blists):
        self.buckets = self.buckets.dupe()  # empty out our list with an empty dupe
        for bl in blists:
            self.buckets += bl              # creates a union of the 2 bucket lists

    # Calculate the piece of the total amount that belongs in each bucket
    def _divide_total_amongst_buckets(self, total):
        list_total = self.buckets.total     # this is a yearly total, from the sum of all the year's paychecks
        for bkt in self.buckets.contents:
            bkt.weight = bkt.total.as_float() / list_total.as_float()   # store the percentage
            bkt.total = round(total.as_float() * bkt.weight)           # derive the *real* total from the amount given


if __name__ == "__main__":
    from usd import USD
    paycheck_path = Transaction_Template.TEMPLATE_DIR + "/danCovid.json"
    paycheck_templs = [Transaction_Template(paycheck_path)]
    tr1 = Starter_Transaction(source_account="checking", start_date="11/12/2001", amount=USD(1000.00), paychks=paycheck_templs)
    print "\n\nPaycheck used:"
    print paycheck_path
    print "\nStart Transaction:"
    print tr1.show()
    print "\nTransaction Breakdown (details):\n"
    print tr1.buckets.show()
