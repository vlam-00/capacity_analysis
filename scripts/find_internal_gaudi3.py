import csv
import sys
import pprint

import argparse
from argparse import RawTextHelpFormatter
from string import Template

import capacity_utils
from capacity_utils import getNumberOfGPUsForProfile
from capacity_utils import isPoweredOn
from capacity_utils import getInstancesFile

parser = argparse.ArgumentParser(description='''Find all VSIs that are using the gx3d-160x1792x8gaudi3 profile and are internal accounts

Example:
python3 find_internal_gaudi3.py Instances-20240719.csv

You can also pass in a set of profiles to look for like this:
find_internal_gaudi3.py gx3d-208x1792x8mi300x,gx3d-160x1792x8gaudi3
''', formatter_class=RawTextHelpFormatter)

parser.add_argument('instances', action=argparse.BooleanOptionalAction, default=None, type=str, help='The path to the Instances.csv file.')
parser.add_argument('profile', type=str, nargs='?', help='An optional comma separated list of alternate profiles to look for.')
parser.add_argument('-showAll', action=argparse.BooleanOptionalAction, default=False, help='Set this flag if you want to see all VSIs that match the profile')

args = parser.parse_args()
profiles = args.profile
showAll = args.showAll

if profiles is None:
    profiles = 'gx3d-160x1792x8gaudi3'

profiles = profiles.split(',')

def getInternalExternalVal(row):
    if row['customerAccountId'] != '-':
        # That means this instance was provisioned through IKS/ROKs
        if row['customerAccountInternal'] == 'true':
            return 'internal-roks'
        else:
            return 'external-roks'

    if row['internalAccount'] == 'False':
        return 'external'
    else:
        return 'internal'

def isInternal(row):
    if showAll:
        return True
    else:
        val = getInternalExternalVal(row)
        return val == 'internal' or val == 'internal-roks'

def printIntro():
    if showAll:
        if len(profiles) == 1:
            print(f'\n\033[1mFinding all VSIs using the {", ".join(profiles)} profile\033[0m')
        else:
            print(f'\n\033[1mFinding all VSIs using the {", ".join(profiles)} profiles\033[0m')
    else:
        if len(profiles) == 1:
            print(f'\n\033[1mFinding all internal VSIs using the {", ".join(profiles)} profile\033[0m')
        else:
            print(f'\n\033[1mFinding all internal VSIs using the {", ".join(profiles)} profiles\033[0m')

# Get the account ID for the row.  For direct provision VSIs that's the accontId field, but
# when the VSI is provisioned through ROKS then we want to use the customerAccountId field
def getAccountID(row):
    val = getInternalExternalVal(row)
    if val == 'internal-roks' or val == 'external-roks':
        return row['customerAccountId']
    else:
        return row['accountId']

# Read in the data
def readData():
    instancesPath = args.instances

    if instancesPath is None:
        instancesPath = getInstancesFile()
    with open(instancesPath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = next(reader, None)

        printIntro()
        print(f'\n\033[1mHost Name\t\tAccount ID\t\t\t\tDirect\tProfile\t\t\tVSI Name\033[0m')
        for row in reader:
            if row['powerState'] == 'Running' and (row['riasState'] == 'Running' or row['riasState'] == 'Starting'):
                val = getInternalExternalVal(row)

                if row['profile'] in profiles and isInternal(row):
                    if val == 'internal' or val == 'external':
                        print(f"{row['hostId']}\t{getAccountID(row)}\tYes\t{row['profile']}\t{row['name']}")
                    else:
                        print(f"{row['hostId']}\t{getAccountID(row)}\tNo\t{row['profile']}\t{row['name']}")

readData()