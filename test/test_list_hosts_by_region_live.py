import os
import json
import requests
import datetime

import test_utils
from test_utils import startSuite
from test_utils import printTestSuccess
from test_utils import printTestFail
from test_utils import runProc

# This is the test suite for the list_hosts_by_region_live.py script.  It will test with local data
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

def generateReportH100():
    lines = runProc(['python3', 'scripts/list_hosts_by_region_live.py', 'gx3d-h100', 'file', '-exact'])
    assert testLine('Validate host count', 'Hosts:', '3', lines)

    assert testLine('Validate tainted count', 'Tainted (Reserved):', '1 (33.3%)', lines)
    
    assert testLine('Validate host count', 'In Use:', '2', lines)

    assert testLine('Validate available hosts count', 'Available:', '0', lines)

    assert testLine('Validate host', 'mad3-qz1-sr1-rk020-s12', 'No instances', lines)

    assert testLine('Validate host', 'mad3-qz1-sr1-rk017-s20', 'itz-mad-gpu6-sfdc', lines)

    assert testLine('Validate host', 'mad3-qz1-sr1-rk017-s12', 'itz-mad-gpu7', lines)

    return True

def generateReportBx3d():
    lines = runProc(['python3', 'scripts/list_hosts_by_region_live.py', 'bx3d', 'file'])
    assert testLine('Validate host count', 'Hosts:', '104', lines)
    
    assert testLine('Validate host count', 'In Use:', '6', lines)

    assert testLine('Validate tainted count', 'Tainted (Reserved):', '12 (11.5%)', lines)

    assert testLine('Validate available hosts count', 'Available:', '86', lines)

    assert testLine('Validate host', 'mad2-qz1-sr1-rk025-s08', 'No instances', lines)

    assert testLine('Validate host', 'mad2-qz1-sr1-rk028-s08', 'big-build', lines)

    assert testLine('Validate host', 'mad1-qz1-sr1-rk114-s34', 'vsi-01, rias-insta-base-gen3-uwk7jmc9', lines)

    return True

def runTests():
    startSuite('List Hosts By Region Live')
    assert generateReportH100()
    assert generateReportBx3d()

    return True
