import os
import json
import requests
import datetime
import csv
import pprint
import pandas as pd

import test_utils
from test_utils import startSuite
from test_utils import printTestSuccess
from test_utils import printTestFail
from test_utils import runProc

# The test suite for the GPU statistics report

profileTypeLabel = 'Profile Type'
totalGPULabel = 'Total GPUs'
availableGPULabel = 'Available GPUs'
internalDirectLabel = 'Internal Direct'
externalDirectLabel = 'External Direct'
internalROKSLabel = 'Internal ROKS'
externalROKSLabel = 'External ROKS'

labels = [totalGPULabel, availableGPULabel, internalDirectLabel, externalDirectLabel, internalROKSLabel, externalROKSLabel]


def generateReport():
    # Our test data is limited to a single region and Pandas can't execute formulas in Excel.
    # Given those constraints we load the Watsonx sheet and a couple of the specific GPU
    # statistics sheets and call it good.

    if not os.path.isdir('test/output'):
        os.mkdir('test/output')

    lines = runProc(['python3',
                     'scripts/generate_gpu_stats_report.py',
                     'test/output'])

    # Load the H100 GPU utilization sheet and check a couple of values
    df = pd.read_excel('test/output/gpu_stats.xlsx', sheet_name='H100 GPU Utilization')

    assert 208 == df.get('Internal ROKS')[0]
    printTestSuccess('Validated H100 Internal ROKS value')

    assert 328 == df.get('Total')[0]
    printTestSuccess('Validated H100 Total value')

    # Load the L40s GPU utilization sheet and check a couple of values
    df = pd.read_excel('test/output/gpu_stats.xlsx', sheet_name='L40s GPU Utilization')

    assert 2 == df.get('External ROKS')[0]
    printTestSuccess('Validated L40s Internal ROKS value')

    assert 44 == df.get('Total')[0]
    printTestSuccess('Validated L40s Total value')

    # Load the Watsonx usage sheet and check a couple of values
    df = pd.read_excel('test/output/gpu_stats.xlsx', sheet_name='Watsonx GPU Utilization')

    assert 18 == df.get('WDC')[1]
    printTestSuccess('Validated 2 x L40s Watsonx usage')

    assert 432 == df.get('WDC')[2]
    printTestSuccess('Validated A100 Watsonx usage')

    assert 216 == df.get('WDC')[3]
    printTestSuccess('Validated H100 Watsonx usage')



    return True

def runTests():
    startSuite('Generate GPU statistics report')
    assert generateReport()


    return True
