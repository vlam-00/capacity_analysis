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

def generateBx4dElevation():
    if not os.path.isdir('test/output'):
        os.mkdir('test/output')

    lines = runProc(['python3',
                     'scripts/elevation_builder.py',
                     'NG2',
                     'test/inputs/server_spec_bx4d.json',
                     'test/inputs/platform-inventory-test',
                     'test/output/elevation_bx4d.xlsx',
                     'test/output/elevation_bx4d.yaml'])


    # Load the generated elevation
    df = pd.read_excel('test/output/elevation_bx4d.xlsx', sheet_name='Elevation')
#    with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
#        print(df)

    assert 3 == df.get('Unnamed: 3')[60]
    printTestSuccess('Validated number of servers in legend')

    assert 'gx3d-h200-smc' == df.get('Unnamed: 4')[60]
    printTestSuccess('Validated class of servers in legend')

    assert 's12\ngx3d-h200-smc' == df.get('Unnamed: 4')[41]
    printTestSuccess('Validated server in slot u12')

    assert 's20\ngx3d-h200-smc' == df.get('Unnamed: 4')[33]
    printTestSuccess('Validated server in slot u20')

    assert 's34\ngx3d-h200-smc' == df.get('Unnamed: 4')[19]
    printTestSuccess('Validated server in slot u34')

    assert 'TOR2 - DCS-7060DX5-64S-R' == df.get('Unnamed: 4')[27]
    printTestSuccess('Validated TOR2 position')

    assert 'MTOR1 - DCS-7010TX-48-R' == df.get('Unnamed: 4')[32]
    printTestSuccess('Validated MTOR1 position')

    return True

def generateGPUElevation():
    if not os.path.isdir('test/output'):
        os.mkdir('test/output')

    lines = runProc(['python3',
                     'scripts/elevation_builder.py',
                     'NG2',
                     'test/inputs/server_spec_h100.json',
                     'test/inputs/platform-inventory-test',
                     'test/output/elevation_gpu.xlsx',
                     'test/output/elevation_gpu.yaml'])


    # Load the generated elevation
    df = pd.read_excel('test/output/elevation_gpu.xlsx', sheet_name='Elevation')
#    with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
#        print(df)

    assert 3 == df.get('Unnamed: 3')[60]
    printTestSuccess('Validated number of servers in legend')

    assert 'gx3d-h200-smc' == df.get('Unnamed: 4')[60]
    printTestSuccess('Validated class of servers in legend')

    assert 's12\ngx3d-h200-smc' == df.get('Unnamed: 4')[41]
    printTestSuccess('Validated server in slot u12')

    assert 's20\ngx3d-h200-smc' == df.get('Unnamed: 4')[33]
    printTestSuccess('Validated server in slot u20')

    assert 's34\ngx3d-h200-smc' == df.get('Unnamed: 4')[19]
    printTestSuccess('Validated server in slot u34')

    assert 'TOR2 - DCS-7060DX5-64S-R' == df.get('Unnamed: 4')[27]
    printTestSuccess('Validated TOR2 position')

    assert 'MTOR1 - DCS-7010TX-48-R' == df.get('Unnamed: 4')[32]
    printTestSuccess('Validated MTOR1 position')

    return True

def generateGen3Elevation():
    if not os.path.isdir('test/output'):
        os.mkdir('test/output')

    lines = runProc(['python3',
                     'scripts/elevation_builder.py',
                     'NG2',
                     'test/inputs/server_spec_gen3.json',
                     'test/inputs/platform-inventory-test',
                     'test/output/elevation_gen3.xlsx',
                     'test/output/elevation_gen3.yaml'])


    # Load the generated elevation
    df = pd.read_excel('test/output/elevation_gen3.xlsx', sheet_name='Elevation')
