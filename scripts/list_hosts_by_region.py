import os
import csv
import sys
import pprint
from string import Template

import argparse
from argparse import RawTextHelpFormatter
from argparse import BooleanOptionalAction

import capacity_utils
from capacity_utils import loadInstances
from capacity_utils import loadHosts
from capacity_utils import calcPercent
from capacity_utils import formatProfileClass

parser = argparse.ArgumentParser(description='''Find all hosts in a specific region by profile class

This script will find all hosts in a specific region for the specific class
and generate a report showing a summary of which hosts are tainted and
available as well as a list of all of the instances running on each host.

Examples:
python3 scripts/list_hosts_by_region.py Instances-20241017.csv Hosts-20241017.csv fra gx2-a100

python3 scripts/list_hosts_by_region.py Instances-20241017.csv Hosts-20241017.csv wdc gx2-a100-il-rdma-ext

python3 scripts/list_hosts_by_region.py Instances-20241017.csv Hosts-20241017.csv wdc gx3d-h100 -exact

You can also find hosts in a specific data center like this:

python3 scripts/list_hosts_by_region.py Instances-20241017.csv Hosts-20241017.csv fra04 gx2-a100

Note: You must use the data center identified of `fra04` in this case instead of the `fra2` location in the host.

You can also pass in a comma separate list of regions to combine multiple regions.  For example, to see all
h100 hosts in SAO and MAD you can do this:

python3 scripts/list_hosts_by_region.py Instances-20241017.csv Hosts-20241017.csv sao,mad gx3d-h100

''', formatter_class=RawTextHelpFormatter)

parser.add_argument('instances', type=str, help='The path to the Instances.csv file.')
parser.add_argument('hosts', type=str, help='The path to the Hosts.csv file.')
parser.add_argument('region', type=str, help='The region to look for.')
parser.add_argument('profile', type=str, help='The profile class to look for.')
parser.add_argument('-exact', action=argparse.BooleanOptionalAction, default=False, help='Set this flag if you want to match the profile exactly')


args = parser.parse_args()
hostsPath = args.hosts
instancesPath = args.instances
profile = args.profile
region = args.region.split(',')
exact = args.exact

instances = {}

# Add the instance in the current row to our list of instances for the host.
# We only add instances that are running on a specific host
def addInstance(row):
    if row['hostId'] == '':
        # This means the VSI wasn't running on a host and we don't care about it
        return

    if row['hostId'] not in instances:
        instances[row['hostId']] = []

    instances[row['hostId']].append(row)

# Read in the list of instances from the Instances.csv file
# We only care acout instances that are in a running state
def readInstances():
    rows = loadInstances(instancesPath)
    for row in rows:
        if row['powerState'] == 'Running' and row['riasState'] == 'Running':
            addInstance(row)

# Match the profile to the profile class of the row.
# If the match is exact then we only match if the profile class is the exaxt string,
# otherwise we'll match if the profile is anywhere in the profile class in any case.
def matchProfile(profile, row):
    if exact:
        return profile == row['profileClass']
    else:
        return profile.lower() in row['profileClass'].lower()

# Return true if the region for the specified row matches the region we're looking for
def matchRegion(region, row):
    for r in region:
        if row['datacenter'].lower().startswith(r.lower()):
            return True

    return False

# Get the instances list for a specified set of host instances as a comma separated
# string.  This will return 'No instances' if there are no instances on the host.
def getInstancesList(hostInstances):
    instanceNames = []
    for instance in hostInstances:
        instanceNames.append(instance['name'])

    if len(instanceNames) == 0:
        return 'No instances'
    else:
        return ', '.join(instanceNames)

# Get the host hash that we use for sorting the hosts.  This is a combination of the
# tainted state plus the number of instances.  This will cause tainted hosts to show
# up at the top of the list with empty hosts first and then other hosts sorted alphabetically
# by the name of the first instance.
def hostHash(hostRow):
    t = 0
    if hostRow['tainted'] == 'False':
        t = 1

    if len(hostRow['instances']) == 0:
        return str(t) + str(len(hostRow['instances']))
    else:
        return str(t) + str(len(hostRow['instances'])) + hostRow['instances'][0]['name']

# Format the specified host row into a string that shows the name, tainted status, and
# list of instances.
def formatRow(hostRow, longestClass):
    return Template('$name\t$dc\t$profileClass $tainted\t $instances').safe_substitute(
        name=hostRow['name'],
        tainted=hostRow['tainted'],
        instances=getInstancesList(hostRow['instances']),
        profileClass=formatProfileClass(hostRow['profileClass'], longestClass),
        dc=hostRow['datacenter'])

# This function loads the instance and host data, finds the hosts that match the query
# parameters, finds the instances for those hosts, and prints out all of the data for
# the report.
def findInstances(profile, region):
    hostRows = loadHosts(hostsPath)
    readInstances()

    matchedHosts = []

    # We want to find the matches rows and get the instances before we do
    # any sorting because we only want to sort the hosts we care about instead
    # of taking the time to sort all hosts.
    for hostRow in hostRows:
        if matchProfile(profile, hostRow) and matchRegion(region, hostRow):
            name = hostRow['name']
            hostInstances = []
            if name in instances:
                hostRow['instances'] = instances[name]
            else:
                hostRow['instances'] = []

            matchedHosts.append(hostRow)

    # Then we sort the matched hosts array in place
    matchedHosts.sort(key=hostHash, reverse=False)

    header = """
\033[1mFinding instances for\033[0m:
Region:         $region
Profile Class:  $profileClass
Exact match:    $exactMatch
    """
    print(Template(header).safe_substitute(region=', '.join(region), profileClass=profile, exactMatch=exact))

    summary = """\033[1mSummary\033[0m:
Hosts:      $hostsCount
Tainted:    $taintedCount ($taintedPercent%)
Available:  $availableCount
    """

    # Then we gather and print the data for the summary
    taintedCount = 0
    availableCount = 0
    longestClass = 0

    for host in matchedHosts:
        if host['tainted'] == 'True':
            taintedCount = taintedCount + 1
        elif len(host['instances']) == 0:
            availableCount = availableCount + 1

        if len(host['profileClass']) > longestClass:
            longestClass = len(host['profileClass'])

    print(Template(summary).safe_substitute(hostsCount=len(matchedHosts), taintedCount=taintedCount,
      availableCount=availableCount, taintedPercent=calcPercent(taintedCount, len(matchedHosts))))

    # Then we print out the list of hosts with the instance data
    classHeader = formatProfileClass('Class', longestClass)
    print(f'\033[1mHost Name\t\tDC\t{classHeader} Tainted\t Instances\033[0m')
    for hostRow in matchedHosts:
        name = hostRow['name']

        print(formatRow(hostRow, longestClass))


findInstances(profile, region)
