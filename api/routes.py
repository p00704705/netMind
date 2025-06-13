from fastapi import APIRouter
from backend.network_scanner import NmapScanner
from backend.status_collector import Collector

router = APIRouter()


@router.get("/ping")
def health_check():
    return {"status": "NetMind API is alive"}


@router.get("/help")
def help():
    return {"help": "netMind is an AI-powered network health and observability platform that helps engineers monitor network performance, detect anomalies, analyze root causes, and search operational knowledge — all from a single, unified interface."}


@router.get("/scan")
def scan_and_collect():
    subnets = ["192.168.1.0/24"]  # You can make this dynamic later
    scan_obj = NmapScanner(subnets).scan_network()
    result = {}
    for subnet in subnets:
        hosts = scan_obj[subnet]["hosts_ips"]
        stats = Collector(hosts).run_test_ping()
        result[subnet] = stats
    return result
