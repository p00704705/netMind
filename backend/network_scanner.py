"""
>>> nm.scan("192.168.1.0/24", arguments='-PR -sn')
'command_line': 'nmap -oX - -PR -sn 192.168.1.0/24',
"""

import datetime
import ipaddress
import json
import logging
import os
import re
import subprocess
import sys
import time
import timeit

import nmap

logging.basicConfig(level=logging.DEBUG)


class NmapScanner:
    def __init__(self, subnets):
        self.subnets = subnets

    def get_subnet_ips(self, subnet):
        ip_list = [str(ip) for ip in ipaddress.IPv4Network(subnet).hosts()]
        return ip_list

    def scan_network(self):
        scan_start_time = time.perf_counter()
        nm = nmap.PortScanner()
        subnet_scan__obj = {}
        logging.info(f"User input subnets are {self.subnets}")
        for subnet in self.subnets:
            logging.info(f"Scanning subnet {subnet}")
            scan_output = nm.scan(subnet, arguments="-PR -sn --max-retries 0")
            logging.info(f"Scan output for subnet {subnet} is {scan_output}\n")
            hosts_details = nm.all_hosts()
            logging.info(
                f"Hosts details for subnet {subnet} is {hosts_details}\n")
            scan_stats = nm.scanstats()
            logging.info(f"Scan stats for subnet {subnet} is {scan_stats}\n")
            subnet_scan__obj[subnet] = {
                "scan_stats": scan_stats,
                "hosts_ips": hosts_details,
                "scan_output": scan_output,
            }
        scan_end_time = time.perf_counter()
        network_scan_duration = scan_end_time - scan_start_time
        logging.info(
            f"Network scan duration is {network_scan_duration} seconds")

        return subnet_scan__obj
