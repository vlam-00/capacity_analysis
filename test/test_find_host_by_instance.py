import os
import json
import requests
import datetime

import test_utils
from test_utils import startSuite
from test_utils import printTestSuccess
from test_utils import printTestFail
from test_utils import runProc

# The test suite for finding a field on a host by the instance name or ID

def findHostFieldByName():
    expected = 'kube-cs206v1w0oe95ge6hit0-watsonxaius-default-0000027e: wdc3-qz1-sr2-rk154-s48: 5.15.0-1041-ibm-gt'
    lines = runProc(['python3',
                     'scripts/find_host_field_by_instance.py',
                     'test/inputs/Instances-20241212-777.csv',
                     'test/inputs/Hosts-20241212-777.csv',
                     'kube-cs206v1w0oe95ge6hit0-watsonxaius-default-0000027e',
                     'kernelVersion'])
    if len(lines) > 0 and lines[0] == expected:
        printTestSuccess('Find host field by instance name')
        return True
    else:
        printTestFail('Unable to find host field by instance name - ' + '\n'.join(lines), expected)
        return False

def findHostFieldById():
    expected = '0777_2af4f1a6-c19c-4547-8698-4f80782196a7: wdc3-qz1-sr2-rk078-s22: 5.15.0-1041-ibm-gt'
    lines = runProc(['python3',
                     'scripts/find_host_field_by_instance.py',
                     'test/inputs/Instances-20241212-777.csv',
                     'test/inputs/Hosts-20241212-777.csv',
                     '0777_2af4f1a6-c19c-4547-8698-4f80782196a7',
                     'kernelVersion'])
    
    if len(lines) > 0 and lines[0] == expected:
        printTestSuccess('Find host field by instance ID')
        return True
    else:
        printTestFail('Unable to find host field by instance ID - ' + '\n'.join(lines), expected)
        return False

def runTests():
    startSuite('Find Host Field By Instance')
    assert findHostFieldByName()
    assert findHostFieldById()

    return True
