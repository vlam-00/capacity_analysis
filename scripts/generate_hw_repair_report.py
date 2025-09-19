from datetime import timezone
import datetime
import argparse
from argparse import RawTextHelpFormatter
from os import walk
import os
import yaml
import csv
import pprint
import progressbar
from progressbar import ProgressBar

from capacity_utils import formatJiraLink

# This script generates a report about all servers waiting for hardware repair
parser = argparse.ArgumentParser(description='''Read data from platform-inventory and generate a report about all servers
in the configuration start for a given class.

You must provide a path to a local copy of the platform-inventory repository and
the location for the file to output.

Examples:
python3 generate_hw_repair_report.py ~/work/platform-inventory gx3d-h100-smc -exact
python3 generate_hw_repair_report.py ~/work/platform-inventory gx3d-h100-smc,gx2-a100
python3 generate_hw_repair_report.py ~/work/platform-inventory gx3d-h100-smc,gx3d-h200-smc,gx3d-gaudi3-dell

There's also an alias for all large GPU types like this:
python3 generate_hw_repair_report.py ~/work/platform-inventory gpu
''', formatter_class=RawTextHelpFormatter)

parser.add_argument('pi_path', type=str, help='The path to the platform-inventory repository')
parser.add_argument('hwclass', type=str, help='The hardware class to look for')
parser.add_argument('-exact', action=argparse.BooleanOptionalAction, default=False, help='Set this flag if you want to match the profile class exactly')
parser.add_argument('-nothw', action=argparse.BooleanOptionalAction, default=False, help='Show servers that are not in the hardware repair workflow')
parser.add_argument('-sort_by_jira', action=argparse.BooleanOptionalAction, default=False, help='Sort the list by Jira ID instead of by server')
args = parser.parse_args()
piPath = args.pi_path
hwclass = args.hwclass.split(',')
exact = args.exact
nothw = args.nothw
jiraSort = args.sort_by_jira
nodes = []

# This is a list of profile classes that we look for if they pass in the alias of gpu
largeGPUs = ['gx3d-h100-smc', 'gx3d-h200-smc',
             'gx3d-gaudi3-dell', 'gx3d-mi300x-dell',
             'bm-2s8570-2048-25600', # This is the bare metal class we use for MI300X
             'gx2-a100']

if hwclass[0].lower() == 'gpu':
    # If they passed in the gpu alias then we'll use the GPU hardware classes.
    hwclass = largeGPUs

# This is the default ticket number that the Release Bundle and Expansion tools use when they
# don't have a Jira ticket since platform-inventory requires them to have a ticket.
DEFAULT_SYS_TICKET = 'SYS-10689'

# Get the node hash that we use for sorting the nodes.  This is a combination of the
# tainted state plus the number of instances.  This will cause tainted nodes to show
# up at the top of the list with empty hosts first and then other nodes sorted alphabetically
# by the name of the first instance.
def nodeHash(node):
    name = node['hostname']
    jiraNum = node['jira']

    if jiraSort:
        return f'{jiraNum} - {name}'
    else:
        index = 1
        if 'jira' in node:
            if jiraNum == DEFAULT_SYS_TICKET:
                return f'0 - {name}'
            else:
                return f'1 - {name}'
        else:
            return f'2 - {name}'

# Joins a folder with two sub folders into a path using the correct separator for the current OS
def joinPath(folder, subFolder, subFolder2):
    return os.path.join(os.path.join(folder, subFolder), subFolder2)

# Returns true if the specified host matches on of the hardware class arguments and false otherwise
def matchesHardwareClass(host):
    for hwc in hwclass:
        if exact:
            if host['class'] == hwc:
                return True
        else:
            if host['class'].find(hwc) > -1:
                return True

    return False

# Returns true if this host matches the workflow state we're looking for based on the nothw flag
def matchesWorkflow(host):
    if nothw:
        return host['workflow'] != 'hw_debug'
    else:
        return host['workflow'] == 'hw_debug'

# Read in the allocations
def readAllocations():
    allocations = []
    path = joinPath(piPath, 'region', 'allocations')
    for (dirpath, dirnames, filenames) in walk(path):
        allocations.extend(filenames)
        break

    bar = ProgressBar(maxval=len(allocations), \
        widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
    bar.start()
    for i, alloc in enumerate(allocations):
        bar.update(i)
        if alloc.endswith('.yaml'):
#            print('Reading file: ' + alloc)
            with open(os.path.join(path, alloc)) as f:
                data = yaml.safe_load(f)
                if data is not None and len(data) > 0:
                    for host in data:
                        #print('Found host: ' + host['hostname'])
                        if matchesHardwareClass(host) and host['inventory_state'] == 'configuration' and matchesWorkflow(host):
                            nodes.append(host)

    bar.finish()

# Split the array of nodes into two arrays with valid and invalid nodes.  The valid nodes
# have Jira tickets and the invalid nodes have either no ticket or the default ticket.
def splitValidAndInvalidNodes():
    invalid = []
    valid = []

    for node in nodes:
        host = node['hostname']
        jira = 'No Jira'
        if 'jira' in node:
            if node['jira'] == DEFAULT_SYS_TICKET:
                invalid.append(node)
            else:
                valid.append(node)
        else:
            invalid.append(node)

    return valid, invalid

# Generate the report of all the nodes in configuration state which match the classs
def generateReport(hardwareClasses):
    nodes.sort(key=nodeHash, reverse=False)

    valid, invalid = splitValidAndInvalidNodes()

    print(f'\n\033[1mGenerating hardware report for: {", ".join(hardwareClasses)}\033[0m')

    if len(invalid) > 0:
        print(f'\n\033[1m{len(invalid)} nodes in configuration state without a valid Jira ticket\033[0m')
        for node in invalid:
            host = node['hostname']
            hwclass = node['class']
            jira = 'No Jira'
            if 'jira' in node:
                jira = formatJiraLink(node['jira'])
            print(f'{host} - {jira} - {hwclass}')
    else:
        print('\n\033[1mNo invalid nodes found\033[0m')

    if len(valid) > 0:
        print(f'\n\033[1m{len(valid)} nodes in configuration state with valid Jira tickets\033[0m')
        for node in valid:
            host = node['hostname']
            hwclass = node['class']
            jira = formatJiraLink(node['jira'])
            print(f'{host} - {jira} - {hwclass}')
    else:
        print('\n\033[1mNo valid nodes found\033[0m')

readAllocations()
generateReport(hwclass)
