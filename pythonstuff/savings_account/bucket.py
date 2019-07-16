#!/usr/bin/python

import csv, json, re, logging

logging.basicConfig(filename="savings.log",
                    format="[%(asctime)s] [%(levelname)-7s] %(message)s",
                    level=logging.DEBUG)

DEFAULT_BUCKET = {
                "total": 0.0,
                "order": 0,
                "weight": 0,
                "title": "",
                "tags": []
                }

class Bucket(object):
    def __init__(self, bucket=DEFAULT_BUCKET):
        self.total = bucket.get("total", DEFAULT_BUCKET['total'])
        self.order = bucket.get("order", DEFAULT_BUCKET['order'])
        self.weight = bucket.get("weight", DEFAULT_BUCKET['weight'])
        self.title = bucket.get("title", DEFAULT_BUCKET['title'])
        self.tags = bucket.get("tags", DEFAULT_BUCKET['tags'])

    def _string2float(self, st):
        money = str(st)                         # incase it is already a number

        money = money.strip()                   # remove any leading/trailing space
        money = money.strip("$")                # remove any leading '$'
        money = re.sub(r',', "", money)         # no commas
        money = re.sub(r'^-$', "0", money)      # a '-' translates to 0
        return float(money)

    @property
    def total(self):
        return self._total

    @total.setter
    def total(self, total):
        self._total = self._string2float(total) 

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


    def __str__(self):
        ret = ""

        ret += "Title:  " + self.title + "\n"
        ret += "Total:  " + str(self.total) + "\n"
        ret += "Weight: " + str(self.weight) + "\n"
        ret += "Order:  " + str(self.order) + "\n"
        ret += "Tags:   " + str(self.tags) + "\n"

        return ret

    def __add__(self, another_bucket):
        if ((self.title == another_bucket.title) or (another_bucket.title == "")):
            sum_total = self._total + another_bucket.total
            return Bucket(total=sum_total)
        else:
            return self

    def __iadd__(self, another_bucket):
        if ((self.title == another_bucket.title) or (another_bucket.title == "")):
            self.total += another_bucket.total
        return self

    def __eq__(self, another_bucket):
        return (
                (self.title == another_bucket.title) and
                (self.weight == another_bucket.weight) and
                (self.total == another_bucket.total)
            )

    def transact(self, xaction):
        self._total += xaction.amount
        return self

if __name__ == "__main__":
    bk = Bucket({"title":"Dan's Bucket", "total":"1,000,000"})
    print bk
