from fastapi import APIRouter, HTTPException, Request
from backend.network_scanner import NmapScanner
from backend.status_collector import Collector
import ipaddress
from datetime import datetime
from fastapi.responses import JSONResponse, HTMLResponse

import backend.db_sql as sqldb
from fastapi.templating import Jinja2Templates
import os
from backend.utils.enrich_net_data import enrich_net_data

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATE_DIR)


@router.get("/", response_class=HTMLResponse)
def landing_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/ping")
def health_check():
    return JSONResponse(
        status_code=200,
        content={
            "status": "NetMind API is alive",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )


@router.get("/help")
def help():
    return {
        "help": "NetMind is an AI-powered network health and observability platform that helps engineers monitor network performance, detect anomalies, analyze root causes, and search operational knowledge — all from a single, unified interface."
    }


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
def get_net_stat(request: Request):
    """
    http://0.0.0.0:4123/net_stat?subnet=192.168.1.0/24&start_date=...&end_date=...
    """
    subnet = request.query_params.get("subnet")
    start_date = request.query_params.get("start_date")
    end_date = request.query_params.get("end_date")

    if not subnet:
        raise HTTPException(status_code=400, detail="Missing subnet parameter")
    try:
        ipaddress.ip_network(subnet)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid subnet format")

    # Fix ISO datetime format
    start_date = start_date.replace("T", " ") if start_date else None
    end_date = end_date.replace("T", " ") if end_date else None

    # Check if DB file exists
    db_path = f"netmind_local_db_{subnet.replace('/', '_')}.db"
    if not os.path.exists(db_path):
        headers = ["IP", "MAC", "Vendor", "Packet Loss (%)", "Avg Latency (ms)", "Timestamp"]
        return templates.TemplateResponse("net_stat.html", {
            "request": request,
            "subnet": subnet,
            "headers": headers,
            "rows": [],
            "message": f"No records found. This subnet ({subnet}) may not have been scanned yet."
        })

    # Fetch from DB
    result = sqldb.fetch_all_stats(subnet, start_date, end_date)
    headers = ["IP", "MAC", "Vendor", "Packet Loss (%)", "Avg Latency (ms)", "Timestamp"]

    return templates.TemplateResponse("net_stat.html", {
        "request": request,
        "subnet": subnet,
        "headers": headers,
        "rows": result,
        "message": "No data found in the selected time range." if not result else None
    })
