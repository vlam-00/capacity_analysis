import csv
import os
import json
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timezone
import sys
from string import Template

import argparse
from argparse import RawTextHelpFormatter

import cu_accounts
import capacity_utils
from capacity_utils import loadBareMetal
from capacity_utils import getBareMetalServersFile
from capacity_utils import getBareMetalServerNodesFile

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

NO_JIRA = 'NO JIRA'

parser = argparse.ArgumentParser(description='''Generate the usage report for Zyphra cluster

Example:
python3 generate_zyphra_usage.py


You must download the Bare Metal Servers CSV file from the Operations
Dashboard and save it in a folder called output like:

  output/BareMetalServers-20250818

''', formatter_class=RawTextHelpFormatter)

parser.add_argument('-testmode', action=argparse.BooleanOptionalAction, default=False, help='Set this flag if you want to run in test mode')

args = parser.parse_args()
bmsPath = ''
bmnPath = ''
testmode = args.testmode

if testmode:
    print('--------------------Running in test mode--------------------')
    bmsPath = 'test/inputs/BareMetalServers-20250918.csv'
    bmnPath = 'test/inputs/ServerSchedulers-20250918.csv'
else:
    bmsPath = getBareMetalServersFile()
    bmnPath = getBareMetalServerNodesFile()

# Get the name of the row.  This shows the scheduler ID (which is the host name)
# if there is one and the ID otherwise.
def getName(row):
    if row['serverSchedulerId'] != '-':
        return row['serverSchedulerId']
    else:
        return row['id']

# Gets the right status indicator color based on an input of r, y, or g
def getStatus(color):
    if color == 'g':
        return '\033[92m\u2B24\033[0m'
    elif color == 'r':
        return '\033[91m\u2B24\033[0m'
    elif color == 'y':
        return '\033[93m\u2B24\033[0m'
    else:
        return '\u25CF'

# Get the correct color for the status based on the number of servers.
def getInUseStatusIndicator(count):
    if count >= 128:
        return getStatus('g')
    elif count >=122:
        return getStatus('y')
    else:
        return getStatus('r')

# Get the status with the count for the in use servers
def getInUseStatus(count):
    if count >= 128:
        return f' {count} '
    elif count >= 122:
        # This is RGB for a bright yellow
        return '\33[30m\033[48;2;252;240;3m' + f' {count}  ' + '\033[0m'
    elif count > 9:
        return '\033[41m' + f' {count} ' + '\033[0m'
    else:
        return '\033[41m' + f'{count} ' + '\033[0m'

# Get the status with count for the available servers
def getAvailableStatus(count):
    if count >= 8:
        return f'  {count}'
    elif count >= 4:
        # This specifies the background color as an RGB value.
        # 252, 240, 3 is yellow indicating that our available
        # pool is getting a little too small.
        return '\33[30m\033[48;2;252;240;3m' + f'   {count}  ' + '\033[0m'
    else:
        return '\033[41m' + f'   {count}  ' + '\033[0m'

# Pad out the specified string with spaces to get to the target length.
# We use this to make the columns in the table line up.
def addSpaces(s, targetLength):
    return s.ljust(targetLength)

# Generate the table of servers in the set of rows
def generateTable(rows):
    print(f'\033[1m{addSpaces("Host Name", 25)}{addSpaces("ID", 45)}{addSpaces("Status", 18)}Name\033[0m')

    for row in rows:
        print(f'{addSpaces(row["serverSchedulerId"], 25)}{addSpaces(row["id"], 45)}{addSpaces(row["state"], 18)}{row["name"]}')

