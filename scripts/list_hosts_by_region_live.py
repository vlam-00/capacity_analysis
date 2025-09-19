import os
import sys
import json
import requests
import datetime
import argparse
from argparse import RawTextHelpFormatter
import urllib3
import pprint
import progressbar
from progressbar import ProgressBar
from string import Template
from dataclasses import dataclass

import capacity_utils
from capacity_utils import calcPercent
from capacity_utils import formatProfileClass
from capacity_utils import getIAMToken
from capacity_utils import printErr
from capacity_utils import getEndpoint
from capacity_utils import getApiToken

if sys.version_info.major < 3:
    from urllib import url2pathname
else:
    from urllib.request import url2pathname

apiVersion=datetime.datetime.now().strftime('%Y-%m-%d')
parser = argparse.ArgumentParser(description='''Find all hosts in a specific region by profile class.

This utility uses the operator API to get live data from the hosts.

This script will find all hosts in a specific region or zone for the specific
class and generate a report showing a summary of which hosts are tainted and
available as well as a list of all of the instances running on each host.

Examples:
python3 scripts/list_hosts_by_region_live.py gx2-a100 fra

python3 scripts/list_hosts_by_region_live.py gx3d-h100 wdc -exact

python3 scripts/list_hosts_by_region_live.py gx3d-h100 wdc WDC07 -exact

You can also pass in a comma separated list of profile classes to look for like this:

python3 scripts/list_hosts_by_region_live.py gx2-a100-cl-rdma,gx2-a100-il-rdma wdc WDC07 -exact

In addition, you can pass in an empty class type like this:

python3 scripts/list_hosts_by_region_live.py "" wdc WDC07

This will show all servers in the specified region and zone.  You can combine that with
other commands to look for specific VSIs.  For example if you're looking for all VSIs in
WDC07 with "granite" in the name then you could use this command:

python3 scripts/list_hosts_by_region_live.py "" wdc WDC07 -exact | grep granite

''', formatter_class=RawTextHelpFormatter)

parser.add_argument('profile', type=str, help='The profile class to look for.')
parser.add_argument('region', type=str, help='The region to look for.')
parser.add_argument('zone', type=str, nargs='?', help='The zone to look for.')
parser.add_argument('-exact', action=argparse.BooleanOptionalAction, default=False, help='Set this flag if you want to match the profile exactly')


args = parser.parse_args()
profile = args.profile
region = args.region
zone = args.zone
exact = args.exact

# The special profiles vela and vela2 act as aliases to load the servers in the IBM Research clusters.
if profile == 'vela2':
    profile = 'gx3d-h100-research'
    region = 'wdc'
    zone = 'WDC07'
    exact = True
elif profile == 'vela':
    profile = 'gx2-a100-cl-rdma,gx2-a100-il-rdma'
    region = 'wdc'
    zone = 'WDC07'
    exact = True

foundNodes = []

NO_INSTANCES = 'No instances'

# The ReqStruct holds data when we make multiple REST calls.  The operator
# API limits us to 100 records per request.  That means we need to make multiple
# requests to get all of the host nodes.  This struct holds the data we need
# to make those multiple requests until we get to the end of the list.
@dataclass
class ReqStruct:
    region: str
    zone: str
    profileClass: str
    iamToken: str
    url: str
    exact: bool
    bar: ProgressBar
    count: int = 0

