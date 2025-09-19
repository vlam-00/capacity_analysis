import os
import sys
import csv
import argparse
from argparse import RawTextHelpFormatter
from argparse import BooleanOptionalAction

parser = argparse.ArgumentParser(description='''Finds the instances list of instances running on a list of hosts

Examples:
python3 scripts/find_instances_for_hosts.py output/Instances-20241008.csv inputs/hosts.txt

''', formatter_class=RawTextHelpFormatter)

parser.add_argument('instances', type=str, help='The path to the Instances.csv file.')
parser.add_argument('hosts', type=str, help='The path to the file containing the hosts to look for')

args = parser.parse_args()
instancesPath = args.instances
hostsPath = args.hosts

def readInstances(path):
    if os.path.isfile(path):
        try:
            with open(path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                fieldnames = next(reader, None)
                hosts = {}
                for row in reader:
                    if row['hostId'] not in hosts:
                        hosts[row['hostId']] = []

                    hosts[row['hostId']].append(row['name'])
                return hosts
        except KeyError as err:
            print('Unable to read the instances file.  Make sure you provided the correct file')
            print(f'Unable to find key {err}')
            quit(-1)
        except Exception as ex:
            print('Unable to read the instances file.  Make sure you provided the correct file')
            print(ex)
            quit(-1)
    else:
        fullPath = os.path.abspath(instancesPath)
        print(f"The file {fullPath} can't be found")
        quit(-1)

def readLines(path):
    if os.path.isfile(path):
        with open(path) as file:
            lines = [line.rstrip() for line in file]
            return lines
    else:
        fullPath = os.path.abspath(path)
        print(f"The hosts file {fullPath} can't be found")
        quit(-1)

def findHosts():
    hostsToFind = readLines(hostsPath)
    hosts = readInstances(instancesPath)

    for host in hostsToFind:
        if host in hosts:
            instances = hosts[host]
            if len(instances) == 1:
                print(host + ' - ' + hosts[host][0])
            else:
                print(host + ':')
                for instance in instances:
                    print('    ' + instance)
        else:
            print(host + ' - No instances found')

findHosts()
