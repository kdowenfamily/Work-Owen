#!/usr/bin/python

import csv, json, re, logging

logging.basicConfig(filename="savings.log",
                    format="[%(asctime)s] [%(levelname)-7s] %(message)s",
                    level=logging.DEBUG)

in_buckets = 'data/buckets.json'
#in_file = 'data/private/cc-export-2018-12-26.csv'
in_file = 'data/private/savings.csv'
in_data = False
headers = []
interesting = ['Date', 'Payee', 'Category', 'Tags', 'Amount']
boring = ['', 'Scheduled', 'Split']
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
                if (not (header in boring)) and (len(row) > head_pos):
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

newlist = sorted(useful, key=lambda k: k['Date'])
for good in newlist:
    if "Tags" in good:
        if "Savings" in good["Tags"]:
            print good
    else:
        print good