# Generate the table of tainted servers in the set of rows
def generateTaintedTable(rows):
    print(f'\033[1m{addSpaces("Host Name", 25)}{addSpaces("Taint Reason", 22)}{addSpaces("Jira", 11)}' +
          f'{addSpaces("Status", 16)}{addSpaces("Days Open", 12)}\033[0m')

    hosts = []

    # We start by building up all the hosts that we're interested in.
    for row in rows:
        hosts.append(getHost(row))

    # Then we get data about those hosts from Jira
    jiraData = getJiraTicketData(hosts)

    # Then we assign the Jira data to each row and sort the array
    for row in rows:
        host = getHost(row)
        if host in jiraData:
            row['ticketData'] = jiraData[host]

    rows.sort(key=rowHash, reverse=True)

    for row in rows:
        host = getHost(row)
        ticket = NO_JIRA
        status = ''
        duration = ''

        if host in jiraData:
            ticketData = jiraData[host]
            ticket = ticketData['key']
            status = ticketData['fields']['status']['name']

            if status == 'SMC Support':
                # Jira should have changed this field name, but they haven't yet so we
                # fix it up.
                status = 'Vendor Support'

            duration = str((datetime.now(timezone.utc) - datetime.fromisoformat(ticketData['fields']['created'])).days)

        print(f'{addSpaces(host, 25)}{addSpaces(row["taintType"], 22)}' +
              f'{printIssue(ticket)}  {addSpaces(status, 16)}{addSpaces(duration, 12)}')

# Get the host for the specified row
def getHost(row):
    if 'serverSchedulerId' in row:
        return row['serverSchedulerId']
    else:
        return row["id"]

# Print the Jira issue as a link to the issue
def printIssue(issueNum):
    if issueNum == NO_JIRA:
        return f'\033[91m{NO_JIRA}\033[0m'
    else:
        uri = f'https://ibm-iaas.atlassian.net/browse/{issueNum}'
        escape_mask = '\033]8;{};{}\033\\{}\033]8;;\033\\'
        return escape_mask.format('', uri, issueNum)

# Print the SNOW ticket as a link to the issue
def printTicket(ticketNum):
    uri = f'https://watson.service-now.com/now/nav/ui/classic/params/target/sn_customerservice_case.do%3Fsysparm_query%3Dnumber%3D{ticketNum}'
    escape_mask = '\033]8;{};{}\033\\{}\033]8;;\033\\'
    return escape_mask.format('', uri, ticketNum)

# We sort the tickets by the total seconds they've been opened
def rowHash(row):
    if 'ticketData' in row:
        return (datetime.now(timezone.utc) - datetime.fromisoformat(row['ticketData']['fields']['created'])).total_seconds()
    else:
        return -1

# Generate the table of rows in mantenance mode
def generateMaintTable(rows):
    print(f'\033[1m{addSpaces("Host Name", 25)}{addSpaces("Name", 20)}{addSpaces("ID", 44)}{addSpaces("Jira", 11)}' +
          f'{addSpaces("Status", 16)}{addSpaces("Days Open", 12)}\033[0m')

    hosts = []

    # We start by building up all the hosts that we're interested in.
    for row in rows:
        hosts.append(getHost(row))

    # Then we get data about those hosts from Jira
    jiraData = getJiraTicketData(hosts)

    # Then we assign the Jira data to each row and sort the array
    for row in rows:
        host = getHost(row)
        if host in jiraData:
            row['ticketData'] = jiraData[host]

    rows.sort(key=rowHash, reverse=True)

    # Then we go through each row and generate the row in the table
    for row in rows:
        host = getHost(row)
        ticket = NO_JIRA
        status = ''
        duration = ''

        if host in jiraData:
            ticketData = jiraData[host]
            ticket = ticketData['key']
            status = ticketData['fields']['status']['name']

            if status == 'SMC Support':
                # Jira should have changed this field name, but they haven't yet so we
                # fix it up.
                status = 'Vendor Support'

            duration = str((datetime.now(timezone.utc) - datetime.fromisoformat(ticketData['fields']['created'])).days)

        print(f'{addSpaces(row["serverSchedulerId"], 25)}{addSpaces(row["name"], 20)}{addSpaces(row["id"], 44)}' +
              f'{printIssue(ticket)}  {addSpaces(status, 16)}{addSpaces(duration, 12)}')


def getEnvVar(name):
    if name in os.environ:
        return os.environ[name]
    else:
        print(f'ERROR: Unable to find required environment variable {name}')
        exit(-1)

