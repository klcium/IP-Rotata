#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from iprotata.aws.vpc import Vpc
from iprotata.aws.ec2 import Ec2
from iprotata.manager.wireguard_manager import WireguardManager
from iprotata.helpers import select_option_int
from iprotata.helpers import confirm
import requests
import subprocess
import logging

def rotate_args(parser, std_parser):
    setup_parser = parser.add_parser('rotate', help='Rotate your IP', parents=[std_parser], formatter_class=std_parser.formatter_class)
    setup_parser.add_argument('--vpc-id', dest="vpc_id", help='If there are more than one VPC, you must send the VPC ID')
    setup_parser.add_argument('--instance-id', dest="instance_id", help='If there are more than one EC2 instance in a VPC, you must send the VPC ID')
    setup_parser.add_argument('--network-interface-id', dest="eni_id", help='By default, we rotate the main IP of the instance')
    # setup_parser.add_argument("--dest-vpc", dest='aws_dest_vpc', help='Destination VPC')
    return parser

def rotate_elastic_ip(ec2_client, elastic_network_interface):
    # Get eni ID
    if len(elastic_network_interface["NetworkInterfaces"]) < 1:
        logging.warning("Could not get an interface network with your public IP")
        return None
    # Veeerry dirty!! Select ENI which is deleted on termination, usually the default one
    # This case is when wg is down and there are two Network Interface sent in this function.
    eni_index = 0
    for index, network_interface in enumerate(elastic_network_interface["NetworkInterfaces"]):
        if network_interface['Attachment']['DeleteOnTermination']==True:
            eni_index = index
    # Deduce network interface ID
    network_interface_id = elastic_network_interface["NetworkInterfaces"][eni_index]["NetworkInterfaceId"]
    try:
        # Use ENI to get 
        allocation_id = elastic_network_interface["NetworkInterfaces"][eni_index]["Association"]["AllocationId"]    
        logging.info('New allocation id is: {}'.format(allocation_id))
        association = ec2_client.describe_elastic_ips(allocation_id_filter=[allocation_id], rotata_filter=False)
        logging.info('New association id is: {}'.format(association['Addresses'][0]['AssociationId']))
    except KeyError as error:
        logging.fatal("The instance you chose has no public IP on its first interface")
        exit(1)

    if len(association['Addresses'])!=1:
        logging.fatal("Could not get the association ID linked to your public IP")
        return None
    
    new_association = ec2_client.assign_new_public_ip(network_interface_id=network_interface_id)
    if 'AssociationId' in new_association:
        eni = ec2_client.describe_network_interfaces(association_id_filter=[new_association['AssociationId']])
        new_ip = eni['NetworkInterfaces'][0]['Association']['PublicIp']
    else:
        logging.fatal("An error occured while attributing a new IP to your network interface")
        # exit(1) # Exiting instead of return none, idk why i do that.

    release_status = ec2_client.release_ip_address(allocation_id)

    if release_status["ResponseMetadata"]["HTTPStatusCode"] != 200:
        logging.warning("Could not free previous public IP, you may have to do it manually to avoid AWS over-billing")   
        logging.info(release_status)

    print("Your IP was successfully ROTATED: {}".format(new_ip))
    return new_ip


def select_vpc(vpc_client):
    # Yes its hardcoded, i know. UwU
    vpc = None
    vpc_name_filter = "VPC-Rotata"
    vpcs = vpc_client.list_vpcs(vpc_name_filter=vpc_name_filter)
    if vpcs is None:
        logging.fatal("Could not get any VPC associated with ROTATA. Exiting")
        exit(1)
    elif len(vpcs["Vpcs"]) > 1:
        print('You have more than one ROTATA VPC, select which you want to rotate')
        print('Id\tVPC ID\t\t\tVPC Name')
        print('-'*45)
        for index,vpc in enumerate(vpcs["Vpcs"]):
            print('{}\t{}\t{}'.format(index, vpc["VpcId"], ''.join([i["Value"] for i in vpc["Tags"] if i["Key"]=="Name"])))
        stupid = True
        while stupid:
            option = select_option_int()
            if option in range(0,len(vpcs["Vpcs"])):
                stupid = False
            else:
                logging.error("You did not select a valid Id")
        vpc = vpcs["Vpcs"][option]
    elif len(vpcs["Vpcs"]) == 1:
        vpc = vpcs["Vpcs"][0]
    return vpc

    

