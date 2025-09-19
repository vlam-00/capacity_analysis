# Data Definitions

This page defined terms and data in capacity analysis for VPC.

## The v1 report

The [vpc-capacity-reports](https://ibm.ent.box.com/folder/160763914825) also known as the v1 report is generated every 30 minutes by the OPs Dashboard. This report contains data from the live running system including which servers are live or tainted.

## `platform-inventory`

The [`platform-inventory`](https://github.ibm.com/cloudlab/platform-inventory) repository is a set of YAML files in GitHub that contain information about all of the nodes in all mzones for VPC. This covers production and non-prod environments.

This shows additional nodes that don't show up in the v1 report like management and Acadia nodes.

These two pages show data from `platform-inventory`:

* [Inventory States](https://github.ibm.com/Zack-Grossbart/pmo-howto/blob/main/hardware/inventory_state.md) shows a breakdown of all the node roles in `platform-inventory` with counts and descriptions of the states.
* [Node Roles](https://github.ibm.com/Zack-Grossbart/pmo-howto/blob/main/hardware/node_roles.md) shows a breakdown of all of the node roles in `platform-inventory` with counts for each role.

## Delta list

The IMS Delta Server List shows all servers that are assigned to the VPC production account (`1187403`) and do not show up in the v1 report

You can access that list in the `IBM Cloud - VPC Server Utilization & Take Rate` report in [Kinaxis](https://na2.kinaxis.net/web/IBCP02_PRD01/saml2). 

_IMS Delta Server List appears to show items in Liquidation and Retired status. There will need to be some additional updates to the definitions to ensure this number is accurate and does not include assets that no longer exist_

## Hardware not assigned to the VPC account

This list, sometimes referred to as the ghost list, is hardware that in use by VPC that hasn't been assigned to the VPC account.  Some of these servers are in programs and aren't accounted for properly, others aren't currently being used.

## Totals

On 31-JUL-2024 here are the totals:

| Count | Notes |
|---|---|
| 4,118 | Servers in the delta list |
| 23,193 | VPC compute nodes in `platform-iventory` |
| 10,283 | Other nodes in `platform-inventory` |
| 7,620 | Not assigned to the account |
| **45,214** | **Total** |

## Buckets

Here are the buckets we want to use for the overall pie chart:

| Name | Notes |
|---|---|
| Compute capacity | All nodes in the `vpc_compute`, `vpc_compute_20_core`, `vpc_compute_bz2f`, `vpc_compute_ext`, `vpc_compute_net1`, `vpc_compute_net2`, `vpc_compute_no_class`, `vpc_compute_no_disk`, `vpc_compute_no_gpu`, and `vpc_compute_standard` roles in `platform-inventory` |
| Management | All nodes in the `k8_master`, `k8_worker`, `management`, `uc_qradar`, `vpc_control`, `vpc_edge`, `vpc_master`, `vpc_service`, `vpc_service_no_disk`, and `vpc_zonelet_control` roles in `platform-inventory` |
| Custom | All nodes in the `custom` role in `platform-inventory` |
| Bare Metal | All nodes in the `vpc_bare_metal` role in `platform-inventory` |
| Acadia | All nodes in the `vpc_acadia` and `vpc_acadia_publicEdge` roles in `platform-inventory` |
| Mixed use | All nodes in the `vpc_mixed_compute_control`, `vpc_mixed_compute_control_disk`, `vpc_mixed_compute_control_service`, `vpc_mixed_control_service`, `vpc_mixed_gpu_compute_control_service`, `vpc_mixed_service_compute` roles in `platform-inventory` |
| NGDC | All nodes in the `ngdc_cd_worker`, `ngdc_customer_dns`, `ngdc_customer_ntp`, `ngdc_generic_k8s_control`, `ngdc_generic_k8s_worker`, `ngdc_generic_k8s_worker_hsm`, `ngdc_hsm`, `ngdc_observability`, `ngdc_unassigned_server` roles in `platform-inventory` |
| Infrastructure | All nodes in the `vpc_observability`, `vpc_tekton`, `vpc_ve` roles in `platform-inventory` |
| Z | All nodes in the `compute` role in `platform-inventory` |
| Unknown | All nodes in the `unknown` role in `platform-inventory` |
| COS | All nodes in the `cos_accesser`, `cos_extra_storage`, `cos_kafka`, `cos_regular_storage`, `cos_slicestor` role in `platform-inventory` |
| SIE | All nodes in the `uc1-sie1_bastion`, `uc1-sie1_patient0`, `uc2-sie1_artifactory`, `uc2-sie1_k8worker_5_32`, `uc2-sie1_k8worker_9_64`, `uc2-sie1_kvm`, `uc2-sie1_kvmsec`, `uc2-sie1_windows` role in `platform-inventory` |
| Delta list | All nodes in the production and non-prod delta list once we've removed the nodes from `platform-iventory` |
| No assigned account | All the servers that look like they should be assigned to VPC that aren't in the VPC account |

# Using Excel to compare

## Filtering Data / Modifications to Source
IMS_DATA: Just both VPC accounts, NULL account, and account 1 hardware, remove bucket: Hardware Class: Liquidation/Retired   			
* (WHEN hardware.account_id IN (1187403, 1882813, 1) OR (hardware.account_id IS NULL))
* (WHEN status.id IN (15,20,21,27,29,41) OR hardware_status.status IN ("REALLOCATED"))

V1_Allocations_Prod: Text to Columns -> Column Y ("Inventory HWID")

## Data Model 
| Active |	Table 1 |	Cardinality |	Filter Direction |	Table 2 |
|---|---|---|---|---|
|Yes|	IMS_DATA [HARDWARE_HOSTNAME]|	Many to One (*:1)|	<< To IMS_DATA|	Platform_Inventory [hostname]|
|Yes| Platform_Inventory [hostname]|	Many to One (*:1)|	<< To Platform_Inventory|	V1_Allocations_Prod [Host Name]|

## Relevant Excel Comparison Formulas
| HEADER | QUERY |
|---|---|
|HWID ON V1|=IF(VLOOKUP([@[HARDWARE_ID]],V1_Allocations_Prod[[#All],[Inventory HWID]],1,FALSE),TRUE,FALSE)|
|HWID ON PI|=IF(VLOOKUP([@[HARDWARE_ID]],Platform_Inventory[[#All],[inventory_hwid]],1,FALSE),TRUE,FALSE)|
|IN IMS NOT PI|=IF(OR([@[ACCOUNT_ID_HARDWARE]]=1187403,[@[ACCOUNT_ID_HARDWARE]]=1882813), IF(ISNA([@[HWID ON PI]]),"MISSING FROM PI","ON PI"),"")|
|MISSING FROM V1 AND PI|=IF([@[IN IMS NOT V1]]="MISSING FROM V1", IF([@[IN IMS NOT PI]]="MISSING FROM PI", "MISSING",""),"")|
|PI HOSTNAME MATCH|=IFNA(VLOOKUP([@[HARDWARE_HOSTNAME]],Platform_Inventory[[#All],[hostname]],1,FALSE),"")|
|MISSING HOSTNAME|=IF(NOT([@[PI HOSTNAME MATCH]]=""), IF([@[MISSING FROM V1 AND PI]]="MISSING",TRUE,FALSE),FALSE)|
