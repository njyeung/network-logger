"""
NetworkLogEntry
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class NetworkLogEntry:
    """Network log entry structure (matches frontend)"""
    timestamp: str
    eventType: str  # connection_change, subnet_change, disconnect, etc.
    networkType: Optional[str]
    isConnected: Optional[bool]
    isInternetReachable: Optional[bool]
    serverConnected: Optional[bool] = None
    additionalInfo: Optional[str] = None
    
    # Network details
    ipAddress: Optional[str] = None
    subnet: Optional[str] = None
    previousSubnet: Optional[str] = None
    
    # WiFi specific
    ssid: Optional[str] = None
    bssid: Optional[str] = None
    
    # Cellular specific
    cellularGeneration: Optional[str] = None
    
    # Raw details
    details: Optional[Dict[str, Any]] = None
    
    # Flexible session context from frontend
    sessionContext: Optional[Dict[str, Any]] = None
    
    # Server-added fields
    server_received_at: Optional[str] = None
    client_ip: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None