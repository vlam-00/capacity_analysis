# Global Report

This page shows the requirements for a new global report that we want to get from Kinaxis showing all of the servers we have in VPC.  This report would need to show quantities for the following categories:


| Category | Type | Service | Notes |
| --- | --- | --- | --- |
| VPC Compute | Sellable | Compute | All servers in the `platform-inventory` allocations that are in the list below in the production mzones. |
| VPC Development   | Overhead    | N/A     | All servers in the `platform-inventory` allocations that are in the list below in the non-production mzones. |
| VPC Control Plane | Overhead    | N/A     | All servers in the `platform-inventory` allocations that are in the list below. |
| Acadia            | Sellable    | Storage | All servers in the `platform-inventory` allocations that are in the `vpc_acadia` or `vpc_acadia_publicEdge` roles in the production mzones. |
| Acadia Dev        | Overhead    | Storage | All servers in the `platform-inventory` allocations that are in the `vpc_acadia` or `vpc_acadia_publicEdge` roles in the non-production mzones. |
| NGDC Undercloud   | Overhead    | Fabric  | All servers in the `platform-inventory` allocations that are in the undercloud roles in all mzones. |
| NGDC COS          | Sellable    | Storage | I don't know how to identify these. |
| NGDC COS Dev      | Sellable    | Storage | I don't know how to identify these. |
| Anything else     |             |         | Any server in all VPC accounts or servers that should be in the VPC account that aren't in any of the other categories. |


## Notes

* We want to skip all servers in the `plan` or `open` `inventory_state` in `platform-inventory` since they don't represent actual servers.


## List of VPC Compute roles

* `vpc_bare_metal`
* `vpc_compute`
* `vpc_compute_20_core`
* `vpc_compute_bz2f`
* `vpc_compute_elba2`
* `vpc_compute_ext`
* `vpc_compute_net1`
* `vpc_compute_net2`
* `vpc_compute_no_class`
* `vpc_compute_no_disk`
* `vpc_compute_no_gpu`
* `vpc_compute_research`
* `vpc_compute_standard`

## List of VPC Development roles

This list contains everything from the VPC Compute roles as well as the following roles:

* `vpc_mixed_compute_control`
* `vpc_mixed_compute_control_disk`
* `vpc_mixed_compute_control_service`
* `vpc_mixed_control_service`
* `vpc_mixed_gpu_compute_control_service`
* `vpc_mixed_service_compute`

## List of Control Plane roles

* `k8_master`
* `management`
* `vpc_control`
* `vpc_edge`
* `vpc_master`
* `vpc_zonelet_control`

## List of Undercloud roles

* `uc1-sie1_bastion`
* `uc2-sie1_artifactory`
* `uc2-sie1_k8worker_5_32`
* `uc2-sie1_k8worker_9_64`
* `uc2-sie1_kvm`
* `uc2-sie1_kvmsec`
* `uc2-sie1_windows`
* `uc_qradar`