#    with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
#        print(df)

    assert 'vx3d' == df.get('Unnamed: 6')[60]
    assert 5 == df.get('Unnamed: 5')[60]
    printTestSuccess('Validated number of vx3d servers in legend')

    assert 'vx3d-elba' == df.get('Unnamed: 6')[61]
    assert 7 == df.get('Unnamed: 5')[61]
    printTestSuccess('Validated number of vx3d-elba servers in legend')

    assert 's38\nvx3d-elba' == df.get('Unnamed: 6')[15]
    printTestSuccess('Validated server in slot u38')

    assert 's28\nvx3d' == df.get('Unnamed: 6')[25]
    printTestSuccess('Validated server in slot u28')

    assert 's06\nvx3d-elba' == df.get('Unnamed: 6')[47]
    printTestSuccess('Validated server in slot u06')

    assert 'TOR2 - DCS-7260CX3-64-R' == df.get('Unnamed: 6')[27]
    printTestSuccess('Validated TOR2 position')

    assert 'MTOR1 - DCS-7010TX-48-R' == df.get('Unnamed: 6')[32]
    printTestSuccess('Validated MTOR1 position')

    return True

def generateBareMetalElevation():
    if not os.path.isdir('test/output'):
        os.mkdir('test/output')

    lines = runProc(['python3',
                     'scripts/elevation_builder.py',
                     'NG3',
                     'test/inputs/server_spec_bm.json',
                     'test/inputs/platform-inventory-test',
                     'test/output/elevation_bm.xlsx',
                     'test/output/elevation_bm.yaml'])


    # Load the generated elevation
    df = pd.read_excel('test/output/elevation_bm.xlsx', sheet_name='Elevation')

    assert 13 == df.get('Unnamed: 6')[60]
    printTestSuccess('Validated number of 2u servers in legend')

    assert 'bm-2s8474C-2048-62400' == df.get('Unnamed: 7')[60]
    printTestSuccess('Validated class of 2u servers in legend')

    assert 17 == df.get('Unnamed: 6')[61]
    printTestSuccess('Validated number of 1u servers in legend')

    assert 'bm-2s6426Y-512-31680' == df.get('Unnamed: 7')[61]
    printTestSuccess('Validated class of 1u servers in legend')

    assert 's50\nbm-2s8474C-2048-62400' == df.get('Unnamed: 7')[3]
    printTestSuccess('Validated server in slot u50')

    assert 'bm-2s6426Y-512-31680' == df.get('Unnamed: 7')[15]
    printTestSuccess('Validated server in slot u13')

    assert 's08\nbm-2s8474C-2048-62400' == df.get('Unnamed: 7')[45]
    printTestSuccess('Validated server in slot u08')

    assert 'TOR2 - DCS-7260CX3-64-R' == df.get('Unnamed: 7')[27]
    printTestSuccess('Validated TOR2 position')

    assert 'MTOR1 - DCS-7010TX-48-R' == df.get('Unnamed: 7')[32]
    printTestSuccess('Validated MTOR1 position')

    return True

def generateBx4dDevElevation():
    if not os.path.isdir('test/output'):
        os.mkdir('test/output')

    lines = runProc(['python3',
                     'scripts/elevation_builder.py',
                     'NG3',
                     'test/inputs/server_spec_bx4d.json',
                     'test/inputs/platform-inventory-test',
                     'test/output/elevation_bx4d.xlsx',
                     'test/output/elevation_bx4d.yaml'])

    # Load the generated elevation
    df = pd.read_excel('test/output/elevation_bx4d.xlsx', sheet_name='Elevation')

    assert 10 == df.get('Unnamed: 6')[60]
    printTestSuccess('Validated number of bx4d servers in legend')

    assert 'bx4d' == df.get('Unnamed: 7')[60]
    printTestSuccess('Validated class of bx4d servers in legend')

    assert 'bx4d' == df.get('Unnamed: 7')[51]
    printTestSuccess('Validated bx4d server in slot u02')

    assert 'bx4d' == df.get('Unnamed: 7')[35]
    printTestSuccess('Validated bx4d server in slot u18')

    assert 'bx4d' == df.get('Unnamed: 7')[17]
    printTestSuccess('Validated bx4d server in slot u36')

    assert 'MTOR1 - DCS-7010TX-48-R' == df.get('Unnamed: 7')[32]
    printTestSuccess('Validated MTOR1 position')

    return True

def runTests():
    startSuite('Elevation Builder')
    assert generateGen3Elevation()
    assert generateGPUElevation()
    assert generateBareMetalElevation()
    assert generateBx4dDevElevation()
    return True