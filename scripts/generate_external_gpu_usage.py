import csv
import sys
import pprint

import argparse
from argparse import RawTextHelpFormatter

import capacity_utils
from capacity_utils import getNumberOfGPUsForProfile
from capacity_utils import isPoweredOn
from capacity_utils import isInstanceStarted
from capacity_utils import INTERNAL_DIRECT
from capacity_utils import EXTERNAL_DIRECT
from capacity_utils import INTERNAL_ROKS
from capacity_utils import EXTERNAL_ROKS
from capacity_utils import AVAILABLE_GPUS
from capacity_utils import TOTAL_GPUS
from capacity_utils import REGION
from capacity_utils import DC
from capacity_utils import PROFILE_TYPE

parser = argparse.ArgumentParser(description='''Generate a usage report that shows internal vs. external GPU usage globally

Example:
python3 generate_external_gpu_usage.py Instances-20240719.csv Hosts-20241010.csv out.csv
''', formatter_class=RawTextHelpFormatter)

parser.add_argument('instances', type=str, help='The path to the Instances.csv file.')
parser.add_argument('hosts', type=str, help='The path to the Hosts.csv file.')
parser.add_argument('out', type=str, help='The path to generate the usage CSV file')
parser.add_argument('-byZone', action=argparse.BooleanOptionalAction, default=False, help='Set this flag if you want show the data by zone instead of region')
args = parser.parse_args()
instancesPath = args.instances
hostsPath = args.hosts
usagePath = args.out

regionString = 'region'
regionTitle = REGION

if args.byZone:
    regionString = 'datacenter'
    regionTitle = DC

nodes = {}
nodesbyRegion = {}
availableGPUCounts = {}

# This array is a list of all the profiles that we consider GPU profiles
gpuProfiles = [
    'gx2-80x1280x8a100', 'gx3d-48x240x2a100p',
    # Put these profiles back if you want to see the Vela cluster
    # 'gx2-80x1280x8a100-cl-rdma', 'gx2-80x1280x8a100-il-rdma'
    'gx3-48x240x2l40s', 'gx3-24x120x1l40s',
    'gx3-64x320x4l4', 'gx3-32x160x2l4', 'gx3-16x80x1l4',
    'gx3d-160x1792x8h100', 'h100-sriov',
    'gx3d-160x1792x8h200', 'h200-sriov',
    'gx3d-160x1792x8gaudi3-internal', 'gx3d-160x1792x8gaudi3',
    'gx3d-208x1792x8mi300x-internal', 'gx3d-208x1792x8mi300x',
    # Put this profile back if you want to see the Vela2 cluster
    # 'gx3d-160x1792x8h100-research',
    'gx2-16x128x2v100', 'gx2-32x256x2v100']

gpuClasses = [
    'gx3-l40s', 'gx3-l4',
    'gx2-a100-il-rdma-ext', 'gx2-a100-il-rdma', 'gx2-a100-cl-rdma', 'gx2-a100-ext',
    'gx3d-a100', 'gx3d-h100', 'gx3d-h100-research', 'gx3d-h200', 'gx3d-h200-research', 'gx3d-gaudi3', 'gx3d-mi300x'
]

# Take the raw profile string like gx2-80x1280x8a100 and return a pretty string like a100.
# This function will combine multiple types of profiles into a single string like combining the inspur and SMC
# a100 profiles into a single profile called a100
def getProfileString(profile):
    if profile == 'gx2-80x1280x8a100':
        return '8xa100'
    elif profile == 'gx2-80x1280x8a100-cl-rdma' or profile == 'gx2-80x1280x8a100-il-rdma':
        return '8xa100-research'
    elif profile == 'gx3d-48x240x2a100p':
        return '2xa100'
    elif profile == 'gx3-24x120x1l40s' or profile == 'gx3-48x240x2l40s':
        return 'l40s'
    elif profile == 'gx3d-152x1536x8h100-sriov':
        return 'h100-sriov'
    elif profile == 'gx3d-160x1792x8h100':
        return 'h100'
    elif profile == 'gx3d-160x1792x8h100-research':
        return 'h100-research'
    elif profile == 'gx3d-152x1536x8h200-sriov':
        return 'h200-sriov'
    elif profile == 'gx3d-160x1792x8h200':
        return 'h200'
    elif profile == 'gx3d-160x1792x8h200-research':
        return 'h200-research'
    elif profile == 'gx3d-160x1792x8gaudi3-internal' or profile == 'gx3d-160x1792x8gaudi3':
        return 'Gaudi 3'
    elif profile == 'gx3d-208x1792x8mi300x-internal' or profile == 'gx3d-208x1792x8mi300x':
        return 'MI300X'
    elif profile == 'gx3-32x160x2l4' or profile == 'gx3-16x80x1l4' or profile == 'gx3-64x320x4l4':
        return 'l4'
    elif profile == 'gx2-16x128x2v100' or profile == 'gx2-32x256x2v100':
        return 'v100'
    else:
        return profile

