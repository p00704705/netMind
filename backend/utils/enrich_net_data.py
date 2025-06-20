import logging

logging.basicConfig(level=logging.INFO)

def enrich_net_data(hosts_details, network_stats):
    """
    Combine host scan info (IP, MAC, vendor) with network stats (packet loss, latency)
    :param hosts: list of dicts from Nmap (ip, mac, vendor)
    :param stats: dict of stats keyed by IP with packet_loss and avg_latency
    :return: enriched list of dicts
    """
    enrich_net_data = []
    for host in hosts_details:
        ip = host.get('ip')
        stat = network_stats.get(ip, {})  # fallback to empty dict if no stats available
        packet_loss_list = stat.get("packet_loss", [0])
        avg_latency_list = stat.get("avg_latency", [0])
        packet_loss = packet_loss_list[0] if packet_loss_list else "N/A"
        avg_latency = avg_latency_list[0] if avg_latency_list else "N/A"
        
        enriched_entry = {
                  "ip": ip,
                  "mac": host.get("mac"),
                  "vendor": host.get("vendor"),
                  "packet_loss": packet_loss,
                  "avg_latency": avg_latency,
                }
        logging.info("Enriching entry: %s", enriched_entry)

        enrich_net_data.append({
            "ip": ip,
            "mac": host.get("mac"),
            "vendor": host.get("vendor"),
            "packet_loss": packet_loss,
            "avg_latency": avg_latency,
        })
    return enrich_net_data

