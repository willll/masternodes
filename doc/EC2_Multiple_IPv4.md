# How to enable multiple IPv4 on Amazon EC2 and Ubuntu 16.04

## Enable a new elastic IPv4

> In NETWORK & SECURITY/Elastic IPs, select Allocate new address,

> Then to IPv address pool, answer "Amazon pool",

> A new Elastic IP is now available.

## Associate an Elastic IP with an interface

> In NETWORK & SECURITY/Network Interfaces, select Create Network Interface,

> Then create the interface, the subnet should match where the instance is running ("Availability Zone"), 

> A new interface will appear with an available status,

## Associate an interface with an instance

> In INSTANCES/Instances, select the instance you want to add a new IPv4,

> In Actions, select Networking/Attache Network Interfaces,

> In Network Interface, select the interface previously created, then Attach,

> Now the instance's description should shows two network interfaces, they still need to be configured.

## Configure an Interface in Ubuntu 16.04

[Source](https://medium.com/@cuttenweiler/aws-ubuntu-14-and-multiple-enis-b151692f6be8)

> SSH into the instance,

> find the new interface : ifconfig -a

> Create the new interface ....
