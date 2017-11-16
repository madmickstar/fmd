#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
login to Cisco WLC and enable LED on WAPs where a specifici client is associated
"""
import os
import re
import sys
import json
import getpass
import logging
import time
from datetime import datetime
from netmiko import ConnectHandler
from argparse import ArgumentParser, RawTextHelpFormatter      # Formatting help

from _version import __version__
import fmd_tools


def process_cli():
    # processes cli arguments and usage guide
    parser = ArgumentParser(prog='fmd',
    description='''         Cisco Wirless Access Point WAP association monitoring tool, this assists with identifiying \n \
        which WAP a client is associated too and reporting it to a log and enabled WAP LED flash feature firewall rules
        ''',
    epilog='''Command line examples \n\n \
        ## Windows and POSIX Users ## \n \
        python fmd.py -wlc 192.168.1.1 00:11:22:33:44:55 \n \
        python fmd.py -wlc 192.168.1.1 -p tyrone \n \
        \n \
        ## Frozen ##
        fmd -wlc 192.168.1.1 00:11:22:33:44:55 \n \
        fmd -wlc 192.168.1.1 -p tyrone \n \
        ''',
    formatter_class=RawTextHelpFormatter)
    g1 = parser.add_mutually_exclusive_group()
    g2 = parser.add_mutually_exclusive_group()
    g1.add_argument('mac',
        nargs='*',
        default=False,
        #default=('00:11:22:33:44:55',),
        metavar=('{MAC Address xx:xx:xx:xx:xx:xx}'),
        help='Client MAC address to monitor')
    g1.add_argument('-p', '--profile',
        nargs='?',
        default=False,
        help='Enable profile settings')
    parser.add_argument('-wlc', '--wireless-lan-controller',
        type=str,
        metavar=('{ip address xx.xx.xx.xx}'),
        help='WLC management IP addresss')
    parser.add_argument('-f', '--frequency',
        default='5',
        type=int,
        choices=[5, 10, 15, 20, 25, 30],
        metavar=('{5, 10, 15, 20, 25, 30}'),
        help='Frequency to update client location and details in seconds, default = 5')
    parser.add_argument('-m', '--minutes',
        default='1',
        type=int,
        choices=[1, 5, 10, 30, 60, 120, 180, 240, 300, 360, 720],
        metavar=('{1, 5, 10, 30, 60, 120, 180, 240, 300, 360, 720}'),
        help='Duration of monitoring client in minutes, default = 1')
    parser.add_argument('-mw', '--max-waps',
        default='2',
        type=int,
        choices=range(2, 10),
        metavar=('{2..10}'),
        help='Max WAPs when disco mode is enabled, default = 2')
    g2.add_argument('-dm', '--disco-mode',
        action="store_true",
        help='Enables follow me disco mode, default = disabled')
    g2.add_argument('-sm', '--sitesurvey-mode',
        action="store_true",
        help='Enables site survey mode, default = disabled')
    parser.add_argument('-cv', '--console-verbose',
        action="store_true",
        help='Enable verbose console mode for SSH session')
    parser.add_argument('-l', '--log',
        action="store_true",
        help='Enable logging to a file')
    parser.add_argument('-t', '--timestamp',
        action="store_true",
        help='Enable timestamping log output to console')
    parser.add_argument('-d', '--debug',
        action="store_true",
        help='Enable debug output to console')
    parser.add_argument('--version',
        action='version',
        version='%(prog)s v'+__version__)

    args = parser.parse_args()
    return args


class Whitelist(logging.Filter):
    def __init__(self, *whitelist):
        self.whitelist = [logging.Filter(name) for name in whitelist]

    def filter(self, record):
        return any(f.filter(record) for f in self.whitelist)


def configure_logging(args):
    """
    Creates logging configuration and sets logging level based on cli argument

    Args:
        args.debug: all arguments parsed from cli

    Returns:
        logging: logging configuration
    """
    if args.debug:
        logging.basicConfig(stream=sys.stdout,
                            #level=logging.INFO,
                            level=logging.DEBUG,
                            datefmt='%Y-%m-%d %H:%M:%S',
                            format='[%(asctime)s] [%(levelname)-5s] [%(name)s] %(message)s')
        for handler in logging.root.handlers:
            handler.addFilter(Whitelist('fmd_tools', '__main__'))
        print_args(args)

    elif args.timestamp:
        logging.basicConfig(stream=sys.stdout,
                            level=logging.INFO,
                            datefmt='%Y-%m-%d %H:%M:%S',
                            format='[%(asctime)s] %(message)s')
    else:
        logging.basicConfig(stream=sys.stdout,
                            level=logging.INFO,
                            format='%(message)s')
    return logging    
    
    
def print_args(args):
    """
    Prints out cli arguments in nice format when debugging is enabled
    """
    logger = logging.getLogger(__name__)
    counter_mac = 0
    logger.debug('')
    logger.debug('CLI Arguments, %s', args)
    if args.mac:
        for macs in args.mac:
            counter_mac += 1
            logger.debug('CLI Arguments, mac %s %s', counter_mac, macs)
    logger.debug('')

    
def process_profiles(profiles_json):
    logger = logging.getLogger(__name__)
    logger.debug('JSON file %s', profiles_json)

    json_data = False
    ## Reading data back
    with open(profiles_json, 'r') as f:
         try:
             json_data = json.load(f)
             logger.info('Profiles loaded from JSON successfully')
             logger.debug('JSON conversion %s', json_data)
         except ValueError as err:
             raise RuntimeError('JSON content bad %s' % err)
         except Exception, err:
             raise RuntimeError('JSON unknown error %s' % err)
    return json_data
    

def get_profile_macs(profile, json_data):
    logger = logging.getLogger(__name__)

    # set profile name to use
    if profile is not None:
        active_profile = profile
    else:
        active_profile = json_data['Activate_profile']

    logger.info('Profile chosen is %s', active_profile)

    profile_macs = False
    for key in json_data['profiles'].keys():
        if key in active_profile:
            profile_macs = json_data['profiles'][key]['macs']
            logger.debug('Profile %s has MACs %s', active_profile, profile_macs)
            break

    if profile_macs:
        if len(profile_macs) >= 1:
            macs_to_monitor = profile_macs
        else:
            raise RuntimeError('Profile has no MACs, found %s' % len(profile_macs))
    else:
        raise RuntimeError('No profiles found matching name %s' % active_profile)

    return macs_to_monitor


class ProfileServer:

    def __init__(self, hostname):
        self._hostname = hostname

        # search and replace unwanted strings in URL like http:// , :80 , /xxxx/xxx
        p = re.compile('^.*//|:.*$|/.*$', re.VERBOSE)
        self._cleaned_domain = p.sub(r'', hostname)

        if self._cleaned_domain[-1] == ".":
            self._cleaned_domain = self._cleaned_domain[:-1] # strip exactly one dot from the right, if present

        allowed = re.compile("(?!-)[A-Za-z0-9-_]{1,63}(?<!-)$", re.IGNORECASE)
        if not all(allowed.match(x) for x in self._cleaned_domain.split(".")):
            raise ValueError("%-30s Invalid characters -" % self._cleaned_domain)
        if len(self._cleaned_domain) > 255:
            raise ValueError("%-30s Invalid length -" % self._cleaned_domain)

        self._hostname_type = self._hostnameType()

    def hostname(self):
        return self._hostname

    def cleaned_domain(self):
        return self._cleaned_domain

    def hostname_type(self):
        return self._hostname_type

    def _hostnameType(self):
        try:
            socket.inet_aton(self._cleaned_domain)
            return "IP"
        except:
            pass
        try:
            valid = re.search('^([A-Za-z0-9-_]){1,63}$', self._cleaned_domain, re.M|re.I)
            valid.group(1)
            return "HOSTNAME"
        except:
            pass
        allowed = re.compile("(?!-)[A-Za-z0-9-_]{1,63}(?<!-)$", re.IGNORECASE)
        if all(allowed.match(x) for x in self._cleaned_domain.split(".")):
            return "FQDN"
        return None


class ProfileMAC:

    def __init__(self, mac):
        """
        validates and profiles mac addresses

        Args:
            mac: mac address to validate and profile
            fronzen_state: Frozen state as a True or False

        Raises:
            ValueError: if validation fails
        """
        self._mac = mac

        p = re.compile('[-\._:]', re.VERBOSE)
        self._cleaned_mac = p.sub(r'', self._mac)

        if not len(self._cleaned_mac) == 12:
            raise ValueError("%-20s Invalid length -" % self._mac)
        if not self._validate_mac():
            raise ValueError("%-20s Invalid characters -" % self._mac)

        self._cisco_mac = '.'.join(a+b+c+d for a,b,c,d in zip(self._cleaned_mac[::4], self._cleaned_mac[1::4], self._cleaned_mac[2::4], self._cleaned_mac[3::4]))
        self._windows_mac = '-'.join(a+b for a,b in zip(self._cleaned_mac[::2], self._cleaned_mac[1::2]))
        self._standard_mac = ':'.join(a+b for a,b in zip(self._cleaned_mac[::2], self._cleaned_mac[1::2]))
        self._iou_search_mac = self._cleaned_mac[:6]

    def cisco_mac(self):
        return self._cisco_mac.lower()

    def windows_mac(self):
        return self._windows_mac.upper()

    def standard_mac(self):
        return self._standard_mac.upper()

    def cleaned_mac(self):
        return self._cleaned_mac

    def iou_search_mac(self):
        return self._iou_search_mac

    def _validate_mac(self):
        try:
            valid = re.search('^([0-9a-f]){12}$', self._cleaned_mac, re.M|re.I)
            valid.group(1)
            return True
        except:
            return False


class ProfileWifiClient:
    '''
    builds a client profile and returns the profile in a dictionary
    '''

    def __init__(self, output):

        self.output = output
        self.client_details = {
            'Status': False
        }

        # real script
        rx_sequence=re.compile(r"^Client.MAC.Address\.+\s(.+)\n^Client.Username\s\.+\s(.+)\n^AP.MAC.Address\.+\s(.+)\n^AP.Name\.+\s(.+)\n",re.MULTILINE)
        # test script
        #rx_sequence=re.compile(r"^\s+Client.MAC.Address\.+\s(.+)\n^\s+Client.Username\s\.+\s(.+)\n^\s+AP.MAC.Address\.+\s(.+)\n^\s+AP.Name\.+\s(.+)\n",re.MULTILINE)
        for match in rx_sequence.finditer(self.output):
            title = match.groups()
            self.client_details['Status'] = True
            self.client_details['Client_MAC'] = title[0].rstrip()
            self.client_details['Username'] = title[1].rstrip()
            self.client_details['WAP_MAC'] = title[2].rstrip()
            self.client_details['WAP_Name'] = title[3].rstrip()
            self.client_details['Signal'] = 'Not Detected'
            self.client_details['SNR'] = 'Not Detected'
            self.client_details['SSID'] = 'Not Detected'

        if self.client_details['Status']:
            # real script
            rx_sequence=re.compile(r"^Wireless.LAN.Network.Name..SSID.\.+\s(.+)\n",re.MULTILINE)
            # test script
            #rx_sequence=re.compile(r"^\s+Wireless.LAN.Network.Name..SSID.\.+\s(.+)\n",re.MULTILINE)
            for match in rx_sequence.finditer(self.output):
                title = match.groups()
                self.client_details['SSID'] = title[0].rstrip()

            # real script
            rx_sequence=re.compile(r"^\s+Radio.Signal.Strength.Indicator\.+\s(.+)\n^\s+Signal.to.Noise.Ratio\.+\s(.+)\n",re.MULTILINE)
            # test script
            #rx_sequence=re.compile(r"^\s+Radio.Signal.Strength.Indicator\.+\s(.+)\n^\s+Signal.to.Noise.Ratio\.+\s(.+)\n",re.MULTILINE)
            for match in rx_sequence.finditer(self.output):
                title = match.groups()
                self.client_details['Signal'] = title[0].rstrip()
                self.client_details['SNR'] = title[1].rstrip()

            #print client_details
            #logger.info('User %s MAC %s WAP %s SSID %s SS %s SNR %s', self.client_details['Username'], self.client_details['Client_MAC'], self.client_details['WAP_Name'], self.client_details['SSID'], self.client_details['Signal'], self.client_details['SNR'])

            # real script
            rx_sequence=re.compile(r"^\s+([A-Z0-9-_]+).slot.\d.\n^\s+antenna\d:\s([0-9]|[1-5][0-9])\ssec.*(-\d{1,3}).dBm\n^\s+antenna\d.*(-\d{1,3}).dBm",re.MULTILINE)
            # test script
            #rx_sequence=re.compile(r"^\s+([A-Z0-9-_]+).slot.\d.\n^\s+antenna\d:\s([0-9]|[1-5][0-9])\ssec.*(-\d{1,3}).dBm\n^\s+antenna\d.*(-\d{1,3}).dBm",re.MULTILINE)

            # use output from WLC and list WAPs and there signal strengths
            self.lol_signals = []
            for match in rx_sequence.finditer(self.output):
                title = match.groups()
                self.lol_signals.append(title)
            #logger.debug('DiscoMode matches %s', rx_sequence)
            #logger.debug('WAPs signal %s', lol_signals)


            # get signal strength average
            self.lol_signals_mean = []
            for wap, timeout, lv1, lv2 in self.lol_signals:
                avg_sig = ((int(lv1) + int(lv2)) / 2)
                wap_avg_sig = wap, avg_sig, timeout
                self.lol_signals_mean.append(wap_avg_sig)
            #logger.debug('WAPs Average signal %s', self.lol_signals_mean)

            # sort by signal strength in reverse order
            self.lol_signals_mean.sort(key=lambda x: x[1], reverse=True)
            self.client_details['WAP_Neighbours'] = self.lol_signals_mean

    def get_client_profile(self):
        return self.client_details
    
    
def format_profile(client_details):
    logger = logging.getLogger(__name__)

    logger.debug('')
    if client_details['Status']:

        logger.debug('Client profile - Username - %s', client_details['Username'])
        logger.debug('Client profile - SSID - %s', client_details['SSID'])
        logger.debug('Client profile - Signal - %s', client_details['Signal'])
        logger.debug('Client profile - WAP_MAC - %s', client_details['WAP_MAC'])
        logger.debug('Client profile - SNR - %s', client_details['SNR'])
        logger.debug('Client profile - WAP_Name - %s', client_details['WAP_Name'])
        logger.debug('Client profile - Client_MAC - %s', client_details['Client_MAC'])
        if len(client_details['WAP_Neighbours']) >= 1:
            counter_neighbours = 0
            logger.debug('Client profile - Neighbour WAPs %s', len(client_details['WAP_Neighbours']))
            for a, b, c in client_details['WAP_Neighbours']:
                counter_neighbours += 1
                logger.debug('Client profile - %s: %s %s dBm %s secs', counter_neighbours, a, b, c)
        else:
            logger.debug('Client profile - No Neighbouring WAPs Detected')
    else:
        logger.debug('Client profile - Status is False')
    #logger.debug('')


def site_survey_mode(net_connect, client_details, flash_secs):
    logger = logging.getLogger(__name__)
    cli_cmd = 'config ap led-state flash %s %s' % (flash_secs, client_details['WAP_Name'])
    logger.debug('Survey Mode - Command sent to WLC %s', cli_cmd)
    output = net_connect.send_command(cli_cmd)
    logger.debug('Survey Mode - WLC response %s', output)
       
        
def disco_mode(net_connect, client_details, flash_secs, max_waps):
    logger = logging.getLogger(__name__)

    # seperate WAPs with highest signal, store only their name
    logger.debug('Disco mode - %s WAPS found', len(client_details['WAP_Neighbours']))
    target_waps = []
    # add associated WAP as first target
    target_waps.append(client_details['WAP_Name'])
    for x in client_details['WAP_Neighbours']:
        if len(target_waps) > max_waps:
            break
        if x[0] not in target_waps:
            target_waps.append(x[0])
    logger.debug('Disco mode - %s WAPS will be used %s', len(target_waps), target_waps)

    for wap in target_waps:
        cli_cmd = 'config ap led-state flash %s %s' % (flash_secs, wap)
        logger.debug('Disco Mode - Command sent to WLC %s', cli_cmd)
        output = net_connect.send_command(cli_cmd)
        logger.debug('Disco Mode - WLC response %s', output)


def main():
    app_dir = '.fmd'
    working_dir = fmd_tools.process_user_home_app_dir(app_dir)
    args = process_cli()

    logging = configure_logging(args)
    logger = logging.getLogger(__name__)

    if args.mac == False and args.profile == False:
        logger.error('No MAC or profile defined, Exiting...')
        sys.exit(1)

    # check write permissions
    profiles_json = 'profiles.json'
    log_file = 'fdm.log'
    try:
        profiles_json, log_file, current_working_dir = fmd_tools.permissions(working_dir, profiles_json, log_file)
    except Exception, err:
        logger.error(str(err))
        sys.exit(1)

    if args.mac:
        macs_to_monitor = args.mac
    elif args.profile is not False:
        try:
            json_data = process_profiles(profiles_json)
        except Exception, err:
            logger.error(str(err))
            sys.exit(1)
        try:
            macs_to_monitor = get_profile_macs(args.profile, json_data)
        except Exception, err:
            logger.error(str(err))
            sys.exit(1)
    else:
        logger.error('No profiles or MACs supplied exiting')
        sys.exit(1)

    username = raw_input('Username: ')
    password = getpass.getpass()

    duration = args.minutes * 60
    flash_secs = args.frequency + 5
    finish_time = time.clock() + duration
    max_waps = args.max_waps - 1
    wlc_ip = args.wireless_lan_controller
    verbose = args.console_verbose
    formatted_time = fmd_tools.format_time(finish_time - time.clock())

    try:
        a = ProfileServer(wlc_ip)
    except ValueError as err:
        logger.error('%s Skipping', err)
        sys.exit(1)
    except Exception, err:
        logger.error('%s Unknown error', err)
        sys.exit(1)

    wlc_ip = a.cleaned_domain()
    conn_dict = {
        'device_type': 'cisco_wlc_ssh',
        'ip' : wlc_ip,
        'username' : username,
        'password' : password,
        'verbose': verbose,
    }

    try:
        net_connect = ConnectHandler(**conn_dict)
    except Exception, err:
        logger.error('%s', err)
        sys.exit(1)
    finally:
        del username, password, conn_dict

    logger.debug('Duration %s', formatted_time)
    while time.clock() < finish_time:
        formatted_time = fmd_tools.format_time(finish_time - time.clock())
        for macs in macs_to_monitor:
            try:
                a = ProfileMAC(macs)
            except Exception, err:
                logger.error('%s Skipping', err)
                continue
            #logger.debug('Processing %s', a.standard_mac())
            cli_cmd = 'show client detail %s' % a.standard_mac()
            output = net_connect.send_command(cli_cmd)

            b = ProfileWifiClient(output)
            client_details = b.get_client_profile()

            if args.debug:
                format_profile(client_details)

            if client_details['Status']:
                # if device has just connected and some values are still unknown
                # or being connected for some time and has neighbours
                if client_details['Signal'] == 'Unknown' or len(client_details['WAP_Neighbours']) >= 1:
                    logger.info('%s User %s MAC %s WAP %s SSID %s SS %s SNR %s', formatted_time, client_details['Username'], client_details['Client_MAC'], client_details['WAP_Name'], client_details['SSID'], client_details['Signal'], client_details['SNR'])
                    if args.sitesurvey_mode:
                        site_survey_mode(net_connect, client_details, flash_secs)
                    elif args.disco_mode:
                        disco_mode(net_connect, client_details, flash_secs, max_waps)
                # else the device has not spoken to WLC in more than 60 seconds it means it has disappeared
                # and WLC will hang on to association for another 5 minutes
                else:
                    logger.info('%s User %s MAC %s WAP %s SSID %s - timeout greater than 60 seconds', formatted_time, client_details['Username'], client_details['Client_MAC'], client_details['WAP_Name'], client_details['SSID'])
            else:
                logger.info('%s Client with MAC %s is not associated with WLC', formatted_time, a.standard_mac())
        time.sleep(args.frequency)


if __name__ == '__main__':
    main()