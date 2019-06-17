#!/usr/bin/python

import csv, json, re, logging

logging.basicConfig(filename="savings.log",
                    format="[%(asctime)s] [%(levelname)-7s] %(message)s",
                    level=logging.DEBUG)

in_buckets = 'buckets.json'
in_file = 'cc-export-2018-12-26.csv'
in_data = False
headers = []
interesting = ['Date', 'Payee', 'Category', 'Tags', 'Amount']
useful = []

with open(in_buckets) as json_data:
    buckets = json.load(json_data) 

with open(in_file) as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if in_data:
            head_pos = 0
            goodies = {}
            for header in headers:
                if header in interesting:
                    goodies[header] = row[head_pos]
                head_pos += 1
            if goodies and goodies["Date"]:
                useful.append(goodies)

        if 'Date' in row:
            in_data = True
            headers = row
        if 'Total Inflows:' in row:
            in_data = False 

logging.info("Done parsing '%s'. %s records total.", in_file, str(len(useful)))

newlist = sorted(useful, key=lambda k: k['Category'])
for good in newlist:
    if "Savings" in good["Tags"]:
        print good
