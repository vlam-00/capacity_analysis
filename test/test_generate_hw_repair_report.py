import os
import json
import requests
import datetime

import test_utils
from test_utils import startSuite
from test_utils import printTestSuccess
from test_utils import printTestFail
from test_utils import runProc

# Takes in a Jira ticket number and formats a link for that ticket.
def formatJiraLink(jiraTicket):
    parameters = ''

    escape_mask = '\033]8;{};{}\033\\{}\033]8;;\033\\'

    return escape_mask.format(parameters, f'https://jiracloud.swg.usma.ibm.com:8443/browse/{jiraTicket}', jiraTicket)

# This is the test suite for the test_generate_hw_repair_report.py script.  It will test with local data
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
    lines = runProc(['python3', 'scripts/generate_hw_repair_report.py', 'test/inputs/platform-inventory-test', 'gx3d-h100-smc', '-exact'])

    assert testLine('Validate host', 'wdc3-qz1-sr4-rk139-s34', formatJiraLink('SYS-10689') + ' - gx3d-h100-smc', lines)
    assert testLine('Validate host', 'wdc3-qz1-sr4-rk069-s12', formatJiraLink('SYS-22783') + ' - gx3d-h100-smc', lines)

    return True

def generateReportCombined():
    lines = runProc(['python3',
                     'scripts/generate_hw_repair_report.py',
                     'test/inputs/platform-inventory-test',
                     'gx3d-h100-smc,gx2d-a100',
                     '-sort_by_jira',
                     '-nothw'])

    assert testLine('Validate host', 'wdc3-qz1-sr4-rk113-s34', formatJiraLink('SYS-22657') + ' - gx3d-h100-smc', lines)
    assert testLine('Validate host', 'wdc3-qz1-sr4-rk209-s34', formatJiraLink('SYS-22867') + ' - gx3d-h100-smc', lines)

    return True

def runTests():
    startSuite('Generate Hardware Repair Report')
    assert generateReportH100()
    assert generateReportCombined()

    return True