# We want to make a single query with all of the hosts since it's much faster
# so we build up a JQL query with each host.  This function adds a host to the
# query.
def addHostToQuery(query, host):
    if query is None:
        return f'%28"Hostname%5BShort%20text%5D"%20~%20"{host}"%20'
    else:
        return f'{query}%20or%20"Hostname%5BShort%20text%5D"%20~%20"{host}"'

# Find the SYS ticket for the server with this specified host name and return the data
def getJiraTicketData(hosts):
    jira_token = getEnvVar('JIRA_TOKEN')
    jira_email = getEnvVar('JIRA_EMAIL')
    auth = HTTPBasicAuth(jira_email, jira_token)

    issueMap = {}
    query = None

    for host in hosts:
        query = addHostToQuery(query, host)

    query = f'{query}%29%20and%20status%20%21%3D%20Closed'
    url = f'https://ibm-iaas.atlassian.net/rest/api/3/search/jql/?jql={query}&fields=created,status,customfield_10315'

    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Cache-Control': 'no-cache',
        'accept': 'application/json'
    }

    response = requests.request('GET', url, headers=headers, verify=False, auth=auth)

    if response.status_code == 200:
        data = json.loads(response.content)
        # When everything works we get a 200 response code
        issues = data['issues']

        for issue in issues:
            issueMap[issue['fields']['customfield_10315']] = issue
    else:
        # Anything else and we treat that like an error.  We just print out the data and
        # exit out.
        print('There was an error loading data from Jira')
        print(response.url)
        print(response)
        print(response.text)
        exit(1)

    return issueMap

# SNOW returns the state of the ticket as a number.  We need to translate it to text.
def getSnowState(state):
    match int(state):
        case 0:
            return 'New'
        case 1:
            return 'Waiting on IBM Internal to Cloud'
        case 2:
            return 'Blocked by customer'
        case 3:
            return 'Closed'
        case 4:
            'Needs attention'
        case 5:
            return 'In Progress'
        case 6:
            return 'Resolved'
        case 7:
            return 'Closed'
        case 8:
            return 'Waiting on 3rd Party/Vendor'
        case 9:
            return 'Waiting on CIR'
        case 10:
            return 'Waiting on Code Fix'
        case 11:
            return 'Waiting on IBM External to Cloud'
        case 12:
            return 'Defect Pending Development'
        case 13:
            return 'Waiting on Event Summary'
        case 16:
            return 'Needs Reply'
        case 17:
            return 'Customer Replied'
        case 21:
            return 'Resolution Provided'
        case 22:
            return 'Waiting on Client'
        case 23:
            return 'In Progress'
        case 24:
            return 'Waiting on Internal'

    return state

# This function gets all of the ServiceNow tickets opened in the Zyphra account.  Right now we're
# looking for tickets in the account 41eca7cb93daee50fce8b3f17cba10f9 even though their official account
# should be 36041e0491654e84b5db6768114a3961.  SNOW is funny about the account number.
#
# We're not calling this function yet because I don't know how we want to present this data.  I need
# to work on that while we get more data.
def getSnowTickets():
    snow_token = getEnvVar('SNOW_TOKEN')
    headers = {
        'Authorization': 'Bearer ' + snow_token,
        'Content-Type': 'application/json; charset=utf-8',
        'Cache-Control': 'no-cache',
        'accept': 'application/json'
    }

    # This is the ServiceNow Table/Extract API
    # production URL is https://watson.service-now.com

    rootUrl = 'https://watson.service-now.com/api/ibmwc/extract/sn_customerservice_case?'
    zyphraAccountNumber = '41eca7cb93daee50fce8b3f17cba10f9'
    limit = '100'
    url = f"{rootUrl}sysparm_exclude_reference_link=true&sysparm_query=u_ibm_accounts={zyphraAccountNumber}^EQ^active=true&sysparm_limit={limit}"
    response = requests.request('GET', url, headers=headers, verify=False)

    if response.status_code == 200:
        data = json.loads(response.content)
        # When everything works we get a 200 response code
