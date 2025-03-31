#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sqlite3
from sys import platform

ROTATA_PATH = os.path.expanduser('~/.rotata')
TMP_PATH = os.path.join('/tmp','rotata_files')

def setup_local_env(logger):    
    if platform != "linux":
        print('Fuck you bill gates, fuck you steve jobs')
        exit(1)

    if not os.path.exists(os.path.join(TMP_PATH)):
        os.mkdir(TMP_PATH)
    
    if not os.path.exists(os.path.join(ROTATA_PATH)):
        logger.info('First time rotata use detected')
        logger.info('Creating folders')
        os.mkdir(ROTATA_PATH)

    folders = ['logs']
    for folder in folders:
        if not os.path.exists(os.path.join(ROTATA_PATH, folder)):
            os.mkdir(os.path.join(ROTATA_PATH, folder))
    