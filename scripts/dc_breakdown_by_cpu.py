import csv
import sys

import argparse
from argparse import RawTextHelpFormatter

parser = argparse.ArgumentParser(description='''Break down a list of servers by data center and label

This script takes a CSV file with a list of servers from a DB2 query and generates a CSV
file that combines the servers by data center and label and outputs a CSV file with the data.

Example:
python3 dc_breakdown.py output/not_in_vpc_account.csv
''', formatter_class=RawTextHelpFormatter)

parser.add_argument('servers', type=str, help='The path to the Servers.csv file.')
parser.add_argument('out', type=str, help='The path to generate the usage CSV file')
parser.add_argument('-oldServers', action=argparse.BooleanOptionalAction, default=False, help='Set this flag if you want to generate a report of older servers instead of the DC breakdown')

args = parser.parse_args()
serversPath = args.servers
usagePath = args.out
oldServers = args.oldServers

servers = {}
labels = []

hardwareStatusInvalid = ['Missing_Parts', 'Spare', 'Hardfail', 'Quarantine']
interestingCascadeLake = ['X11QPH+_R1.20', 'X11DPU+_R1.10', 'X11QPH+_R1.01']
oldRows = []

# Get the label for the specified row.  The label is based on the hardware status if the row is in various liquidation
# states, spare, or missing parts or the processor description if it isn't.
def getLabel(row):
    if row['HARDWARE_STATUS'] == 'Liquidation' or row['HARDWARE_STATUS'] == 'Liquidate_Prep' or row['HARDWARE_STATUS'] == 'Retired':
        oldRows.append(row)
        return 'Liquidation'
    elif row['HARDWARE_STATUS'] == 'Spare':
        oldRows.append(row)
        return 'Spare'
    elif row['DATACENTER'] == 'AUS01':
        return 'Austin'
    elif row['DATACENTER'] == 'POK01':
        return 'POK - Development'
    elif row['HARDWARE_STATUS'] == 'Missing_Parts':
        oldRows.append(row)
        return 'Missing Parts'
    elif 'Cascade-Lake' in row['PROCESSOR_DESCRIPTION']:
        if row['HARDWARE_STATUS'] not in hardwareStatusInvalid and row['MOTHERBOARD_MODEL'] in interestingCascadeLake and row['CHASSIS_SIZE'] == '2':
            return 'Cascade-Lake - Potential for production'
        else:
            return 'Not suitable for VPC production'
    elif 'XEON-8474C-Sapphire-Rapids' in row['PROCESSOR_DESCRIPTION']:
        return 'Sapphire-Rapids for VSI'
    elif 'XEON-6426Y-Sapphire-Rapids' in row['PROCESSOR_DESCRIPTION']:
        return 'Sapphire-Rapids for Bare Metal'
    elif 'XEON-8490H-Sapphire-Rapids' in row['PROCESSOR_DESCRIPTION']:
        return 'Sapphire-Rapids for SAP'
    elif 'Broadwell' in row['PROCESSOR_DESCRIPTION'] or 'Skylake' in row['PROCESSOR_DESCRIPTION']:
        oldRows.append(row)
        return 'Dell - Too old to use'
    elif 'Haswell' in row['PROCESSOR_DESCRIPTION']:
        return 'Haswell'
    elif 'Icelake' in row['PROCESSOR_DESCRIPTION']:
        oldRows.append(row)
        return 'Icelake'
    elif 'Unknown' in row['PROCESSOR_DESCRIPTION']:
        return 'Uknown CPU type - missing parts'
    else:
        return row['PROCESSOR_DESCRIPTION']

