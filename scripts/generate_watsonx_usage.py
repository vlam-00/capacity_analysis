import csv
import sys

import argparse
from argparse import RawTextHelpFormatter

import cu_accounts
import capacity_utils
from capacity_utils import getGPUProfiles
from capacity_utils import getGPUProfileString
from capacity_utils import loadInstances
from capacity_utils import getNumberOfGPUsForProfile
from capacity_utils import TOTAL_GPUS
from capacity_utils import TOTAL_SERVERS
from capacity_utils import SERVER_TYPE
from capacity_utils import REGION

parser = argparse.ArgumentParser(description='''Generate the usage report for Watsonx GPU usage

Example:
python3 generate_watsonx_usage.py Instances-20240719.csv out.csv
''', formatter_class=RawTextHelpFormatter)

parser.add_argument('instances', type=str, help='The path to the Instances.csv file.')
parser.add_argument('out', type=str, help='The path to generate the usage CSV file')
parser.add_argument('accountIDs', type=str, nargs='?', help='An optional list of alternative account IDs to use.')
args = parser.parse_args()
instancesPath = args.instances
usagePath = args.out

watsonxAccounts = cu_accounts.watsonxAIAccounts

if args.accountIDs:
    watsonxAccounts = args.accountIDs.split(',')



nodes = {}
nodesbyRegion = {}

# We use a combination of the data center and profile name as the key in the dictionary object
# as a unique combination key to manage the counts per data center.  Right now we're only showing
# the region data, but I wanted to include this in case we needed it later.
def getNodeCat(row):
    return row['datacenter'] + '-' + getGPUProfileString(row['profile'])

# We use a combination of the region and profile name as the key in the dictionary object
# as a unique combination key to manage the counts.
def getNodeReg(row):
    return row['region'] + '-' + getGPUProfileString(row['profile'])

# Print out the totals of all profile usage. This isn't strictly need to get the GPU totals, but
# it's useful information and helps debugging.
def printTotals():
    print('Totals:')
    for node in nodesbyRegion:
        print(node + ': ' + str(nodesbyRegion[node]['total']))

def getGPUCount(row):
    return row['total'] * getNumberOfGPUsForProfile(row['profile'])

# Generate all of the output CSV file with the GPU profiles we care about.
def generateCSV():
    with open(usagePath, 'w', newline='') as file:
        writer = csv.writer(file)

        # Start by writing the headers
        field = [REGION, SERVER_TYPE, TOTAL_SERVERS, TOTAL_GPUS]
        writer.writerow(field)

        for node in sorted(nodesbyRegion.items(), key=lambda item: item[0], reverse=False):
            row = nodesbyRegion[node[0]]
            if row['profile'] in getGPUProfiles():
                field = [row['region'], getGPUProfileString(row['profile']), row['total'], getGPUCount(row)]
                writer.writerow(field)

def incrementCount(obj, key, row):
    totalKey = 'total'
    if key not in obj:
        obj[key] = row

    val = obj[key]
    if totalKey in val:
        val[totalKey] = val[totalKey] + 1
    else:
        val[totalKey] = 1


rows = loadInstances(instancesPath)
for row in rows:
    if (row['customerAccountId'] in watsonxAccounts or row['accountId'] in watsonxAccounts):
#        print('Found instance on host: ' + row['hostId'])
        nodeCat = getNodeCat(row)
        nodeReg = getNodeReg(row)

        incrementCount(nodes, nodeCat, row.copy())
        incrementCount(nodesbyRegion, nodeReg, row.copy())

#printTotals()
generateCSV()