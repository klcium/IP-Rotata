#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from iprotata.aws.vpc import Vpc
from iprotata.aws.ec2 import Ec2
import logging

def list_args(parser, std_parser):
    setup_parser = parser.add_parser('list', help='List ressources of AWS', parents=[std_parser], formatter_class=std_parser.formatter_class)
    subparsers = setup_parser.add_subparsers(title='Resources', dest='resource', description='Available resources to list' )
    # Keys parsing
    subparsers.add_parser('keys', help='List EC2 Key pairs', parents=[std_parser], formatter_class=std_parser.formatter_class)
    return parser

def init_sess_object(client_type, session_object, region_name=''):
    aws_session_object = None
    match client_type:
        case 'EC2':
            aws_session_object = Ec2(session=session_object._session, region_name=region_name)
        case 'VPC':
            aws_session_object = Vpc(session=session_object._session, region_name=region_name)
    return aws_session_object


def list_resources(args, session_object):
    match args.resource:
        case 'keys':
            ec2_client = init_sess_object(client_type='EC2', session_object=session_object, region_name=args.region_name)
            response = ec2_client.describe_key_pairs()
            if hasattr(response, '__iter__') and ('KeyPairs' in response):
                print('The following keys were found:')
                print('-'*40)
                print('Key ID\t\t\tKey Name')
                print('-'*40)
                for key in response['KeyPairs']:
                    print('{}\t{}'.format(key["KeyPairId"],key["KeyName"]))
        
