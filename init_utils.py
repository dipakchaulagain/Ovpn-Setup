import shutil
import socket
import logging
import subprocess

logger = logging.getLogger(__name__)

def check_system_dependencies():
    """
    Checks if required system dependencies (iptables) are installed.
    Returns True if all dependencies are met, False otherwise.
    """
    iptables_path = shutil.which("iptables")
    if not iptables_path:
        logger.error("iptables not found. Please install iptables.")
        return False
        
    # Check for persistence tools (optional but recommended)
    if not shutil.which("netfilter-persistent") and not shutil.which("iptables-save"):
         logger.warning("Persistence tools (netfilter-persistent or iptables-save) not found. Rules may not survive reboot.")
         
    return True

def get_host_ip():
    """
    Auto-detects the host's private IP address.
    Returns the IP address as a string, or None if detection fails.
    """
    try:
        # Connect to a public DNS server to determine the local IP used for routing
        # We don't actually send data, just establish the socket to get the local endpoint
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.error(f"Error detecting host IP: {e}")
        return None

def check_initial_config(db, SystemConfig):
    """
    Checks if the system has been configured (User Network defined).
    Returns True if configured, False otherwise.
    """
    try:
        config = SystemConfig.query.first()
        if config and config.user_network_cidr:
            return True
        return False
    except Exception as e:
        # If table doesn't exist or other error
        logger.warning(f"Config check failed (likely first run): {e}")
        return False
