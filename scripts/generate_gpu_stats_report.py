import xlsxwriter
import csv
import sys
import os
import argparse
import pprint
from argparse import RawTextHelpFormatter

from capacity_utils import INTERNAL_DIRECT
from capacity_utils import EXTERNAL_DIRECT
from capacity_utils import INTERNAL_ROKS
from capacity_utils import EXTERNAL_ROKS
from capacity_utils import AVAILABLE_GPUS
from capacity_utils import TOTAL_GPUS
from capacity_utils import TOTAL_SERVERS
from capacity_utils import SERVER_TYPE
from capacity_utils import REGION
from capacity_utils import PROFILE_TYPE

# This script generates a single Excel file that contains the data in the specific format
# that we need for the weekly calls.  This generates a file named gpu_stats.xlsx in the output
# directory.

parser = argparse.ArgumentParser(description='''Generates an Excel file with the statistics about the GPUs
in the exact format we need for the weekly executive report
so there are no copy and paste errors.  This script doesn't
take any arguments.

python3 scripts/generate_gpu_stats_report.py

''', formatter_class=RawTextHelpFormatter)

parser.add_argument('outputPath', type=str, nargs='?', help='The path to the output folder.')

args = parser.parse_args()
outputPath = args.outputPath

if outputPath is None:
    outputPath = 'output'

args = parser.parse_args()

# The list of nicely formatted region names
regions = {
    'au-syd':   'SYD',
    'br-sao':   'SAO',
    'ca-tor':   'TOR',
    'eu-de':    'FRA',
    'eu-es':    'MAD',
    'eu-fr2':   'PAR',
    'eu-gb':    'LON',
    'jp-osa':   'OSA',
    'jp-tok':   'TOK',
    'us-east':  'WDC',
    'us-south': 'DAL'
}

# The list of nicely formatted GPU names
gpuTypes = {
    '1xl4':   '1 x L4',
    '2xl4':   '2 x L4',
    'l4':   '4 x L4',
    '1xl40s': '1 x L40s',
    '2xl40s': '2 x L40s',
    'h100':   'H100',
    'h200':   'H200',
    '2xa100': 'A100-PCIe',
    '8xa100': 'A100',
    'Gaudi 3': 'Gaudi 3',
    'MI300X': 'MI300X'
}

# Get a nicely formatted name for a GPU type
def getGpuName(gpu):
    if gpu in gpuTypes:
        return gpuTypes[gpu]
    else:
        return gpu

# Get a nicely formatted name for a region
def getRegionName(region):
    return regions[region]