# This class provides special handling for loading local files based on a
# special 'file` region argument.  This supports local testing without hitting
# the live API.  This allows us to have a fixed set of test data.
class FileAdapter(requests.adapters.BaseAdapter):
    @staticmethod
    # This function normalizes the path from the URL.  It will remove a leading slash
    # so we use relative paths and remove all URL parameters after the ? if there are any.
    def _normalizePath(path):
        if path.startswith('/'):
            path = path[1:]

        if '?' in path:
            path = path[0:path.find('?')]

        if path == 'operator/v1/nodes':
            # This is kind of a hack, but we replace the first path
            # with the location of our test input so we don't have to
            # change the arguments of the command.
            path = 'test/inputs/servers1.json'

        return path

    @staticmethod
    # Check the current method and path to make sure they're support.
    # Right now we only support GET since we don't need any other HTTP methods.
    def _checkPath(method, path):
        path = FileAdapter._normalizePath(path)
        if method.lower() != 'get':
            return 405, "Method Not Allowed"
        elif os.path.isdir(path):
            return 400, f'Not a file: {path}'
        elif not os.path.isfile(path):
            return 404, f'Not found: {path}'
        elif not os.access(path, os.R_OK):
            return 403, f'Access denied: {path}'
        else:
            return 200, "OK"

    def send(self, req, **kwargs):
        path = os.path.normcase(os.path.normpath(url2pathname(req.path_url)))
        path = self._normalizePath(path)
        response = requests.Response()

        response.status_code, response.reason = self._checkPath(req.method, path)
        if response.status_code == 200 and req.method.lower() != 'head':
            try:
                response.raw = open(path, 'rb')
            except (OSError, IOError) as err:
                print(err)
                response.status_code = 500
                response.reason = str(err)

        response.url = req.url
        response.request = req
        response.connection = self

        return response

    def close(self):
        pass


# Save all the nodes that match the profile class
def saveNodes(nodes, rqs):
    profileClasses = rqs.profileClass.split(',')
    for node in nodes:
        if len(rqs.profileClass) == 0:
            foundNodes.append(node)
        elif rqs.exact:
            if node['profile_class'] in profileClasses:
                foundNodes.append(node)
        else:
            for pc in profileClasses:
                if node['profile_class'].find(pc) > -1:
                    foundNodes.append(node)

    #print('Saving nodes: ' + str(len(nodes)))

def isFileUrl(url):
    return url.startswith('file://')

