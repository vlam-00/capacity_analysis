import csv
import sys

import argparse
from argparse import RawTextHelpFormatter

parser = argparse.ArgumentParser(description='''Find a specified field for a host based in the instance ID

Example:
python3 find_host_field_by_instance.py Instances-20240719.csv Hosts-20240719.csv kube-ci5hbm6w0fljlek612ig-watsonxprod-workerp-00022614 kernelVersion
''', formatter_class=RawTextHelpFormatter)

parser.add_argument('instances', type=str, help='The path to the Instances.csv file.')
parser.add_argument('hosts', type=str, help='The path to the Hosts.csv file.')
parser.add_argument('instance', type=str, help='The VSI name or instance ID to look for.')
parser.add_argument('field', type=str, help='The field to return.')
args = parser.parse_args()
hostsPath = args.hosts
instancesPath = args.instances
instance = args.instance
field = args.field

def findHost(hostName):
    with open(hostsPath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = next(reader, None)
        for row in reader:
            if row['name'] == hostName:
                print(instance + ': ' + hostName + ': ' + row[field])
                sys.exit(0)

with open(instancesPath, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    fieldnames = next(reader, None)
    for row in reader:
        if row['instanceId'] == instance or row['name'] == instance:
            findHost(row['hostId'])
            
            

            
print('Unable to find host: ' + host)
sys.exit(-1)
        
        