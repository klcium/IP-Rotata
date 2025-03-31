#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# THIS PAGE IS MOSTLY COPY PASTA FROM 
# Source https://github.com/Porchetta-Industries/CrackMapExec/blob/31542973d79a0acdbad5c28d155eec0205371200/cme/logger.py#L124

import logging
import sys
import re
from termcolor import colored
from datetime import datetime
import os

ROTATA_PATH = os.path.expanduser('~/.rotata')

def setup_logger(level=logging.INFO, log_prefix=None, logger_name='ROTATA'):
    formatter = logging.Formatter("%(message)s")

    streamHandler = logging.StreamHandler(sys.stdout)
    streamHandler.setFormatter(formatter)

    rotata_logger = logging.getLogger(logger_name)
    rotata_logger.propagate = False
    rotata_logger.addHandler(streamHandler)

    rotata_logger.setLevel(level)
    return rotata_logger

def log_ip_action(action, ip):
    log_prefix = 'IP_History'
    log_filename = '{}_{}.log'.format(log_prefix.replace('/', '_'), datetime.now().strftime('%y-%m-%d'))
    

    with open("{}/logs/{}".format(ROTATA_PATH, log_filename), 'a') as logfile:
        time = datetime.now().strftime('[%Y-%m-%d_%H:%M]')
        message = "{} {}\t{}\n".format(time, action, ip)
        logfile.write(message)
