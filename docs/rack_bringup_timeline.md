# Rack Bring Up State Transitions

This document shows how to find the state transitions of a rack during the bring up process.  We'll use `fra02-qz1-sr2-rk266` as an example.  This rack is part of a [composite rack](https://jiracloud.swg.usma.ibm.com:8443/issues/?jql=labels%20%3D%20MI300X%20and%20labels%20%3D%20FRA02).  

## What's in the rack

This rack is an MI300X rack and it contains the following hardware:

| ID | Hostname | Type | Date Racked |
|---|---|---|---|
| [3589406](https://internal.softlayer.com/Hardware/view/3589406) | `fra1-qz1-sr2-rk491-pdu-1` | PDU | 30-APR-2025 | 
| [3589414](https://internal.softlayer.com/Hardware/view/3589414) | `fra1-qz1-sr2-rk491-pdu-2` | PDU | 30-APR-2025 |
| [3583674](https://internal.softlayer.com/Hardware/view/3583674) | `fra1-qz1-sr2-rk491-s12` | WEBSVR | 08-APR-2025 | 
| [3583920](https://internal.softlayer.com/Hardware/view/3583920) | `fra1-qz1-sr2-rk491-s20` | WEBSVR | 08-APR-2025 |
| [3533564](https://internal.softlayer.com/Hardware/view/3533564) | `ngms266.sr02.fra02` | SWITCH | 08-APR-2025 |

The gear was ordered in the following POs:

| PO | Title | Create date | Date Locked |
|---|---|---|---|
| [147669231](https://internal.softlayer.com/HardwareLease/editHardwareLease/138114) | FRA02 - Networking Infrastructure Buy Ahead - Arista - 00260465 | 12-JAN-2025 | 06-FEB-2024|
| [164068260](https://internal.softlayer.com/HardwareLease/editHardwareLease/144794) | FRA02-Compute/Workloads: GPU/AI-Dell-28229198-G-FRA02-MDC: 7708173462 | 11-NOV-2024 | 26-FEB-2025 | 
| [165010218](https://internal.softlayer.com/HardwareLease/editHardwareLease/146674) | POC FRA02 - COMPUTE/WORKLOADS: GPU/AI - MI300X - SERVER TECH - Q4W4525: 7807492706 | 28-JAN-2025 | 24-MAR-2025 |

## Timeline

### 04-NOV-2024

* [CAPREQ-217: Rack space request for AMD MI300 GPU program in FRA02](https://jsw.ibm.com/browse/CAPREQ-217) created

**Source** - IBM Jira

### 11-NOV-2024

[NETENGREQ-23793: Fiber BOM: FRA02.SR02 for AMD GPU MI300 Fiber length & Optics Request

### 27-NOV-2024

* Racks allocated

**Source** - IBM Jira

### 09-DEC-2024

* [DCIDX-3054: FRA02](https://jiracloud.swg.usma.ibm.com:8443/browse/DCIDX-3054) created

**Source** - Cloud lab Jira

### 06-JAN-2025

* [DCIDX-3106: FRA02.SR02.RK266](https://jiracloud.swg.usma.ibm.com:8443/browse/DCIDX-3106) created
* [FRA02.SR02 Fiber Lengths](https://internal.softlayer.com/Ticket/ticketPreview/165194126) created

**Source** - Cloud lab Jira and IMS

### 27-JAN-2025

* CSM created and IMS ticket created for fiber order
* [FRA02.SR02 - Prod - AMD MI300 - Fiber, optics, CAT6 request - NETENGREQ-23793](https://internal.softlayer.com/Ticket/ticketEdit/165554538)

**Source** - SoftLayer and IMS

### 17-MAR-2025

* [NETCONF-25042: FRA02-QZ1-SR02-RK245,247,249,251,256,258,260,262,266,268,270,272,277](https://jira.softlayer.local/browse/NETCONF-25042) created

**Source** - SoftLayer Jira

### 24-MAR-2025

* POs are locked except for VBARs

**Source** - IMS

### 27-MAR-2025

* Last of the network gear received

**Source** - SoftLayer Jira

### 09-APR-2025

* [CHG10936055](https://watson.service-now.com/now/nav/ui/classic/params/target/change_request.do%3Fsys_id%3D42ef187193f0e6943a99317a7bba1023%26sysparm_stack%3Dchange_request_list.do%253fsysparm_query%253dactive%253dtrue%26sysparm_view%3DDefault%2Bview%26sysparm_view_forced%3Dtrue) - Fiber connected

**Source** - SoftLayer Jira and ServiceNow

### 24-APR-2025

* [SYS-36566: [NEW] AMD MI300x (x2) - fra1-qz1-sr2-rk266 (FRA02) (erk491)](https://jiracloud.swg.usma.ibm.com:8443/browse/SYS-36566) created
* Allocations completed
* Port mappings done

**Source** - Cloud lab Jira and [#41943](https://github.ibm.com/cloudlab/platform-inventory/pull/41943)

### 27-APR-2025

* VBARs arrive on site

### 30-APR-2025

All gear racked

**Source** - IMS

### 01-MAY-2025

* IMS updates and RIF completed

**Source** - IMS and [#42279](https://github.ibm.com/cloudlab/platform-inventory/pull/42279)

### 02-MAY-2025

* Rack passed SBB

**Source** - Cloud lab Jira

### 05-MAY-2025

* Switch configuration received

**Source** - SoftLayer Jira

### 07-MAY-2025

* Switch config completed

**Source** - Cloud lab Jira

### 08-MAY-2025

* Servers handed off for bring up

**Source** - Cloud lab Jira