# Composite Racks and Effective Rack Numbers

This document describes the issue we have in the Gaudi 3 and MI300X programs with the way we've handled effective rack numbers when building composite racks.

## Background

The H100/H200 offerings have two servers per rack.  We included switches in each rack which is a very inefficient use of our rack numbers, IP address space, and physical hardware.  We're starting to run out of space and we wanted to use it more efficiently for Gaudi 3 and MI300X.

## The problem

For the Gaudi 3 and MI300X programs we introduced a new concept called composite racks.  In this concept we use a single set of switches for multiple racks.

It looks like this:

```
wdc2-qz1-sr1-rk193
Physical Rack: 193
Effective Rack: 193
Composite Rack: 195
Full Rack Name: wdc2-qz1-sr1-rk193
IPs: 10.51.47.217-10.51.47.218

wdc2-qz1-sr1-rk195
Physical Rack: 195
Effective Rack: 195
Composite Rack: 195
Full Rack Name: wdc2-qz1-sr1-rk195
IPs: 10.51.47.231-10.51.47.232
```

Note that both of these racks use the same composite rack number of `195`.  We use this to determine the IP addresses for the `mgmt_cidr` of `192.168.195.0/24` for both racks.  This means that both racks are effectively sharing the same address space and it works well.

The problem arrises with the host names.  Each rack contains a server in `s12` and `s20`.  That results in the following host names:

```
wdc2-qz1-sr1-rk193-s12
wdc2-qz1-sr1-rk193-s20
wdc2-qz1-sr1-rk195-s12
wdc2-qz1-sr1-rk195-s20
```

This is an inefficient use of our rack numbers.  In additional, we've found some places where these host names had collisions.

We can share the same rack number in the `mgmt_cidr`, but we can't share the composite rack number in the host names or else we'd have collisions like this:

```
wdc2-qz1-sr1-rk195-s12
wdc2-qz1-sr1-rk195-s20
wdc2-qz1-sr1-rk195-s12
wdc2-qz1-sr1-rk195-s20
```

However, we also have collisions if we use the physical rack number in the host name since these were already used by other racks.  For example, we want to add `wdc2-qz1-sr1-rk193-s20`, but there's already `wdc2-qz1-sr2-rk193-s20` which collides since we don't use the server room in the host name in our production network routing.

We could change the slot numbers and have a scheme like this:

```
wdc2-qz1-sr1-rk195-s06
wdc2-qz1-sr1-rk195-s12
wdc2-qz1-sr1-rk195-s20
wdc2-qz1-sr1-rk195-s34
```

...but that would mean introducing the concept of an effective slot number which has never existed in our environment.  Both Malcolm and Zack estimate the cost of implementing that change in `platform-inventory` and their respective tooling as much too large to fit in the timeframe for the Gaudi 3 and MI300X programs.

## The solution

The solution to this problem is to introduce a new effective rack number separate from the composite rack number.  In essence, we would choose an effective rack number that we use just in the host name and not in any of the IP address space calculations.  IP address octets are limited to 8 bits, but our current systems support 9 bits for host names.  That means we have 256 extra host names to use.

The results would look like this:

```
wdc2-qz1-sr1-rk193
Physical Rack: 193
Effective Rack: 495
Composite Rack: 195
Full Rack Name: wdc2-qz1-sr1-rk193
IPs: 10.51.47.217-10.51.47.218
```

This would mean we use the composite rack number when doing the network CIDRs, but the effective rack number when doing the host name.  The result would be a `mgmt_cidr` for the rack of `192.168.195.0/24` with host names that look like this:

```
wdc2-qz1-sr1-rk495-s12
wdc2-qz1-sr1-rk495-s20
```

The resulting entries in IMS would look like this:

```
Host ID: 3584548 SN: SL01FQLP, Type: WEBSVR, Location: wdc06.sr01.rk193.sl39, Hostname: wdc2-qz1-sr1-rk495-s12, Status: ACTIVE, Account: 1187403, Eth Port: 0, IP: 10.51.47.217
Host ID: 3584528 SN: SL01FQLA, Type: WEBSVR, Location: wdc06.sr01.rk193.sl31, Hostname: wdc2-qz1-sr1-rk495-s20, Status: ACTIVE, Account: 1187403, Eth Port: 0, IP: 10.51.47.218
```

The resulting rack allocation looks like this:

```yaml
- id: wdc2-qz1-sr1-rk495
  location: wdc06.sr01.rk193
  inventory_state: production
  workflow: none
  class: gaudi3_s12_s20_pdu_down
  config_version: unknown
  ng_data:
    mgmt_cidr: 192.168.195.0/24
    composite:
      id: gaudi3-wdc06-prod-composite
      type: gaudi3-32node-cluster
      name: 1-mtor
  vpc_data:
    data_cidr: 172.27.138.0/24
```

We've also decided to do effective rack numbers for all of the racks instead of just the ones with collisions so we don't use up an entire CIDR block with the host names when we aren't using any of the IPs.

## The ask

We need to validate this solution with at least the following people:

| Name | Slack ID | Approved | 
|---|---|---|
| Malcolm Allen-Ware | @malcolm_allen-ware  | Yes |
| Alan Benner | @Alan Benner | Yes |
| Peter Donovan | @peter.donovan |  |
| Eran Gampel | @gampel | Yes |
| Zack Grossbart | @zgrossbart | Yes | 
| Brent Tang | @btang |  | 
| Drew Thorstensen | @thorst  | Yes | 

## Pull Requests

This change was implemented for FRA02 and WDC06 in the following PRs:

* [#39184](https://github.ibm.com/cloudlab/platform-inventory/pull/39184)
* [#39187](https://github.ibm.com/cloudlab/platform-inventory/pull/39187)
* [#39188](https://github.ibm.com/cloudlab/platform-inventory/pull/39188)
* [#39192](https://github.ibm.com/cloudlab/platform-inventory/pull/39192)
* [#39197](https://github.ibm.com/cloudlab/platform-inventory/pull/39197)
* [#39199](https://github.ibm.com/cloudlab/platform-inventory/pull/39199)
* [#39363](https://github.ibm.com/cloudlab/platform-inventory/pull/39363)
* [#39366](https://github.ibm.com/cloudlab/platform-inventory/pull/39366)
* [#39368](https://github.ibm.com/cloudlab/platform-inventory/pull/39368)
