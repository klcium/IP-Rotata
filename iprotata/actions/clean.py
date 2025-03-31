#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
from iprotata.aws.vpc import Vpc
from iprotata.aws.ec2 import Ec2
from iprotata.helpers import confirm
from iprotata.manager.wireguard_manager import WireguardManager
from os.path import isfile
import subprocess
import logging
import sys

wg_path = "/etc/wireguard/wgrotata.conf"

def clean_args(parser, std_parser):
    setup_parser = parser.add_parser('delete', help='Delete resources in a region with Rotata tag', parents=[std_parser], formatter_class=std_parser.formatter_class)
    # setup_parser.add_argument("--dest-vpc", dest='aws_dest_vpc', help='Destination VPC')
    return parser

def get_rotata_vpcs(vpc_client, vpc_name_filter='VPC-Rotata'):
    vpcs = vpc_client.list_vpcs(vpc_name_filter=vpc_name_filter)
    if vpcs is None:
        logging.fatal("Could not get any VPC associated with ROTATA. Exiting")
        exit(1)
    return vpcs

def check_wg_running():
    is_root = WireguardManager.is_root()

    if  is_root is False:
        logging.warning("You are not running as root, the file {} will not be deleted".format(wg_path))
        if confirm() is False:
            exit(1)
    else:    
        wg_command_output = subprocess.run(["wg"], capture_output=True)
        if len(wg_command_output.stdout) > 1:
            logging.fatal("Please shutdown your wireguard tunnel before terminating your instances")
            exit(1)



def detach_dynamic_ips(ec2_client, pub_ip_list):
    for pub_ip in pub_ip_list:
        if "AssociationId" in pub_ip:
            print("Disassociating public IP allocation: {}".format(pub_ip["AssociationId"]))
            ec2_client.disassociate_address(association_id=pub_ip["AssociationId"])

def release_dynamic_pub_ips(ec2_client, pub_ip_list):
    for pub_ip in pub_ip_list:
        print("Releasing public IP allocation: {}".format(pub_ip["AllocationId"]))
        ec2_client.release_ip_address(allocation_id=pub_ip["AllocationId"])

def remove_wg_rotata_file():
    is_root = WireguardManager.is_root()
    if is_root and isfile(wg_path):
        subprocess.run(["rm",wg_path])

def list_instances_to_terminate(ec2_client, vpcs):
    terminate_instances_list = []
    reservations = None
    for vpc in vpcs["Vpcs"]:
        reservations = ec2_client.describe_instances(vpc_id_filter=[vpc["VpcId"]])["Reservations"]
        for reservation in reservations:
            instances = reservation["Instances"]
            for instance in instances:
                terminate_instances_list.append(instance["InstanceId"])
    print("Terminating instances: {}\n".format(terminate_instances_list))
    print("This may take some time...")
    return reservations, terminate_instances_list

def terminate_ec2_instances(ec2_client, terminate_instances_list, reservations):
    if len(terminate_instances_list) > 0:
        ec2_client.terminate_instances(instances_ids=terminate_instances_list)
        are_all_instances_terminated = False
    else:
        are_all_instances_terminated = True
    i = 0
    condition = 600
    print("-"*10)
    while (are_all_instances_terminated == False) and (i < condition):
        
        i = i+1
        time.sleep(2)
        are_all_instances_terminated = True
        
        if i%100 == 0:
            print('Still waiting')

        # Loop through instances to check termination status
        if reservations is not None:
            before_recheck_reservations = reservations
        reservations = ec2_client.describe_instances(instances_id=terminate_instances_list)["Reservations"]
        for reservation in reservations:
            instances = reservation["Instances"]
            if reservations != before_recheck_reservations:
                for instance in instances:
                    print("Instance: {}\tStatus:{}".format(instance["InstanceId"],instance["State"]["Name"]))
                print("-"*10)  
            for instance in instances:
                if(instance["State"]["Code"] != 48):
                    are_all_instances_terminated = False
    if i >= condition:
        logging.fatal('An error occured: Timeout during termination of EC2 instances, cannot delete VPC')
        exit(1)