# Get the pretty label for each profile class.
def getProfileClassString(profileClass):
    if profileClass == 'gx3-l40s':
        return 'l40s'
    elif profileClass == 'gx3-l4':
        return 'l4'
    elif profileClass == 'gx2-a100-il-rdma-ext' or profileClass == 'gx2-a100-ext':
        return '8xa100'
    elif profileClass == 'gx2-a100-il-rdma' or profileClass == 'gx2-a100-cl-rdma':
        return '8xa100-research'
    elif profileClass == 'gx3d-a100':
        return '2xa100'
    elif profileClass == 'gx3d-h100':
        return 'h100'
    elif profileClass == 'gx3d-h100-research':
        return 'h100-research'
    elif profileClass == 'gx3d-h200':
        return 'h200'
    elif profileClass == 'gx3d-h200-research':
        return 'h200-research'
    elif profileClass == 'gx3d-gaudi3':
        return 'Gaudi 3'
    elif profileClass == 'gx3d-mi300x':
        return 'MI300X'
    elif profileClass == 'gx2':
        return 'v100'
    else:
        return profileClass

# This is a utility function with the business logic of knowing how many GPUs there are for each profile class
def getNumberOfGPUsForClass(profileClass):
    if profileClass == 'gx3-l40s':
        return 2
    elif profileClass == 'gx3-l4':
        return 4
    elif profileClass == 'gx2-a100-il-rdma-ext' or profileClass == 'gx2-a100-ext':
        return 8
    elif profileClass == 'gx3d-a100':
        return 2
    elif profileClass == 'gx3d-h100':
        return 8
    elif profileClass == 'gx3d-h200':
        return 8
    elif profileClass == 'gx3d-h100-research':
        return 8
    elif profileClass == 'gx3d-h200-research':
        return 8
    elif profileClass == 'gx3d-gaudi3':
        return 8
    elif profileClass == 'gx3d-mi300x':
        return 8
    elif profileClass == 'gx2':
        return 2
    else:
        return -1

# We use a combination of the data center and profile name as the key in the dictionary object
# as a unique combination key to manage the counts per data center.  Right now we're only showing
# the region data, but I wanted to include this in case we needed it later.
def getNodeCat(row):
    return row['datacenter'] + '-' + row['profile']

# We use a combination of the region and profile name as the key in the dictionary object
# as a unique combination key to manage the counts.
def getNodeReg(row):
    return row[regionString] + '-' + getProfileString(row['profile'])

# Print out the totals of all profile usage. This isn't strictly need to get the GPU totals, but
# it's useful information and helps debugging.
def printTotals():
    print('| Region | Server Type | Internal | External |')
    print('|---|---|---|---|')
    for n in nodesbyRegion:
        node = nodesbyRegion[n]
        print('| `' + node[regionString] + '` | `' + getProfileString(node['profile']) + '` | ' + str(getNodeInternalCount(node)) + ' | ' + str(getNodeExternalCount(node)) + ' |')

# Get the internal node count or zero if it hasn't been set.
def getNodeInternalCount(node, direct=True):
    key = 'internal'

    if not direct:
        key = 'internal-roks'

    if key in node:
        return node[key]
    else:
        return 0

# Get the external node count or zero if it hasn't been set.
def getNodeExternalCount(node, direct=True):
    key = 'external'

    if not direct:
        key = 'external-roks'

    if key in node:
        return node[key]
    else:
        return 0



# Generate all of the output CSV file with the GPU profiles we care about.
def generateCSV():
    with open(usagePath, 'w', newline='') as file:
        writer = csv.writer(file)

        # Start by writing the headers
        field = [regionTitle, PROFILE_TYPE, INTERNAL_DIRECT, EXTERNAL_DIRECT, INTERNAL_ROKS, EXTERNAL_ROKS, AVAILABLE_GPUS, TOTAL_GPUS]
        writer.writerow(field)

        for node in sorted(nodesbyRegion.items(), key=lambda item: item[0], reverse=False):
            row = node[1]
            if row['profile'] in gpuProfiles:
                #total = getNodeInternalCount(row) + getNodeExternalCount(row) + getNodeInternalCount(row, False) + getNodeExternalCount(row, False) + getAvailableGPUs(row[regionString], getProfileString(row['profile']))
                total = getGpuTotalCount(row[regionString], getProfileString(row['profile']))
                available = total - (getNodeInternalCount(row) + getNodeExternalCount(row) + getNodeInternalCount(row, False) + getNodeExternalCount(row, False))
                if available < 0:
                    # This can happen if there are tainted servers with active VSIs
                    available = 0
                field = [row[regionString], getProfileString(row['profile']),
                        getNodeInternalCount(row), getNodeExternalCount(row),
                        getNodeInternalCount(row, False), getNodeExternalCount(row, False),
                        available, total]
                writer.writerow(field)

