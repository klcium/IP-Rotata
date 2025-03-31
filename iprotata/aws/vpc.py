#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3
import botocore.exceptions
import logging
from iprotata.helpers import confirm

class Vpc:

    def __init__(self, session, region_name):
        self.region_name = region_name
        self.client = session.client("ec2", region_name=self.region_name)

    def list_vpcs(self, vpc_name_filter=None):
        vpcs = {'Vpcs':[],'NextToken': None}
        
        if vpc_name_filter is None:
            fltr = [{}]
        else:
            fltr = [{'Name':'tag:Name', 'Values':[vpc_name_filter]}]
        try: 
            vpcs = self.client.describe_vpcs(Filters=fltr)
        except botocore.exceptions.ClientError as error:
            logging.fatal('Something wrong happened: {}'.format(error))
        # self.vpcs=vpcs
        return vpcs

    # Improve with more arguments in entry
    # Should it be init ? Static ?
    def create_vpc(self, is_dry_run, vpc_name):
        # ec2_client = self.session.client("ec2", region_name=self.region_name)
        vpc = None
        
        # Create vpc
        try: 
            vpc = self.client.create_vpc(
                CidrBlock='10.200.0.0/16',
                DryRun=is_dry_run,
                TagSpecifications=[
                    {
                        'ResourceType': 'vpc',
                        'Tags': [
                            {
                                'Key': 'tool',
                                'Value': 'Rotata'
                            },
                            {
                                'Key': 'Name',
                                'Value': vpc_name
                            }
                        ]
                    },
                ]
            )
        except botocore.exceptions.ClientError as error:
            match error.response['Error']['Code']:
                case "DryRunOperation":
                    logging.info('Created a dryrun VPC, continuing as expected')
                    vpc = None
                case "VpcLimitExceeded":
                    print("You exceeded maximum VPC limit for a region, try either to delete a VPC or use the default-subnet function")
                case default:
                    logging.fatal('Something wrong happened: {}'.format(error))
                    exit(1)
        return vpc

    def check_vpc_exists(self, vpc_name):
        # Check if VPC with the same name exists, return bool
        if type(vpc_name) != str:
            raise Exception("Check_vpc_exist was sent a VPC Name that is not a string")
        result = True

        try:
            vpcs = self.list_vpcs(vpc_name_filter=vpc_name)
            if len(vpcs["Vpcs"]) > 0:
                print("You already have a VPC with the same name !\n")
                print('VPC Id \t\t\tVPC Name')
                print('-----------------------------')
                for vpc in vpcs["Vpcs"]:
                    print('{} - {}'.format(vpc["VpcId"],''.join([i["Value"] for i in vpc["Tags"] if i["Key"]=="Name"])))
                print('-----------------------------\n')
                print('Do you want to continue ? This.actions.will destroy the previous wireguard config !')
                result = confirm()
        except Exception as err:
            result = False
            logging.error("Failed to check if VPC with the same name already exists")
            logging.error(err)
        return result


    def create_subnet(self, is_dry_run, vpc_id, subnet_name_arg="SNET-Rotata"):
        response=None
        try:
            response = self.client.create_subnet(
                TagSpecifications=[
                    {
                        'ResourceType': 'subnet',
                        'Tags': [
                            {
                                'Key': 'tool',
                                'Value': 'Rotata'
                            },
                            {
                                'Key': 'Name',
                                'Value': subnet_name_arg
                            }
                        ]
                    },
                ],
                CidrBlock='10.200.1.0/24',
                VpcId=vpc_id,
                DryRun=is_dry_run,
                Ipv6Native=False
            )
        except botocore.exceptions.ClientError as err:
            logging.error("Something wrong happened when creating subnets:")
            logging.error(err)
        return response

    # Should be at the end because i should sort methods by alphabetical order
    def describe_subnets(self, subnet_ids=[], vpc_id_filter=[]):
        response = None
        fltr = [{}]
        if len(vpc_id_filter) > 0:
            fltr.append({'Name':'vpc-id', 'Values':vpc_id_filter})
        try:
            response = self.client.describe_subnets(
                Filters=fltr,
                SubnetIds=subnet_ids
            )
        except botocore.exceptions.ClientError as err:
            logging.error("Something wrong happened when describing subnets:")
            logging.error(err)
        return response

    def delete_vpc(self, vpc_id):
        response = None
        try:
            response = self.client.delete_vpc(
                VpcId=vpc_id
            )
        except botocore.exceptions.ClientError as err:
            logging.error("Something wrong happened when deleting VPCS:")
            logging.error(err)
        return response

    def delete_subnet(self, subnet_id):
        response = None
        try:
            response = self.client.delete_subnet(
                SubnetId=subnet_id
            )
        except botocore.exceptions.ClientError as err:
            logging.error("Something wrong happened when deleting subnets:")
            logging.error(err)
        return response

