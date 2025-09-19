import csv
import sys

import argparse
from argparse import RawTextHelpFormatter
from argparse import BooleanOptionalAction

parser = argparse.ArgumentParser(description='''This script finds drives with a missing serial map based on a
very specific search result from IPOps.  This is not a generally useful script.

Examples:
python3 find_missing_nvme.py Hosts-20240719.csv gx2-a100

python3 find_available_host.py Hosts-20240719.csv gx3d-h100 -exact

''', formatter_class=RawTextHelpFormatter)

parser.add_argument('hosts', type=str, help='The path to the Hosts.csv file.')

args = parser.parse_args()
hostsPath = args.hosts

def readHosts():
    with open('inputs/hosts.txt') as file:
        lines = [line.rstrip() for line in file]
        return lines

def readLines():
    with open(hostsPath) as file:
        lines = [line.rstrip() for line in file]
        return lines

def printHost(host, hosts):
    if host in hosts:
        print(host)

def findMissing():
    lines = readLines()
    hosts = readHosts()
    l = len(lines)

    for i, line in enumerate(lines):
        # [38;2;38;150;150;40mHost: wdc3-qz1-sr2-rk166-s14 (192.168.166.29)[0m
        if 'Host:' in line:
            nextLine = lines[i + 1]

            if str(nextLine) != '/var/lib/ssd-nvme/serialmap':
                host = line[27:49]
                printHost(host, hosts)

findMissing()
