#!/usr/bin/python

import csv, json, re, logging
from transaction import Transaction

logging.basicConfig(filename="savings.log",
                    format="[%(asctime)s] [%(levelname)-7s] %(message)s",
                    level=logging.DEBUG)

class Bucket(object):
    def __init__(self, total=0.0, order=0, weight=0, title="", tags=[]):
        self.total = total
        self.order = order
        self.weight = weight
        self.title = title
        self.tags = tags

    @property
    def total(self):
        return self._total

    @total.setter
    def total(self, total):
        money = str(total)                   # incase it is already a number

        money = money.strip()                # remove any leading/trailing space
        money = money.strip("$")             # remove any leading '$'
        money = re.sub(r',', "", money)      # no commas
        money = re.sub(r'^-$', "0", money)   # a '-' translates to 0
        money = float(money)

        self._total = money

    @property
    def order(self):
        return self._order

    @order.setter
    def order(self, order):
        self._order = int(order)               # incase it is a string

    @property
    def weight(self):
        return self._weight

    @weight.setter
    def weight(self, weight):
        self._weight = int(weight)             # incase it is a string

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._title = str(title)               # incase it is unicode

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, tags):
        if not isinstance(tags, list):
            tags = [tags]

        self._tags = []
        for tag in tags:
            if isinstance(tag, list):
                for tg in tag:
                    self._tags.append(str(tg)) # incase it is unicode
            else:
                self._tags.append(str(tag))    # incase it is unicode

    def __add__(self, another_bucket):
        if ((self.title == another_bucket.title) or (another_bucket.title == "")):
            self._total += another_bucket._total
            return self
        else:
            return None

    def transact(self, xaction):
        self._total += xaction.amount
        return self
