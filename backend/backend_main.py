import json
import logging
import os
import db_sql as sqldb
from cache import RedisClient
from network_scanner import NmapScanner
from status_collector import Collector
import db_mongo as mongodb
from utils.enrich_net_data import enrich_net_data

logging.basicConfig(level=logging.INFO)


def print_netmind_small_ascii():
    print(
        """

            _  ___  ____           _
           | | |  \/  (_)         | |
 _ __   ___| |_| .  . |_ _ __   __| |
| '_ \ / _ \ __| |\/| | | '_ \ / _` |
| | | |  __/ |_| |  | | | | | | (_| |
|_| |_|\___|\__\_|  |_/_|_| |_|\__,_|


SDE: zamikx
@05-24-2025 22:21
    """
    )


def main():
    print_netmind_small_ascii()
    print("\U0001f600")
    # config = json.load(open("../config/tool_config.json"))
    # Get the directory where main.py is located
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(base_dir)
    # Construct the full path to the config file
    config_path = os.path.join(base_dir, "..", "config", "tool_config.json")
    print(config_path)
    # Load the config
    with open(config_path) as f:
        config = json.load(f)

    logging.info(f"Loading Configuration {config}")
    network_stats = {}
    subnets = config["subnets"]
    subnets_scan_obj = NmapScanner(subnets).scan_network()
    redis_client = RedisClient(host="localhost", port=6379, db=0)
    mongodb_client = mongodb.init_mongo_client()
    for subnet in subnets:
        hosts_ips=[]
        hosts_details = subnets_scan_obj.get(subnet).get("hosts")
        logging.info(f"Hosts details are : {hosts_details}")
        for host in hosts_details:
            hosts_ips.append(host.get("ip"))

        print("---------")
        logging.info(f"Hosts IPs are : {hosts_ips}")
        collector = Collector(hosts_ips)
        network_stats[subnet] = collector.run_test_ping()
        enriched_net_data = enrich_net_data(hosts_details, network_stats.get(subnet))
        redis_client.set_cache(key=subnet+"_network_latency_cache", data=enriched_net_data, ttl=3000)
    # redis_client.get_cache(key="peter_latency_cache")
    # print("trying again after 3 seconds")
    # time.sleep(3)
    # redis_client.get_cache(key="peter_latency_cache")
    # redis_client.get_cache(key = "peter_latency_cache")
        logging.info(f"Subnet {subnet} has enriched network data : {enriched_net_data}")
        sqldb.create_table(subnet)
        sqldb.insert_network_stats(subnet, enriched_net_data)
    # sqldb.fetch_all_stats()
    
        mongodb.insert_network_data_mondb(mongodb_client, subnet, enriched_net_data)


if __name__ == "__main__":
    main()
