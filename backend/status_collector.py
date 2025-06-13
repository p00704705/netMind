"""
Business logic

collector.py – Metric collector engine
        •	Runs periodic ping or iperf3 tests to targets (e.g., 8.8.8.8, internal IPs)
        •	Parses latency/jitter/bandwidth from results
        •	Writes structured data into DB (via db.py)
        •	Logs failures, timeouts, unreachable hosts
        •	Later: could accept a YAML config file for dynamic targets
"""

import logging
import re
import subprocess


logging.basicConfig(level=logging.DEBUG)


class Collector:
    def __init__(self, targets, ping_command="ping -c 5 "):
        self.targets = targets
        self.ping_command = ping_command

    def run_test_ping(self):
        network_state = {}
        for target in self.targets:
            logging.info(f"== Pinging target: {target} ==")
            p = subprocess.Popen(
                self.ping_command + target,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdoutdata, stderrdata = p.communicate()
            # logging.info(f"stdoutdata: \n{stdoutdata}")
            if stderrdata:
                logging.info(f"stderrdata: \n{stderrdata}")
            packet_loss, avg_latency = self.analyze_ping_results(stdoutdata)
            network_state[target] = {
                "packet_loss": packet_loss,
                "avg_latency": avg_latency,
            }
        logging.info(f"Network_state: {network_state}")
        return network_state

    def analyze_ping_results(self, ping_results):
        # Extract all packet loss values
        packet_loss = re.findall(r"(\d+|\d+\.\d+)% packet loss", ping_results)

        # Extract all average latencies
        avg_latency = re.findall(
            r"rtt min/avg/max/mdev = [\d.]+/([\d.]+)", ping_results
        )

        logging.info(f"Packet Loss Values:{packet_loss}")
        logging.info(f"Average Latencies:{avg_latency}")
        return packet_loss, avg_latency
