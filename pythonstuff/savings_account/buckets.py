#!/usr/bin/python

import csv, json, re, logging
from bucket import Bucket

BUCKETS_FILE = "data/buckets.json"

logging.basicConfig(filename="savings.log",
                    format="[%(asctime)s] [%(levelname)-7s] %(message)s",
                    level=logging.DEBUG)

class Buckets(object):
    def __init__(self, json=BUCKETS_FILE):
        # read the JSON file and make one bucket per bucket dict
        self.titles2buckets = {}
        self.tags2buckets = {}
        self.ordered_titles = []
        self.contents = self.init_buckets(json)

    def init_buckets(self, file=""):
        buckets = []

        logging.info("Parsing bucket-config file, '%s'.", file)
        with open(file) as json_data:
            buckets = json.load(json_data) 

        for bucket in buckets:
            bkt = Bucket(title=bucket['title'], order=bucket['order'], weight=bucket['weight'], tags=bucket['tags'])
            self.titles2buckets[bucket['title']] = bkt
            for tag in bkt.tags:
                if tag in self.tags2buckets.keys():
                    logging.warning("Dupe tag: '%s' in config record '%s, %s'.", tag, 
                                    bkt.title, bkt.weight)
                else:
                    self.tags2buckets[tag] = bkt

        for bucket in sorted(buckets, key=lambda k: k['order']):
            self.ordered_titles.append(bucket['title'])

        logging.info("Done parsing bucket-config file, %s buckets.",
            len(self.titles2buckets.keys()))

        return buckets


    def find(self, title=""):
        return self.titles2buckets(title)

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

    def __eq__(self, other_buckets):
        for title in self.ordered_titles:
            my_bkt = self.title2buckets[title]
            o_bkt = other_buckets.find(title)
            if not (my_bkt == o_bkt):
                return False

        return True 

if __name__ == "__main__":
    bks = Buckets()
    print bks._print_titles()
    print bks
