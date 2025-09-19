import time
import os, shutil

import test_find_host_by_vsi
import test_list_hosts_by_region
import test_watsonx_usage
import test_external_usage
import test_find_x_in_y
import test_find_host_field
import test_find_host_by_instance
import test_list_hosts_by_region_live
import test_generate_hw_repair_report
import test_gpu_statistics
import test_elevation_builder
import test_zyphra_usage_report

import test_utils
from test_utils import testsPassed
from test_utils import testsFailed

# This is a very simple test harness that calls each test suite.
#
# I may want to use a library to support this functionality in the future, but
# for right now the needs are really simple so I'm sticking with this.

# We want to start by removing any old generated files in the test output directory that may be hanging around from previous test runs.
folder = 'test/output'
for filename in os.listdir(folder):
    file_path = os.path.join(folder, filename)
    try:
        if os.path.isfile(file_path) and (file_path.endswith('.yaml') or file_path.endswith('.csv') or file_path.endswith('.xlsx')):
            os.unlink(file_path)
    except Exception as e:
        print('Failed to delete %s. Reason: %s' % (file_path, e))


start = time.time()

assert test_zyphra_usage_report.runTests()
assert test_elevation_builder.runTests()
assert test_generate_hw_repair_report.runTests()
assert test_list_hosts_by_region_live.runTests()
assert test_find_host_by_instance.runTests()    
assert test_find_host_field.runTests()
assert test_find_x_in_y.runTests()
assert test_external_usage.runTests()    
assert test_watsonx_usage.runTests()
assert test_find_host_by_vsi.runTests()
assert test_list_hosts_by_region.runTests()
assert test_gpu_statistics.runTests()

testsPassed(time.time() - start)
