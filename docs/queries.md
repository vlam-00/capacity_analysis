# Capacity Analysis Queries

This document outlines the SQL queries that we use when doing capacity analysis.

These queries use the DB2 instance that loads data from a combination of IMS through Cognos, the capacity report, `platform-inventory`, and other sources.

## Servers not in the VPC account

This query looks for servers that have comments indicating they should be in one of the two VPC accounts (`1882813` or `1187403`), but aren't in either account.
*This query has been captured using the `LANDING.V_VPC_HDW_NULL_ACCNT` view to return the same results.*

```sql
SELECT *
FROM LANDING.HARDWARE_SOURCE t1
         left join landing.VPC_IMS_ACCOUNT_ID t2 on t1.IMS_ACCOUNT_ID = t2.IMS_ACCOUNT_ID
WHERE DATE = '8/16/2024'
  and t2.IMS_ACCOUNT_ID is null
  and hardware_type = 'Server'
  and ((lower(HARDWARE_STATUS_REASON) like '%nextgen%' or lower(HARDWARE_STATUS_REASON) like '%vpc%' or
        lower(HARDWARE_STATUS_REASON) like '%genesis%')
    or (lower(LAST_HARDWARE_NOTE) like '%nextgen%' or lower(LAST_HARDWARE_NOTE) like '%vpc%' or
        lower(LAST_HARDWARE_NOTE) like '%genesis%'))
```    

This query looks for the strings `nextgen`, `genesis`, or `vpc`.  We can change this to look for more keywords or do a more complex search.

## IMS delta list

This query shows all servers that are assigned to one of the two VPC accounts (`1882813` or `1187403`), but aren't in `platform-inventory` based on the hardware ID.  

```sql
with ims as (SELECT hs.*
             FROM HARDWARE_SOURCE HS
             where HS.IMS_ACCOUNT_ID IN ('1187403', '1882813')
               AND HS.HARDWARE_TYPE = 'Server'
               and hs.date = '8/16/2024')


select *
from ims
         left join V_PLATFORM_INVENTORY_CURR_DT PI on ims.HARDWARE_ID = pi.HARDWARE_ID
where pi.hardware_id is null;
```

We could improve this query to look for host names as well as hardware IDs, but this a good first pass.

## Servers in Platform Inventory Missing in IMS Lists

This query shows all servers in Platform Inventory which are neither assigned to a VPC Account nor intended for VPC based off of the `HARDWARE_STATUS_REASON` and `LAST_HARDWARE_NOTE` strings. *Change the dates to reflect the intended time snapshot.*

```sql
select *
from v_platform_inventory t1
         left join (SELECT hardware_id
                    FROM HARDWARE_SOURCE HS
                    where HS.IMS_ACCOUNT_ID IN ('1187403', '1882813')
                      AND HS.HARDWARE_TYPE = 'Server'
                      and hs.date = '8/16/2024'
                    union
                    select HARDWARE_ID
                    from V_VPC_HDW_NULL_ACCNT where date = '8/16/2024') t2
                   on t1.hardware_id = t2.hardware_id
where t1.date = '8/16/2024'
  and t2.HARDWARE_ID is null
  and t1.HARDWARE_ID is not null;
```
## Finding Duplicate `HARDWARE_ID` Records in Platform Inventory

This query shows all `HARDWARE_ID` objects in `platform-inventory` which have duplicated records. You can retrieve the list using the following query.

```sql
select * from LANDING.V_PLATFORM_INVENTORY_DUPE_HWID;
```
