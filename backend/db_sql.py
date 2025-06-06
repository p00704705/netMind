import sqlite3
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO)

DB_FILE = "netmind_local_db.db"

def create_table():
    conn = sqlite3.connect(DB_FILE)
    logging.info(f"Connecting to Sqlite3 DB at {conn}")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS network_stats (
            ip_address TEXT,
            packet_loss REAL,
            avg_latency REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def insert_network_stats(network_data: Dict[str, Dict[str, Dict[str, list]]]):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    for subnet, ip_data in network_data.items():
        for ip, stats in ip_data.items():
            packet_loss_list = stats.get('packet_loss', [])
            avg_latency_list = stats.get('avg_latency', [])

            packet_loss = float(packet_loss_list[0]) if packet_loss_list else None
            avg_latency = float(avg_latency_list[0]) if avg_latency_list else None

            cursor.execute('''
                INSERT INTO network_stats (ip_address, packet_loss, avg_latency)
                VALUES (?, ?, ?)
            ''', (ip, packet_loss, avg_latency))

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
