import logging
import sqlite3
from typing import Dict, List
import os
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
        packet_loss = entry.get("packet_loss", 0)
        avg_latency = entry.get("avg_latency", 0)
        try:
            packet_loss = float(packet_loss)
        except (ValueError, TypeError):
            packet_loss = None

        try:
            avg_latency = float(avg_latency)
        except (ValueError, TypeError):
            avg_latency = None

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


def fetch_all_stats(subnet, start_date=None, end_date=None):
    db_path = f"netmind_local_db_{subnet.replace('/', '_')}.db"

    if not os.path.exists(db_path):
        logging.warning(f"Database file for subnet {subnet} does not exist.")
        return []

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        query = """
            SELECT ip_address, mac_address, vendor, packet_loss, avg_latency, timestamp
            FROM network_stats
            WHERE 1=1
        """
        params = []

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)

        query += " ORDER BY timestamp DESC"

        logging.info(f"Executing query: {query} with params: {params}")
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return rows
    except sqlite3.OperationalError as e:
        logging.error(f"SQLite error: {e}")
        return []
    finally:
        conn.close()


