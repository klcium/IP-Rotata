#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from iprotata.aws.vpc import Vpc
from iprotata.aws.ec2 import Ec2
from iprotata.manager.wireguard_manager import WireguardManager
from iprotata.helpers import confirm
from os.path import exists
from os.path import isfile
import base64
import logging
import os
import time

wg_path = "/etc/wireguard/wgrotata.conf"

ami_dict={
    "ap-south-2":"",
    "ap-south-1":"ami-01a4f99c4ac11b03c",
    "eu-south-1":"",
    "eu-south-2":"ami-07f3cf9598f36cd14",
    "me-central-1":"",
    "ca-central-1":"ami-092e716d46cd65cac",
    "eu-central-1":"",
    "eu-central-2":"",
    "us-west-1":"",
    "us-west-2":"",
    "af-south-1":"",
    "eu-north-1":"ami-01e030f0ef61658cf",
    "eu-west-3":"ami-0c829a4b65fb753d5",
    "eu-west-2":"",
    "eu-west-1":"ami-0649a986224ded9da",
    "ap-northeast-3":"",
    "ap-northeast-2":"",
    "me-south-1":"",
    "ap-northeast-1":"ami-06ee4e2261a4dc5c3",
    "sa-east-1":"ami-08f74c738bf3f5a45",
    "ap-east-1":"",
    "ap-southeast-1":"ami-0753e0e42b20e96e3",
    "ap-southeast-2":"",
    "ap-southeast-3":"",
    "ap-southeast-4":"",
    "us-east-1":"ami-006dcf34c09e50022",
    "us-east-2":"ami-05bfbece1ed5beb54",
}

def setup_args(parser, std_parser):
    setup_parser = parser.add_parser('setup', help='Setup an AWS environnement', parents=[std_parser], formatter_class=std_parser.formatter_class)
    #setup_parser.add_argument("--dest-vpc", dest='aws_dest_vpc', help='Destination VPC')
    setup_parser.add_argument("--key-name","-k", dest='ec2_key_name', help='Key name for ssh connexions, useful for debugging')
    setup_parser.add_argument("--ami-id", dest='ami_id', help='Boot EC2 on a specific AMI')
    return parser


def run_checks(args, session_object, ec2_client, vpc_client, vpc_name):
    """Various checks to ensure the user did not forget anything"""
    
    # Check if wg file exists
    try:
        if exists(wg_path):
            if  isfile(wg_path):
                print("A wireguard file already exists at the location {}".format(wg_path))
                print("Do you want to override it?")
                if confirm() is False:
                    exit(1)
            else:
                print("Dude, wtf did you put at {} ??? Get rid of that >:(".format(wg_path))
                exit(1)

    except Exception as error:
        logging.fatal("Could not check if wgrotata.conf already exists, exitting")
        exit(1)

    if vpc_client.check_vpc_exists(vpc_name=vpc_name) is not True:
        exit(1)

    # Checking if key argument exists and is not an empty string
    # If key is missing, using latest created key
    if (not isinstance(args.ec2_key_name, str)) or (len(args.ec2_key_name) < 1):
        keys = ec2_client.describe_key_pairs()
        if (keys is not None) and ("KeyPairs" in keys) and (hasattr(keys["KeyPairs"], '__iter__')):
            if (len(keys["KeyPairs"])<=0):
                logging.warning("No a key pair and rerun the program, havent implemented the create_key funtion yet")
            #reverse sort the create timestamps of the keys
            try:
                keys["KeyPairs"].sort(key=lambda x: x['CreateTime'], reverse=True) 
                logging.warning("No key pair was defined in parameters, using the latest created key: {}".format(keys["KeyPairs"][0]["KeyName"]))
                args.ec2_key_name = keys["KeyPairs"][0]["KeyName"]
            except IndexError:
                logging.fatal("Sorry, you don't have any key in that region and i'm not planning on creating one for you. Create one yourself in that region and come back later.")
                exit(1)
    return None

