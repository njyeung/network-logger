"""
Helper functions
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from .models import NetworkLogEntry


def get_client_file_path(log_directory: str, client_ip: str, user_id: Optional[str] = None) -> str:
    """Get the JSON file path for a specific client IP and optionally user ID"""
    # Sanitize IP address for filename (replace special chars)
    safe_ip = client_ip.replace(':', '_').replace('.', '_')
    
    # If user_id is available from session context, create user-specific file
    if user_id:
        safe_user_id = str(user_id).replace('/', '_').replace('\\', '_')
        return os.path.join(log_directory, f"{safe_ip}_user_{safe_user_id}.json")
    
    return os.path.join(log_directory, f"{safe_ip}.json")


def extract_user_id_from_logs(logs_data: List[Dict[str, Any]]) -> Optional[str]:
    """Extract user ID from session context in logs"""

    for log_data in logs_data:
        session_context = log_data.get('sessionContext', {})

        if session_context and 'userId' in session_context:
            return str(session_context['userId'])
    return None


async def save_logs_to_file(new_logs: List[NetworkLogEntry], file_path: str, max_logs: int, logger: logging.Logger) -> None:
    """Save logs to specific JSON file"""
    try:
        # Load existing logs from this specific file
        existing_logs = await load_logs_from_file(file_path, logger)
        
        # Combine logs (newest first)
        all_logs = new_logs + existing_logs
        
        # Limit logs if needed
        if len(all_logs) > max_logs:
            all_logs = all_logs[:max_logs]
        
        # Save to file
        with open(file_path, 'w') as f:
            json.dump([asdict(log) for log in all_logs], f, indent=2)
            
    except Exception as e:
        logger.error(f"Failed to save logs to {file_path}: {e}")
        raise


async def load_logs_from_file(file_path: str, logger: logging.Logger) -> List[NetworkLogEntry]:
    """Load logs from specific JSON file"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return [NetworkLogEntry(**item) for item in data]
    except FileNotFoundError:
        return []
    except Exception as e:
        logger.error(f"Failed to load logs from {file_path}: {e}")
        return []


async def get_client_log_count(log_directory: str, client_ip: str, logger: logging.Logger) -> int:
    """Get log count for specific client"""
    client_file = get_client_file_path(log_directory, client_ip)
    logs = await load_logs_from_file(client_file, logger)
    return len(logs)