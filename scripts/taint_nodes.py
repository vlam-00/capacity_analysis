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
parser = argparse.ArgumentParser(description='''Taint a list of nodes

This utility uses the operator API to taint a list of nodes

python3 scripts/taint_nodes.py wdc3-qz1-sr4-rk020-s12,wdc3-qz1-sr4-rk021-s34 triage SYS-32614

''', formatter_class=RawTextHelpFormatter)

parser.add_argument('nodes', type=str, help='The nodes to taint.')
parser.add_argument('reason', type=str, help='The reason for tainting the node.  This can be reserve, triage, or decommission.')
parser.add_argument('context', type=str, nargs='?', help='The context for tainting the node.  This must be a string of letters follow by numbers like FLT-11111 or CHG00000000.')


args = parser.parse_args()
nodes = args.nodes.split(',')
reason = args.reason
context = args.context

def taintNode(iamToken, node, reason, context):
    print(f'Applying taint for {node}')
    endpoint = getEndpointFromNode(node)
    url = f'{endpoint}/operator/v1/operator_actions?version={apiVersion}&generation=2'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + iamToken
    }

    payload = {
        "action": {
            "type": "taint",
            "target": {
                "id": node
            },
            "parameters": {
                "taint_reason": reason
            }
        },
        "name": f'taint-{node}-{timestamp()}'
    }

    if context == None:
        # You don't have to specify a reason for the taint when it's a reserve
        if reason != 'reserve':
            print('ERROR: Tainting a node requires a context if the reason is not reserve.')
            exit(-1)
    else:
        payload['context'] = context


#    rich.print_json(json.dumps(payload, sort_keys=True, indent=4))
#    return

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code != 201:
        print(response)
        print(response.text)
        raise Exception('Unable to taint node.,n' + response.text)
    else:
        print(f'Taint successfully submitted for {node}\n')

def taintNodes():
    iamToken = getIAMToken(getApiToken())

    for node in nodes:
        taintNode(iamToken, node, reason, context)


taintNodes()