# Read the data from the Watsonx CSV
def readWatsonxData(path):
    data = {}
    if os.path.isfile(f'{outputPath}/{path}'):
        with open(f'{outputPath}/{path}', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
#            fieldnames = next(reader, None)

            for row in reader:
                if row[REGION] not in data:
                    data[row[REGION]] = {}
                data[row[REGION]][row[SERVER_TYPE]] = {}
                data[row[REGION]][row[SERVER_TYPE]] = {
                    'servers': row[TOTAL_SERVERS],
                    'gpus': row[TOTAL_GPUS]
                }
        return data
    else:
        print(f'Unable to find the {outputPath}/{path} file')
        sys.exit(-1)

def addUnique(val, vals):
    for v in vals:
        if v == val:
            return
    vals.append(val)

# Read the data from the internal/external report
def readInternalExternalData():
    data = {}
    if os.path.isfile(f'{outputPath}/internal-external-gpu-usage-2.csv'):
        with open(f'{outputPath}/internal-external-gpu-usage-2.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
#            fieldnames = next(reader, None)

            for row in reader:
                if row[PROFILE_TYPE] not in data:
                    data[row[PROFILE_TYPE]] = {}

                if row[REGION] not in data[row[PROFILE_TYPE]]:
                    data[row[PROFILE_TYPE]][row[REGION]] = {
                        INTERNAL_DIRECT: row[INTERNAL_DIRECT],
                        EXTERNAL_DIRECT: row[EXTERNAL_DIRECT],
                        INTERNAL_ROKS: row[INTERNAL_ROKS],
                        EXTERNAL_ROKS: row[EXTERNAL_ROKS],
                        AVAILABLE_GPUS: row[AVAILABLE_GPUS],
                        TOTAL_GPUS: row[TOTAL_GPUS],
                    }
        return data
    else:
        print(f'Unable to find the {outputPath}/internal-external-gpu-usage-2.csv file')
        sys.exit(-1)

# Get the Watsonx value for a specific region and GPU
def getWatsonxVal(region, gpu, data):
    if gpu in data[region]:
        return int(data[region][gpu]['gpus'])
    else:
        return None

def gpuHash(gpu):
    return getGpuName(gpu)

# We want to sort the regions with a specific order for the first 6 and then alphabetically
# for the rest
def regionHash(region):
    if region == 'us-east':
        return 1
    elif region == 'eu-de':
        return 2
    elif region == 'eu-gb':
        return 3
    elif region == 'jp-tok':
        return 4
    elif region == 'au-syd':
        return 5
    elif region == 'ca-tor':
        return 6
    elif region == 'us-south':
        return 7
    elif region == 'br-sao':
        return 8
    elif region == 'eu-fr2':
        return 9
    elif region == 'jp-tok':
        return 10
    elif region == 'jp-osa':
        return 11
    else:
        return 100

# Generate the Watsonx usage tab in the spreadsheet
def generateWatsonxUsage(workbook, worksheet, path):
    bold = workbook.add_format({"bold": True})
    worksheet.write('A1', 'GPU Type', bold)
    data = readWatsonxData(path)

    worksheet.write(f"{chr(ord('@')+(len(data.keys())+2))}1", 'Total', bold)

    totalRegions = []
    totalGPUs = []

    # This part gets complicated.  We're missing data for cells since not all
    # GPUs are in use for all regions.  However, that's difficult since we need
    # to have all keys there in the same order for the indexes to add up right.
    # To make that all work we loop through a first time to build up the full
    # list of regions and GPUs and then loop a second time to write the worksheet.
    for i,region in enumerate(data.keys()):
        addUnique(region, totalRegions)
        for j,gpu in enumerate(data[region].keys()):
            addUnique(gpu, totalGPUs)

    totalRegions.sort(key=regionHash,reverse=False)
    totalGPUs.sort(key=gpuHash,reverse=False)
    for i,region in enumerate(totalRegions):
        col = chr(ord('@')+(i+2))
        worksheet.write(f'{col}{1}', getRegionName(region), bold)

        for j,gpu in enumerate(totalGPUs):
            worksheet.write(f'A{j+2}', getGpuName(gpu))
            val = getWatsonxVal(region, gpu, data)
            if val != None:
                worksheet.write_number(f'{col}{j+2}', getWatsonxVal(region, gpu, data))

    # Now do the total column
    for i,gpu in enumerate(totalGPUs):
        col = chr(ord('@')+(len(data.keys())+1))
        worksheet.write_formula(i+1, len(data.keys())+1, f'=SUM(A{i+2}:{col}{i+2})')

    # Now the full total
    col = chr(ord('@')+(len(data.keys())+2))
    worksheet.write_formula(len(totalGPUs) + 1, len(data.keys())+1, f'=SUM({col}{2}:{col}{len(totalGPUs) + 1})')

# Generate a new worksheet about a specific GPU type
def generateGPUStats(workbook, worksheet, gpu, data):
    bold = workbook.add_format({"bold": True})
    redBold = workbook.add_format({"bold": True, 'font_color': 'red'})
    percent_format = workbook.add_format({"num_format": "0%"})

    # We start by generating the column headers
    worksheet.write('A1', 'MZR', bold)
    worksheet.write('B1', 'Total', bold)
    worksheet.write('C1', INTERNAL_DIRECT, bold)
    worksheet.set_column("C:C", 15)
    worksheet.write('D1', INTERNAL_ROKS, bold)
    worksheet.set_column("D:D", 15)
    worksheet.write('E1', EXTERNAL_DIRECT, bold)
    worksheet.set_column("E:E", 15)
    worksheet.write('F1', EXTERNAL_ROKS, bold)
    worksheet.set_column("F:F", 15)
    worksheet.write('G1', 'Available', bold)
    worksheet.write('H1', 'Used', bold)

    # Then we iterate through each region and generate a row with with the region name and
    # all of the data for the columns included
    if gpu not in data:
        # Then they had no usage for this GPU type so we're done.
        return
        
    for i,region in enumerate(data[gpu].keys()):
        worksheet.write(f'A{i+2}', getRegionName(region))
        worksheet.write(f'B{i+2}', int(data[gpu][region][TOTAL_GPUS]))
        worksheet.write(f'C{i+2}', int(data[gpu][region][INTERNAL_DIRECT]))
        worksheet.write(f'D{i+2}', int(data[gpu][region][INTERNAL_ROKS]))
        worksheet.write(f'E{i+2}', int(data[gpu][region][EXTERNAL_DIRECT]))
        worksheet.write(f'F{i+2}', int(data[gpu][region][EXTERNAL_ROKS]))
        worksheet.write(f'G{i+2}', int(data[gpu][region][AVAILABLE_GPUS]))

        # This formula shows the percentage used for this GPU type
        worksheet.write_formula(i+1, 7, f'=(B{i+2}-G{i+2})/B{i+2}', percent_format)

    # Lastly we add the Total row at the end
    worksheet.write(f'A{len(data[gpu].keys())+2}', 'Total', bold)
    i = 1

    # Then we iterate through all of the columns and add a formula to add up the totals
    while i <= 7:
        col = chr(ord('@')+i+1)
        format = bold

        if i == 6:
            # The penultimate column is the number of available GPUs and we make that red.
            format = redBold
        if i == 7:
            # The last column shows the total percentage used with a formula
            row = len(data[gpu].keys())+1
            worksheet.write_formula(row, i, f'=(B{row+1}-G{row+1})/B{row+1}', percent_format)
        else:
            worksheet.write_formula(len(data[gpu].keys())+1, i, f'=SUM({col}2:{col}{len(data[gpu].keys())+1})', format)
        i += 1

workbook = xlsxwriter.Workbook(f'{outputPath}/gpu_stats.xlsx')

generateWatsonxUsage(workbook, workbook.add_worksheet('Watsonx GPU Utilization'), 'watsonx_gpu_usage.csv')
generateWatsonxUsage(workbook, workbook.add_worksheet('RedHat GPU Utilization'), 'redhat_gpu_usage.csv')
generateWatsonxUsage(workbook, workbook.add_worksheet('InstructLab GPU Utilization'), 'instructlab_gpu_usage.csv')

data = readInternalExternalData()
generateGPUStats(workbook, workbook.add_worksheet('L4 GPU Utilization'), 'l4', data)
generateGPUStats(workbook, workbook.add_worksheet('L40s GPU Utilization'), 'l40s', data)
generateGPUStats(workbook, workbook.add_worksheet('H100 GPU Utilization'), 'h100', data)
generateGPUStats(workbook, workbook.add_worksheet('H200 GPU Utilization'), 'h200', data)
generateGPUStats(workbook, workbook.add_worksheet('Gaudi 3 GPU Utilization'), 'Gaudi 3', data)
generateGPUStats(workbook, workbook.add_worksheet('MI300X GPU Utilization'), 'MI300X', data)
generateGPUStats(workbook, workbook.add_worksheet('8xA100 GPU Utilization'), '8xa100', data)
generateGPUStats(workbook, workbook.add_worksheet('2xA100 GPU Utilization'), '2xa100', data)
workbook.close()