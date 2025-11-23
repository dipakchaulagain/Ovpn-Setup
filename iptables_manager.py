import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IptablesManager:
    def __init__(self):
        self.chain_name = "FIREWALL_MANAGER"

    def generate_iptables_file_content(self, users):
        """
        Generates the content for an iptables-restore file.
        """
        filter_rules = []
        nat_rules = []

        for user in users:
            for rule in user.rules:
                if user.forward_mode == 'NAT':
                    # NAT (Masquerade)
                    # -A POSTROUTING -s <user_ip> -d <dest_ip> -j MASQUERADE
                    cmd = ["-A", "POSTROUTING"]
                    cmd.extend(["-s", user.ip_address])
                    cmd.extend(["-d", rule.destination_ip])
                    
                    if rule.protocol != 'all':
                        cmd.extend(["-p", rule.protocol])
                        if rule.destination_port:
                            cmd.extend(["--dport", str(rule.destination_port)])
                            
                    cmd.extend(["-j", "MASQUERADE"])
                    nat_rules.append(" ".join(cmd))
                    
                else: # ROUTE
                    # Forwarding
                    # -A FORWARD -s <user_ip> -d <dest_ip> -j <action>
                    cmd = ["-A", "FORWARD"]
                    cmd.extend(["-s", user.ip_address])
                    cmd.extend(["-d", rule.destination_ip])
                    
                    if rule.protocol != 'all':
                        cmd.extend(["-p", rule.protocol])
                        if rule.destination_port:
                            cmd.extend(["--dport", str(rule.destination_port)])
                            
                    cmd.extend(["-j", rule.action])
                    filter_rules.append(" ".join(cmd))
        
        # Build the content
        lines = []
        
        # Filter Table
        lines.append("*filter")
        # We do NOT set policies here to avoid overriding existing ones if using -n
        # But we DO flush the chains we manage
        lines.append("-F FORWARD")
        lines.append("-F INPUT") # Manage INPUT to ensure access
        
        # System Access Rules (INPUT)
        # 1. Allow Loopback
        lines.append("-A INPUT -i lo -j ACCEPT")
        # 2. Allow Established/Related
        lines.append("-A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT")
        # 3. Allow SSH
        lines.append("-A INPUT -p tcp --dport 22 -j ACCEPT")
        # 4. Allow Portal (Flask default 5000, plus standard web ports)
        lines.append("-A INPUT -p tcp --dport 5000 -j ACCEPT")
        lines.append("-A INPUT -p tcp --dport 80 -j ACCEPT")
        lines.append("-A INPUT -p tcp --dport 443 -j ACCEPT")
        
        lines.extend(filter_rules)
        lines.append("COMMIT")
        
        # NAT Table
        lines.append("*nat")
        lines.append("-F POSTROUTING")
        lines.extend(nat_rules)
        lines.append("COMMIT")
        
        return "\n".join(lines) + "\n"

    def apply_rules(self, users):
        """
        Generates the rules file and applies it using iptables-restore.
        """
        content = self.generate_iptables_file_content(users)
        
        try:
            # Write to a temporary file
            import tempfile
            import os
            
            fd, path = tempfile.mkstemp(text=True)
            try:
                with os.fdopen(fd, 'w') as tmp:
                    tmp.write(content)
                
                # Apply using iptables-restore -n (no flush of other chains)
                cmd = f"iptables-restore -n < {path}"
                logger.info(f"Running: {cmd}")
                
                # In a real environment, we would run this:
                # subprocess.run(cmd, shell=True, check=True, stderr=subprocess.PIPE)
                
                # For this environment/demo, we simulate or try-catch
                subprocess.run(cmd, shell=True, check=True, stderr=subprocess.PIPE)
                
            finally:
                os.remove(path)
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error applying rules: {e}")
            if e.stderr:
                logger.error(f"Stderr: {e.stderr.decode()}")
            raise e
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e