## setup a routine to ask user to fill in the information ?? use context instead ?
def setup_aws(args, session_object):
    """This function setups the environment for the AWS default or specified aws region"""
    # Create various clients
    vpc_client = Vpc(session=session_object._session, region_name=args.region_name)
    ec2_client = Ec2(session=session_object._session, region_name=args.region_name)
    
    
    # Create WG manager
    # If you have other configuration parameters, do it yourself or edit wireguardManager.py init function UwU
    wireguard_mgr = WireguardManager()

    vpc_name = "VPC-Rotata"

    # Run checks to ensure that it won't mess up
    run_checks(args, session_object, ec2_client, vpc_client,vpc_name)

    # Also checking if region is supported
    if args.ami_id is not None:
        ami_id = args.ami_id
    elif args.region_name is not None:
        ami_id = ami_dict[args.region_name]
    else:
        ami_id = ami_dict[session_object._session.region_name]

    if len(ami_id) == 0:
        loggin.fatal("Sorry, the region you selected is currently not supported. Do not hestitate to submit a git issue so that the lazy dev that i am adds the free tier iam for your stupid region")
        exit(1)

    logging.info("Your private key is: {}".format(wireguard_mgr.user_private_key))
    logging.info("Server public key is: {}".format(wireguard_mgr.user_public_key))
    # Create VPCs
    aws_new_vpc = None
    
    aws_new_vpc = vpc_client.create_vpc(is_dry_run=args.is_dryrun, vpc_name=vpc_name)
        
    print('The following VPC was successfully created: {} - {}'.format([i["Value"] for i in aws_new_vpc["Vpc"]["Tags"] if i["Key"]=="Name"], aws_new_vpc["Vpc"]["VpcId"]))
    new_subnet = vpc_client.create_subnet(is_dry_run=args.is_dryrun, vpc_id=aws_new_vpc["Vpc"]["VpcId"])
    print('The following Subnet was successfully created: {} - {}'.format([i["Value"] for i in new_subnet["Subnet"]["Tags"] if i["Key"]=="Name"], new_subnet["Subnet"]["SubnetId"]))

    # Create Security group
    new_sg = ec2_client.create_security_group(vpc_id=aws_new_vpc["Vpc"]["VpcId"], is_dry_run=args.is_dryrun)
    
    # Will add one day a curl to get my pub ip, but for now 0.0.0.0 FTW
    # Add SSH rule
    source_cidr_ip = "0.0.0.0/0"
    to_port = 22
    from_port=22
    ip_protocol = '6' #6 is TCP, 17 is UDP
    new_sg_rule = ec2_client.add_security_group_ingress(sg_group_id=new_sg["GroupId"], source_cidr_ip=source_cidr_ip, port_range=[from_port, to_port], ip_protocol=ip_protocol , is_dry_run=args.is_dryrun)
    
    # Add WG rule
    new_sg_rule = ec2_client.add_security_group_ingress(sg_group_id=new_sg["GroupId"], source_cidr_ip=source_cidr_ip, port_range=[51820, 51820], ip_protocol='17' , is_dry_run=args.is_dryrun)

    # Create IGW
    new_igw = ec2_client.create_internet_gateway()
    # Attach IGW
    igw_vpc = ec2_client.attach_internet_gateway(igw_id=new_igw["InternetGateway"]["InternetGatewayId"], vpc_id=aws_new_vpc["Vpc"]["VpcId"])
    print("The following IGW was successfully created: {}".format(new_igw["InternetGateway"]["InternetGatewayId"]))
    
    # Prepare setup_script
    # setup_script = ""
    setup_script = '''#!/bin/sh
sudo yum update -y
sudo su
export rwfile="/etc/yum.repos.d/wireguard.repo"
export rwurl="https://copr.fedorainfracloud.org/coprs/jdoss/wireguard/repo/epel-7/jdoss-wireguard-epel-7.repo"
wget --output-document="$rwfile" "$rwurl"
amazon-linux-extras install -y epel
yum install wireguard-dkms wireguard-tools -y
yum clean all -y
cd /etc/wireguard
umask 077
echo 1 > /proc/sys/net/ipv4/ip_forward
sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
cat << EOF > /etc/wireguard/wg0.conf
{}
EOF
wg-quick up wg0
systemctl enable wg-quick@wg0'''.format(wireguard_mgr.gen_server_wg_file())
    user_data = base64.b64encode(setup_script.encode()).decode()



    # Create EC2
    print("The following Security Group was successfully created: {}".format(new_sg["GroupId"]))


    new_ec2 = ec2_client.create_instance(is_dry_run=args.is_dryrun, ami_id=ami_id, user_data=user_data, security_group_ids=[new_sg["GroupId"]], subnet_id=new_subnet["Subnet"]["SubnetId"], key_name=args.ec2_key_name)
    if new_ec2 is None:
        print('No new machine was created, an error has probably occured')
        exit(1)
    for instance in new_ec2["Instances"]:
        # Attach first pubip to instance
        assign_pubip_response = ec2_client.assign_new_public_ip(instance_id=instance["InstanceId"])
        # Create 2nd eni
        second_eni = ec2_client.create_network_interface(sg_ids=[new_sg["GroupId"]], subnet_id=new_subnet["Subnet"]["SubnetId"],  is_dry_run=False)
        # Create 2nd elastic IP to 2nd interface
        second_eip = ec2_client.assign_new_public_ip(network_interface_id=second_eni["NetworkInterface"]["NetworkInterfaceId"])
        # Attach 2nd interface to the EC2
        ec2_client.attach_network_interface(network_interface_id=second_eni["NetworkInterface"]["NetworkInterfaceId"], instance_id=instance["InstanceId"])


    # Print created instances and their public IP
    new_instances_ids=[instance["InstanceId"] for instance in new_ec2["Instances"]]
    new_ec2 = ec2_client.describe_instances(instances_id=new_instances_ids)
    
    instance = new_ec2["Reservations"][0]["Instances"][0]
    
    # Don't forget to add instance["NetworkInterfaces"][0 and 1]["Association"]["PublicIp"] to the logs
    
    if len(instance["NetworkInterfaces"]) <=1:
        logging.warning("Hm, it fucked up. Timing issue, sleeping 10s")
        for i in range(0,10):
            time.sleep(10)
            instance = ec2_client.describe_instances(instances_id=new_instances_ids)["Reservations"][0]["Instances"][0]
            if len(instance["NetworkInterfaces"]) <=1:
                logging.warning("Waiting 10 more seconds")
            else:
                logging.warning('Now its gud !')
                break
        if len(instance["NetworkInterfaces"]) <=1:
            logging.fatal("Did not work, sorry, delete and retry setup your env")
            exit(1)
        
    # print(instance["NetworkInterfaces"][0]["Association"]["PublicIp"])
    # print(instance["NetworkInterfaces"][1]["Association"]["PublicIp"])
    interface_index = 0
    # Very dirty fix, wgrotata.conf uses the newly created interface which is not deleted on termination
    for index, network_interface in enumerate(instance["NetworkInterfaces"]):
        if network_interface['Attachment']['DeleteOnTermination']==False:
            interface_index = index

    wg_pubip = instance["NetworkInterfaces"][interface_index]["Association"]["PublicIp"]
    print("The following EC2 Instance was successfully created: {} - {}".format(instance["InstanceId"], wg_pubip))
    wireguard_mgr.server_public_ip =  wg_pubip
    
    
    with open(wg_path, "w") as wg_file:
        wg_file.write(wireguard_mgr.gen_user_wg_file())
        wg_file.close()
    
    print("\nYou can now run the following command:\nsudo wg-quick up wgrotata")
    print("\nInstance is still setting up, 'ping 10.0.0.1' until something comes back. UwU")