## setup a routine to ask user to fill in the information ?? use context instead ?
def clean_aws(args, session_object):
    # Check if root and if wg is setup
    # Ask user for confirmation
    print("This function will clean all ressources within VPC with the ROTATA tag.")
    if not confirm():
        exit(1)
    
    # Check if running as root + if wg is running
    check_wg_running()

    # Init clients
    vpc_client = Vpc(session=session_object._session, region_name=args.region_name)
    ec2_client = Ec2(session=session_object._session, region_name=args.region_name)
    
    # List VPCs where name is rotata
    vpcs = get_rotata_vpcs(vpc_client)
    
    #Printing of all listed VPCs of the region, maybe should be migrated as static in the list_vpcs ?
    for vpc in vpcs["Vpcs"]:
            vpcname = ""
            if "Tags" in vpc:
                vpcname = [i["Value"] for i in vpc["Tags"] if i["Key"]=="Name"]

    # Remove WG ROTATA FILE
    remove_wg_rotata_file()

    # List running EC2 in rotata VPC
    reservations, terminate_instances_list = list_instances_to_terminate(ec2_client=ec2_client,vpcs=vpcs)  

    # Send delete instruction and wait for termination
    terminate_ec2_instances(reservations=reservations, terminate_instances_list=terminate_instances_list, ec2_client=ec2_client)

    # List Pub IPs
    pub_ip_list = ec2_client.describe_elastic_ips(rotata_filter=True)
    
    # Detach Pub Ips
    detach_dynamic_ips(ec2_client=ec2_client, pub_ip_list=pub_ip_list['Addresses'])   
    
    # Release Pub Ips
    release_dynamic_pub_ips(ec2_client=ec2_client, pub_ip_list=pub_ip_list['Addresses'])

    # list network interfaces in VPC
    for vpc in vpcs["Vpcs"]:
        net_interfaces = ec2_client.describe_network_interfaces(vpc_id_filter=vpc["VpcId"], is_dry_run=False)
        for eni in net_interfaces['NetworkInterfaces']:
            ec2_client.delete_network_interface(eni['NetworkInterfaceId'])
    
    # Listing and deleting non-default security groups
    for vpc in vpcs["Vpcs"]:
        security_groups = ec2_client.describe_security_groups(vpc_id_filter=[vpc["VpcId"]])
        if security_groups is not None:
            for sg in security_groups["SecurityGroups"]:
                #TODO: List network interfaces attached to the security group and remove them manually   
                if sg["GroupName"] != 'default':
                    logging.info("Deleting security group: {}".format(sg["GroupName"]))
                    ec2_client.delete_security_group(sg_group_id=sg["GroupId"])


    # Deleting IGW, must be done after alls pub ip of vpc are released
    # Listing with rotata tag, if list with VPC, detached instances will not be fetched
    igws = ec2_client.describe_internet_gateways(rotata_filter=True)
    for igw in igws["InternetGateways"]:
        print("Deleting {}".format(igw["InternetGatewayId"]))
        ec2_client.delete_internet_gateway(igw_id=igw["InternetGatewayId"])

    # Loop through all subnets and delete them
    for vpc in vpcs["Vpcs"]:
        subnets = vpc_client.describe_subnets(vpc_id_filter=[vpc["VpcId"]])["Subnets"]
        for subnet in subnets:
            print("Deleting {}".format(subnet["SubnetId"]))
            response = vpc_client.delete_subnet(subnet_id=subnet["SubnetId"])
    
    # Loop through all VPCS and delete them
    for vpc in vpcs["Vpcs"]:
        print("Deleting {}".format(vpc["VpcId"]))
        response = vpc_client.delete_vpc(vpc["VpcId"])
        if response is None:
            logging.fatal("Could not delete VPC, this is probably due to vpc depedencies not managed by this tool\n")