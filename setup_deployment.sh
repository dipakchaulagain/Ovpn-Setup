#!/bin/bash

# Exit on error
set -e

echo "Starting Firewall Manager Deployment Setup..."

# 1. Install Dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip iptables netfilter-persistent iptables-persistent

# 2. Create Service User
echo "Creating service user 'fwmanager'..."
if id "fwmanager" &>/dev/null; then
    echo "User 'fwmanager' already exists."
else
    sudo useradd -r -s /bin/false fwmanager
    echo "User 'fwmanager' created."
fi

# 3. Setup Application Directory
APP_DIR="/opt/firewall-manager"
echo "Setting up application directory at $APP_DIR..."

if [ ! -d "$APP_DIR" ]; then
    sudo mkdir -p $APP_DIR
    # Copy current directory contents to APP_DIR (assuming script is run from source)
    # In a real scenario, you might git clone here. 
    # For now, we assume the user will copy files manually or we are in the dir.
    echo "Please ensure application files are copied to $APP_DIR"
else
    echo "Directory exists."
fi

# 4. Setup Virtual Environment
echo "Setting up virtual environment..."
if [ ! -d "$APP_DIR/venv" ]; then
    sudo python3 -m venv $APP_DIR/venv
fi

# Install requirements (assuming requirements.txt exists)
if [ -f "requirements.txt" ]; then
    echo "Installing Python requirements..."
    sudo $APP_DIR/venv/bin/pip install -r requirements.txt
    sudo $APP_DIR/venv/bin/pip install gunicorn  # Install gunicorn for production
else
    echo "WARNING: requirements.txt not found. Please install dependencies manually."
fi

# 5. Configure Permissions
echo "Configuring permissions..."
sudo chown -R fwmanager:fwmanager $APP_DIR

# 6. Configure Sudo Access for iptables
echo "Configuring sudo access for iptables..."
SUDOERS_FILE="/etc/sudoers.d/fwmanager-iptables"
if [ ! -f "$SUDOERS_FILE" ]; then
    echo "fwmanager ALL=(ALL) NOPASSWD: /usr/sbin/iptables, /usr/sbin/iptables-restore, /usr/sbin/iptables-save" | sudo tee $SUDOERS_FILE
    sudo chmod 440 $SUDOERS_FILE
    echo "Sudoers file created."
else
    echo "Sudoers file already exists."
fi

# 7. Install Systemd Service
echo "Installing systemd service..."
SERVICE_FILE="firewall-manager.service"
if [ -f "$SERVICE_FILE" ]; then
    sudo cp $SERVICE_FILE /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable firewall-manager
    echo "Service installed and enabled."
    echo "To start the service, run: sudo systemctl start firewall-manager"
else
    echo "ERROR: $SERVICE_FILE not found!"
fi

echo "Setup Complete!"
echo "NOTE: You may need to adjust the ExecStart in /etc/systemd/system/firewall-manager.service if using Gunicorn."