def select_instance(ec2_client, vpc_id):
    reservations = ec2_client.describe_instances(vpc_id_filter=[vpc_id])
    selected_instance = None

    # If more than one instance, let user choose
    if len(reservations['Reservations']) > 1:
        print('You have more than one instance in the Rotata VPC, select which you want to rotate')
        print('{}\t{}'.format('Id','Instance Id'))
        print('-'*50)
        for index, instances in enumerate(reservations['Reservations']):
            instance = instances['Instances'][0]
            print('{}\t{}'.format(index, instance['InstanceId']))
        stupid = True
        while stupid:
            option = select_option_int()
            if option in range(0,len(reservations['Reservations'])):
                stupid = False
            else:
                logging.error("You did not select a valid Id")
        selected_instance = reservations['Reservations'][option]

    # If one instance pick it
    elif len(reservations['Reservations']) == 1:
        selected_instance = reservations['Reservations'][0]
    else:
        logging.fatal("Could not find any EC2 instance in your VPC")
        exit(1)
    return selected_instance

def describe_instance(ec2_client, instance_id):
    rotate_instance = ec2_client.describe_instances(instances_id=[instance_id])
    if rotate_instance is None:
        logging.fatal("Instance not found")
        exit(1)
    print(rotate_instance)
    exit("TODO")
    return rotate_instance

def check_wg_running():
    is_root = WireguardManager.is_root()
    is_wg_up = False
    if  is_root is False:
        logging.warning("You are not running as root, is wireguard running ?")
        if confirm(default_choice="y") is False:
            exit(1)
        else: 
            is_wg_up = True
    else:    
        wg_command_output = subprocess.run(["wg"], capture_output=True)
        if len(wg_command_output.stdout) > 1:
            is_wg_up = True
    return is_wg_up

def get_public_ip():
    try: 
        wg_ip = requests.get("https://ipinfo.io").json()["ip"]
    except Exception as error:
        logging.error(error)
        logging.warning("Can't get your public IP, your Wireguard tunnel is probably broken.")
        wg_ip = None
    return wg_ip

def rotate(args, session_object):
    # Init clients
    vpc_client = Vpc(session=session_object._session, region_name=args.region_name)
    ec2_client = Ec2(session=session_object._session, region_name=args.region_name)

    is_wg_up = check_wg_running()
    use_default_rotate_method = True
        
    # If instance id is set, don't bother doing the default method thing
    if args.instance_id is not None:
        use_default_rotate_method = False
        instance = describe_instance(ec2_client=ec2_client, instance_id=args.instance_id)
        print(instance)
        exit("TODO")
    # Check if wg-rotate is up
    elif is_wg_up is True:
        # Curl ipinfo.io and search the ENI or Dynamic IP with that pubip
        use_default_rotate_method = False
        old_ip = get_public_ip()
        if old_ip is not None:
            eni = ec2_client.describe_network_interfaces(public_ip_filter=old_ip)
            print("Wait while we ROTATE your IP")
            new_eip = rotate_elastic_ip(ec2_client=ec2_client, elastic_network_interface=eni)
            if new_eip == None:
                # If can't rotate using public IP, fallback to default method
                use_default_rotate_method = True
                
        else:
            logging.warning("Could not get your public ip")
            use_default_rotate_method = True
    
    # Check if multiple VPC
    if use_default_rotate_method is True:
        vpc = select_vpc(vpc_client=vpc_client)
        if vpc is None:
            logging.fatal("No VPC found")
            exit(1)
        instance = select_instance(ec2_client=ec2_client, vpc_id=vpc['VpcId'])
        network_interfaces = ec2_client.describe_network_interfaces(instance_id_filter=[instance['Instances'][0]['InstanceId']])
        rotate_elastic_ip(ec2_client=ec2_client, elastic_network_interface=network_interfaces)
        # Describe ENI in one VPC
        # Ask user to select which to rotate


