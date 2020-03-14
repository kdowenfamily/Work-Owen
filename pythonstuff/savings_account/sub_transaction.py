#!/usr/bin/python

import logging
from datetime import timedelta
from transaction import Transaction 

logging.basicConfig(filename="savings.log",
        format="[%(asctime)s] [%(levelname)-7s] [%(filename)s:%(lineno)d] %(message)s",
        level=logging.DEBUG)
log = logging.getLogger(__name__)

# Represents one transfer, deposit, or payment.  This corresponds to 
# one line in a Credit-Card or Savings-Account report.
class SubTransaction(Transaction):
    def __init__(self, source_account="", xact_data={}, parent=None):
        log.info("Creating sub-transaction for %s." % source_account)
        super(SubTransaction, self).__init__(source_account, xact_data)
        self.parent = parent
        log.info("Done setting up sub-transaction: %s, %s (from %s to %s)." 
                % (self.date_time, self.init_total, self.payer, self.payee) )

    # make a list of the strings we need to print out, as a sub-transaction
    def list_out(self):
        log.debug("Listing sub-transaction for %s." % self.title)
        # make temporary alterations
        subtitle = self.title
        subdate = self.date_time
        self.title = "- %s (%s)" % (subtitle, subdate.strftime("%a, %m/%d/%y"))
        # Measure the date in 100*years + day of year, call that "seconds", and add them to the date.
        yr = subdate.year
        day = subdate.timetuple().tm_yday
        plus_secs = (100 * yr) + day
        self.date_time = self.parent.date_time + timedelta(seconds=plus_secs)
        ret = [str(self.date_time), self.description, "", str(self.total)] + self.buckets.list_out()

        # undo the alterations, in case we need to do this again
        self.title = subtitle
        self.date_time = subdate

        return [ret]


if __name__ == "__main__":
    sample = {"Date": "11/12/1965", "Amount": 250, "Payee": "savings"}
    tr1 = Transaction(source_account="checking", xact_data=sample)
    print tr1.titles()
    print tr1.show()

    sample = {"Date": "9/4/1965", "Amount": 610, "Payee": "savings"}
    tr2 = Transaction(source_account="checking", xact_data=sample)
    print tr2.titles()
    print tr2.show()

    sample = {"Date": "7/23/19", "Amount": 2000, "Payee": "savings"}
    tr3 = Transaction(source_account="checking", xact_data=sample)
    print tr3.titles()
    print tr3.show()
