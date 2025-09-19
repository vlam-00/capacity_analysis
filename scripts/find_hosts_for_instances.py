import sys
import csv
import argparse
from argparse import RawTextHelpFormatter
from argparse import BooleanOptionalAction

import capacity_utils
from capacity_utils import loadInstances

parser = argparse.ArgumentParser(description='''Finds the hosts for a given list of instances

Examples:
python3 scripts/find_hosts_for_instances.py output/Instances-20241008.csv inputs/instances.txt

''', formatter_class=RawTextHelpFormatter)

parser.add_argument('instances', type=str, help='The path to the Instances.csv file.')
parser.add_argument('instancesList', type=str, help='The path to the file containing the instances to look for')

args = parser.parse_args()
instancesPath = args.instances
instancesListPath = args.instancesList

def readInstances(path):
    rows = loadInstances(path)

    instances = {}

    for row in rows:
        instances[row['name']] = row

    return instances

def readLines(path):
    with open(path) as file:
        lines = [line.rstrip() for line in file]
        return lines

def findHosts():
    instancesToFind = readLines(instancesListPath)
    instances = readInstances(instancesPath)

    for instance in instancesToFind:
        if instance in instances:
            host = instances[instance]['hostId']
            print(f'{instance} - {host}')
        else:
            print(instance + ' - Not found')

findHosts()
