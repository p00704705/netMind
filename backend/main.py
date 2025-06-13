import json
import logging
import os
import db_sql as sqldb
from cache import RedisClient
from network_scanner import NmapScanner
from status_collector import Collector
import db_mongo as mongodb
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
    for subnet in subnets:
        hosts_ips = subnets_scan_obj.get(subnet).get("hosts_ips")
        print("---------")
        print(hosts_ips)
        collector = Collector(hosts_ips)
        network_stats[subnet] = collector.run_test_ping()
    redis_client = RedisClient(host="localhost", port=6379, db=0)

    redis_client.set_cache(key="peter_latency_cache", data=network_stats, ttl=30)
    # redis_client.get_cache(key="peter_latency_cache")
    # print("trying again after 3 seconds")
    # time.sleep(3)
    # redis_client.get_cache(key="peter_latency_cache")
    # redis_client.get_cache(key = "peter_latency_cache")
    print(network_stats)
    sqldb.create_table()
    sqldb.insert_network_stats(network_stats)
    # sqldb.fetch_all_stats()
    mongodb_client = mongodb.init_mongo_client()
    mongodb.insert_network_data_mondb(mongodb_client, network_stats)


if __name__ == "__main__":
    main()