# Load the next set of nodes from the operator REST API
def loadNodes(rqs):
    headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + rqs.iamToken
    }

    response = {}

    if isFileUrl(rqs.url):
        # If the URL starts with file:// then we're in test mode so we want to
        # use the local file adapter instead of the general requests object.
        requests_session = requests.session()
        requests_session.mount('file://', FileAdapter())
        response = requests_session.get(rqs.url)
    else:
        response = requests.get(rqs.url, headers=headers)

    if response.status_code == 200:
        data = json.loads(response.content)

        if 'total_count' in data and data['total_count'] == 0:
            # This means that there were zero servers of any type.  That likely means the combination of region
            # and zone was incorrect.
            if rqs.zone is not None:
                print(f'Unable to find any servers in region {rqs.region} and zone {rqs.zone}.  That likely means the region and zone combination was incorrrect.\n\n')
                sys.exit(-1)
        saveNodes(data['nodes'], rqs)

        if 'next' in data:
            if rqs.bar == 0:
                rqs.bar = ProgressBar(maxval=int(data['total_count']), \
                    widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
                rqs.bar.start()

            rqs.count = rqs.count + len(data['nodes'])
            rqs.bar.update(rqs.count)
            rqs.url = data['next']['href'] + f'&version={apiVersion}&generation=2'

            if rqs.zone != None:
                # We need to make sure to append the zone to the subsequent requests or
                # we'll get the wrong results.
                zone = rqs.zone
                rqs.url = rqs.url + f'&location.zone.data_center={zone}'
            loadNodes(rqs)
        else:
            if rqs.bar != 0:
                rqs.bar.finish()
    else:
        print(response)
        print(response.text)
        raise Exception('Unable to list nodes.,n' + response.text)

# Get all the nodes data
def getNodes(region, zone, profileClass):
    endpoint = getEndpoint(region)

    iamToken = getIAMToken(getApiToken())

    print('Getting nodes data...')

    url = f'{endpoint}/operator/v1/nodes?version={apiVersion}&generation=2&limit=100'
    if zone != None:
        zone = zone.upper()
        url = url + f'&location.zone.data_center={zone}'

    rqs = ReqStruct(region, zone, profileClass, iamToken, url, exact, 0)

    loadNodes(rqs)

    #print(f'Found {len(foundNodes)} nodes')
    printNodesReport(rqs)

# Get the node hash that we use for sorting the nodes.  This is a combination of the
# tainted state plus the number of instances.  This will cause tainted nodes to show
# up at the top of the list with empty hosts first and then other nodes sorted alphabetically
# by the name of the first instance.
def nodeHash(node):
    t = 2
    if isTaintedReserved(node):
        t = 0
    elif isTaintedNotReserved(node):
        t = 1

    if len(node['instances']) == 0:
        return str(t) + '0'
    else:
        return str(t) + str(len(node['instances'])) + node['instances'][0]['name']

# Return true if the node is tainted and false otherwise
def isTainted(node):
    return 'taint' in node

# Return a label indicating the taint reason for a tainted node
def getTaintedLabel(node):
    l = len('Tainted       ')
    val = ''
    if 'taint' in node:
        val = f"{node['taint']['reason'].capitalize()}"
    else:
        val = 'Untainted'

    i = 0
    while i < l:
        if i > len(val):
            val = val + ' '
        i += 1
    return val

# Return true if the node is tainted with a reason of reserve and false otherwise
def isTaintedReserved(node):
    return 'taint' in node and node['taint']['reason'] == 'reserve'

# Return true if the node is not tainted with a reason of reserve and false otherwise
def isTaintedNotReserved(node):
    return 'taint' in node and node['taint']['reason'] != 'reserve'

# Get the list of instances on the specific host as a comma separated list
def getInstancesList(hostInstances):
    instanceNames = []
    for instance in hostInstances:
        instanceNames.append(instance['name'])

    if len(instanceNames) == 0:
        return NO_INSTANCES
    else:
        return ', '.join(instanceNames)

# Format a row for the report
def formatRow(node, longestClass):
    return Template('$name\t$dc\t$profileClass $tainted $instances').safe_substitute(
        name=node['id'],
        tainted=getTaintedLabel(node),
        instances=getInstancesList(node['instances']),
        profileClass=formatProfileClass(node['profile_class'], longestClass),
        dc=node['location']['zone']['data_center'])

# Print out the report of all the nodes
def printNodesReport(rqs):
    foundNodes.sort(key=nodeHash, reverse=False)

    zone = 'All'

    if rqs.zone != None:
        zone = rqs.zone

    header = """
\033[1mFinding instances for\033[0m:
Region:         $region
Zone:           $zone
Profile Class:  $profileClass
Exact match:    $exactMatch
    """
    print(Template(header).safe_substitute(region=rqs.region,
                                           zone=zone,
                                           profileClass=rqs.profileClass,
                                           exactMatch=rqs.exact))

    summary = """\033[1mSummary\033[0m:
Hosts:              $hostsCount
In Use:             $usedCount
Tainted (Reserved): $taintedCount ($taintedPercent%)
Tainted (Other):    $taintedCountOther ($taintedPercentOther%)
Available:          $availableCount
    """

    # Then we gather and print the data for the summary
    taintedCount = 0
    taintedOtherCount = 0
    availableCount = 0
    longestClass = 0
    inUse = 0

    for node in foundNodes:
        if isTaintedReserved(node):
            taintedCount = taintedCount + 1
        elif isTaintedNotReserved(node):
            taintedOtherCount = taintedOtherCount + 1
        elif len(node['instances']) == 0:
            availableCount = availableCount + 1

        if getInstancesList(node['instances']) != NO_INSTANCES:
            inUse = inUse + 1

        if len(node['profile_class']) > longestClass:
            longestClass = len(node['profile_class'])

    print(Template(summary).safe_substitute(hostsCount=len(foundNodes), taintedCount=taintedCount, taintedCountOther=taintedOtherCount,
      availableCount=availableCount, taintedPercent=calcPercent(taintedCount, len(foundNodes)),
      taintedPercentOther=calcPercent(taintedOtherCount, len(foundNodes)), usedCount=inUse))

    # Then we print out the list of hosts with the instance data
    classHeader = formatProfileClass('Class', longestClass)
    print(f'\033[1mHost Name\t\tDC\t{classHeader} Tainted       Instances\033[0m')
    for node in foundNodes:
        name = node['name']

        print(formatRow(node, longestClass))

getNodes(region, zone, profile)
