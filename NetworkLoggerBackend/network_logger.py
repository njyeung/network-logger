"""
NetworkLogger Backend
Creates separate JSON files for each client IP + client ID in a directory structure
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from .models import NetworkLogEntry
from .helper_functions import get_client_file_path, extract_user_id_from_logs, save_logs_to_file, load_logs_from_file, get_client_log_count


class NetworkLogger:
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
    
    

    async def handle_log_upload(self, request_data: Dict[str, Any], client_ip: str) -> Dict[str, Any]:
        """Handle log upload from frontend - saves to client-specific JSON file"""

        try:
            logs_data = request_data.get('logs', [])
            device_info = request_data.get('deviceInfo', {})
            
            user_id = extract_user_id_from_logs(logs_data)
            
            # Convert to NetworkLogEntry and add server info
            new_logs = []
            for log_data in logs_data:
                    
                log = NetworkLogEntry(**log_data)
                log.server_received_at = datetime.now().isoformat()
                log.client_ip = client_ip
                log.device_info = device_info
                new_logs.append(log)
            
            # Get client-specific file path
            client_file = get_client_file_path(self.log_directory, client_ip, user_id)
            
            # Save to client's JSON file
            await save_logs_to_file(new_logs, client_file, self.max_logs, self.logger)
            
            # Console logging
            if self.enable_console_logging:
                self.logger.info(f"Received {len(new_logs)} network logs from {client_ip}")
                if user_id:
                    self.logger.info(f"User ID: {user_id}")
                self.logger.info(f"Device info: {device_info}")
                self.logger.info(f"Saved to: {client_file}")
            
            
            total_stored = await get_client_log_count(self.log_directory, client_ip, self.logger)
            
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
    
    
    
    async def get_logs_ip(self, client_ip: str, limit: Optional[int] = None) -> List[NetworkLogEntry]:
        """Get logs for specific client IP (all users on that IP)"""
        safe_ip = client_ip.replace(':', '_').replace('.', '_')
        all_logs = []
        
        # Find all files for this IP (with or without user ID)
        for filename in os.listdir(self.log_directory):
            if filename.endswith('.json') and filename.startswith(f"{safe_ip}"):
                file_path = os.path.join(self.log_directory, filename)
                logs = await load_logs_from_file(file_path, self.logger)
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
            client_file = get_client_file_path(self.log_directory, client_ip, user_id)
            logs = await load_logs_from_file(client_file, self.logger)
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
                    logs = await load_logs_from_file(file_path, self.logger)
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
                    logs = await load_logs_from_file(file_path, self.logger)
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
                    logs = await load_logs_from_file(file_path, self.logger)
                    total_count += len(logs)
                    
                    with open(file_path, 'w') as f:
                        json.dump([], f)
            
            if self.enable_console_logging:
                self.logger.info(f"Cleared {total_count} total logs from all clients")
            
            return total_count
    
    
    async def get_total_log_count(self) -> int:
        """Get total log count across all clients"""
        total_count = 0
        for filename in os.listdir(self.log_directory):
            if filename.endswith('.json'):
                file_path = os.path.join(self.log_directory, filename)
                logs = await load_logs_from_file(file_path, self.logger)
                total_count += len(logs)
        return total_count
    
    async def get_logs_user(self, user_id: str, limit: Optional[int] = None) -> List[NetworkLogEntry]:
        """Get logs for a specific user ID from session context"""
        user_logs = []
        
        for filename in os.listdir(self.log_directory):
            if filename.endswith('.json') and f'_user_{user_id}' in filename:
                file_path = os.path.join(self.log_directory, filename)
                logs = await load_logs_from_file(file_path, self.logger)
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
                logs = await load_logs_from_file(file_path, self.logger)

                for log in logs:
                    if not log.sessionContext or session_field not in log.sessionContext:
                        continue

                    if str(log.sessionContext[session_field]) == str(session_value):
                        matching_logs.append(log)
                    
        matching_logs.sort(key=lambda x: x.timestamp, reverse=True)

        if limit:
            matching_logs = matching_logs[:limit]
        
        return matching_logs
