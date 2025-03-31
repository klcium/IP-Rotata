#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import botocore.exceptions
import logging
from iprotata.logger import log_ip_action

class Ec2:
    def __init__(self, session, region_name):
        self.session = session
        self.region_name = region_name
        self.client = session.client("ec2", region_name=region_name)

    #### ADD ####

    def add_security_group_ingress(self, sg_group_id, source_cidr_ip, port_range, ip_protocol, is_dry_run=False):
        response = None
        try:
            response = self.client.authorize_security_group_ingress(
                CidrIp=source_cidr_ip,
                GroupId=sg_group_id,
                IpProtocol=ip_protocol,
                DryRun=is_dry_run,
                FromPort=port_range[0],
                ToPort=port_range[1],
                TagSpecifications=[
                    {
                        'ResourceType': 'security-group-rule',
                        'Tags': [
                            {
                                'Key': 'tool',
                                'Value': 'Rotata'
                            },
                        ]
                    },
                ]
            )
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response 

    #### ASSIGN ####

    def assign_new_public_ip(self, instance_id=None, network_interface_id=None, is_dry_run=False):
        response = None
        if instance_id == network_interface_id == None:
            logging.fatal("Assign new public ip function is called with instnace_id and network_interface_id being both null")
            exit(1)
        try:
            response = self.client.allocate_address(TagSpecifications=[
                {
                    'ResourceType': 'elastic-ip',
                    'Tags': [
                        {
                            'Key': 'tool',
                            'Value': 'Rotata'
                        },
                    ]
                },
            ])
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                log_ip_action(action='ALLOCATE',ip=response['PublicIp'])
            else:
                logging.error("Could not get a new public ip")
                logging.info(response)
                exit(1)

            if instance_id is not None:
                # Create dynamic pub IP
                
                logging.info("Waiting for instance {} to be running before assigning a public IP".format(instance_id))
                waiter = self.client.get_waiter('instance_running')
                waiter.wait(InstanceIds=[instance_id])
                # Attach dynamic pub IP
                response = self.client.associate_address(
                    AllocationId=response['AllocationId'],
                    InstanceId=instance_id,
                    AllowReassociation=True,
                    DryRun=is_dry_run
                )
            elif network_interface_id is not None:
                    # Attach dynamic pub IP
                    response = self.client.associate_address(
                        AllocationId=response['AllocationId'],
                        NetworkInterfaceId=network_interface_id,
                        AllowReassociation=True,
                        DryRun=is_dry_run
                    )
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response

    # def associate_route_table(self, igw_id, route_table_id, is_dry_run=False):
    #     # NOT IN USE ATM, REMOVE BEFORE FLIGHT
    #     response = None
    #     try:
    #         response = self.client.associate_route_table(
    #             DryRun=is_dry_run,
    #             RouteTableId=route_table_id,
    #             # SubnetId='string',
    #             GatewayId=igw_id
    #         )
    #     except botocore.exceptions.ClientError as error:
    #         logging.fatal('Something wrong happened: {}'.format(error))
    #     return response 

    #### ATTACH ####

    def attach_internet_gateway(self, igw_id, vpc_id, is_dry_run=False, setup_route=True):
        # This function will setup the routing table for the IGW by default to the VPC it is attached to
        response = None
        # Check if VPC already has IGW:
        
        response = self.describe_internet_gateways(vpc_id_filter=[vpc_id], rotata_filter=False, is_dry_run=is_dry_run)
        if hasattr(response["InternetGateways"], "Attachments") and (len(response["InternetGateways"]["Attachments"])>0):
            logging.warning("Could not attach IGW {} to VPC {} because an IGW is already attached to this VPC".format(igw_id, vpc_id))
            return None
        try:
            response = self.client.attach_internet_gateway(
                DryRun=is_dry_run,
                InternetGatewayId=igw_id,
                VpcId=vpc_id
            )
            if response is None:
                logging.error("An error occured during the setup of routing tables")
            elif setup_route:
                route_tables = self.describe_route_tables(vpc_id_filter=[vpc_id], is_dry_run=is_dry_run)
                for table in route_tables["RouteTables"]: 
                    # self.associate_route_table(igw_id=igw_id, route_table_id=table["RouteTableId"])
                    self.create_route_igw(igw_id=igw_id, route_table_id=table["RouteTableId"])
                
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response      

    def attach_network_interface(self, instance_id, network_interface_id, is_dry_run=False):
        try:
            # Create IGW
            response = self.client.attach_network_interface(
                DeviceIndex=1,
                DryRun=is_dry_run,
                InstanceId=instance_id,
                NetworkInterfaceId=network_interface_id
            )
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response  

    #### CREATE ####

    def create_instance(self, is_dry_run, ami_id, subnet_id, key_name, security_group_ids=[], user_data=''):
        response = None
        try:
            response = self.client.run_instances(
                BlockDeviceMappings=[
                    {
                        'DeviceName': '/dev/sdh',
                        'Ebs': {
                            'DeleteOnTermination': True,
                            'VolumeSize': 8,
                            'VolumeType': 'standard',
                            'Encrypted': True
                        },
                    },
                ],
                ImageId=ami_id,
                InstanceType='t2.nano',
                MinCount=1,
                MaxCount=1,
                SecurityGroupIds=security_group_ids,
                # SubnetId=subnet_id,
                UserData=user_data,
                DryRun=is_dry_run,
                SubnetId=subnet_id,
                KeyName=key_name,
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {
                                'Key': 'tool',
                                'Value': 'Rotata'
                            },
                            {
                                'Key': 'Name',
                                'Value': 'Rotata-Instance'
                            }
                        ]
                    },
                ],
            )
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response


    def create_internet_gateway(self, is_dry_run=False):
        response = None
        try:
            # Create IGW
            response = self.client.create_internet_gateway(TagSpecifications=[{
                        'ResourceType': 'internet-gateway',
                        'Tags': [
                            {
                                'Key': 'tool',
                                'Value': 'Rotata'
                            },
                        ],
                    }
                ],
                DryRun=is_dry_run
            )
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response      

    def create_network_interface(self, subnet_id, sg_ids, is_dry_run=False):
        response = None  
        try:
            response = self.client.create_network_interface(
                Description='string',
                DryRun=is_dry_run,
                Groups=sg_ids,# must be array
                SubnetId=subnet_id,
                TagSpecifications=[
                    {
                        'ResourceType': 'network-interface',
                        'Tags': [
                            {
                                'Key': 'tool',
                                'Value': 'Rotata'
                            },
                        ]
                    },
                ]
            )
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response    

    def create_route_igw(self, route_table_id, igw_id, is_dry_run=False):
        response = None  
        try:
            response = self.client.create_route(
                DestinationCidrBlock="0.0.0.0/0",
                DryRun=is_dry_run,
                GatewayId=igw_id,
                RouteTableId=route_table_id
            )
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response    

    def create_security_group(self, vpc_id, is_dry_run=False):
        response = None
        try:
            response = self.client.create_security_group(
                Description='Rotata-SG',
                GroupName='Rotata-SG',
                VpcId=vpc_id,
                TagSpecifications=[
                    {
                        'ResourceType': 'security-group',
                        'Tags': [
                            {
                                'Key': 'tool',
                                'Value': 'Rotata'
                            },
                        ]
                    },
                ],
                DryRun=is_dry_run
            )
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response

    #### DELETE ####

    def delete_internet_gateway(self, igw_id, is_dry_run=False):
        response = None
        try:
            # Check if  IGW attached, and detach it before del
            # igws_id must be an array of ids
            igws = self.describe_internet_gateways(igw_ids=[igw_id], rotata_filter=False)
            for igw in igws["InternetGateways"]:
                if (len(igw["Attachments"]))>0:
                    for attachment in igw["Attachments"]:
                        self.detach_internet_gateway(igw_id=igw["InternetGatewayId"], vpc_id=attachment["VpcId"])
            # Del IGW
            response = self.client.delete_internet_gateway(
                DryRun=is_dry_run,
                InternetGatewayId=igw_id
            )
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response

    def delete_network_interface(self, eni_id, is_dry_run=False):
        response = None
        try:
            response = self.client.delete_network_interface(
                DryRun=is_dry_run,
                NetworkInterfaceId=eni_id
            )
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response     

    def delete_security_group(self, sg_group_id, is_dry_run=False):
        response = None
        try:
            response = self.client.delete_security_group(
                GroupId=sg_group_id,
                DryRun=is_dry_run
            )
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response

    #### DESCRIBE ####

    def describe_elastic_ips(self, allocation_id_filter=None, public_ips_filter=None, rotata_filter=True, is_dry_run=False):
        response = None
        fltr = [{}]
        if public_ips_filter is not None:
            fltr.append({'Name':'public-ip', 'Values':public_ips_filter})
        if rotata_filter:
            fltr.append({'Name':'tag:tool', 'Values':['Rotata']})
        if allocation_id_filter is not None:
            fltr.append({'Name':'allocation-id', 'Values':allocation_id_filter})

        try:
            response = self.client.describe_addresses(
                Filters=fltr,
                DryRun=is_dry_run
            )
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response    


    def describe_internet_gateways(self, igw_ids=None, vpc_id_filter=None, rotata_filter=True, is_dry_run=False):
        response = None
        fltr=[]
        if rotata_filter:
            fltr.append({'Name': 'tag:tool','Values': ['Rotata']})
        if vpc_id_filter is not None:
            fltr.append({'Name': 'attachment.vpc-id', 'Values':vpc_id_filter})
        try:
            if igw_ids is None:
                response = self.client.describe_internet_gateways(
                    Filters=fltr,
                    DryRun=is_dry_run
                )
            else:
                response = self.client.describe_internet_gateways(
                    InternetGatewayIds=igw_ids,
                    Filters=fltr,
                    DryRun=is_dry_run
                )   
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response

    def describe_instances(self, vpc_id_filter=[], instances_id=[]):
        response = None
        fltr = [{}]
        if len(vpc_id_filter) > 0:
            fltr.append({'Name':'network-interface.vpc-id', 'Values':vpc_id_filter})
        try:
            response = self.client.describe_instances(
                Filters=fltr,     
                InstanceIds=instances_id
            )
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response

    def describe_key_pairs(self):
        response = None
        try:
            response = self.client.describe_key_pairs()
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response


    def describe_network_interfaces(self, vpc_id_filter=None, rotata_filter=False, association_id_filter=None, public_ip_filter=None, instance_id_filter=None, is_dry_run=False):
        response = None
        fltr = [{}]
        if vpc_id_filter is not None:
            fltr.append({'Name':'vpc-id', 'Values':[vpc_id_filter]})
        if rotata_filter is True:
            fltr.append({'Name':'tool','Values':'Rotata'})
        if public_ip_filter is not None:
            fltr.append({'Name':'association.public-ip', 'Values':[public_ip_filter]})
        if association_id_filter is not None:
            fltr.append({'Name':'association.association-id','Values':association_id_filter})
        if instance_id_filter is not None:
            fltr.append({'Name':'attachment.instance-id','Values':instance_id_filter})
        try:
            response = self.client.describe_network_interfaces(
                Filters=fltr,
                DryRun=is_dry_run
            )
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response


    def describe_route_tables(self, vpc_id_filter=None, route_table_id=None, is_dry_run=False):
        response = None
        fltr=[]
        if vpc_id_filter is not None:
            fltr.append({'Name': 'vpc-id','Values': vpc_id_filter})
        try:
            if route_table_id is None:
                response = self.client.describe_route_tables(
                    Filters=fltr,
                    DryRun=is_dry_run
                )
            else:
                response = self.client.describe_route_tables(
                    Filters=fltr,
                    DryRun=is_dry_run,
                    RouteTableIds=route_table_id
                )
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response

    def describe_security_groups(self, vpc_id_filter=None, is_dry_run=False):
        response = None
        fltr=[]
        if vpc_id_filter is not None:
            fltr.append({'Name': 'vpc-id','Values': vpc_id_filter})
        try:
            response = self.client.describe_security_groups(
                Filters=fltr,
                DryRun=is_dry_run
            )
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response
        
    #### DETACH ####

    def detach_internet_gateway(self, igw_id, vpc_id, is_dry_run=False):
        response = None
        try:
            response = self.client.detach_internet_gateway(
                DryRun=is_dry_run,
                InternetGatewayId=igw_id,
                VpcId=vpc_id
            )
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response

    #### DISASSOCIATE ####

    def disassociate_address(self, association_id, is_dry_run=False):
        response = None
        try:
            response = self.client.disassociate_address(
                AssociationId=association_id,
                DryRun=is_dry_run
            )
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response

    #### RELEASE ####

    def release_ip_address(self,allocation_id, is_dry_run=False):
        response = None
        try:
            pub_ip = self.client.describe_addresses(
                AllocationIds=[allocation_id],
                DryRun=is_dry_run
            )
            response = self.client.release_address(
                AllocationId=allocation_id,
                DryRun=is_dry_run
            )
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                log_ip_action(action='RELEASE',ip=pub_ip['Addresses'][0]['PublicIp'])
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response


    #### TERMINATE ####

    def terminate_instances(self, instances_ids, is_dry_run=False):
        response = None
        try:
            response = self.client.terminate_instances(
                InstanceIds=instances_ids,
                DryRun=is_dry_run
            )
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        return response
