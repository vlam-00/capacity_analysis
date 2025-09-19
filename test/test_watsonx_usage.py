import os
import json
import requests
import datetime
import csv

import test_utils
from test_utils import startSuite
from test_utils import printTestSuccess
from test_utils import printTestFail
from test_utils import runProc

# The test suite for the Watsonx usage report

serverTypeLabel = 'Server Type'
totalServersLabel = 'Total Servers'
totalGPULabel = 'Total GPUs'



def findRowAndVal(serverType, totalLabel, totalVal, data, title):
    if serverType in data:
        if data[serverType][totalLabel] == totalVal:
            printTestSuccess(title)
            return True
        else:
            printTestFail(title, f'Expected {totalLabel} to be {totalVal} and got {data[serverType][totalLabel]} instead')
            return False
            
    printTestFail(title, f'Expected {serverType} and did not find it')
    return False

def generateReport():
    if not os.path.isdir('test/output'):
        os.mkdir('test/output')
        
    runProc(['python3', 'scripts/generate_watsonx_usage.py', 'test/inputs/Instances-20241212-777.csv', 'test/output/redhat_gpu_usage.csv', '8064a02a442140dbbfa41b260ff190cb'])
    runProc(['python3', 'scripts/generate_watsonx_usage.py', 'test/inputs/Instances-20241212-777.csv', 'test/output/instructlab_gpu_usage.csv', '8d28df3cd15b4072a69a252c0b2188fc,e3e25bff28064d78adc53b5e939904b7'])
    lines = runProc(['python3', 'scripts/generate_watsonx_usage.py', 'test/inputs/Instances-20241212-777.csv', 'test/output/watsonx_gpu_usage.csv'])
    data = {}

    with open('test/output/watsonx_gpu_usage.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = next(reader, None)
        for row in reader:
            data[row[serverTypeLabel]] = {
                totalServersLabel: row[totalServersLabel],
                totalGPULabel: row[totalGPULabel]
            }
        
    assert findRowAndVal('h100', totalServersLabel, '27', data, 'Find H100 server count')

    assert findRowAndVal('h100', totalGPULabel, '216', data, 'Find H100 GPU count')

    assert findRowAndVal('2xl40s', totalServersLabel, '9', data, 'Find L40s server count')

    assert findRowAndVal('2xl40s', totalGPULabel, '18', data, 'Find L40s GPU count')
            
    return True

def runTests():
    startSuite('Generate Watsonx usage report')
    assert generateReport()

    return True
