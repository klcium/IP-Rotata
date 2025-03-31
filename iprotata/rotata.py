#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from iprotata.cli import gen_cli_args
from iprotata.first_run import setup_local_env
from iprotata.actions.setup import setup_aws
from iprotata.actions.clean import clean_aws
from iprotata.logger import setup_logger
from iprotata.actions.list import list_resources
from iprotata.actions.rotate import rotate
from iprotata.actions.session import Session
import boto3

logger = setup_logger()

def main():
    # STOP BEING SUSSY
    setup_local_env(logger)
    args = gen_cli_args()
    # if args.egg:
    #     print("HIHI egg funni")
    #     exit(0)
    session_object = Session(profile_name=args.profile_name)
    match args.action:
        case 'setup':
            setup_aws(args, session_object)
        case 'delete':
            clean_aws(args, session_object)
        case 'list':
            list_resources(args, session_object)
        case 'rotate':
            rotate(args, session_object)

