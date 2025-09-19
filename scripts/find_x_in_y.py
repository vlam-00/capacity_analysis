import sys

import argparse
from argparse import RawTextHelpFormatter
from argparse import BooleanOptionalAction

parser = argparse.ArgumentParser(description='''Finds all lines from one file on another file.

This is useful when comparing lists.  For example, if you have a list of hosts
with a specific issue and you want to know how many of them are in a specific
profile class.

This will compare line by line and strips white space characters from the start
and end of the lines.

Examples:
python3 find_x_in_y.py hosts_with_issue.txt all_hosts_of_type.txt

''', formatter_class=RawTextHelpFormatter)

parser.add_argument('x', type=str, help='The path to the file containing the lines to look for')
parser.add_argument('y', type=str, help='The path to the file containing the lines to look in')

args = parser.parse_args()
xPath = args.x
yPath = args.y

def readLines(path):
    with open(path) as file:
        lines = [line.rstrip() for line in file]
        return lines
        
def findXInY():
    xLines = readLines(xPath)
    yLines = readLines(yPath)
    
    for line in xLines:
        if line in yLines:
            print(line)
            
findXInY()
