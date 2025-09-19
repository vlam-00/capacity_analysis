import os
import json
import requests
import datetime

import test_utils
from test_utils import startSuite
from test_utils import printTestSuccess
from test_utils import printTestFail
from test_utils import runProc

# The test suite for finding a field on a host by host ID

def findHostField():
    lines = runProc(['python3', 'scripts/find_host_field.py', 'test/inputs/Hosts-20241212-777.csv', 'wdc3-qz1-sr3-rk006-s30', 'kernelVersion'])
    if len(lines) > 0 and lines[0] == '5.15.0-1041-ibm-gt':
        printTestSuccess('Find host field by host ID')
        return True
    else:
        printTestFail('Unable to find host field by host ID - ' + '\n'.join(lines), '5.15.0-1041-ibm-gt')
        return False

def runTests():
    startSuite('Find Host Field By Host Id')
    assert findHostField()

    return True
