#!/usr/bin/python

import re
from copy import deepcopy
from transaction import Transaction
from teller import Teller
from usd import USD
from constants import log

# Represents a bank manager, to ask the user questions and alter transactions
# as needed.
class Manager(Teller):
    def __init__(self, name="Lindsey"):
        log.info("Creating manager, %s." % name)
        super(Manager, self).__init__(name = name)
        log.info("%s is good.  Promoting to manager." % name)

    # bring the user into the vault to trade money between buckets
    def play_in_vault(self, buckets=None, date='1/1/65'):
        print "My name is %s.  Welcome to the vault.  How can I help you?" % self.name
        self.transaction = Transaction("Savings", {'Date':date,'Memo/Notes':'Play in vault'})
        t = self.transaction
        bkts = deepcopy(buckets)
        t.buckets += bkts.dupe()
        quit = False
        while not quit:
            print "\nBuckets:\n"
            print bkts.show()
            raw_answer = raw_input("Enter an amount, a source bucket and a destination bucket ('q' to quit):  ")

            # split up the answer
            raw_answer.strip()
            user_words = raw_answer.split()
            if not user_words:
                print self._help_str()
                continue

            # nibble off and assess the first word
            amt = user_words.pop(0)
            if re.search(r'^-?\d+(\.\d+)?$', amt):
                amt = USD(amt)
            elif re.search(r'^q$', amt, re.IGNORECASE):
                quit = True
                continue
            else:
                print "Bad amount for bucket %s; expected 'a' or dollar amount, got '%s'" % (bkt.title, amt)
                continue

            # nibble off bucket numbers and exchange
            bkt1_num = int(user_words.pop(0))
            bkt1 = bkts.find(bkt1_num)
            bkt1.total -= amt
            bkt1a = t.buckets.find(bkt1_num)
            bkt1a.total -= amt
            bkt2_num = int(user_words.pop(0))
            bkt2 = bkts.find(bkt2_num)
            bkt2.total += amt
            bkt2a = t.buckets.find(bkt2_num)
            bkt2a.total += amt

            # record any comment
            if user_words and len(user_words) > 1 and user_words[0] == '-c':
                user_words.pop(0)    # lose the -c
                t.title += ": " + " ".join(user_words) + " (" + str(amt) + ")"

        return self.transaction

    def __str__(self):
        return "Hello, my name is %s.  I am the manager here.  How can I help you?" % self.name


if __name__ == "__main__":
    daria = Manager("Daria")
    print daria

    sample = {"Date": "11/12/1965", "Amount": 1950, "Payee": "savings"}
    xact1 = daria.process_transaction(source_account="savings", xact_data=sample)
    sample = {"Date": "9/4/1965", "Amount": 2345, "Payee": "savings"}
    xact2 = daria.process_transaction(source_account="savings", xact_data=sample)
    xact1.buckets += xact2.buckets
    daria.play_in_vault(buckets = xact1.buckets, date='5/6/95')
