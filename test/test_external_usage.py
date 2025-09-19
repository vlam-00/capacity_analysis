import os
import json
import requests
import datetime
import csv
import pprint

import test_utils
from test_utils import startSuite
from test_utils import printTestSuccess
from test_utils import printTestFail
from test_utils import runProc

# The test suite for the internal and external GPU usage report

profileTypeLabel = 'Profile Type'
totalGPULabel = 'Total GPUs'
availableGPULabel = 'Available GPUs'
internalDirectLabel = 'Internal Direct'
externalDirectLabel = 'External Direct'
internalROKSLabel = 'Internal ROKS'
externalROKSLabel = 'External ROKS'

labels = [totalGPULabel, availableGPULabel, internalDirectLabel, externalDirectLabel, internalROKSLabel, externalROKSLabel]



def findRowAndVal(serverType, totalLabel, totalVal, data, title):
    if serverType in data:
        if data[serverType][totalLabel] == totalVal:
            printTestSuccess(title)
            return True
        else:
            printTestFail(title, f'Expected {totalLabel} for {serverType} to be {totalVal} and got {data[serverType][totalLabel]} instead')
            return False

    printTestFail(title, f'Expected {serverType} and did not find it')
    return False

def generateReport():
    if not os.path.isdir('test/output'):
        os.mkdir('test/output')

    lines = runProc(['python3',
                     'scripts/generate_external_gpu_usage.py',
                     'test/inputs/Instances-20250116-777.csv',
                     'test/inputs/Hosts-20250116-777.csv',
                     'test/output/internal-external-gpu-usage-2.csv'])
    data = {}

    with open('test/output/internal-external-gpu-usage-2.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = next(reader, None)
        for row in reader:
            data[row[profileTypeLabel]] = {}
            for label in labels:
                data[row[profileTypeLabel]][label] = row[label]

    assert findRowAndVal('l40s', totalGPULabel, '44', data, 'Find L40s total GPUs')
    
    assert findRowAndVal('l40s', availableGPULabel, '20', data, 'Find L40s available GPUs')
    
    assert findRowAndVal('h100', internalDirectLabel, '88', data, 'Find H100 internal count')

    assert findRowAndVal('h100', externalDirectLabel, '16', data, 'Find H100 external')

    assert findRowAndVal('h100', externalROKSLabel, '0', data, 'Find H100 external ROKS')

    assert findRowAndVal('h100', availableGPULabel, '16', data, 'Find H100 available GPUs')

    assert findRowAndVal('h100', totalGPULabel, '328', data, 'Find H100 total GPUs')
    
    assert findRowAndVal('h200', internalDirectLabel, '0', data, 'Find H200 internal direct GPUs')

    assert findRowAndVal('h200', totalGPULabel, '8', data, 'Find H200 total GPUs')
    
    assert findRowAndVal('h200', availableGPULabel, '8', data, 'Find H200 available GPUs')

    assert findRowAndVal('v100', internalDirectLabel, '34', data, 'Find H100 internal count')
    
    assert findRowAndVal('Gaudi 3', availableGPULabel, '0', data, 'Find Gaudi 3 available GPUs')
    
    assert findRowAndVal('Gaudi 3', internalDirectLabel, '8', data, 'Find Gaudi 3 available GPUs')
    
    assert findRowAndVal('MI300X', availableGPULabel, '0', data, 'Find MI300X available GPUs')
    
    assert findRowAndVal('MI300X', internalDirectLabel, '8', data, 'Find MI300X available GPUs')

    return True

def runTests():
    startSuite('Generate internal and external GPU usage report')
    assert generateReport()


    return True