#        print(json.dumps(data, indent=4))

        print(f'\033[1mZyphra has {len(data["result"])} open tickets in ServiceNow:\033[0m')
        print(f'\033[1m{addSpaces("Number", 12)}{addSpaces("Status", 12)}{addSpaces("Description", 2)}\033[0m')
        for ticket in data['result']:
            print(f'{printTicket(ticket["number"])}   {addSpaces(getSnowState(ticket["state"]), 12)}{ticket["short_description"]}')

    else:
        # Anything else and we treat that like an error.  We just print out the data and
        # exit out.
        print('There was an error loading data from Jira')
        print(response.url)
        print(response)
        print(response.text)
        exit(1)

# If a server is qualifying that means we're running it in our account and testing to see if
# it's ready to go back.  If it isn't ready and needs more hardware repair then we should put
# it in the Maintenance state.  However, that takes an ECR right now and we don't want to do
# that.  So... the only way to tell if a qualifying server is actually in repair is to look for
# a Jira ticket and see if it's in the SMC Support category.  If it is then we put it in a new
# category called fixing.
def splitQualifyingServers(ibmRunning):
    qualifying = []
    fixing = []
    hosts = []

    # We start by building up all the hosts that we're interested in.
    for row in ibmRunning:
        hosts.append(getHost(row))

    # Then we get data about those hosts from Jira
    jiraData = getJiraTicketData(hosts)

    # Then we assign the Jira data to each row and sort the array
    for row in ibmRunning:
        host = getHost(row)
        if host in jiraData:
            row['ticketData'] = jiraData[host]

    ibmRunning.sort(key=rowHash, reverse=True)

    # Then we go through each row and generate the row in the table
    for row in ibmRunning:
        host = getHost(row)
        ticket = NO_JIRA
        status = ''
        duration = ''

        if host in jiraData:
            ticketData = jiraData[host]
            ticket = ticketData['key']
            status = ticketData['fields']['status']['name']

            if status == 'SMC Support' or status == 'Vendor Support':
                # Jira should have changed this field name, but they haven't yet so we
                # fix it up.
                status = 'Vendor Support'
                fixing.append(row)
            else:
                qualifying.append(row)

            duration = str((datetime.now(timezone.utc) - datetime.fromisoformat(ticketData['fields']['created'])).days)

        else:
            qualifying.append(row)

    return qualifying,fixing



def isZyphraAccount(row):
    return True
    # Right now we're not checking account IDs since the entire capacity is basically reserved
    # for Zyphra.  However, at some point in the future we may want to filter for the following accounts
    #
    # Zyphra - AMD GPU Cluster (36041e0491654e84b5db6768114a3961) - This is the Zyphra commercial account
    # 62f360ff16f268d9266f934877e4e756 - This is the Bare Metal dev account that we used for testing
    #
    # return row['accountId'] == '36041e0491654e84b5db6768114a3961' or row['accountId'] == '62f360ff16f268d9266f934877e4e756'

# Return true if this is the IBM test account and false otherwise.
def isIBMAccount(row):
    # This is the Bare Metal dev account that we used for testing.  We do all of our qualification and testing in this account
    return row['accountId'] == '62f360ff16f268d9266f934877e4e756'

# Returns true if the node meets our definition of a Zyphra node
def isZyphraServer(row):
    return (row['profileName'] == 'cx3d-metal-112x2048' or row['profileName'] == 'gx3d-metal-224x2048x8mi300x') and row['datacenter'] == 'WDC07'

def isMI300XNode(row):
    # TODO: This is a little hacky since it depends on us only having MI300X nodes with this processor that are Bare Metal.
    return row['cpuFamily'] == 'Xeon-Platinum' and row['datacenter'] == 'WDC07'

def formatLength(arr):
    if len(arr) < 10:
        return f'  {len(arr)}'
    elif len(arr) < 99:
        return f' {len(arr)}'
    else:
        return f'{len(arr)}'

def formatNum(n):
    if n < 10:
        return f'  {n}'
    elif n < 99:
        return f' {n}'
    else:
        return f'{n}'

