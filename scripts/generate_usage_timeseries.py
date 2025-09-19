import os
import csv
import json
import requests
import datetime
import argparse
from argparse import RawTextHelpFormatter
import subprocess
import capacity_utils
from capacity_utils import getInstancesFileInPast
from capacity_utils import getHostsFile
from pathlib import Path
import xlsxwriter
import pprint

home = Path.home()

parser = argparse.ArgumentParser(description='''Generates timeseries data about the usage of a set of accounts

You must have the Instances CSV file for all of the days that you want to generate the series for.

python3 scripts/generate_usage_timeseries.py

''', formatter_class=RawTextHelpFormatter)

parser.add_argument('numberOfDays', type=int, help='The number of days to go back in history.')
args = parser.parse_args()

numberOfDays = args.numberOfDays

regions = {}
servers = {}
columns = {}

def addToTotal(d, key, day, val):
    if key not in d:
        d[key] = {}

    if day not in d[key]:
        d[key][day] = 0

    d[key][day] = d[key][day] + int(val)

def addIfNotThere(d, key):
    if key not in d:
        d[key] = {}

# The first step is to generate the usage data for the number of days we're interested in
# and read in those reports and store them in the regions object
def generateUsage(days):
    os.makedirs('output/timeseries', exist_ok=True)
    i = 0
    foundDays = []
    while i < days:
        instancesPath = getInstancesFileInPast(i)
        if instancesPath is not None:
            print(f'Generating usage report for day - {instancesPath}')
            foundDays.append(i)
            subprocess.run(['python3', 'scripts/generate_watsonx_usage.py', instancesPath, f'output/timeseries/watsonx_gpu_usage-{i}.csv'])

            with open(f'output/timeseries/watsonx_gpu_usage-{i}.csv', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    addIfNotThere(regions, row['Region'])
                    addIfNotThere(regions[row['Region']], row['Server Type'])
                    addIfNotThere(regions[row['Region']][row['Server Type']], i)
                    regions[row['Region']][row['Server Type']][i] = row['Total GPUs']

                    addToTotal(servers, row['Server Type'], i, row['Total GPUs'])

        i += 1

    # This problem gets really tricky.  We don't want to show empty columns for days where
    # we don't have data, but we also need to allow for the fact that we don't have data for
    # every row when we have a column.  The best way to handle that is to build a dict so
    # we can look up the correct column for a given day.  Then we can look that up later
    # and don't have to know all of the columns for every row at the time we process each
    # row.
    for j,day in enumerate(sorted(foundDays, reverse=False)):
        columns[day] = (len(foundDays) - j) - 1

# The second step is to use that data to generate a combined spreadsheet with the sparklines
def generateTimeseries(workbook, worksheet):
    bold = workbook.add_format({"bold": True})
    worksheet.set_default_row(35)

    # Write out the first two headers
    worksheet.write('A1', 'Region', bold)
    worksheet.write('B1', 'Server Type', bold)
    row = 1

    cols = {}
    maxLength = 0
    for region in regions.keys():
        for type in regions[region].keys():
            maxLength = max(maxLength, len(regions[region][type].keys()))

    # Write out the individual rows
    for region in regions.keys():
        for type in regions[region].keys():
            worksheet.write(row, 0, region)
            worksheet.write(row, 1, type)
            maxDays = 0
            for i, day in enumerate(sorted(regions[region][type].keys(), reverse=True)):
                col = columns[day]
                date = datetime.datetime.today() - datetime.timedelta(days=day)

                worksheet.write(0, col + 3, f"{date.strftime('%d-%b-%y')}", bold)
                worksheet.write_number(row, col + 3, int(regions[region][type][day]))
                maxDays = i

            # Now we add the spark line
            col = xlsxwriter.utility.xl_col_to_name(maxLength + 2)
            worksheet.add_sparkline(row, 2,
                                      {
                                          "range": [f'D{row+1}:{col}{row+1}'],
                                          "first_point": True,
                                          "last_point": True
                                      })

            # Set the width of the sparkline column
            worksheet.set_column(f'C:C', 55)
            row += 1

    i = 0
    worksheet.write(f'A{row+1}', 'Total', bold)
    col = xlsxwriter.utility.xl_col_to_name(maxLength + 2)
    worksheet.add_sparkline(row, 2,
                              {
                                  "range": [f'D{row+1}:{col}{row+1}'],
                                  "first_point": True,
                                  "last_point": True
                              })
    while i < maxLength:
        col = xlsxwriter.utility.xl_col_to_name(i + 3)
        worksheet.write_formula(row, i + 3, f'=SUM({col}2:{col}{row})')
        i += 1

# The third step is to use the data to generate the second sheet that combines all server types globally instead
# of showing by region.
def generateTimeseriesGlobal(workbook, worksheet):
    bold = workbook.add_format({"bold": True})
    worksheet.set_default_row(35)

    # Write out the first two headers
    worksheet.write('A1', 'Server Type', bold)
    row = 1

    cols = {}
    maxLength = 0
    for server in servers.keys():
        maxLength = max(maxLength, len(servers[server].keys()))

    # Write out the individual rows
    for server in servers.keys():
        worksheet.write(row, 0, server)
        maxDays = 0
        for i, day in enumerate(sorted(servers[server].keys(), reverse=True)):
            col = columns[day]
            date = datetime.datetime.today() - datetime.timedelta(days=day)

            worksheet.write(0, col + 2, f"{date.strftime('%d-%b-%y')}", bold)
            worksheet.write_number(row, col + 2, int(servers[server][day]))
            maxDays = i

        # Now we add the spark line
        col = xlsxwriter.utility.xl_col_to_name(maxLength + 1)
        worksheet.add_sparkline(row, 1,
                                  {
                                      "range": [f'C{row+1}:{col}{row+1}'],
                                      "first_point": True,
                                      "last_point": True
                                  })

        # Set the width of the sparkline column
        worksheet.set_column(f'B:B', 55)
        row += 1

    i = 0
    worksheet.write(f'A{row+1}', 'Total', bold)
    while i < maxLength:
        col = xlsxwriter.utility.xl_col_to_name(i + 2)
        worksheet.write_formula(row, i + 2, f'=SUM({col}2:{col}{row})')
        i += 1


generateUsage(numberOfDays)

workbook = xlsxwriter.Workbook(f'output/watsonx_usage_timeseries.xlsx')
generateTimeseries(workbook, workbook.add_worksheet('Timeseries by Region'))
generateTimeseriesGlobal(workbook, workbook.add_worksheet('Timeseries Global'))
workbook.close()