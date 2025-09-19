import os
from os import walk
import sys
import csv
import yaml
import argparse
import json
from argparse import RawTextHelpFormatter
from argparse import BooleanOptionalAction

parser = argparse.ArgumentParser(description='''Generates a report of the hosts that will be impacted by the UPS maintenance

Examples:
python3 scripts/generate_zyphra_ups.py inputs/hosts.csv inputs/weeks.json

''', formatter_class=RawTextHelpFormatter)

parser.add_argument('hosts', type=str, help='The path to the CSV file containing the physical hosts and bare metal server names to look for')
parser.add_argument('weeks', type=str, help='The path to the JSON file containing the data about the weeks of maintenance')

args = parser.parse_args()
hostsPath = args.hosts
weeksPath = args.weeks

# Joins a folder with two sub folders into a path using the correct separator for the current OS
def joinPath(folder, subFolder, subFolder2, subFolder3):
    return os.path.join(os.path.join(os.path.join(folder, subFolder), subFolder2), subFolder3)

# Read all of the racks from platform-inventory and return a dict with the ID of each
# rack as the key and the information about the rack as the value.
def readRacks(piPath):
    rackFiles = []
    path = joinPath(piPath, 'region', 'allocations', 'rack')
    for (dirpath, dirnames, filenames) in walk(path):
        rackFiles.extend(filenames)
        break

    racks = {}
    for rackFile in rackFiles:
        if rackFile.endswith('.yaml'):
#            print('Reading file: ' + rackFile)
            with open(os.path.join(path, rackFile)) as f:
                data = yaml.safe_load(f)
                for rack in data:
                    #print('Found host: ' + host['hostname'])
                    racks[rack['id']] = rack

    return racks

# Read the CSV file containing the information about the hosts to look for.
def readLines(path):
    if os.path.isfile(path):
        with open(path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = next(reader, None)
            rows = []
            for row in reader:
                rows.append(row)

            return rows
#        with open(path) as file:
#            lines = [line.rstrip() for line in file]
#            return lines
    else:
        fullPath = os.path.abspath(path)
        print(f"The hosts file {fullPath} can't be found")
        quit(-1)

def getInstance(hosts, index):
    if index < len(hosts):
        return hosts[index]['instance']
    else:
        return ''

def getInstances(hosts):
    return f'{getInstance(hosts,0)},{getInstance(hosts,1)},{getInstance(hosts,2)}'

# Find the rack and week information for the hosts and print out the CSV with the final output
def findHosts():
    hosts = readLines(hostsPath)

    hostData = []

    weeks = {}
    with open(weeksPath) as f:
        weeks = json.load(f)

    racks = readRacks('/Users/zackgrossbart/work/platform-inventory')

    locs = {}

    for host in hosts:
        r = host['host'][:18]
        loc = racks[r]['location']
        w = []

        for week in weeks:
            if loc in weeks[week]:
                w.append(week)

        if loc not in locs:
            locs[loc] = {}
            locs[loc]['rack'] = r
            locs[loc]['weeks'] = w
            locs[loc]['hosts'] = []

        locs[loc]['hosts'].append(host)

    weekCounts = [
        0,
        0,
        0,
        0,
        0
    ]

    print('Rack,# of Zyphra Instances,Instance 1, Instance 2, Instance 3, First Week, Second Week')
    for loc in locs:
        l = locs[loc]

        print(f'{loc},{len(l["hosts"])},{getInstances(l["hosts"])},{l["weeks"][0]},{l["weeks"][1]}')

        weekCounts[int(l['weeks'][0]) - 1] += len(l["hosts"])
        weekCounts[int(l['weeks'][1]) - 1] += len(l["hosts"])

#    print(f'weekCounts: {weekCounts}')

findHosts()