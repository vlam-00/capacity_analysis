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

def findHostByName():
    lines = runProc(['python3', 'scripts/find_host_by_vsi.py', 'test/inputs/Instances-20241212-777.csv', 'kube-cie9agrw03kb77s3pr1g-lhicdprodus-cmx216x-003d1065'])
    for l in lines:
      if l == 'wdc3-qz1-sr2-rk189-s30':
          printTestSuccess('Find host by VSI name')
          return True
      else:
          printTestFail('Unable to find host by VSI name - ' + l, 'wdc3-qz1-sr2-rk189-s30')
          return False

def findHostById():
    lines = runProc(['python3', 'scripts/find_host_by_vsi.py', 'test/inputs/Instances-20241212-777.csv', '0777_77faa76f-2284-41e2-b5be-5525e2b2a4b0'])
    for l in lines:
      if l == 'wdc3-qz1-sr2-rk186-s42':
          printTestSuccess('Find host by VSI Id')
          return True
      else:
          printTestFail('Unable to find host by VSI name - ' + l, 'wdc3-qz1-sr2-rk186-s42')
          return False

def runTests():
    startSuite('Find Host By Id')
    assert findHostByName()
    assert findHostById()

    return True
