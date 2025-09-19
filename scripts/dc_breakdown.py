import csv
import sys

import argparse
from argparse import RawTextHelpFormatter

parser = argparse.ArgumentParser(description='''Break down a list of servers by data center

This script takes a CSV file with a list of servers from a DB2 query and generates a CSV
file that combines the servers by data center

Example:
python3 dc_breakdown.py output/not_in_vpc_account.csv
''', formatter_class=RawTextHelpFormatter)

parser.add_argument('servers', type=str, help='The path to the Servers.csv file.')

args = parser.parse_args()
serversPath = args.servers

servers = {}

# Get the label for the specified row.  The label is based on the hardware status if the row is in various liquidation
# states, spare, or missing parts or the processor description if it isn't.
def getLabel(row):
    return row['DATACENTER']

# Print out the CSV file with all the counts.
def printCounts():
    print('DATACENTER,count')
    for server in servers:
        print(server + ',' + str(servers[server]))

# Increment the count for this row and add a new row of this label isn't in the count yet.
def incrementServerCount(row):
    proc = getLabel(row)
    if proc not in servers:
        servers[proc] = 0

    servers[proc] = servers[proc] + 1

with open(serversPath, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    fieldnames = next(reader, None)
    for row in reader:
        incrementServerCount(row)

#print(servers)
printCounts()
