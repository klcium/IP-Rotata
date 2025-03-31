#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3
import boto3.session
from botocore.config import Config
import botocore.exceptions
import logging

class Session:
    def __init__(self, profile_name):
        try:
            self._session = boto3.Session(profile_name=profile_name)
        except botocore.exceptions.ProfileNotFound as error:
            logging.error('The parameters you provided are incorrect: {}'.format(error))
            exit(1)