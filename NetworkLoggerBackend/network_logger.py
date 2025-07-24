"""
NetworkLogger Backend - Simple Python Library
Creates separate JSON files for each client IP in a directory structure
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


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


class NetworkLoggerBackend:
    """Backend logger that creates separate JSON files per client IP"""
    
    def __init__(self, log_directory: str = "./network_logs", max_logs: int = 100, enable_console_logging: bool = True):
        self.log_directory = log_directory
        self.max_logs = max_logs
        self.enable_console_logging = enable_console_logging
        self.logger = logging.getLogger(__name__)
        
        # Create directory if it doesn't exist
        os.makedirs(log_directory, exist_ok=True)
        
        if enable_console_logging:
            logging.basicConfig(level=logging.INFO)
    
    def _get_client_file_path(self, client_ip: str, user_id: Optional[str] = None) -> str:
        """Get the JSON file path for a specific client IP and optionally user ID"""
        # Sanitize IP address for filename (replace special chars)
        safe_ip = client_ip.replace(':', '_').replace('.', '_')
        
        # If user_id is available from session context, create user-specific file
        if user_id:
            safe_user_id = str(user_id).replace('/', '_').replace('\\', '_')
            return os.path.join(self.log_directory, f"{safe_ip}_user_{safe_user_id}.json")
        
        return os.path.join(self.log_directory, f"{safe_ip}.json")
    
    def _extract_user_id_from_logs(self, logs_data: List[Dict[str, Any]]) -> Optional[str]:
        """Extract user ID from session context in logs"""

        for log_data in logs_data:
            session_context = log_data.get('sessionContext', {})

            if session_context and 'userId' in session_context:
                return str(session_context['userId'])
        return None

    async def handle_log_upload(self, request_data: Dict[str, Any], client_ip: str) -> Dict[str, Any]:
        """Handle log upload from frontend - saves to client-specific JSON file"""

        try:
            logs_data = request_data.get('logs', [])
            device_info = request_data.get('deviceInfo', {})
            
            user_id = self._extract_user_id_from_logs(logs_data)
            
            # Convert to NetworkLogEntry and add server info
            new_logs = []
            for log_data in logs_data:
                    
                log = NetworkLogEntry(**log_data)
                log.server_received_at = datetime.now().isoformat()
                log.client_ip = client_ip
                log.device_info = device_info
                new_logs.append(log)
            
            # Get client-specific file path
            client_file = self._get_client_file_path(client_ip, user_id)
            
            # Save to client's JSON file
            await self._save_logs_to_file(new_logs, client_file)
            
            # Console logging
            if self.enable_console_logging:
                self.logger.info(f"Received {len(new_logs)} network logs from {client_ip}")
                if user_id:
                    self.logger.info(f"User ID: {user_id}")
                self.logger.info(f"Device info: {device_info}")
                self.logger.info(f"Saved to: {client_file}")
            
            
            total_stored = await self._get_client_log_count(client_ip)
            
            return {
                'success': True,
                'received': len(new_logs),
                'total_stored': total_stored,
                'saved_to': client_file,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error handling log upload from {client_ip}: {e}")
            return {
                'success': False,
                'error': str(e),
                'client_ip': client_ip,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _save_logs_to_file(self, new_logs: List[NetworkLogEntry], file_path: str) -> None:
        """Save logs to specific JSON file"""
        try:
            # Load existing logs from this specific file
            existing_logs = await self._load_logs_from_file(file_path)
            
            # Combine logs (newest first)
            all_logs = new_logs + existing_logs
            
            # Limit logs if needed
            if len(all_logs) > self.max_logs:
                all_logs = all_logs[:self.max_logs]
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump([asdict(log) for log in all_logs], f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save logs to {file_path}: {e}")
            raise
    
    async def _load_logs_from_file(self, file_path: str) -> List[NetworkLogEntry]:
        """Load logs from specific JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return [NetworkLogEntry(**item) for item in data]
        except FileNotFoundError:
            return []
        except Exception as e:
            self.logger.error(f"Failed to load logs from {file_path}: {e}")
            return []
    
    async def get_logs_ip(self, client_ip: str, limit: Optional[int] = None) -> List[NetworkLogEntry]:
        """Get logs for specific client IP (all users on that IP)"""
        safe_ip = client_ip.replace(':', '_').replace('.', '_')
        all_logs = []
        
        # Find all files for this IP (with or without user ID)
        for filename in os.listdir(self.log_directory):
            if filename.endswith('.json') and filename.startswith(f"{safe_ip}"):
                file_path = os.path.join(self.log_directory, filename)
                logs = await self._load_logs_from_file(file_path)
                all_logs.extend(logs)
        
        # Sort by timestamp (newest first)
        all_logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        if limit:
            all_logs = all_logs[:limit]
        
        return all_logs
    
    async def clear_logs(self, client_ip: Optional[str] = None, user_id: Optional[str] = None) -> int:
        """Clear logs - optionally for specific client IP and/or user ID"""
        
        if client_ip and user_id:
            # Clear logs for specific client IP and user ID
            client_file = self._get_client_file_path(client_ip, user_id)
            logs = await self._load_logs_from_file(client_file)
            count = len(logs)
            
            with open(client_file, 'w') as f:
                json.dump([], f)
            
            if self.enable_console_logging:
                self.logger.info(f"Cleared {count} logs for client {client_ip}, user {user_id}")
            
            return count
        elif client_ip:
            # Clear all logs for specific client IP (all users on that IP)
            safe_ip = client_ip.replace(':', '_').replace('.', '_')
            count = 0
            
            for filename in os.listdir(self.log_directory):
                if filename.endswith('.json') and filename.startswith(f"{safe_ip}"):
                    file_path = os.path.join(self.log_directory, filename)
                    logs = await self._load_logs_from_file(file_path)
                    count += len(logs)
                    
                    with open(file_path, 'w') as f:
                        json.dump([], f)
            
            if self.enable_console_logging:
                self.logger.info(f"Cleared {count} logs for client {client_ip}")
            
            return count
        elif user_id:
            # Clear all logs for specific user ID (across all IPs)
            count = 0
            
            for filename in os.listdir(self.log_directory):
                if filename.endswith('.json') and f'_user_{user_id}' in filename:
                    file_path = os.path.join(self.log_directory, filename)
                    logs = await self._load_logs_from_file(file_path)
                    count += len(logs)
                    
                    with open(file_path, 'w') as f:
                        json.dump([], f)
            
            if self.enable_console_logging:
                self.logger.info(f"Cleared {count} logs for user {user_id}")
            
            return count
        else:
            # Clear all logs
            total_count = 0
            for filename in os.listdir(self.log_directory):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.log_directory, filename)
                    logs = await self._load_logs_from_file(file_path)
                    total_count += len(logs)
                    
                    with open(file_path, 'w') as f:
                        json.dump([], f)
            
            if self.enable_console_logging:
                self.logger.info(f"Cleared {total_count} total logs from all clients")
            
            return total_count
    
    async def _get_client_log_count(self, client_ip: str) -> int:
        """Get log count for specific client"""
        client_file = self._get_client_file_path(client_ip)
        logs = await self._load_logs_from_file(client_file)
        return len(logs)
    
    async def get_total_log_count(self) -> int:
        """Get total log count across all clients"""
        total_count = 0
        for filename in os.listdir(self.log_directory):
            if filename.endswith('.json'):
                file_path = os.path.join(self.log_directory, filename)
                logs = await self._load_logs_from_file(file_path)
                total_count += len(logs)
        return total_count
    
    async def get_logs_user(self, user_id: str, limit: Optional[int] = None) -> List[NetworkLogEntry]:
        """Get logs for a specific user ID from session context"""
        user_logs = []
        
        for filename in os.listdir(self.log_directory):
            if filename.endswith('.json') and f'_user_{user_id}' in filename:
                file_path = os.path.join(self.log_directory, filename)
                logs = await self._load_logs_from_file(file_path)
                user_logs.extend(logs)
        
        # Sort by timestamp (newest first)
        user_logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        if limit:
            user_logs = user_logs[:limit]
            
        return user_logs
    
    async def get_logs_session_context(self, session_field: str, session_value: str, limit: Optional[int] = None) -> List[NetworkLogEntry]:
        """Get logs matching specific session context field/value"""

        matching_logs = []
        for filename in os.listdir(self.log_directory):
            if filename.endswith('.json'):
                file_path = os.path.join(self.log_directory, filename)
                logs = await self._load_logs_from_file(file_path)

                for log in logs:
                    if not log.sessionContext or session_field not in log.sessionContext:
                        continue

                    if str(log.sessionContext[session_field]) == str(session_value):
                        matching_logs.append(log)
                    
        matching_logs.sort(key=lambda x: x.timestamp, reverse=True)

        if limit:
            matching_logs = matching_logs[:limit]
        
        return matching_logs
