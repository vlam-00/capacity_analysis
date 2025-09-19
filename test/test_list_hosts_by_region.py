import os
import json
import requests
import datetime

import test_utils
from test_utils import startSuite
from test_utils import printTestSuccess
from test_utils import printTestFail
from test_utils import runProc

# This is the test suite for the list_hosts_by_region.py script.  It will test both the exact
# and not exact version of running this script.

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

def generateExactReport():
    lines = runProc(['python3', 'scripts/list_hosts_by_region.py', 'test/inputs/Instances-20241212-777.csv', 'test/inputs/Hosts-20241212-777.csv', 'wdc', 'gx3d-h100', '-exact'])
    assert testLine('Validate host count', 'Hosts:', '48', lines)

    assert testLine('Validate tainted count', 'Tainted:', '5 (10.4%)', lines)

    assert testLine('Validate available hosts count', 'Available:', '2', lines)

    assert testLine('Validate host', 'wdc3-qz1-sr4-rk024-s20', 'kube-chideflw0fg8q3vvk0fg-watsonxypqa-gpu8h10-0005a692', lines)

    assert testLine('Validate host', 'wdc3-qz1-sr4-rk023-s12', 'prod-rhel-ai-training-client-h100-2', lines)

    return True

def generateReport():
    lines = runProc(['python3', 'scripts/list_hosts_by_region.py', 'test/inputs/Instances-20241212-777.csv', 'test/inputs/Hosts-20241212-777.csv', 'wdc', 'gx3d-h100'])
    assert testLine('Validate host count', 'Hosts:', '175', lines)

    assert testLine('Validate tainted count', 'Tainted:', '6 (3.4%)', lines)

    assert testLine('Validate available hosts count', 'Available:', '9', lines)

    assert testLine('Validate host', 'wdc3-qz1-sr4-rk231-s20', 'No instances', lines)

    assert testLine('Validate host', 'wdc3-qz1-sr4-rk145-s20', 'h100-test-zmm5s-gdr-worker-3-nfbq8', lines)

    assert testLine('Validate host', 'wdc3-qz1-sr4-rk145-s20', 'h100-test-zmm5s-gdr-worker-3-nfbq8', lines)

    return True

def runTests():
    startSuite('List Hosts By Region')
    assert generateReport()
    assert generateExactReport()

    return True
