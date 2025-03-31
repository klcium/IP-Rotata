#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse
from argparse import RawTextHelpFormatter
from termcolor import colored
import termcolor
# from iprotata.actions.setup import Setup
from iprotata.formatter_class import CustomHelpFormatter
from iprotata.actions.setup import setup_args
from iprotata.actions.clean import clean_args
from iprotata.actions.list import list_args
from iprotata.actions.rotate import rotate_args


def gen_cli_args():

    VERSION = '0.0.9'
    root_parser = argparse.ArgumentParser(description=f"""
    _____________________________________________________________________________________
    
    ::::::::::: :::::::::        :::::::::   :::::::: ::::::::::: ::: ::::::::::: :::     
        :+:     :+:    :+:       :+:    :+: :+:    :+:    :+:   :+: :+:   :+:   :+: :+:   
        +:+     +:+    +:+       +:+    +:+ +:+    +:+    +:+  +:+   +:+  +:+  +:+   +:+  
        +#+     +#++:++#+        +#++:++#:  +#+    +:+    +#+ +#++:++#++: +#+ +#++:++#++: 
        +#+     +#+              +#+    +#+ +#+    +#+    +#+ +#+     +#+ +#+ +#+     +#+ 
        #+#     #+#              #+#    #+# #+#    #+#    #+# #+#     #+# #+# #+#     #+# 
    ########### ###              ###    ###  ########     ### ###     ### ### ###     ### 
    _____________________________________________________________________________________
    
                        {colored("Rotata makes your IP ROTATE", 'yellow', attrs=['bold'])}{colored(" FASSTERRR  !!!", 'red', attrs=['bold'])}
                        
                                {colored("VERSION : ", 'magenta', attrs=['bold'])}{colored(VERSION, 'magenta', attrs=['bold'])}
    """,
    formatter_class=RawTextHelpFormatter)

    global_parser = argparse.ArgumentParser(
        add_help=False,
        formatter_class=CustomHelpFormatter
        )
    # global_parser.add_argument("--egg", dest='egg', action='store_true', help='Variable test')
    global_parser.add_argument("--profile ", "-p", dest='profile_name', default='default', type=str, help='AWS configuration profile to use')
    global_parser.add_argument("--region ","-r", dest='region_name', default=None, type=str, help='AWS region to use, overrides your default session')
    global_parser.add_argument("--dry-run", dest='is_dryrun', action='store_true', help='Dry run does not actually creates/modify or delete any resources')

    subparsers = root_parser.add_subparsers(title='Actions', dest='action', description='available actions' )
    setup_args(subparsers, global_parser)
    rotate_args(subparsers, global_parser)
    list_args(subparsers, global_parser)
    clean_args(subparsers, global_parser)


    if len(sys.argv) == 1:
        root_parser.print_help()
        sys.exit(1)

    args = root_parser.parse_args()

    return args