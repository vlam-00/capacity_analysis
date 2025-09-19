import csv
import sys

import argparse
from argparse import RawTextHelpFormatter

parser = argparse.ArgumentParser(description='''Find the count of all server types based on CPU

This script takes a CSV file with a list of servers from a DB2 query and generates a CSV
file that combines the servers by processor type and hardware state and gives counts of
each type in a useful format to create an overall pie chart.

Example:
python3 cpu_breakdown.py output/not_in_vpc_account.csv
''', formatter_class=RawTextHelpFormatter)

parser.add_argument('servers', type=str, help='The path to the Servers.csv file.')

args = parser.parse_args()
serversPath = args.servers

servers = {}

hardwareStatusInvalid = ['Missing_Parts', 'Spare', 'Hardfail', 'Quarantine']
interestingCascadeLake = ['X11QPH+_R1.20', 'X11DPU+_R1.10', 'X11QPH+_R1.01']

# Get the label for the specified row.  The label is based on the hardware status if the row is in various liquidation
# states, spare, or missing parts or the processor description if it isn't.
def getLabel(row):
    if row['HARDWARE_STATUS'] == 'Liquidation' or row['HARDWARE_STATUS'] == 'Liquidate_Prep' or row['HARDWARE_STATUS'] == 'Retired':
        return 'Liquidation'
    elif row['HARDWARE_STATUS'] == 'Spare':
        return 'Spare'
    elif row['DATACENTER'] == 'AUS01':
        return 'Austin'
    elif row['DATACENTER'] == 'POK01':
        return 'POK - Development'
    elif row['HARDWARE_STATUS'] == 'Missing_Parts':
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
        return 'Dell - Too old to use'
    elif 'Haswell' in row['PROCESSOR_DESCRIPTION']:
        return 'Haswell'
    elif 'Icelake' in row['PROCESSOR_DESCRIPTION']:
        return 'Icelake'
    elif 'Unknown' in row['PROCESSOR_DESCRIPTION']:
        return 'Uknown CPU type - missing parts'
    else:
        return row['PROCESSOR_DESCRIPTION']

# Print out the CSV file with all the counts.
def printCounts():
    print('PROCESSOR_DESCRIPTION,count')
    for server in servers:
        print(server + ',' + str(servers[server]))

# Increment the count for this row and add a new row of this label isn't in the count yet.
def incrementServerCount(row):
    proc = getLabel(row)
    if proc not in servers:
        servers[proc] = 0

    servers[proc] = servers[proc] + 1

with open(serversPath, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    fieldnames = next(reader, None)
    for row in reader:
        incrementServerCount(row)

#print(servers)
printCounts()
