# Capacity Analysis Automated Tests

This document covers details about the automated tests for the capacity analysis scripts.

## How to run the tests

Right now the tests are run manually.  Eventually it would be good run the tests in a pipeline, but we're not currently using PRs for these scripts since they're maintained by a single person.  It's easier to just run them manually before committing code.

To run the tests just run the following command:

```
python3 test/test_harness.py
```

If everything passes you'll see a message like this at the end of the test output:

```
=================================================
All tests passed ✓ in 10.2 seconds
=================================================
```

If the tests don't pass then you'll see an assertion with details about the tests that didn't pass.  

It's expected to run the tests before committing any code change.

## How the tests are structured

The tests all run from a main testing harness defined in [test/test_harness.py](test/test_harness.py).  This is a very simple harness that tracks the time of the test suite and then calls each suite individually.  Each suite defines a `runTests` function which must return a boolean `True` or `False`.

The test harness looks like this:

```python
start = time.time()

assert test_generate_hw_repair_report.runTests()
assert test_list_hosts_by_region_live.runTests()

testsPassed(time.time() - start)
```

## Defining tests

Tests are defined in the individual test suites.  Typically individual test suites, but that's not required.  

[test/test_find_x_in_y.py](test/test_find_x_in_y.py) is a good simple test suite to use as an example.

The `find_x_in_y.py` script finds instances of a string in a list of other strings so the test suite tests that functionality.  

The `runTests` function looks like this:

```python
def runTests():
    startSuite('Find X in Y')
    assert findXInY()

    return True
```

It starts by calling the `startSuite` function to print out information about the tests it will run and then asserts that the tests in the `findXInY` passed successfully.

That function is also very short:

```python
def findXInY():
    lines = runProc(['python3', 'scripts/find_x_in_y.py', 'test/inputs/x.txt', 'test/inputs/y.txt'])
    output = '\n'.join(lines)
    if val.strip() == output:
        printTestSuccess('Find X in Y')
        return True
    else:
        printTestFail(f'''Invalid results finding X in Y
Expected:
{val}

Found:
{output}''')
        return False
```

This calls the script with a well known input and test if the output matches what's expected.  The [inputs](inputs) directory contains files with well known data that we can use to run tests with expected results.    