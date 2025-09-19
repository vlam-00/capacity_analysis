import subprocess
from decimal import Decimal


# Print out that all tests pass and exit with return code 0
def testsPassed(time):
    d = Decimal(time)
    s = str(round(d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize(), 1))
    print('\n=================================================')
    print('All tests passed ' + '\033[92m' + u'\u2713' + '\033[0m' + f' in {s} seconds')
    print('=================================================')
    exit(0)

# Print out that some tests failed and exit with return code 1
def testsFailed():
    print('\n=================================================')
    print('One or more tests failed ' + '\033[91m' + 'X' + '\033[0m')
    print('=================================================')
    exit(1)

# Print a successful test
def printTestSuccess(text):
    print('\033[92m' + u'\u2713' + '\033[0m' + ' ' + text)

# Print a failed test with the expected value
def printTestFail(text, expected):
    print('\033[91m' + 'X' + '\033[0m' + ' ' + text)
    print(f'  Expected: {expected}')

# Print out the title at the start of a test suite
def startSuite(name):
    print(f'\n\033[1mStarting suite - {name}\033[0m')

# Run a sub-process using the specified arguments and return an array
# of each line returned from that process with the extra characters stripped
# from the start and end of each line.
def runProc(args):
    proc = subprocess.run(args,stdout=subprocess.PIPE,text=True)
    lines = proc.stdout.split('\n')
    return lines