from fastapi import APIRouter, HTTPException, Request
from backend.network_scanner import NmapScanner
from backend.status_collector import Collector
import ipaddress
from datetime import datetime
from fastapi.responses import JSONResponse, HTMLResponse
from backend.cache import RedisClient
import backend.db_sql as sqldb
from fastapi.templating import Jinja2Templates
import os
from backend.utils.enrich_net_data import enrich_net_data

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATE_DIR)


@router.get("/ping")
def health_check():
    return JSONResponse(
        status_code=200,
        content={"status": "NetMind API is alive",
                 "timestamp": datetime.utcnow().isoformat() + "Z"}
    )


@router.get("/help")
def help():
    return {"help": "netMind is an AI-powered network health and observability platform that helps engineers monitor network performance, detect anomalies, analyze root causes, and search operational knowledge — all from a single, unified interface."}


@router.get("/live_ip_scan", response_class=HTMLResponse)
def scan_and_collect(request: Request, subnet: str):
    """
    http://0.0.0.0:4123/live_ip_scan?subnet=192.168.1.0/24
    """
    try:
        ipaddress.ip_network(subnet)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid subnet format")

    scan_obj = NmapScanner([subnet]).scan_network()
    subnets_scan_obj = NmapScanner([subnet]).scan_network()
    hosts_details = subnets_scan_obj.get(subnet).get("hosts")
    hosts = scan_obj[subnet]["hosts"]
    hosts_ips = [host["ip"] for host in hosts]
    network_stats = Collector(hosts_ips).run_test_ping()
    enriched_net_data = enrich_net_data(hosts_details, network_stats)
    print(enriched_net_data)
    headers = ["IP", "MAC", "Vendor", "Packet Loss (%)", "Avg Latency (ms)"]

    return templates.TemplateResponse("live_scan.html", {
        "request": request,
        "subnet": subnet,
        "headers": headers,
        "rows": enriched_net_data
    })


@router.get("/net_stat", response_class=HTMLResponse)
def get_net_stat(request: Request, subnet: str):
    """
    http://0.0.0.0:4123/net_stat?subnet=192.168.1.0/24
    """
    try:
        ipaddress.ip_network(subnet)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid subnet format")
    redis_client = RedisClient(host="localhost", port=6379, db=0)
    result = redis_client.get_cache(key=subnet + "_network_latency_cache")
    result = sqldb.fetch_all_stats(subnet)
    headers = ["IP", "MAC", "Vendor", "Packet Loss (%)", "Avg Latency (ms)", "Timestamp"]

    return templates.TemplateResponse("net_stat.html", {
        "request": request,
        "subnet": subnet,
        "headers": headers,
        "rows": result
    })
