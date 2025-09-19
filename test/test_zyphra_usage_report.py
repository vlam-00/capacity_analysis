import os
import json
import requests
import datetime

import test_utils
from test_utils import startSuite
from test_utils import printTestSuccess
from test_utils import printTestFail
from test_utils import runProc

# This is the test suite for the generate_zyphra_usage.py.  It will test with local data
# from the test/inputs directory

def testLine(title, starts, ends, lines):
    for l in lines:
        if l.startswith(starts):
            if l.endswith(ends):
                printTestSuccess(title)
                return True
            else:
                printTestFail(title + l, ends)
                return False
    printTestFail(title, f'{starts} and it was not found')
    return False

def generateUsageReport():
    lines = runProc(['python3', 'scripts/generate_zyphra_usage.py', '-testmode'])

    assert testLine('Validate use count', '    In Use:', '128 ', lines)
    assert testLine('Validate total count', '    Total Nodes:', '139', lines)
    assert testLine('Validate stopped nodes', 'wdc3-qz1-sr5-rk480-s34', 'cnode-8', lines)

    return True



def runTests():
    startSuite('Zyphra Usage Report')
    assert generateUsageReport()

    return True
