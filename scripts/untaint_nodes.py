import os
import json
import requests
import datetime
import argparse
from argparse import RawTextHelpFormatter
import urllib3
import progressbar
from progressbar import ProgressBar
from string import Template
from dataclasses import dataclass
import rich

import capacity_utils
from capacity_utils import calcPercent
from capacity_utils import formatProfileClass
from capacity_utils import getIAMToken
from capacity_utils import printErr
from capacity_utils import getEndpoint
from capacity_utils import getApiToken
from capacity_utils import getEndpointFromNode
from capacity_utils import timestamp

apiVersion=datetime.datetime.now().strftime('%Y-%m-%d')
parser = argparse.ArgumentParser(description='''Untaint a list of nodes

This utility uses the operator API to untaint a list of nodes

python3 scripts/untaint_nodes.py wdc3-qz1-sr4-rk020-s12,wdc3-qz1-sr4-rk021-s34

''', formatter_class=RawTextHelpFormatter)

parser.add_argument('nodes', type=str, help='The nodes to taint.')

args = parser.parse_args()
nodes = args.nodes.split(',')

def untaintNode(iamToken, node):
    print(f'Requesting untaint for {node}')
    endpoint = getEndpointFromNode(node)
    url = f'{endpoint}/operator/v1/operator_actions?version={apiVersion}&generation=2'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + iamToken
    }

    payload = {
        "action": {
            "type": "untaint",
            "target": {
                "id": node
            }
        },
        "name": f'untaint-{node}-{timestamp()}'
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code != 201:
        print(response)
        print(response.text)
        raise Exception('Unable to untaint node.,n' + response.text)
    else:
        print(f'Untaint successfully submitted for {node}')

def untaintNodes():
    iamToken = getIAMToken(getApiToken())

    for node in nodes:
        untaintNode(iamToken, node)


untaintNodes()