# How many servers do we really have?

The document shows the effort to reconcile the available servers between IMS and VPC. This effort will:

* Determine how many servers we have _on the floor_ that could be deployed into VPC
* Reconcile the 4,200 servers in the `IMS Delta Server Count`
* Make recommendations for improving the processes we use to manage this asset inventory

## IMS Delta Server List

All servers for classic and VPC have records in IMS.  These records are created when a server arrives at a data center and is first scanned.  Servers assigned to VPC are added to the `1187403` account for production and staging and `1882813` for integration and development.  

The OPs dashboard generates a [`vpc-capacity-report`](https://ibm.ent.box.com/folder/160763914825) every 30 minutes that shows all of the compute resources.  Any server that's assigned to the production account and not in the capacity report shows up on the **IMS Delta Server List**.  That list hovers around 4,200 servers.  

This document breaks down that 4,200 number, shows where those servers come from, and makes recommendations for how we can improve this process.

## Where does 4,200 come from?

One 10-JUL-2024 there were 4,288 servers in the `IMS Delta Server Count` list in [Kinaxis](https://na2.kinaxis.net/web/IBCP02_PRD01/saml2).  This list shows all servers that are:

* Assigned to the VPC production account
* Not listed in the capacity report from the Operations Dashboard

This number fluctuates a little day by day, but hovers around 4,200.

| Label | Count | Notes | Action |
|---|---|---|---|
| **Total** | **4,288** | |
| 1U servers | 1,899 | These are mostly Broadwell and too old to deploy to production | We need to move these to liquidation or retirement |
| Acadia | 787 | These servers are used in the Acadia project | We're going to add these to a separate Acadia bucket. |
| Management | 737 | These are management rack servers.  Some of the are also 1U. | We're going to add these to a separate management bucket. |
| 8U servers | 357 | These are H100 servers that are in the process of getting deployed | We need to add to allocations as soon as they're purchased. |
| Reserved | 293 | These are reserved for a specific program and in the process of installation | These servers should be added to allocations as soon as the order is confirmed. |
| qRadar | 62 | These servers run the qRadar service | We're going to add these to a separate management bucket. |
| Hardware failure | 31 | These would need some repair before they could be deployed | We should diagnose these servers and either fix them or get them back in the fleet.
| Retired, liquidations, or decommission | 11 | These can never be deployed | No actions needed. |
| Missing parts | 5 | We've identified many more in this state and are updating IMS | We've found many more  servers that are missing parts, but aren't in the correct status.  We're working to resolve that. |
| Quarantine | 3 | Waiting for repairs | No actions needed. |
| Unknown | 103 | This leaves 103 unknown servers. | We're still working on these. |

**Note**: These numbers are a little off since some servers are counted in multiple buckets.  We need to do a little more work in Kinaxis to fix that issue.

## Conclusions so far

We've identified about 4,100 of the 4,200 in the delta server list.  We're working on integrating that into Kinaxis so we can automate this process moving forward.  Based on our experiences with this effort we've identified the following conclusions and next steps:

### 7,620 that are meant for VPC aren't assigned to VPC accounts

There are currently two accounts associated with the VPC project in IMS (one for production and one for non-prod).  Not all servers associated with VPC are in those two accounts.  We ran a query looking for servers that have comments containing keywords like `VPC` or `NextGen` which indicate they should be assigned to VPC accounts, but are not assigned to either of the VPC accounts.

On 29-JUL-2024 were 5,395 servers in this state.  Those servers are in many different states.  Some are broken, some are healthy severs which aren't being used, and some are assigned to programs.  We don't have visibility to track any of them.  Some people call this the ghost list.

We must change our procedures to ensure that VPC servers are assigned to the correct accounts and can be tracked.

More data about these servers in the <a href="#vpc-servers-that-arent-in-the-vpc-accounts">VPC servers that aren't in the VPC accounts</a> section of this document.

### We need to add servers to allocations as soon as they're scanned

Right now we don't add servers to the allocations in `platform-inventory` until relatively late in the process.  That means we lose visibility into servers that are in the bring up process.  This accounts for the 357 8U servers in the delta list as well as many others.

`platform-inventory` supports multiple [`inventory_states`](https://github.ibm.com/Zack-Grossbart/pmo-howto/blob/main/hardware/inventory_state.md) where we could track this, but we aren't using them effectively.

This will require a fundamental change to the VPC hardware bring up workflow.  We're just starting on a design for an improvement to this process.

### IMS data clean up

We need to clean up data in IMS.  We found over 550 servers with missing CPUs that weren't in the `MISSING_PARTS` status.  We've found many servers that are broken, unused, or in transit, but still in `ACTIVE` status.  We need to clean up data in IMS and clean up our process so we don't keep adding bad data.

Zack and Neil are working with DCOps to get these cleaned up in IMS.  We still need to design the process improvements to make sure we don't get into this state in the future.

### IMS and `platform-inventory` are out of sync

Right now keeping IMS and `platform-inventory` in sync is a collection of processes without a central organization point.  Some are completely manual and some use custom tools that are run manually.  We've found many cases where IMS and `platform-inventory` are out of sync.  This results in servers that are listed as active in one system and decommissioned in another.  It also results in servers getting lost between the two systems.  The many servers that were meant to be assigned to VPC and aren't in the VPC production account are examples of this issue.  

We're in the process of designing a fix for this issue.

### We need to drive consistency in `platform-inventory`

The YAML files in the [`platform-inventory`](https://github.ibm.com/cloudlab/platform-inventory) repository are essentially a database of all of the servers that are allocated to VPC, where they're located, their state, and what role they play in the VPC environment ...or at least they should be.  Right now they're edited by hand as well as a handful of custom tools.  We need a formalized tool to manage hardware in VPC that forces referential consistency and a process that ensures we have well known [deployment types](https://github.ibm.com/cloudlab/platform-inventory/tree/master/region/deployments#deployment-types) as well as other issues.

This tool will ensure:

* Consistency
* Error detection and prevention
* Referential integrity
* Reduced management time

In addition, this tool is required before we can move to [Netbox](https://github.com/netbox-community/netbox) since we can't move to a different data source until we can abstract and ensure the consistency of `platform-inventory`.

The [NextGen Zone Availability Board](https://9.208.144.219:8500/servers) covers some of this area, but doesn't come close to providing a comprehensive management solution.

We're just starting to design a solution here.

### We need to extend Kinaxis to cover `platform-inventory`

Our delta list is made up of servers that are assigned to one of the VPC accounts, but don't have a hardware ID that shows up in specific fields in the `platform-inventory` repository.  This does a good job of finding servers that are in the VPC fleet, but it misses out on other [deployment types](https://github.ibm.com/cloudlab/platform-inventory/tree/master/region/deployments#deployment-types) like Acadia or management racks in the examples below.

We need to review all of the deployment types and make sure we can track them correctly in Kinaxis.  This will require integrating `platform-inventory` as a datasource for Kinaxis.  We've already developed [code](https://github.ibm.com/cloudlab/platform-inventory/blob/master/scripts/nodes_to_csv.py) that can pull data out of `platform-inventory` and we're in the process of automating this and pulling it into Kinaxis.

## Data details and breakdown

This section shows the details and breakdown of the data above.  It also shows examples of servers in the specific categories from above.

### Data from IMS

By looking at Cognos and IMS, we have 4,200 hundred servers assigned to VPC that aren't available to customers in Kinaxis.  This number is the number of servers that are assigned to VPC accounts in IMS, but aren't available in the allocations in the [`platform-inventory`](https://github.ibm.com/cloudlab/platform-inventory) repository.  

This number fluctuates every day, but hovers around 4,200.  This number accurately shows the number of servers that we have which aren't in use as capacity.  These servers can be in many different states.  For example:

* Missing parts
* Broken hardware
* In process of getting deployed
* Being cross shipped

We need to break down this 4,200 number into buckets so we can get more insight into where they servers are and how the process is working.


### Data from hardware PMs

I talked to Gabe Toney and Neil Smith about this and they gave a very different number.  

Gabe estimates that there are under 100 and probably under 50 servers that are assigned to VPC and sitting on the floor that are assigned to VPC in all regions.  He says he can verify that there are no extra servers in this category in TOK, SAO, OSA, and many WDC and DAL zones.  He can't back that up with data right now.

We also have a lot of capacity that's racked for projects, but not available to customers yet.  Gabe says we have about 40 racks worldwide like that.  Some of those racks are stalled for parts like fiber or structured fiber.  We're going to be pulling from that pool to cover the 60 racks we need for Citi.

Somer needs 1,300 servers for staging.

Gabe thinks that we will use up all of our excess servers and still need more to meet the needs of IKS in staging and Citi.  Neil verifies that belief.

### VPC servers that aren't in the VPC accounts

All servers in VPC should be assigned to one of the VPC accounts in IMS.  However, sometimes servers are use in VPC or earmarked from VPC and not assigned to an account.  We look for those questions with the following logic:

> Find all servers with no associated account where the terms `nextgen`, `genesis`, or `vpc` show up in the `Status Reason` or `Internal Note` fields.

That logic results in the following SQL query in the Kinaxis DB2 database (the database containing extracted data from IMS > Cognos):

```sql
SELECT *
FROM LANDING.HARDWARE_SOURCE t1
         left join landing.VPC_IMS_ACCOUNT_ID t2 on t1.IMS_ACCOUNT_ID = t2.IMS_ACCOUNT_ID
WHERE DATE = '7/28/2024'
  and t2.IMS_ACCOUNT_ID is null
  and hardware_type = 'Server'
  and ((lower(HARDWARE_STATUS_REASON) like '%nextgen%' or lower(HARDWARE_STATUS_REASON) like '%vpc%' or
        lower(HARDWARE_STATUS_REASON) like '%genesis%')
    or (lower(LAST_HARDWARE_NOTE) like '%nextgen%' or lower(LAST_HARDWARE_NOTE) like '%vpc%' or
        lower(LAST_HARDWARE_NOTE) like '%genesis%'))
```

That query returns 5,396 servers.

1,877 of those servers are 1U which indicates that they're older servers that aren't useful in our current environment.  An additional 204 are in either `Liquidation` or `Liquidate_Prep`. That leaves 3,315 servers on this list.

Here are some examples of servers that are part of active programs:

| Location | Location Path | Hardware Status | Hardware Internal Serial | Chassis Vendor | Processor Description | Notes |
|---|---|---|---|---|---|---|
| EU | fra04.sr04 | Reserved | [SL01KUV3](https://internal.softlayer.com/Hardware/view/3508869) | SuperMicro | XEON-8260-Cascade-Lake | Reserved for Citi Uni T1 cross shipments. Do not touch without approval from Neil Smith / Malcolm Ware |
| Americas | dal12.sr02.rk551.sl39 | Reserved | [SL01HL8T](https://internal.softlayer.com/Hardware/view/3139504) | SuperMicro | Xeon-Cascade-Lake / 6248 | Missing drives |
| Americas | mon04.sr02.rk21.sl49 | Reserved | [LS00132S](https://internal.softlayer.com/Hardware/view/3552145) | Lenovo | Xeon-Sapphire-Rapids / 8474C-PLATINUM | Reserved for MON04 NGDC buildout: https://jiracloud.swg.usma.ibm.com:8443/browse/DCIDX-1852 |
| Americas | wdc07.sr01.rk190.sl33 | Inventory | [LS000BIM](https://internal.softlayer.com/Hardware/view/3486371) | Lenovo |Xeon-Sapphire-Rapids / 8474C-PLATINUM | Updating status from Planned, NextGen to Inventory, per Status Change Request ticket 161061033 |
| Americas | dal10.sr02.rk258.sl15 | Planned | [SL01KE1L](https://internal.softlayer.com/Hardware/view/3425943) | SuperMicro |Xeon-Cascade-Lake / 8260-PLATINUM | X-Ship https://internal.softlayer.com/Ticket/ticketPreview/162086991 - NG Urgent Need - these are in front of SR02 cause no room in LPR |

These examples are likely available capacity. These are all in the `PLANNED` hardware status:

| Location | Location Path | Hardware Internal Serial | Chassis Vendor | Processor Description | Notes | Last change |
|---|---|---|---|---|---|---|
| Americas | wdc07.sr02 | [SL01LLDL](https://internal.softlayer.com/Hardware/view/3437458) | SuperMicro | Xeon-Cascade-Lake / 8260-PLATINUM | Received order from dal07 per shipment ID 1083564 | 09-JUL-2024 |
| Americas | dal07.str03.strlane 03 | [SL01HBAV](https://internal.softlayer.com/Hardware/view/3442680) | SuperMicro | Xeon-Cascade-Lake / 8260-PLATINUM | Converting BX2D to BX2 by removing 2 X 3.2 TB SSDs. | 15-NOV-2023 |
| Americas | dal07.str03.strlane 04 | [SL01D95W](https://internal.softlayer.com/Hardware/view/3439394) | SuperMicro | Xeon-Cascade-Lake / 8260-PLATINUM | Updating to current location. Please see Justin B's note ACAIDA BACKFILL, THIS SHOULD ONLY BE USED FOR ACADIA | 26-JUL-2024 |
| Americas | dal07.str03.strlane 05 | [SL01LRJ3](https://internal.softlayer.com/Hardware/view/3388546) | SuperMicro | Xeon-Cascade-Lake / 8260-PLATINUM | adding ram, procs, and nics to create a BX2 server | 18-AUG-2023 |
| Americas | dal07.str03.strlane 05 | [SL01LV7W](https://internal.softlayer.com/Hardware/view/3437204) | SuperMicro | Xeon-Cascade-Lake / 8260-PLATINUM | NextGen unallocated | 18-AUG-2023 |
| Americas | dal07.str03.strlane 05 | [SL01CY8X](https://internal.softlayer.com/Hardware/view/3117532) | Lenovo | Xeon-Cascade-Lake / 8260-PLATINUM | PLANNED for DAL14 per https://internal.softlayer.com/Ticket/ticketPreview/153962590 | 12-JUN-2024 |
| Americas | dal10.sr01.rk268.sl17 | [SL01CY8X](https://internal.softlayer.com/Hardware/view/3117532) | SuperMicro | Xeon-Cascade-Lake / 8260-PLATINUM | Received order from dal07 per shipment ID 1078938 | 24-JAN-2024 |
| Americas | dal10.sr01.rk268.sl19 | [SL01LYX2](https://internal.softlayer.com/Hardware/view/3492833) | SuperMicro | Xeon-Cascade-Lake / 8260-PLATINUM | Received order from dal07 per shipment ID 1078938 | 24-JAN-2024 |
| Americas | dal10.sr01.rk268.sl49 | [SL01HL7P](https://internal.softlayer.com/Hardware/view/3139368) | SuperMicro | Xeon-Cascade-Lake / 8260-PLATINUM | Received order from dal07 per shipment ID 1078938 | 24-JAN-2024 |
| EU | lon04.sr06 | [SL01K4PO](https://internal.softlayer.com/Hardware/view/3404614) | SuperMicro | Xeon-Cascade-Lake / 8260-PLATINUM | NG2 Loose Inventory | 11-APR-2022 |
| Americas | pok01.sr01.rk43.sl23 | [SL01J54C](https://internal.softlayer.com/Hardware/view/3026602) | SuperMicro | Xeon-Cascade-Lake / 8260-PLATINUM | Received order from wdc07 per shipment ID 925174 | 25-JUN-2024 |
| Americas | tor05.sr02 | [SL01M31I](https://internal.softlayer.com/Hardware/view/3495359) | SuperMicro | Xeon-Cascade-Lake / 8260-PLATINUM | Received order from mad05 per shipment ID 1089735 | 27-JUN-2024 |
| Americas | wdc06.sr01 | [LS000BQB](https://internal.softlayer.com/Hardware/view/3528010) | Lenovo | Xeon-Sapphire-Rapids / 8474C-PLATINUM | Hardware set as leased asset | 14-FEB-2024 |
| Americas | wdc06.sr02 | [LS000BV1](https://internal.softlayer.com/Hardware/view/3543640) | SuperMicro | Xeon-Cascade-Lake / 8260-PLATINUM | Updated to Planned per ticket - https://internal.softlayer.com/Ticket/ticketEdit/161016419 | 20-MAY-2024 |

#### Update

We were unable to follow all status reasons because of [#762: Incorrect status reason for Hardware 3425803 and 3379546](https://github.ibm.com/bluemixanalytics/Analytics-IaaS-Deliverables/issues/762). This bug was fixed and we were able to track down more servers in this category.  The new number is 7,620.

Of those 7,620 we've found 417 of them in `platform-inventory`.

### Stella's hardware report

Stella has a report that's generated from Cognos/IMS once a week that shows this.  She's sent me the latest copy of the report and I still need to go through it.  This report is automatically generated and was created for her by Mike Gale.  It shows Cascade Lake servers from both classic and VPC. 

Based on the hardware report from 24-JUN-2024 we can track down some individual servers that should be assigned to VPC and aren't in the VPC accounts.

#### SMC Server SL01LSZD

| Row | Location | Datacenter | Location Path | Hardware Status | Hardware Internal Serial | Hardware Type | Chassis Vendor | Processor Description | 
|---|---|---|---|---|---|---|---|---|
| 32 | Americas | DAL07 | dal07.spr02 | Inventory | [SL01LSZD](https://internal.softlayer.com/Hardware/view/3379546) | Server | SuperMicro | XEON-8260-Cascade-Lake |

This server was first scanned on 26-APR-2022.  The current age is two years and two months.  The Status Reason is `Inventory - NextGen`.

The server was first stored in DAL10 and was cross shipped to DAL07 on 18-AUG-2023.

The server is sat in DAL07 spare parts room 02 for 11 months until 10-JUL-2024 when it was tested and the `Internal Note` was updated to:

> this chassis is hardfailed it had issues when testing or posting 

This is not part of the 4,200 since it isn't in the VPC account, but it is allocated to VPC in the comments.

#### SMC Server SL01LZ5X

| Row | Location | Datacenter | Location Path | Hardware Status | Hardware Internal Serial | Hardware Type | Chassis Vendor | Processor Description | 
|---|---|---|---|---|---|---|---|---|
| 368 | Americas | DAL07 | dal07.str02 | Inventory | [SL01LZ5X](https://internal.softlayer.com/Hardware/view/3425803) | Server | SuperMicro | Unknown |

This server was first scanned on 20-OCT-2022.  The current age is one year and 8 months.

The server was cross shipped from WDC04 to DAL07.

The server is now listed as located in DAL10 storage room two.  This indicates that the server chassis is available, but may not contain any processors.  

This is not part of the 4,200 since it isn't in the VPC account, but it is allocated to VPC in the comments.

#### SMC Server SL01M3ZQ

| Row | Location | Datacenter | Location Path | Hardware Status | Hardware Internal Serial | Hardware Type | Chassis Vendor | Processor Description | 
|---|---|---|---|---|---|---|---|---|
| 4751 | Americas | DAL10 | dal10.sr01 | Inventory | [SL01M3ZQ](https://internal.softlayer.com/Hardware/view/3459278) | Server | SuperMicro | XEON-8260-Cascade-Lake |

This server was first scanned on 26-JAN-2024.  The current age is one year and five months.

This server was removed from the rack on 14-MAR-2024 as part of ticket [159723608](https://internal.softlayer.com/Ticket/ticketPreview/159723608).  The comment was:

>  Remove 22 existing broke servers and install 13 OX2 servers

This server is now in DAL10 storage room one and is likely broken.  We would need to investigate this server and see if it was repairable before we could add it to the capacity pool.

This is not part of the 4,200 since it isn't in the VPC account, but it is allocated to VPC in the comments.

### Delta server list examples

These servers do show up in our `IMS Delta Server Count` list in Kinaxis.

#### SMC Server SL01LD0S

| Location | Datacenter | Location Path | Hardware Status | Hardware Internal Serial | Hardware Type | Chassis Vendor | Processor Description | 
|---|---|---|---|---|---|---|---|
| Americas | DAL12 | dal12.sr02 | Active | [SL01LD0S](https://internal.softlayer.com/Hardware/view/3181958) | Server | SuperMicro | XEON-8260-Cascade-Lake |

This server was first scanned on 05-FEB-2021.  It's three years and five months old.

This server was in a rack at location `dal2-qz1-sr2-rk076-s04` and was removed as part of [SYS-20274: OX2 - DAL12 - Remove and Replace](https://jiracloud.swg.usma.ibm.com:8443/browse/SYS-20274).  

It's listed with internal notes of `Planned for NextGen-2 EXP-DAL MZR` and has a status of `ACTIVE` even though it isn't active.  It's been in that state and unused since 02-APR-2024.

The state of this server is unclear.  Sometimes servers in this state were removed because there was a hard fail. In this case they should be in the `hardfail` state and get diagnosed and possibly returned to the vendor for repair.  It's possible they didn't update that state.  Other times this is fully working and ready for use which means it should be in the `planned` state.  

In this case the Jira ticket above indicates that there was a problem with the server and it should be in the `hardfail` state.  We're fixing this specific instance, but there are others and we need a good way to find them programatically.  

This server is still in an `inventory_state` of `production` in `platform-inventory`.

#### SMC Server SL01LRGC

| Location | Datacenter | Location Path | Hardware Status | Hardware Internal Serial | Hardware Type | Chassis Vendor | Processor Description | 
|---|---|---|---|---|---|---|---|
| Americas | DAL12 | dal12.sr02 | Active | [SL01LRGC](https://internal.softlayer.com/Hardware/view/3320298) | Server | SuperMicro | XEON-8260-Cascade-Lake |

This server was first scanned on 06-JAN-2022 and is two years and six months old.

This server is listed as rack location `dal12.sr02.rk113.sl41`.  It's listed in the [`dal2.qz1.sr2.rk113.yaml`](https://github.ibm.com/cloudlab/platform-inventory/blob/master/region/rif/dal2.qz1.sr2.rk113.yaml#L181) and [`dal2-qz1.yaml`](https://github.ibm.com/cloudlab/platform-inventory/blob/master/region/allocations/dal2-qz1.yaml#L5128) in the platform inventory, but it's not in an mzone, it's not in the capacity report, and the hardware ID doesn't show up anywhere in `platform-inventory`.

This server has been marked as `RESERVED` and `ACTIVE` since 10-NOV-2023.  This is a management rack server in active use at `dal2-qz1-sr2-rk113-s10`.  We need to improve our tracking of this server on the Kinaxis side.

There are 737 nodes with the `management` role and all of the ones I've checked are in the delta list.  `dal3-qz1-sr1-rk311-s40` and `dal1-qz1-sr3-rk201-s06` are examples of this.

#### SMC Server SL01LZD1

| Location | Datacenter | Location Path | Hardware Status | Hardware Internal Serial | Hardware Type | Chassis Vendor | Processor Description | 
|---|---|---|---|---|---|---|---|
| Americas | WDC06 | wdc06.sr01.rk12.sl39 | Active | [SL01LZD1](https://internal.softlayer.com/Hardware/view/3413445) | Server | SuperMicro | XEON-8260-Cascade-Lake |

This server was first scanned on 14-SEP-2024 and is one year and 10 months old.  

This server is currently deployed in production and in use at `wdc2-qz1-sr1-rk012-s12`.  It's listed in `platform-inventory` in [`wdc1-qz1.yaml`](https://github.ibm.com/cloudlab/platform-inventory/blob/master/region/allocations/wdc2-qz1.yaml#L8) and in [`wdc2.qz1.sr1.rk012.yaml`](https://github.ibm.com/cloudlab/platform-inventory/blob/master/region/rif/wdc2.qz1.sr1.rk012.yaml#L100).  The hardware ID for this server (`3413445`) doesn't show up in `platform-inventory`.

This server is assigned to the Acadia program and doesn't show up in the Ops Dashboard.  This server is in active use in production, but is showing up in the delta list because the hardware ID doesn't show up in the `platform-inventory` repository.  

There are currently 778 servers in the `role` of `vpc_acadia`, `vpc_acadia_privateEdge`, and `vpc_acadia_publicEdge` combined in `platform-inventory` and we're likely adding all of them to the delta list.  Some of those are in `qz2`.

I checked a few more nodes in that role and they're all on the delta list even though they're active in production:

* [dal1-qz1-sr3-rk160-s20](https://internal.softlayer.com/Hardware/view/1460615)
* [lon1-qz1-sr6-rk056-s36](https://internal.softlayer.com/Hardware/view/3399418)
* [wdc1-qz1-sr4-rk001-s28](https://internal.softlayer.com/Hardware/view/3413743)

It's also worth noting that I found many cases (like [dal1-qz1-sr3-rk165-s04](https://internal.softlayer.com/Hardware/view/1460121)) with an `inventory_state` and `workflow` of `decommission` in `platform-inventory`, but a `Status` of `ACTIVE` in IMS.  Many of those are older Broadwell processors.

#### SMC Server LS000C86

| Location | Datacenter | Location Path | Hardware Status | Hardware Internal Serial | Hardware Type | Chassis Vendor | Processor Description | 
|---|---|---|---|---|---|---|---|
| Americas | WDC07 | wdc07.sr04 | Active | [LS000C86](https://internal.softlayer.com/Hardware/view/3550495) | Server | SuperMicro | Xeon-Sapphire-Rapids / 8474C-PLATINUM |

This server was first scanned on 04-JUN-2024 and is a little over one month old.

This server is listed in location `wdc07.sr04.rk125.sl39`, but it isn't physically there yet.  This server is listed in a hardware state of `ACTIVE`, but it's actually in a `racking` state in the `platform-inventory` repository.  

This server is part of the H100 program and is actively being racked right now.  This is an example of the system working correctly even though this server shows up in the delta list.  This server is also part of the 357 8U servers listed below.

#### Inspur Server SL01LT9A

| Location | Datacenter | Location Path | Hardware Status | Hardware Internal Serial | Hardware Type | Chassis Vendor | Processor Description | 
|---|---|---|---|---|---|---|---|
| EU | FRA04 | fra04.sr03 | Active | [SL01LT9A](https://internal.softlayer.com/Hardware/view/3311340) | Server | Inspur | XEON-8260-Cascade-Lake |

This is an `8xa100` server. It was first scanned on 17-DEC-2021.  It's two years and six months old.

This server was part of the Vela cluster until it was removed and cross shipped to FRA for use by the Watsonx team.  This server is currently being racked  and is waiting power distribution units.

This server shows up as `ACTIVE` and in the delta list because it was removed from `platform-inventory` when it was removed from the rack and hasn't been added yet.  This has been waiting to be racked since 23-JUN-2024.

This is another example of the system working well and the server showing up on the delta list because we don't have a good way to determine that programmatically yet.

#### Lenovo Server SL01LUXL

| Location | Datacenter | Location Path | Hardware Status | Hardware Internal Serial | Hardware Type | Chassis Vendor | Processor Description | 
|---|---|---|---|---|---|---|---|
| Americas | DAL10 | dal10.sr03 | Reserved | [SL01LUXL](https://internal.softlayer.com/Hardware/view/3446638) | Server | Lenovo | Xeon-Sapphire-Rapids / 8474C-PLATINUM QSfD |

This server was first scanned on 16-DEC-2022.  It's one year and six months old.

This was purchased as a development server and added to `platform-inventory` with the unusual role of `custom`.  This server had a bad motherboard and was removed from a rack for service.  The motherboard was replaced and the last comment indicates that it was repaired and does boot up.

This server is currently sitting on a pallet in `dal10.sr03` and has been there since 04-MAR-2024. It's in a `RESERVED` state, but isn't reserved for any specific project and should be in `INVENTORY` state.  This is a server that we could deploy back into a development mzone.

There are 2,802 nodes currently identified as `custom`.  We haven't broken down how many of them are on the delta list.

#### SuperMicro Server SL01K6GS

| Location | Datacenter | Location Path | Hardware Status | Hardware Internal Serial | Hardware Type | Chassis Vendor | Processor Description | 
|---|---|---|---|---|---|---|---|
| Americas | DAL10 | dal1-qz1-sr3-rk201-s14 | Reserved | [SL01K6GS](https://internal.softlayer.com/Hardware/view/3208804) | Server | Lenovo | Xeon-Cascade-Lake / 8260-PLATINUM |

This server was first scanned on 24-MAR-2021.  It's three years and three months old.

This server is in the role of `uc_qradar` and in location `dal1-qz1-sr3-rk201-s14`.  This server is healthy and running successfully in production.  

We're unable to track this server in Kinaxis since the hardware ID (`3208804`) doesn't show up in `platform-inventory`.  We need a way to track this.  There are 62 QRadar nodes.

#### SuperMicro Server SL01KI16

| Location | Datacenter | Location Path | Hardware Status | Hardware Internal Serial | Hardware Type | Chassis Vendor | Processor Description | 
|---|---|---|---|---|---|---|---|
| Americas | DAL14 | dal4-qz1-sr1-rk019-s06 | Active | [SL01KI16](https://internal.softlayer.com/Hardware/view/3419417) | Server | SMC | Xeon-Cascade-Lake / 8260-PLATINUM |

This server was first scanned on 29-SEP-2024 and is one year and 9 months old.

It's listed in [`dal4.qz1.sr1.rk019.yaml`](https://github.ibm.com/cloudlab/platform-inventory/blob/master/region/rif/dal4.qz1.sr1.rk019.yaml#L133), but is not listed in allocations.  This server is healthy and active in DAL14, but is not correctly represented in `platform-inventory`.

There are 111 servers in that state, but some of them are in POK and don't show up on the delta list because they're virtual appliance entries that don't correspond to physical servers.  The following are examples of servers in this category that do show up on the delta list:

* `dal1-qz2-sr3-rk196-s09` - [0000200406F8-S09](https://internal.softlayer.com/Hardware/view/3543074)
* `dal2-qz1-sr2-rk037-s08` - [ASL01FUG0](https://internal.softlayer.com/Hardware/view/1467363) (this is also on the 1U list)
* `dal4-qz1-sr1-rk019-s49` - [SL01LR8V](https://internal.softlayer.com/Hardware/view/3311840)

There are 35 servers in this state in `dal` and I suspect they're all on the delta list.  The rest are in `pok` and I suspect most of them are not on the delta list.  We need to investigate them.

<!--
## Categories for the delta

* **Unusable** are no longer usable in VPC, like the 1U servers
	* Any server that's 1U
	* Any server in the following `IMS Inventory State`:
		* `Decommission`
		* `Hardfail`
		* `Liquidate_Prep`
		* `Liquidation`
		* `Liquidation_Processing`
		* `Retired`
* **Usable** represent usable capacity that we aren't using now
* **Unknown** show servers we need to do more digging on
* **8U** shows large GPU servers

List out all of the qualifications that make a server unusable:

* 1U chassis
* Hardware failure
* Missing parts
* Retired or liquidations 

Other requests for buckets:

* Separate Cascade Lake from Sapphire Rapids
* Break down by configuration so we can separate bare metal servers from VSI servers

## Updates

| Date | Update |
|---|---|
| 09-JUL-2024 | Neil and Zack have made some progress with the asset team getting the servers missing CPUs assigned to the correct `missing parts` status in IMS.  This should show up on the weekly capacity report next week. |
| 09-JUL-2024 | Yanping and Tyler are going to breakdown the `IMS Delta Server Count` into three categories so we can drive a better understanding of what makes up that number |
| 10-JUL-2024 | Tyler and I decided that breaking this down into two categories `Unusable` and `Unknown` was a good place to start.  We'll add the third category once we have a clearer definition of it. |
-->

## People

| Name | Slack ID | Title | 
|---|---|---|
| Tyler Fishbeck | @Tyler | Senior Business Analyst |
| Zack Grossbart | @zgrossbart | STSM - IaaS PMO |
| Neil Smith | @neil.smith2 | Project Manager, IBM Cloud Infrastructure |
| Gabe Toney | @gabriel.toney | Senior Project Manager IBM Cloud | 
| Somer Walker | @somer.walker  | Programs Director - IaaS Environments |
| Yanping Wang | @yanpingw | Program Director, IBM Cloud Business Analytics & Intelligence |
| Stella Yan | @stella.yan | Sr Program Manager, IaaS Engineering and Operations | 

## Links

* [`platform-inventory`](https://github.ibm.com/cloudlab/platform-inventory) is the repository of YAML files with information about VPC servers.
* [Inventory States](https://github.ibm.com/Zack-Grossbart/pmo-howto/blob/main/hardware/inventory_state.md) shows a breakdown of all the node roles in `platform-inventory` with counts and descriptions of the states.
* [Node Roles](https://github.ibm.com/Zack-Grossbart/pmo-howto/blob/main/hardware/node_roles.md) shows a breakdown of all of the node roles in `platform-inventory` with counts for each role.
* [Kinaxis](https://na2.kinaxis.net/web/IBCP02_PRD01/saml2)
* [`vpc-capacity-report`](https://ibm.ent.box.com/folder/160763914825) shows the current VPC capacity every 30 minutes.

<!--
## Notes

Sitting on the floor that's not deployed is under 100

There are 140 chassis that don't have PROCS in DAL and 200 total in the company

Somer needs 1,300 for staging

Stalled by fiber
Structured fiber
We have 40 racks of capacity that's ready to deploy to production world wide.  They're going to get pulled out of FRA and LON to help cover the 60 racks we need for staging.

After that we'll be negative cascade lake servers

Classic uses the same chassis and a different processor
-->
