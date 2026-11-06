"""
AirGuard AI — Local Gateway REST Router
Endpoints for local network discovery, gateway health checks, and device reachability probing.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
import httpx
import socket
import asyncio
import ipaddress

from services.gateway.discovery import gateway, DiscoveredService, GatewayStatus
from services.api.security import get_current_user
from services.api.models import User

router = APIRouter(prefix="/gateway", tags=["Local Discovery Gateway"])

# Whitelisted ports for local IoT device probing
WHITELISTED_IOT_PORTS = {80, 8080, 8123, 9926, 6053, 1883, 8883, 8000}

@router.get("/status", response_model=GatewayStatus)
async def get_gateway_status(current_user: User = Depends(get_current_user)):
    """Returns the health, active network interfaces, and operational mode of the local gateway."""
    return gateway.get_status()

@router.post("/scan", response_model=List[DiscoveredService])
async def trigger_network_scan(
    timeout: float = Query(2.0, ge=0.5, le=10.0),
    current_user: User = Depends(get_current_user)
):
    """
    Triggers an authorized local network scan for mDNS, SSDP, and IoT devices.
    Returns discovered network beacons strictly labeled is_verified=False.
    """
    discovered = await gateway.scan(timeout=timeout)
    return discovered

from pydantic import BaseModel

class ProbeDeviceRequest(BaseModel):
    host: str
    port: Optional[int] = None
    expected_protocol: Optional[str] = None

class ProbeDeviceResponse(BaseModel):
    reachable: bool
    latency_ms: float
    detected_service: Optional[str] = None
    suggested_capabilities: Dict[str, List[str]]
    error: Optional[str] = None

@router.post("/probe", response_model=ProbeDeviceResponse)
async def probe_device(
    req: ProbeDeviceRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Probes an IP or hostname on the local network to verify reachability
    and inspect device endpoints before pairing.
    Hardened with strict SSRF protection, loopback/private subnet allowlisting,
    and port restriction.
    """
    host = req.host.strip()
    port = req.port or 80

    # 1. Port Whitelist Validation
    if port not in WHITELISTED_IOT_PORTS:
        raise HTTPException(
            status_code=400,
            detail=f"SSRF Security Violation: Probing is restricted to whitelisted IoT device ports: {sorted(list(WHITELISTED_IOT_PORTS))}."
        )

    # 2. Host Resolution & SSRF Address Validation
    try:
        target_ip = socket.gethostbyname(host)
        ip_obj = ipaddress.ip_address(target_ip)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"SSRF Security Violation: Host resolution failed for '{host}': {str(e)}"
        )

    # Reject cloud metadata endpoints (e.g. AWS/GCP 169.254.169.254)
    if ip_obj.is_link_local:
        raise HTTPException(
            status_code=400,
            detail="SSRF Security Violation: Probing cloud metadata and link-local addresses (169.254.0.0/16) is strictly prohibited."
        )

    # Reject multicast and reserved ranges
    if ip_obj.is_multicast or ip_obj.is_reserved:
        raise HTTPException(
            status_code=400,
            detail="SSRF Security Violation: Probing multicast or reserved address ranges is prohibited."
        )

    # Restrict to private RFC 1918 subnets or local loopback
    if not (ip_obj.is_private or ip_obj.is_loopback):
        raise HTTPException(
            status_code=400,
            detail="SSRF Security Violation: Probing is restricted to private local area networks (RFC 1918) or loopback."
        )

    start_time = asyncio.get_event_loop().time()
    
    # Check socket connection
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect((target_ip, port))
        sock.close()
        elapsed_ms = (asyncio.get_event_loop().time() - start_time) * 1000.0
        
        detected_service = "http" if port in (80, 8080, 8123, 9926) else "tcp"
        if port == 8123:
            detected_service = "home_assistant"
        elif port in (1883, 8883):
            detected_service = "mqtt"
        elif port == 6053:
            detected_service = "esphome"

        caps = {
            "measurements": ["PM2.5", "Temperature", "Humidity"],
            "controls": ["Power", "Fan Speed"] if port in (8123, 80) else []
        }

        return ProbeDeviceResponse(
            reachable=True,
            latency_ms=round(elapsed_ms, 2),
            detected_service=detected_service,
            suggested_capabilities=caps
        )
    except Exception as e:
        elapsed_ms = (asyncio.get_event_loop().time() - start_time) * 1000.0
        return ProbeDeviceResponse(
            reachable=False,
            latency_ms=round(elapsed_ms, 2),
            suggested_capabilities={"measurements": [], "controls": []},
            error=f"Could not connect to {host}:{port} — {str(e)}"
        )
