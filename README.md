# Firewall Manager

A web-based application to manage IPTables firewall rules for users. Built with Flask and Bootstrap 5.

## Features

- **Dashboard**: View system status, user counts, and active rules.
- **User Management**: Add, edit, and delete users with assigned IP addresses.
- **Rule Management**: Create, modify, and delete firewall rules (TCP, UDP, ICMP) for specific users.
- **Validation**: Review generated IPTables commands before applying them.
- **Responsive UI**: Modern interface built with Bootstrap 5.
- **Automated IP Allocation**: Automatically suggests the next available IP in the defined network.

## Prerequisites

- Python 3.x
- Linux system with `iptables` (for applying rules)
- Root/Sudo privileges (required for manipulating iptables)

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/dipakchaulagain/Ovpn-Setup.git
    cd Ovpn-Setup
    ```

2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Run the application:
    ```bash
    python app.py
    # OR
    flask run --host=0.0.0.0
    ```

2.  Open your browser and navigate to `http://localhost:5000`.

3.  **Initial Setup**: On first run, you will be prompted to configure the Host IP and User Network CIDR (e.g., `10.8.0.0/24`).

## Configuration

- **Database**: Defaults to SQLite (`firewall.db`). Can be configured for MySQL in `app.py`.
- **Security**: Ensure the application is running behind a secure web server (like Nginx) in production and restrict access to the management interface.

## Project Structure

- `app.py`: Main Flask application entry point.
- `models.py`: Database models (User, Rule, SystemConfig).
- `iptables_manager.py`: Logic for generating and applying IPTables rules.
- `init_utils.py`: System initialization and dependency checks.
- `templates/`: HTML templates (Jinja2).
- `static/`: CSS and other static assets.
