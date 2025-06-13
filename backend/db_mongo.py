from pymongo.server_api import ServerApi
from pymongo import MongoClient
import logging
import os
import json
from urllib.parse import quote_plus
from datetime import datetime
logging.basicConfig(level=logging.INFO)


def init_mongo_client():
    logging.info(f"Initiating MongoDB Client..")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "..", "config", "tool_config.json")
    with open(config_path) as f:
        config = json.load(f)

    password = quote_plus(config['mongo_database']['password'])

    uri = f"{config['mongo_database']['service']}{config['mongo_database']['user']}:{password}{config['mongo_database']['uri']}"

    logging.info(f"Using MongoDB URI: {uri}")

    # Create a new client and connect to the server
    mon_client = MongoClient(uri, server_api=ServerApi("1"))

    # Send a ping to confirm a successful connection
    try:
        logging.info(f"Sending ping to confirm successful connection: {mon_client.admin.command('ping')}")
        return mon_client
    except Exception as e:
        logging.error(f"MongoDB connection failed: {e}")
        exit(1)


def insert_network_data_mondb(mon_client, network_stats_data={}):
    logging.info(f"Inserting data into MongoDB:\n {network_stats_data}")
    db = mon_client["netmind"]
    collection = db["latency"]
    for subnet, hosts in network_stats_data.items():
        for ip, metrics in hosts.items():
            document = {
                "subnet": subnet,
                "ip": ip,
                "packet_loss": float(metrics.get("packet_loss", ["0"])[0]),
                "avg_latency": float(metrics["avg_latency"][0]) if metrics.get("avg_latency") and metrics["avg_latency"] else None,
                "timestamp": datetime.utcnow()
            }
            collection.insert_one(document)