# Generate all of the output CSV file with the GPU profiles we care about.
def generateCSV():
    with open(usagePath, 'w', newline='') as file:
        writer = csv.writer(file)

        # Start by writing the headers
        field = ['Datacenter']
        totals = {}
        for label in labels:
            field.append(label)
            totals[label] = 0
        writer.writerow(field)


        for dc in sorted(servers.items(), key=lambda item: item[0], reverse=False):
            dcRec = servers[dc[0]]
            field = []
            field.append(dc[0])
            for label in labels:
                if label in dcRec:
                    field.append(dcRec[label])
                    totals[label] = totals[label] + dcRec[label]
                else:
                    field.append('')

            writer.writerow(field)

        # We write out a final row with the totals for every label
        field = ['Totals']
        for label in labels:
            field.append(totals[label])
        writer.writerow(field)

def generateOldRowsCSV():
    with open(usagePath, 'w', newline='') as file:
        writer = csv.writer(file)

        # Start by writing the headers
        field = ['IMS_ACCOUNT_ID', 'DATE', 'DATACENTER', 'LOCATION_PATH', 'HARDWARE_STATUS', 'HARDWARE_STATUS_REASON', 'HARDWARE_TYPE', 'CHASSIS_VENDOR', 'CHASSIS_NAME', 'MOTHERBOARD_MODEL', 'PROCESSOR_DESCRIPTION', 'CHASSIS_SIZE', 'CHASSIS_VERSION_CODE', 'HARDWARE_INTERNAL_SERIAL_NUMBER', 'HARDWARE_ID', 'HARDWARE_COUNT', 'PROCESSOR_COUNT', 'PROCESSOR_VERSION_CODE', 'HARDWARE_MFR_SERIAL_NUMBER', 'HARDWARE_AGE_MONTHS', 'PROCESSOR_CODE', 'ASSET_MANAGEMENT_SKU', 'CAPACITY_MANAGEMENT_SKU', 'POD', 'PRIMARY_BCR_HOSTNAME', 'IBM_PO_NUMBER', 'PO_NUMBER', 'HARDWARE_SERVICE_START_DATE', 'RACK_HARDWARE_ID', 'HOSTNAME', 'LAST_HARDWARE_NOTE', 'HARDWARE_CLASS', 'HARDWARE_STATUS_DURATION_DAYS', 'LEASE_ORDER_FLAG', 'IBM_ACCOUNT_CLASS', 'IMS_ACCOUNT_TYPE', 'IMS_ACCOUNT_NAME', 'BSS_ACCOUNT_ID', 'IBM_CUSTOMER_NUMBER', 'PROCESSOR_FAMILY', 'PROCESSOR_FAMILY_GROUP', 'TOTAL_PHYSICAL_CORES', 'PROCESSOR_VENDOR', 'HARDWARE_TAG', 'HARDWARE_TAG_DATE', 'HARDWARE_PRIOR_STATUS', 'HARDWARE_PRIOR_STATUS_REASON', 'STATUS_DATE', 'IMS_ACCOUNT_ID', 'IMS_ACCOUNT_NAME', 'ENVIRONMENT']
        writer.writerow(field)

        print(oldRows[0])
        for oldRow in oldRows:
            outputRow = []
            for label in oldRow:
                outputRow.append(oldRow[label])

            writer.writerow(outputRow)


# Get the label for the specified row.  The label is based on the hardware status if the row is in various liquidation
# states, spare, or missing parts or the processor description if it isn't.
def getDC(row):
    return row['DATACENTER']

# Increment the count for this row and add a new row of this label isn't in the count yet.
def incrementServerCount(row):
    dc = getDC(row)
    total = 'Total'

    if total not in labels:
        labels.append(total)

    if dc not in servers:
        dcRow = {}
        servers[dc] = dcRow
        dcRow[total] = 0

    dcRec = servers[dc]
    proc = getLabel(row)
    if proc not in labels:
        labels.append(proc)

    if proc not in dcRec:
        dcRec[proc] = 0

    dcRec[proc] = dcRec[proc] + 1
    dcRec[total] = dcRec[total] + 1


with open(serversPath, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    fieldnames = next(reader, None)
    for row in reader:
        incrementServerCount(row)

#print(servers)

if oldServers:
    generateOldRowsCSV()
else:
    generateCSV()
