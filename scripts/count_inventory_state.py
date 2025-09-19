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
# repository and generates a Markdown table with all of the inventory states and their counts
parser = argparse.ArgumentParser(description='''Read data from the platform-inventory YAML files and generate a Markdown
table showing all of the states and counts.

You must provide a path to a local copy of the platform-inventory repository and
the location for the file to output.

Example:
python3 count_inventory_state.py /Users/zackgrossbart/work/platform-inventory
''', formatter_class=RawTextHelpFormatter)

parser.add_argument('pi_path', type=str, help='The path to the platform-inventory repository')
args = parser.parse_args()
piPath = args.pi_path
nodes = {}

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

def generateCounts():
    counts = {}
    for node in nodes:
        state = nodes[node]['inventory_state']
#        print('state: ' + state)
        if state not in counts:
            counts[state] = 0

        counts[state] = counts[state] + 1
        
    return counts
         
def generateTable(counts):
    print('| State Name | State Count | Notes |')
    print('|---|---|---|')
    
    for count in counts:
        print('| `' + count + '` | ' + str(counts[count]) + ' | | ')
    

readAllocations()
generateTable(generateCounts())