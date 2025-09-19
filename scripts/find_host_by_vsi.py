import csv
import sys

import argparse
from argparse import RawTextHelpFormatter

parser = argparse.ArgumentParser(description='''Find the hostId for a given VSI by VSI name or ID

Example:
python3 find_host_by_vsi.py Instances-20240719.csv kube-ci5hbm6w0fljlek612ig-watsonxprod-workerp-00022614
''', formatter_class=RawTextHelpFormatter)

parser.add_argument('instances', type=str, help='The path to the Instances.csv file.')
parser.add_argument('instance', type=str, help='The VSI name or instance ID to look for.')
args = parser.parse_args()
instancesPath = args.instances
instance = args.instance


with open(instancesPath, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    fieldnames = next(reader, None)
    for row in reader:
        if row['instanceId'] == instance or row['name'] == instance:
            print(row['hostId'])
            sys.exit(0)
            
print('Unable to find instance: ' + instance)
sys.exit(-1)
        
        