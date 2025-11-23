# Firewall Manager

A web-based application to manage IPTables firewall rules for users. Built with Flask and Bootstrap 5.

## Features

- **Dashboard**: View system status, user counts, and active rules.
- **User Management**: Add, edit, and delete users with assigned IP addresses.
- **Forwarding Modes**:
    - **ROUTE**: Direct packet forwarding (standard routing).
    - **NAT**: Masquerade traffic (hide user IP behind host IP).
- **Rule Management**: Create, modify, and delete firewall rules (TCP, UDP, ICMP) for specific users.
- **System Access**: Automatically manages `INPUT` chain to allow SSH (22), Web Portal (5000/80/443), and Loopback traffic.
- **Atomic Updates**: Uses `iptables-restore` to apply rules safely without disrupting existing connections or unmanaged chains.
- **Validation**: Review generated IPTables commands before applying them.
- **Responsive UI**: Modern interface built with Bootstrap 5.
- **Automated IP Allocation**: Automatically suggests the next available IP in the defined network.

## Prerequisites

- Python 3.x
- Linux system with `iptables`
- `netfilter-persistent` or `iptables-save` (for persistence checks)
- Root/Sudo privileges (required for manipulating iptables)

## Installation & Deployment (Ubuntu 24.04)

We provide a setup script to automate the deployment process, including installing dependencies, creating a service user, and setting up the systemd service.

1.  Clone the repository:
    ```bash
    git clone https://github.com/dipakchaulagain/Ovpn-Setup.git
    cd Ovpn-Setup
    ```

2.  Run the deployment script:
    ```bash
    sudo bash setup_deployment.sh
    ```
    This script will:
    - Install `iptables`, `netfilter-persistent`, `python3-venv`.
    - Create a system user `fwmanager`.
    - Configure sudoers to allow `fwmanager` to run iptables commands.
    - Set up the virtual environment and install dependencies.
    - Install and enable the `firewall-manager` systemd service.

3.  Start the service:
    ```bash
    sudo systemctl start firewall-manager
    ```

4.  Check status:
    ```bash
    sudo systemctl status firewall-manager
    ```

## Manual Development Setup

1.  Create a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Run the application:
    ```bash
    python app.py
    ```

4.  Open your browser and navigate to `http://localhost:5000`.

5.  **Initial Setup**: On first run, you will be prompted to configure the Host IP and User Network CIDR (e.g., `10.8.0.0/24`).

## Configuration

- **Database**: Defaults to SQLite (`instance/firewall.db`). Can be configured for MySQL in `app.py`.
- **Security**: Ensure the application is running behind a secure web server (like Nginx) in production and restrict access to the management interface.

## Project Structure

- `app.py`: Main Flask application entry point.
- `models.py`: Database models (User, Rule, SystemConfig).
- `iptables_manager.py`: Logic for generating and applying IPTables rules (uses `iptables-restore`).
- `init_utils.py`: System initialization and dependency checks.
- `templates/`: HTML templates (Jinja2).
- `static/`: CSS and other static assets.
- `setup_deployment.sh`: Automated deployment script.
- `firewall-manager.service`: Systemd service unit file.