# Some nodes are artifacts that don't represent physical servers like
# failed or unprovisioning instances.  This function gets the count of
# physical servers.
def countPhysicalHosts(nodes):
    count = 0
    for nodeArr in nodes:
        for node in nodeArr:
            if getHost(node) != '-':
                # Then this is a physical node and we increment the count
                count += 1
    return count

# Generate the report
def generateReport():
    rows = loadBareMetal(bmsPath)
    nodeRows = loadBareMetal(bmnPath)
    inUse = []
    ibmRunning = []
    fixing = []
    available = []
    stopped = []
    hotSpares = []
    other = []
    maint = []
    hosts = []
    tainted = []

    nodes = [inUse, ibmRunning, fixing, available, stopped, hotSpares, other, maint, tainted]

    for row in rows:
        if isZyphraServer(row) and isZyphraAccount(row):
            hosts.append(row['serverSchedulerId'])
            if row['state'] == 'Running':
                if isIBMAccount(row):
                    ibmRunning.append(row)
                else:
                    inUse.append(row)
            elif row['state'] == 'Maintenance':
                maint.append(row)
            elif row['state'] == 'Stopped':
                if isIBMAccount(row):
                    stopped.append(row)
                else:
                    # If a server is stopped in the Zyphra account then it counts as a hot spare
                    hotSpares.append(row)
            else:
                other.append(row)
    ibmRunning,fixing = splitQualifyingServers(ibmRunning)

    for row in nodeRows:
        if isMI300XNode(row) and row['id'] not in hosts:
            # This means we found an empty MI300X server
            if row['taintType'] == '-':
                # Then this is an empty and untainted row which means it's available
                available.append(row)
            else:
                tainted.append(row)

    header = """
\033[1mZyphra Cluster Report\033[0m - $status

    In Use:         $inUseCount
    Zyphra Stopped:  $hotSparesCount
    Available:      $availableCount
    Stopped:         $stoppedCount
    Qualifying:      $qualCount

    Fixing:          $fixingCount
    Maintenance:     $maintCount
    Tainted:         $emptyNodesCount

    Other:           $otherCount
    ----------------------------
    Without Nodes:   $total
    Total Nodes:     $totalNodes
    """
    print(Template(header).safe_substitute(inUseCount=getInUseStatus(len(inUse)),
                                           availableCount=getAvailableStatus(len(available)),
                                           status=getInUseStatusIndicator(len(inUse)),
                                           qualCount=formatLength(ibmRunning),
                                           fixingCount=formatLength(fixing),
                                           hotSparesCount=formatLength(hotSpares),
                                           otherCount=formatLength(other),
                                           totalNodes=countPhysicalHosts(nodes),
                                           emptyNodesCount=formatLength(tainted),
                                           stoppedCount=formatLength(stopped),
                                           total=formatNum((len(other) + len(maint) + len(hotSpares) + len(inUse) + len(available) + len(tainted) + len(stopped) + len(ibmRunning) + len(fixing)) - countPhysicalHosts(nodes)),
                                           maintCount=formatLength(maint)))

    if len(maint) > 0:
        print('\n\033[1mMaintenance Nodes\033[0m')
        generateMaintTable(maint)

    if len(other) > 0:
        print('\n\033[1mOther Nodes\033[0m')
        generateTable(other)

    if len(hotSpares) > 0:
        print('\n\033[1mZyphra Stopped Nodes\033[0m')
        generateTable(hotSpares)
        
    #if len(available) > 0:
    #    print('\n\033[1mAvailable Nodes\033[0m')
    #    print(available)

    #if len(inUse) > 0:
    #    print('\n\033[1mZyphra In Use\033[0m')
    #    generateTable(inUse)

    if len(fixing) > 0:
        print('\n\033[1mNodes Getting Fixed\033[0m')
        generateMaintTable(fixing)

    if len(tainted) > 0:
        print('\n\033[1mTainted Nodes\033[0m')
        generateTaintedTable(tainted)
#        generateMaintTable(tainted)
    

    print('')


generateReport()

#getSnowTickets()