# Take the object, add the key if it isn't there, and increment the specified value by one
def incrementCount(obj, key, row, val):
    totalKey = val
    if key not in obj:
        obj[key] = row

    val = obj[key]
    if totalKey in val:
        val[totalKey] = val[totalKey] + getNumberOfGPUsForProfile(row['profile'])
    else:
        val[totalKey] = getNumberOfGPUsForProfile(row['profile'])

def getAvailableGPUs(region, profileClass):
    if profileClass not in availableGPUCounts[region]:
        # This can happen when there are many tainted, but in use hosts
        # in a specific region.
        return 0
    else:
        return availableGPUCounts[region][profileClass]

# Read in the hosts file and save only the GPU hosts we're interested in.  We also do special
# handling for v100 hosts
def readHosts():
    hostRows = []
    with open(hostsPath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = next(reader, None)
        count = 0
        for row in reader:
            if row['profileClass'] in gpuClasses:
                hostRows.append(row)
            elif row['profileClass'] == 'gx2' and int(row['nonTaintedTotalGPUs']) == 2:
                # This is a V100 which don't have a special profile class we can look for
                hostRows.append(row)
        return hostRows

# Increment the GPU count for this specific region and profile
def incrementGpuCount(region, profile, gpus):
    if region not in availableGPUCounts:
        availableGPUCounts[region] = {}

    if profile not in availableGPUCounts[region]:
        availableGPUCounts[region][profile] = 0

    availableGPUCounts[region][profile] = availableGPUCounts[region][profile] + gpus

def getGpuTotalCount(region, profile):
    if profile in availableGPUCounts[region]:
        return availableGPUCounts[region][profile]
    else:
        return 0

# Count the available GPUs by the type and region and increment the counts.
def countAvailableGPUsByType():
    hostRows = readHosts()
    for row in hostRows:
        profileClass = getProfileClassString(row['profileClass'])

        if isPoweredOn(row) and row['status'] == 'Normal' and row['tainted'] == 'False':
            # Then this is an untainted empty node
            gpus = getNumberOfGPUsForClass(row['profileClass'])
            #gpus = int(row['schedulerAvailableGPUs'])
            incrementGpuCount(row[regionString], profileClass, gpus)

# It's possible that a region has GPU servers available, but none of them are in use.
# In that case we want to show a row where we show that zero GPUs are in use and all
# GPUs are available.  To make that happen we need to go through all of the GPU profiles
# that we're interested in and generate a special row which we add manually to the
# nodesbyRegion array so we can have a row when we're generating the CSV.
#
# I wish I could figure out a more elegant way to manage this, but I couldn't find one
# since we're driving everything based on the instance and there are no instances in this
# case.  Hackito ergo sum.
def generateEmptyRows():
    profiles = gpuProfiles

    for region in availableGPUCounts:
        for profile in profiles:
            if getProfileString(profile) in availableGPUCounts[region] and availableGPUCounts[region][getProfileString(profile)] > 0:
                key = region + '-' + getProfileString(profile)

                if key not in nodesbyRegion:
                    row = {
                        'external-roks': 0,
                        'external': 0,
                        'internal-roks': 0,
                        'internal': 0,
                        regionString: region,
                        'profile': profile
                    }
                    nodesbyRegion[key] = row


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

# Read in the data
def readData():
    with open(instancesPath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = next(reader, None)
        for row in reader:
            if isInstanceStarted(row):
                #if getProfileString(row['profile']) == '2xa100':
                #    print('name: ' + row['name'])
                val = getInternalExternalVal(row)
                #if getProfileString(row['profile']) == 'h100':
                #    print('name: ' + row['datacenter'] + '-' + row['name'] + '-' + row['hostId'])

                #print('Found instance on host: ' + row['hostId'])
                #nodeCat = getNodeCat(row)
                nodeReg = getNodeReg(row)

                #incrementCount(nodes, nodeCat, row.copy(), val)
                incrementCount(nodesbyRegion, nodeReg, row, val)

readData()
countAvailableGPUsByType()
generateEmptyRows()
#pprint.pprint(availableGPUCounts)
#printTotals()
generateCSV()