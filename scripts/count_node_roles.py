from datetime import timezone
import datetime
import argparse
from argparse import RawTextHelpFormatter
from os import walk
import os
import yaml
import csv
import pprint

# This is a small script that iterates over all of the allocation YAML files in the platform-inventory
# repository and generates a Markdown table with all of the node roles and their counts
parser = argparse.ArgumentParser(description='''Read data from the platform-inventory YAML files and generate a Markdown
table showing all of the node roles and counts.

You must provide a path to a local copy of the platform-inventory repository and
the location for the file to output.

Example:
python3 count_node_roles.py /Users/zackgrossbart/work/platform-inventory role_desc.csv
''', formatter_class=RawTextHelpFormatter)

parser.add_argument('pi_path', type=str, help='The path to the platform-inventory repository')
parser.add_argument('desc_path', type=str, help='The path to CSV file containing the role descriptions')
args = parser.parse_args()
piPath = args.pi_path
descPath = args.desc_path
nodes = {}
descs = {}

# Joins a folder with two sub folders into a path using the correct separator for the current OS
def joinPath(folder, subFolder, subFolder2):
    return os.path.join(os.path.join(folder, subFolder), subFolder2)

# Read in the allocations
def readAllocations():
    allocations = []
    path = joinPath(piPath, 'region', 'allocations')
    for (dirpath, dirnames, filenames) in walk(path):
        allocations.extend(filenames)
        break

    for alloc in allocations:
        if alloc.endswith('.yaml'):
            print('Reading file: ' + alloc)
            with open(os.path.join(path, alloc)) as f:
                data = yaml.safe_load(f)
                for host in data:
                    #print('Found host: ' + host['hostname'])
                    nodes[host['hostname']] = host

def readDescs():
    with open(descPath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = next(reader, None)
        for row in reader:
            descs[row['name']] = row['note']

def generateCounts():
    counts = {}
    for node in nodes:
        role = nodes[node]['role']
#        print('state: ' + state)
        if role not in counts:
            counts[role] = 0

        counts[role] = counts[role] + 1

    return sorted(counts.items(), key=lambda item: item[0], reverse=False)

def formatNum(num):
    return f"{num:,d}"

def generateTable(counts):
    print('| Node Role | Count | Notes |')
    print('|---|---|---|')
    total = 0

    for count in counts:
        desc = ''
        total += count[1]
        if count[0] in descs:
            desc = descs[count[0]]

        print('| `' + count[0] + '` | ' + formatNum(count[1]) + ' | ' + desc + ' | ')

    print('| **Total** | **' + formatNum(total) + '** | ' + desc + ' | ')

    print('Role count: ' + str(len(counts)))


readDescs()
readAllocations()
generateTable(generateCounts())