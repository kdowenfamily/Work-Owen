#!/usr/bin/python

import csv, json, re, logging
from bucket import Bucket

BUCKETS_FILE = "data/buckets.json"

logging.basicConfig(filename="savings.log",
                    format="[%(asctime)s] [%(levelname)-7s] %(message)s",
                    level=logging.DEBUG)

class Buckets(object):
    @classmethod
    def from_file(cls, file_path=""):
        # read the JSON file and make one bucket per bucket dict
        buckets = []

        logging.info("Parsing bucket-config file, '%s'.", file_path)
        with open(file_path) as json_data:
            buckets = json.load(json_data) 

        return cls(buckets)

    def __init__(self, buckets=[]):
        # read the JSON file and make one bucket per bucket dict
        self.titles2buckets = {}
        self.tags2buckets = {}
        self.ordered_titles = []
        self.total = 0
        self.contents = self.init_buckets(buckets)

    def init_buckets(self, buckets=[]):
        bkts = []
        for bucket in buckets:
            bkt = Bucket(bucket)
            bkts.append(bkt)

            self.titles2buckets[bkt.title] = bkt
            self.total += bkt.total
            for tag in bkt.tags:
                if tag in self.tags2buckets.keys():
                    logging.warning("Dupe tag: '%s' in config record '%s, %s'.", tag, 
                                    bkt.title, bkt.total)
                else:
                    self.tags2buckets[tag] = bkt

        for bucket in sorted(bkts, key=lambda k: k.order):
            self.ordered_titles.append(bucket.title)

        logging.info("Done parsing bucket-config file, %s buckets.", len(bkts))

        return bkts


    def find(self, title=""):
        return self.titles2buckets[title]

    def _print_titles(self):
        ret = ""

        for title in self.ordered_titles:
            ret += self.titles2buckets[title].title + ","

        return ret

    def __str__(self):
        ret = ""

        for title in self.ordered_titles:
            ret += str(self.titles2buckets[title].total) + ","

        return ret

    def __iadd__(self, other_buckets):
        for title in self.titles2buckets:
            my_bkt = self.titles2buckets(title)
            o_bkt = other_buckets.find(title)
            my_bkt += obkt
            self.total += obkt.total

    def __eq__(self, other_buckets):
        for title in self.ordered_titles:
            my_bkt = self.title2buckets[title]
            o_bkt = other_buckets.find(title)
            if not (my_bkt == o_bkt):
                return False

        return True 

if __name__ == "__main__":
    bks = Buckets.from_file(BUCKETS_FILE)
    print bks._print_titles()
    print bks
