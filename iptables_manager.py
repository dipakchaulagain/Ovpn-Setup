import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IptablesManager:
    def __init__(self):
        self.chain_name = "FIREWALL_MANAGER"

    def generate_rules(self, users):
        """
        Generates a list of iptables commands based on the users and their rules.
        """
        commands = []
        
        # 1. Flush and recreate custom chains to ensure clean state
        # We use a custom chain to avoid messing up other system rules too much
        commands.append(f"iptables -N {self.chain_name}")
        commands.append(f"iptables -F {self.chain_name}")
        
        # Ensure we have a jump from FORWARD to our chain
        # This might duplicate if run multiple times without cleanup, 
        # but 'apply_rules' should handle cleanup or we can check existence.
        # For simplicity in this script, we'll assume we flush FORWARD or manage it carefully.
        # Better approach: Flush FORWARD and re-add the jump (aggressive) 
        # OR just insert if not exists. 
        # Let's go with a safer approach: Just generate the rules for the custom chain.
        # The user of this class is responsible for hooking the chain.
        
        # Actually, the user wants to manage the firewall. 
        # Let's define a standard set of commands to reset and apply.
        
        # Reset standard chains (Caution: this clears everything!)
        # commands.append("iptables -F FORWARD")
        # commands.append("iptables -t nat -F POSTROUTING")
        
        # Let's stick to specific rules for users as requested.
        
        for user in users:
            for rule in user.rules:
                # Base command structure
                cmd = ["iptables"]
                
                if user.forward_mode == 'NAT':
                    # NAT (Masquerade)
                    # iptables -t nat -A POSTROUTING -s <user_ip> -d <dest_ip> -j MASQUERADE
                    cmd.extend(["-t", "nat", "-A", "POSTROUTING"])
                    cmd.extend(["-s", user.ip_address])
                    cmd.extend(["-d", rule.destination_ip])
                    
                    if rule.protocol != 'all':
                        cmd.extend(["-p", rule.protocol])
                        if rule.destination_port:
                            cmd.extend(["--dport", str(rule.destination_port)])
                            
                    cmd.extend(["-j", "MASQUERADE"])
                    
                else: # ROUTE
                    # Forwarding
                    # iptables -A FORWARD -s <user_ip> -d <dest_ip> -j <action>
                    cmd.extend(["-A", "FORWARD"])
                    cmd.extend(["-s", user.ip_address])
                    cmd.extend(["-d", rule.destination_ip])
                    
                    if rule.protocol != 'all':
                        cmd.extend(["-p", rule.protocol])
                        if rule.destination_port:
                            cmd.extend(["--dport", str(rule.destination_port)])
                            
                    cmd.extend(["-j", rule.action])
                
                commands.append(" ".join(cmd))
                
        return commands

    def apply_rules(self, commands):
        """
        Executes the list of commands.
        """
        # First, flush relevant chains to avoid duplicates
        # This is a simplified approach. In production, you'd want atomic updates (iptables-restore).
        flush_cmds = [
            "iptables -F FORWARD",
            "iptables -t nat -F POSTROUTING"
        ]
        
        for cmd in flush_cmds:
            self._run_command(cmd)
            
        for cmd in commands:
            self._run_command(cmd)

    def _run_command(self, cmd):
        try:
            logger.info(f"Running: {cmd}")
            # subprocess.run(cmd, shell=True, check=True, capture_output=True)
            # For safety in this environment, we will just log it if we are not root or on windows
            # But the user asked for the app. 
            # We will try to run it, but catch errors gracefully.
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running command: {cmd}")
            logger.error(f"Stderr: {e.stderr.decode()}")
            # Don't raise, just log, so one failure doesn't stop everything?
            # Or maybe we should raise. Let's log for now.
