import csv
import sys

import argparse
from argparse import RawTextHelpFormatter

parser = argparse.ArgumentParser(description='''A specified field for a host in the hosts file

Example:
python3 find_host_field.py Hosts-20240719.csv wdc3-qz1-sr3-rk006-s30 kernelVersion
''', formatter_class=RawTextHelpFormatter)

parser.add_argument('hosts', type=str, help='The path to the Hosts.csv file.')
parser.add_argument('host', type=str, help='The host ID to look for.')
parser.add_argument('field', type=str, help='The field to return.')
args = parser.parse_args()
hostsPath = args.hosts
host = args.host
field = args.field


with open(hostsPath, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    fieldnames = next(reader, None)
    for row in reader:
        if row['name'] == host:
            print(row[field])
            sys.exit(0)
            
print('Unable to find host: ' + host)
sys.exit(-1)
        
        