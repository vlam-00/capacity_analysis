import os
import json
from xml.dom.minidom import parse, parseString
import requests
import datetime
import argparse
from argparse import RawTextHelpFormatter
import urllib3
import progressbar
from progressbar import ProgressBar
from string import Template
from dataclasses import dataclass
from pathlib import Path
import rich

import capacity_utils
from capacity_utils import formatProfileClass
from capacity_utils import getIAMToken
from capacity_utils import getFastCosToken

apiVersion=datetime.datetime.now().strftime('%Y-%m-%d')
parser = argparse.ArgumentParser(description='''Gets the FAST logs from COS

python3 scripts/get_fastds_log.py CHG11153297

''', formatter_class=RawTextHelpFormatter)

parser.add_argument('cr', type=str, help='The CR to get the logs for')

args = parser.parse_args()
cr = args.cr

# Get the log ID for the CR
def getLogId(iamToken):
    url = f'https://s3.us.cloud-object-storage.appdomain.cloud/vpc-bundle-logs?list-type=2&prefix={cr}'
    headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + iamToken
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        dom = parseString(response.content)
        keys = dom.getElementsByTagName('Key')
        if len(keys) > 0:
            return keys[0].firstChild.nodeValue
        else:
            print(f'Unable to find the logs for {cr}')


    elif response.status_code == 404:
        print(f'Unable to find the logs for {cr}')
    else:
        print(response)
        print(response.text)
        raise Exception('Unable to get log data.,n' + response.text)

# Now that we have the key we can download the log file
def downloadLog(iamToken, key):
    print(f'Downloading log: {key}')
    url = f'https://s3.us.cloud-object-storage.appdomain.cloud/vpc-bundle-logs/{key}'
    headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + iamToken
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        if Path(key).is_file():
            print(f'\n\nERROR: The file {key} already exists.  Please move or rename it.')
        else:
            print(f'Writing file: {key}')
            with open(key, "wb") as f:
                f.write(response.content)

    elif response.status_code == 404:
        print(f'Unable to find the logs for {key}')
    else:
        print(response)
        print(response.text)
        raise Exception('Unable to get log data.,n' + response.text)

token = getIAMToken(getFastCosToken())
key = getLogId(token)
if key is not None:
    downloadLog(token, key)
