import csv
import sys

import argparse
from argparse import RawTextHelpFormatter
from argparse import BooleanOptionalAction

parser = argparse.ArgumentParser(description='''Find all available hosts with a given profile type

Examples:
python3 find_available_host.py Hosts-20240719.csv gx2-a100

python3 find_available_host.py Hosts-20240719.csv gx3d-h100 -exact

''', formatter_class=RawTextHelpFormatter)

parser.add_argument('hosts', type=str, help='The path to the Hosts.csv file.')
parser.add_argument('profile', type=str, help='The profile to look for.')
parser.add_argument('-tainted', action=argparse.BooleanOptionalAction, default=False, help='Set this flag if you want to find tainted hosts')
parser.add_argument('-exact', action=argparse.BooleanOptionalAction, default=False, help='Set this flag if you want to match the profile exactly')


args = parser.parse_args()
hostsPath = args.hosts
profile = args.profile
tainted = args.tainted
exact = args.exact

def matchProfile(profile, row):
    if exact:
#        print('profileClass: ' + row['profileClass'])
        return profile == row['profileClass']
    else:
        return profile in row['profileClass']

with open(hostsPath, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    fieldnames = next(reader, None)
    count = 0
    for row in reader:
        if matchProfile(profile, row):
            if row['tainted'] == str(tainted) and int(row['instanceCount']) == 0 and (row['powerState'] == 'powered-on' or row['powerState'] == 'unknown') and row['status'] == 'Normal':
                print(row['name'])
                count = count + 1
    print('Available host count: ' + str(count))


