import os
import json
import requests
import datetime

import test_utils
from test_utils import startSuite
from test_utils import printTestSuccess
from test_utils import printTestFail
from test_utils import runProc

# The test suite for finding a host by either the VSI name or VSI ID.

val = '''wdc3-qz1-sr3-rk037-s04
wdc3-qz1-sr3-rk042-s34
wdc3-qz1-sr3-rk050-s08
wdc3-qz1-sr3-rk087-s08
wdc3-qz1-sr3-rk129-s34
wdc3-qz1-sr3-rk094-s34
wdc3-qz1-sr3-rk044-s16
wdc3-qz1-sr3-rk049-s16
wdc3-qz1-sr3-rk011-s34
wdc3-qz1-sr3-rk002-s16
wdc3-qz1-sr3-rk006-s16
'''

def findXInY():
    lines = runProc(['python3', 'scripts/find_x_in_y.py', 'test/inputs/x.txt', 'test/inputs/y.txt'])
    output = '\n'.join(lines)
    
    if val.strip() == output.strip():
        printTestSuccess('Find X in Y')
        return True
    else:
        printTestFail(output, val)
        return False

def runTests():
    startSuite('Find X in Y')
    assert findXInY()

    return True
