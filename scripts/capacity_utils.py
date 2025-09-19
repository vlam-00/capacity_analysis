import os
import csv
import sys
import datetime
import requests
import json
import time
from decimal import Decimal
from pathlib import Path

INTERNAL_DIRECT = 'Internal Direct'
EXTERNAL_DIRECT = 'External Direct'
INTERNAL_ROKS = 'Internal ROKS'
EXTERNAL_ROKS = 'External ROKS'
AVAILABLE_GPUS = 'Available GPUs'
TOTAL_GPUS = 'Total GPUs'
TOTAL_SERVERS = 'Total Servers'
SERVER_TYPE = 'Server Type'
REGION = 'Region'
DC = 'Data Center'
PROFILE_TYPE = 'Profile Type'

# Read in the list of instances from the Instances.csv file
# We only care acout instances that are in a running state
def loadInstances(instancesPath):
    if os.path.isfile(instancesPath):
        try:
            with open(instancesPath, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                fieldnames = next(reader, None)
                if 'profileClass' in fieldnames:
                    print('The instances file contains hosts data.  Did you pass in the wrong instances file?')
                    quit(-1)

                rows = []
                for row in reader:
                    if row['powerState'] == 'Running' and (row['riasState'] == 'Running' or row['riasState'] == 'Starting' or row['riasState'] == '-'):
                        rows.append(row)
                return rows
        except KeyError as err:
            print('Unable to read the instances file.  Make sure you provided the correct file')
            print(f'Unable to find key {err}')
            quit(-1)
        except Exception as ex:
            print('Unable to read the instances file.  Make sure you provided the correct file')
            print(ex)
            quit(-1)
    else:
        fullPath = os.path.abspath(instancesPath)
        print(f"The file {fullPath} can't be found")
        quit(-1)


# Read in the list of instances from the Instances.csv file
# We only care acout instances that are in a running state
def loadBareMetal(bareMetalPath):
    if os.path.isfile(bareMetalPath):
        try:
            with open(bareMetalPath, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                fieldnames = next(reader, None)

                rows = []
                for row in reader:
                    rows.append(row)
                return rows
        except KeyError as err:
            print('Unable to read the bare metal file.  Make sure you provided the correct file')
            print(f'Unable to find key {err}')
            quit(-1)
        except Exception as ex:
            print('Unable to read the bare metal file.  Make sure you provided the correct file')
            print(ex)
            quit(-1)
    else:
        fullPath = os.path.abspath(instancesPath)
        print(f"The file {fullPath} can't be found")
        quit(-1)

# Read in all the hosts from the Hosts.csv file.
# We only care about hosts that are powered on and in a normal state.
def loadHosts(hostsPath):
    hostRows = []
    if os.path.isfile(hostsPath):
        try:
            with open(hostsPath, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                fieldnames = next(reader, None)
                if 'instanceId' in fieldnames:
                    print('The hosts file contains instances data.  Did you pass in the wrong hosts file?')
                    quit(-1)
                for row in reader:
                    if isPoweredOn(row) and row['status'] == 'Normal':
                        hostRows.append(row)
                return hostRows
        except KeyError as err:
            print('Unable to read the hosts file.  Make sure you provided the correct file')
            print(f'Unable to find key {err}')
            quit(-1)
        except Exception as ex:
            print('Unable to read the hosts file.  Make sure you provided the correct file')
            print(ex)
            quit(-1)
    else:
        fullPath = os.path.abspath(hostsPath)
        print(f"The file {fullPath} can't be found")
        quit(-1)

# Return what percentage the value is of the total to a single decimal point and
# removing the trailing zero if the result is an integer and not a decimal.
def calcPercent(val, total):
    if total == 0:
        return 'N/A'

    d = Decimal((val / total) * 100)
    s = str(round(d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize(), 1))
    if s.endswith('.0'):
        return s[:-2]
    else:
        return s

# The profile class is a variable length early in the table.
# We want to make sure that all profile classes are the same
# length so our table colums line up well.
def formatProfileClass(profileClass, length):
    spaces = (length - len(profileClass)) + 3
    return profileClass + ''.join(' ' for i in range(spaces))

# Take the raw profile string like gx2-80x1280x8a100 and return a pretty string like a100.
# This function will combine multiple types of profiles into a single string like combining the inspur and SMC
# a100 profiles into a single profile called a100
def getGPUProfileString(profile):
    if profile == 'gx2-80x1280x8a100' or profile == 'gx2-80x1280x8a100-cl-rdma' or profile == 'gx2-80x1280x8a100-il-rdma':
        return '8xa100'
    elif profile == 'gx3d-48x240x2a100p':
        return '2xa100'
    elif profile == 'gx3-24x120x1l40s':
        return '1xl40s'
    elif profile == 'gx3-48x240x2l40s':
        return '2xl40s'
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
    elif profile == 'gx3d-160x1792x8gaudi3-internal' or profile == 'gx3d-160x1792x8gaudi3':
        return 'Gaudi 3'
    elif profile == 'gx3d-208x1792x8mi300x-internal' or profile == 'gx3d-208x1792x8mi300x':
        return 'MI300X'
    elif profile == 'gx3-32x160x2l4':
        return '2xl4'
    elif profile == 'gx3-16x80x1l4':
        return '1xl4'
    elif profile == 'gx3-64x320x4l4':
        return 'l4'
    elif profile == 'gx2-16x128x2v100' or profile == 'gx2-32x256x2v100':
        return 'v100'
    else:
        return profile

# Get the array of profiles that we use at GPU profiles
def getGPUProfiles():
    # This array is a list of all the profiles that we consider GPU profiles
    gpuProfiles = [
        'gx2-80x1280x8a100', 'gx2-80x1280x8a100-cl-rdma', 'gx2-80x1280x8a100-il-rdma', 'gx3d-48x240x2a100p',
        # Put these profiles back if you want to see the Vela cluster
        # 'gx2-80x1280x8a100-cl-rdma', 'gx2-80x1280x8a100-il-rdma'
        # Put this profile back if you want to see the Vela2 cluster
        # 'gx3d-160x1792x8h100-research',
        'gx3-48x240x2l40s', 'gx3-24x120x1l40s',
        'gx3-64x320x4l4', 'gx3-32x160x2l4', 'gx3-16x80x1l4',
        'gx3d-160x1792x8h100', 'h100-sriov',
        'gx3d-160x1792x8h200', 'h200-sriov',
        'gx3d-160x1792x8gaudi3-internal', 'gx3d-160x1792x8gaudi3',
        'gx3d-208x1792x8mi300x-internal', 'gx3d-208x1792x8mi300x',
        'gx2-16x128x2v100', 'gx2-32x256x2v100']

    return gpuProfiles

# Get the array of hardware classes that we consider to be GPU classes
def getGPUClasses():
    gpuClasses = [
        'gx3-l40s', 'gx3-l4',
        'gx2-a100-il-rdma-ext', 'gx2-a100-il-rdma', 'gx2-a100-cl-rdma', 'gx2-a100-ext',
        'gx3d-a100', 'gx3d-h100', 'gx3d-h100-research', 'gx3d-h200', 'gx3d-gaudi3', 'gx3d-mi300x', 'gx3d-h200-research'
    ]

    return gpuClasses

# Returns True if the row representented by the servers meets our criteria for being powered on and false otherwise
def isPoweredOn(row):
    return row['powerState'] == 'powered-on' or row['powerState'] == 'unknown' or row['powerState'] == '-'

riasRunningStates = [
    'Running',
    'Starting',
    '-'
]

# Sometimes the Operations Dashboard shows a strange riasState for instances that are actually running.  This function
# returns true if we meet any of those states.
def isInstanceStarted(row):
    return row['powerState'] == 'Running' and row['riasState'] in riasRunningStates

gpuCountsForProfile = {
    'gx2-80x1280x8a100': 8,
    'gx2-80x1280x8a100-cl-rdma': 8,
    'gx2-80x1280x8a100-il-rdma': 8,
    'gx3d-48x240x2a100p': 2,
    'gx3-24x120x1l40s': 1,
    'gx3-48x240x2l40s': 2,
    'gx3d-152x1536x8h100-sriov': 8,
    'gx3d-160x1792x8h100': 8,
    'gx3d-160x1792x8h100-research': 8,
    'gx3d-152x1536x8h200-sriov': 8,
    'gx3d-160x1792x8h200': 8,
    'gx3d-160x1792x8h200-research': 8,
    'gx3d-160x1792x8gaudi3-internal': 8,
    'gx3d-160x1792x8gaudi3': 8,
    'gx3d-208x1792x8mi300x-internal': 8,
    'gx3d-208x1792x8mi300x': 8,
    'gx3-32x160x2l4': 2,
    'gx3-16x80x1l4': 1,
    'gx3-64x320x4l4': 4,
    'gx2-16x128x2v100': 2,
    'gx2-32x256x2v100': 2
}

# Get the number of GPUs for the specified profile class.
def getNumberOfGPUsForProfile(profile):
    if profile in gpuCountsForProfile:
        return gpuCountsForProfile[profile]
    else:
        return 0

# Load an IAM token
def getIAMToken(apiKey):
    print('Loading IAM token...')
    url = 'https://iam.cloud.ibm.com/identity/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }
    form_data = {
        'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
        'apikey': apiKey
    }

    response = requests.post(url, data=form_data, headers=headers)
    if response.status_code == 200:
        print('Finished loading IAM token...')
        data = json.loads(response.content)
        return data['access_token']
    else:
        print(response)
        print(response.text)
        printErr('Unable to get IAM token.,n' + response.text)

# These are all of the RIAS API endpoints.
# This calls the operator API from here:
# https://pages.github.ibm.com/vpc/vpc-spec-artifacts/branch/master/swagger-ui.html?version=today
endpoints = {
    'file': 'file://',
    'dal': 'https://us-south.operator.iaas.cloud.ibm.com',
    'wdc': 'https://us-east.operator.iaas.cloud.ibm.com',
    'lon': 'https://eu-gb.operator.iaas.cloud.ibm.com',
    'fra': 'https://eu-de.operator.iaas.cloud.ibm.com',
    'mad': 'https://eu-es.operator.iaas.cloud.ibm.com',
    'osa': 'https://jp-osa.operator.iaas.cloud.ibm.com',
    'par': 'https://eu-fr2.operator.iaas.cloud.ibm.com',
    'sao': 'https://br-sao.operator.iaas.cloud.ibm.com',
    'syd': 'https://au-syd.operator.iaas.cloud.ibm.com',
    'tok': 'https://jp-tok.operator.iaas.cloud.ibm.com',
    'tor': 'https://ca-tor.operator.iaas.cloud.ibm.com'
}

# Print an error message and quit
def printErr(error):
    print(error)
    quit(-1)

# Get the RIAS endpoint for the specified key
def getEndpoint(key):
    if key.lower() in endpoints:
        return endpoints[key.lower()]
    else:
        regions = ', '.join(list(endpoints.keys()))
        printErr(f'The region {key} is not supported by this utility.  The supported regions are: {regions}')

# Get the endpoint based on the region in a node name
def getEndpointFromNode(node):
    return getEndpoint(node[:3])
    
# Get the operator API key environment variable
def getApiToken():
    try:
        return os.environ['OPERATOR_API_KEY']
    except KeyError:
        printErr('Unable to find the OPERATOR_API_KEY environment variable.  The operator API key must be set to use this utility.')

# Get the FAST_COS API key environment variable
def getFastCosToken():
    try:
        return os.environ['FAST_COS_API_KEY']
    except KeyError:
        printErr('Unable to find the FAST_COS_API_KEY environment variable.  The FAST COS API key must be set to use this utility.')
        
def timestamp():
    return round(time.time() * 1000)
    
# Takes in a Jira ticket number and formats a link for that ticket.
def formatJiraLink(jiraTicket):
    parameters = ''

    escape_mask = '\033]8;{};{}\033\\{}\033]8;;\033\\'

    return escape_mask.format(parameters, f'https://jiracloud.swg.usma.ibm.com:8443/browse/{jiraTicket}', jiraTicket)


currentDate=datetime.datetime.now().strftime('%Y%m%d')

# Get the path to the instances file and validate if it exists.
def getInstancesFile():
    p = f'output/Instances-{currentDate}.csv'
    if Path(p).is_file():
        return p
    else:
        print(f'The file {p} wasn\'t found.')
        exit(-1)

# Get the path to the bare metal servers file and validate if it exists.
def getBareMetalServersFile():
    p = f'output/BareMetalServers-{currentDate}.csv'
    if Path(p).is_file():
        return p
    else:
        print(f'The file {p} wasn\'t found.')
        exit(-1)

# Get the path to the bare metal servers file and validate if it exists.
def getBareMetalServerNodesFile():
    p = f'output/ServerSchedulers-{currentDate}.csv'
    if Path(p).is_file():
        return p
    else:
        print(f'The file {p} wasn\'t found.')
        exit(-1)

# Get the path to the instances file and validate if it exists.
def getInstancesFileInPast(days=0):
    p = f'output/Instances-{currentDate}.csv'
    if days > 0:
        date = datetime.datetime.today() - datetime.timedelta(days=days)
        p = f"output/Instances-{date.strftime('%Y%m%d')}.csv"
    if Path(p).is_file():
        return p
    else:
        None

# Get the path to the hosts file and validate if it exists.
def getHostsFile():
    p = f'output/Hosts-{currentDate}.csv'
    if Path(p).is_file():
        return p
    else:
        print(f'The file {p} wasn\'t found.')
        exit(-1)