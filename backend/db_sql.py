import logging
import sqlite3
from typing import Dict, List

logging.basicConfig(level=logging.INFO)

DB_FILE = "netmind_local_db"


def create_table(subnet):
    conn = sqlite3.connect(DB_FILE + "_" + str(subnet).replace("/", "_") + ".db")
    logging.info(f"Connecting to Sqlite3 DB at {conn}")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS network_stats (
            ip_address TEXT,
            mac_address TEXT,
            vendor TEXT,
            packet_loss REAL,
            avg_latency REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def insert_network_stats(subnet, network_data: List[Dict[str, str]]):
    conn = sqlite3.connect(DB_FILE + "_" + str(subnet).replace("/", "_") + ".db")
    cursor = conn.cursor()
    logging.info(f"Inserting network data to SQL table:\n{network_data}")

    for entry in network_data:
        ip = entry.get("ip")
        mac = entry.get("mac")
        vendor = entry.get("vendor")
        packet_loss = float(entry.get("packet_loss", 0))
        avg_latency = float(entry.get("avg_latency", 0))

        cursor.execute(
            """
            INSERT INTO network_stats (
                ip_address,
                mac_address,
                vendor,
                packet_loss,
                avg_latency
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (ip, mac, vendor, packet_loss, avg_latency),
        )

    conn.commit()
    conn.close()


def fetch_all_stats():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM network_stats ORDER BY timestamp DESC")
    rows = cursor.fetchall()

    for row in rows:
        print(row)
        print()

    conn.close()
