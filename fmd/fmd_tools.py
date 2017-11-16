#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
import time
import json
import logging
import datetime
from codecs import open


def process_user_home_app_dir(app_dir):
    '''
    Checks for working dir in home directory and if writable
    If it is not there it checks for write access to home dir and creates working dir

    Returns Users home application dir
    '''
    # prep working dir in users home DIR
    user_home_dir = os.path.expanduser('~')
    user_home_app_dir = os.path.join(user_home_dir, app_dir)

    if os.path.isdir(user_home_app_dir):
        if not check_write_dir(user_home_app_dir):
            sys.stderr.write('ERROR: Failed write access to user home app DIR %s, exiting....' % user_home_app_dir)
            sys.exit(1)
    else:
        if not os.path.isdir(user_home_dir):
            sys.stderr.write('ERROR: Failed to find user home DIR %s, exiting....' % user_home_dir)
            sys.exit(1)
        else:
            if not check_write_dir(user_home_dir):
                sys.stderr.write('ERROR: Failed write access to user home DIR %s, exiting....' % user_home_dir)
                sys.exit(1)
            else:
                # create working dir in home dir
                try:
                    os.makedirs(user_home_app_dir)
                except:
                    sys.stderr.write('ERROR: Failed to create user home app DIR %s, exiting....' % user_home_app_dir)
                    sys.exit(1)
    return user_home_app_dir

def create_sample_profiles_file(profiles_json):
    # create sample profiles json file
    tyrone_macs = ['00:11:22:33:44:55', '11:22:33:44:55:66']
    tbone_macs = ['00:11:22:33:44:55']
    sample_profile = {
         'Activate_profile': 'tyrone',
         'profiles': {
             'tyrone': {
                   'macs' : tyrone_macs
             },
             'tbone': {
                   'macs' : tbone_macs
             }
         }
    }
    ## Writing JSON data
    with open(profiles_json, 'w') as f:
         json.dump(sample_profile,
                   f,
                   sort_keys = False,
                   indent = 4,
                   ensure_ascii = False)

def permissions(user_home_app_dir, profiles_json, log_file):
    # check write permissions
    logger = logging.getLogger(__name__)

    current_dir = os.getcwd()
    app_dir = os.path.dirname(sys.argv[0])
    app_dir_complete = os.path.join(current_dir, app_dir)
    log_file = os.path.join(user_home_app_dir, log_file)
    profiles_json = os.path.join(current_dir, app_dir, profiles_json)

    logger.debug('Current DIR  %s', current_dir)
    logger.debug('Application DIR %s', app_dir)
    logger.debug('Application DIR complete %s', app_dir_complete)
    logger.debug('Log DIR complete %s', log_file)
    logger.debug('Resulting JSON file %s', profiles_json)
    
    # test current dir
    if not check_write_dir(current_dir):
        raise RuntimeError('Permissions check - Failed write access in current working folder %s exiting....' % current_dir)
    else:
        logger.debug('Current working DIR is writable %s', current_dir)

    # test app dir
    if not check_write_dir(app_dir_complete):
        raise RuntimeError('Permissions check - Failed write access in Application folder %s exiting....' % app_dir_complete)
    else:
        logger.debug('Application DIR is writable %s', app_dir_complete)

    # test creds file
    if os.path.isfile(log_file):
        if not check_read_file(log_file):
            raise RuntimeError('Permissions check - Creds file failed read test %s exiting....' % log_file)
        else:
            logger.debug('Creds file exists and is readable %s', log_file)

    # test profiles file
    if os.path.isfile(profiles_json):
        if not check_write_file(profiles_json):
            raise RuntimeError('Permissions check - profiles file failed write test %s exiting....' % profiles_json)
        else:
            logger.debug('Profiles file exists and is readable %s', profiles_json)
    else:
        create_sample_profiles_file(profiles_json)

    logger.debug('Successfully passed all read write access tests')
    return profiles_json, log_file, current_dir
    
def format_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    formatted_time = "%d:%02d:%02d" % (h, m, s)
    return formatted_time    
    
def check_write_dir(test_dir):
    if not os.access(test_dir, os.W_OK):
        return False
    return True


def check_write_file(test_file):
    if not os.access(test_file, os.W_OK):
        return False
    return True


def check_exists_file(test_file):
    if not os.access(test_file, os.F_OK):
        return False
    return True

def check_read_file(test_file):
    if not os.access(test_file, os.R_OK):
        return False
    return True