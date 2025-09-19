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

apiVersion=datetime.datetime.now().strftime('%Y-%m-%d')
parser = argparse.ArgumentParser(description='''Gets the details of a node from the operator API

python3 scripts/get_node.py wdc3-qz1-sr4-rk020-s12

''', formatter_class=RawTextHelpFormatter)

parser.add_argument('node', type=str, help='The nodes to get the details of.')

args = parser.parse_args()
node = args.node

def getNodeInfo(iamToken, node):
    endpoint = getEndpointFromNode(node)
    url = f'{endpoint}/operator/v1/nodes/{node}?version={apiVersion}&generation=2'
    headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + iamToken
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response_json = json.dumps(json.loads(response.content), sort_keys=True, indent=4)
        rich.print_json(response_json)
    elif response.status_code == 404:
        print(f'Unable to find node {node}')
    else:
        print(response)
        print(response.text)
        raise Exception('Unable to get node data.,n' + response.text)


getNodeInfo(getIAMToken(getApiToken()), node)