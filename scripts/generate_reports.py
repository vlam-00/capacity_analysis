import os
import json
import requests
import datetime
import argparse
from argparse import RawTextHelpFormatter
import subprocess
import cu_accounts
import capacity_utils
from capacity_utils import getInstancesFile
from capacity_utils import getHostsFile
from pathlib import Path
home = Path.home()


parser = argparse.ArgumentParser(description='''Generates all reports in one command.

This script expects the Hosts and Instances CSV files for the current date to be in a directory
named output relative to the current execution path.

python3 scripts/generate_reports.py

''', formatter_class=RawTextHelpFormatter)

args = parser.parse_args()


# Generate the Red Hat usage report
def generateRedHatUsage():
    print('Generating Red Hat usage report')
    subprocess.run(['python3',
                    'scripts/generate_watsonx_usage.py',
                    getInstancesFile(),
                    'output/redhat_gpu_usage.csv',
                    ','.join(cu_accounts.redHatAccounts)])

# Generate the Adapt usage report
def generateAdaptUsage():
    print('Generating a-d-a-p-t.ai LLC usage report')
    subprocess.run(['python3',
                    'scripts/generate_watsonx_usage.py',
                    getInstancesFile(),
                    'output/adaptai_gpu_usage.csv',
                    ','.join(cu_accounts.adaptAccounts)])

# Generate the InstructLab usage report
def generateInstructLabUsage():
    print('Generating InstructLab usage report')
    subprocess.run(['python3',
                    'scripts/generate_watsonx_usage.py',
                    getInstancesFile(),
                    'output/instructlab_gpu_usage.csv',
                    ','.join(cu_accounts.instructLabAccounts)])

# Generate the Research usage report
def generateResearchUsage():
    print('Generating Research usage report')
    subprocess.run(['python3',
                    'scripts/generate_watsonx_usage.py',
                    getInstancesFile(),
                    'output/ibm_research_gpu_usage.csv',
                    ','.join(cu_accounts.researchAccounts)])

# Generate the Intel usage report
def generateIntelUsage():
    print('Generating Intel usage report')
    subprocess.run(['python3',
                    'scripts/generate_watsonx_usage.py',
                    getInstancesFile(),
                    'output/intel_gpu_usage.csv',
                    ','.join(cu_accounts.intelAccounts)])

# Generate the AMD usage report
def generateAMDLabUsage():
    print('Generating AMD usage report')
    subprocess.run(['python3',
                    'scripts/generate_watsonx_usage.py',
                    getInstancesFile(),
                    'output/amd_gpu_usage.csv',
                    ','.join(cu_accounts.amdAccounts)])

# Generate the WCA usage report
def generateWCALabUsage():
    print('Generating WCA usage report')
    subprocess.run(['python3',
                    'scripts/generate_watsonx_usage.py',
                    getInstancesFile(),
                    'output/watson_code_assistant_gpu_usage.csv',
                    ','.join(cu_accounts.wcaAccounts)])

def generatevGPUCloudLabUsage():
    print('Generating vGPU Cloud usage report')
    subprocess.run(['python3',
                    'scripts/generate_watsonx_usage.py',
                    getInstancesFile(),
                    'output/vgpu_cloud_gpu_usage.csv',
                    ','.join(cu_accounts.vgpuCloudAccounts)])

# Generate the Watsonx Orchestrate usage report
def generateWatsonxOrchestrateUsage():
    print('Generating Watsonx Orchestrate usage report')
    subprocess.run(['python3',
                    'scripts/generate_watsonx_usage.py',
                    getInstancesFile(),
                    'output/watsonx_orchestrate_gpu_usage.csv',
                    ','.join(cu_accounts.watsonOrchestrateAccounts)])

# Generate the TechZone usage report
def generateTechZoneUsage():
    print('Generating TechZone usage report')
    subprocess.run(['python3',
                    'scripts/generate_watsonx_usage.py',
                    getInstancesFile(),
                    'output/techzone_gpu_usage.csv',
                    ','.join(cu_accounts.techZoneAccounts)])

# Show the internal Gaudi 3 usage
def showInternalGaudi3Usage():
    subprocess.run(['python3',
                    'scripts/find_internal_gaudi3.py',
                    'gx3d-208x1792x8mi300x,gx3d-160x1792x8gaudi3'])

# Generate the GPU stats
def generateGPUStats():
    print('Generating GPU Statistics')
    subprocess.run(['python3',
                    'scripts/generate_gpu_stats_report.py'])

# Show servers in hardware repair
def showHWReport():
    subprocess.run(['python3',
                    'scripts/generate_hw_repair_report.py',
                    f'{home}/work/platform-inventory',
                    'gx3d-h100-smc,gx3d-h200-smc,gx3d-gaudi3-dell,gx3d-mi300x-dell,gx2-a100'])

# Generate the Watsonx usage report
def generateWatsonxUsage():
    print('Generating Watsonx usage report')
    subprocess.run(['python3', 'scripts/generate_watsonx_usage.py', getInstancesFile(), 'output/watsonx_gpu_usage.csv'])

# Generate the time series data for Watsonx
def generateWatsonxTimeseries():
    print('Generating Watsonx time series')
    subprocess.run(['python3', 'scripts/generate_usage_timeseries.py', '14'])

# Generate the internal and external GPU usage report
def generateInternalExternalUsage():
    print('Generating Internal and External usage report')
    subprocess.run(['python3', 'scripts/generate_external_gpu_usage.py', getInstancesFile(), getHostsFile(), 'output/internal-external-gpu-usage-2.csv'])

    print('Generating Internal and External usage report by DC')
    subprocess.run(['python3', 'scripts/generate_external_gpu_usage.py', getInstancesFile(), getHostsFile(), 'output/internal-external-gpu-usage-2-zone.csv', '-byZone'])


generateInternalExternalUsage()
generateTechZoneUsage()
generateAdaptUsage()
generateIntelUsage()
generateResearchUsage()
generatevGPUCloudLabUsage()
generateWCALabUsage()
generateAMDLabUsage()
generateWatsonxOrchestrateUsage()
generateWatsonxUsage()
generateInstructLabUsage()
generateRedHatUsage()
generateGPUStats()
generateWatsonxTimeseries()
showInternalGaudi3Usage()

#showHWReport()