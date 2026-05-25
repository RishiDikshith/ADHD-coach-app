import os
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Create a dedicated audit logger
audit_logger = logging.getLogger("security_audit")
audit_logger.setLevel(logging.INFO)

# Avoid adding multiple handlers if already configured
if not audit_logger.handlers:
    # Handler for writing structured JSON audit logs
    file_handler = logging.FileHandler("logs/security_audit.log", encoding="utf-8")
    
    # Custom formatter for JSON audit log format
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_data = record.msg
            if isinstance(log_data, dict):
                return json.dumps(log_data)
            return json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": record.getMessage(),
                "level": record.levelname
            })
            
    file_handler.setFormatter(JSONFormatter())
    audit_logger.addHandler(file_handler)

def audit_log(
    username: str,
    action: str,
    status: str,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    severity: str = "INFO"
):
    """
    Log security and transaction critical events in a structured JSON audit log format.
    """
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "severity": severity.upper(),
        "username": username or "anonymous",
        "action": action,
        "status": status,
        "ip_address": ip_address or "unknown",
        "details": details or {}
    }
    
    log_msg = f"Audit Log - {severity.upper()} - User: {username} - Action: {action} - Status: {status} - Details: {json.dumps(details or {})}"
    
    # Also log to main app logger for general visibility
    logging.info(log_msg)
    
    # Log structured event to dedicated audit log
    if severity.upper() == "CRITICAL":
        audit_logger.critical(event)
    elif severity.upper() in ("WARNING", "WARN"):
        audit_logger.warning(event)
    else:
        audit_logger.info(event)
