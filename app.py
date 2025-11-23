from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, User, Rule, SystemConfig
from iptables_manager import IptablesManager
import os
import init_utils

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
# Use SQLite for local dev if MySQL URI not provided, but default to MySQL as requested
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:password@localhost/firewall_db'
# For this environment, I'll use SQLite to ensure it runs, but comment how to switch.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///firewall.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
iptables = IptablesManager()

@app.before_request
def check_setup():
    # Skip check for static files and setup route itself to avoid infinite loop
    if request.endpoint in ['setup', 'static']:
        return
        
    # Check if system is configured
    try:
        # Create tables if they don't exist (simplified migration)
        # In production, use Alembic
        with app.app_context():
             # This is a bit hacky to do on every request, but safe for SQLite/Dev
             # Better to do it once on startup, but before_request context is safer for DB access
             pass

        config = SystemConfig.query.first()
        if not config or not config.is_configured:
            return redirect(url_for('setup'))
    except Exception:
        # If DB not init, might fail
        pass

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        host_ip = request.form.get('host_ip')
        user_network_cidr = request.form.get('user_network_cidr')
        
        if host_ip and user_network_cidr:
            try:
                # Validate IP
                ipaddress.ip_address(host_ip)
                # Validate CIDR
                ipaddress.ip_network(user_network_cidr)
                
                # Save config
                config = SystemConfig.query.first()
                if not config:
                    config = SystemConfig(host_ip=host_ip, user_network_cidr=user_network_cidr, is_configured=True)
                    db.session.add(config)
                else:
                    config.host_ip = host_ip
                    config.user_network_cidr = user_network_cidr
                    config.is_configured = True
                
                db.session.commit()
                flash('System initialized successfully!', 'success')
                return redirect(url_for('index'))
            except ValueError as e:
                flash(f'Invalid Input: {str(e)}', 'error')
        else:
            flash('Please fill all fields.', 'error')
            
    # Auto-detect IP
    detected_ip = init_utils.get_host_ip() or "127.0.0.1"
    
    # Check dependencies
    if not init_utils.check_system_dependencies():
        flash('WARNING: iptables not found. Firewall rules will not be applied.', 'error')
        
    return render_template('setup.html', host_ip=detected_ip)

@app.route('/')
def index():
    # Ensure setup is done (handled by before_request, but good to be safe)
    config = SystemConfig.query.first()
    if not config or not config.is_configured:
        return redirect(url_for('setup'))

    user_count = User.query.count()
    rule_count = Rule.query.count()
    iptables_available = init_utils.check_system_dependencies()
    
    return render_template('dashboard.html', 
                           user_count=user_count, 
                           rule_count=rule_count, 
                           system_config=config,
                           iptables_available=iptables_available)



import ipaddress

def get_next_available_ip():
    config = SystemConfig.query.first()
    if not config:
        return None
        
    network = ipaddress.ip_network(config.user_network_cidr)
    used_ips = [u.ip_address for u in User.query.all()]
    
    # Start from the second IP (first is usually gateway/network)
    for ip in network.hosts():
        ip_str = str(ip)
        if ip_str not in used_ips and ip_str != config.host_ip:
            return ip_str
    return None

@app.route('/users')
def list_users():
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/user/add/page', methods=['GET', 'POST'])
def add_user_page():
    if request.method == 'POST':
        username = request.form.get('username')
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        contact = request.form.get('contact')
        user_type = request.form.get('user_type')
        forward_mode = request.form.get('forward_mode', 'ROUTE')
        ip_address = request.form.get('ip_address')
        
        # Validation
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
        elif User.query.filter_by(ip_address=ip_address).first():
            flash('IP Address already assigned.', 'error')
        else:
            new_user = User(
                username=username,
                full_name=full_name,
                email=email,
                contact=contact,
                user_type=user_type,
                forward_mode=forward_mode,
                ip_address=ip_address
            )
            db.session.add(new_user)
            db.session.commit()
            flash('User added successfully!', 'success')
            return redirect(url_for('list_users'))
            
        return redirect(url_for('add_user_page'))

    recommended_ip = get_next_available_ip()
    return render_template('user_form.html', user=None, recommended_ip=recommended_ip)

@app.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.full_name = request.form.get('full_name')
        user.email = request.form.get('email')
        user.contact = request.form.get('contact')
        user.user_type = request.form.get('user_type')
        user.forward_mode = request.form.get('forward_mode', 'ROUTE')
        
        new_ip = request.form.get('ip_address')
        if new_ip != user.ip_address:
            if User.query.filter_by(ip_address=new_ip).first():
                 flash('IP Address already assigned to another user.', 'error')
                 return redirect(url_for('edit_user', user_id=user.id))
            user.ip_address = new_ip
            
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('list_users'))
        
    return render_template('user_form.html', user=user, recommended_ip=user.ip_address)

# Deprecated simple add route, redirecting to new page logic if needed or keeping for API
# But for now, let's remove the old add_user and rely on add_user_page

@app.route('/user/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted!', 'success')
    return redirect(url_for('index'))

@app.route('/rules')
def manage_rules():
    user_id = request.args.get('user_id')
    protocol = request.args.get('protocol')
    action = request.args.get('action')
    
    query = Rule.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    if protocol:
        query = query.filter_by(protocol=protocol)
    if action:
        query = query.filter_by(action=action)
        
    rules = query.all()
    all_users = User.query.all()
    
    return render_template('rules.html', rules=rules, all_users=all_users, user=None)

@app.route('/user/<int:user_id>/rules')
def user_rules(user_id):
    user = User.query.get_or_404(user_id)
    
    protocol = request.args.get('protocol')
    action = request.args.get('action')
    
    query = Rule.query.filter_by(user_id=user_id)
    
    if protocol:
        query = query.filter_by(protocol=protocol)
    if action:
        query = query.filter_by(action=action)
        
    rules = query.all()
    all_users = User.query.all()
    
    return render_template('rules.html', rules=rules, all_users=all_users, user=user)

@app.route('/rules/add', methods=['POST'])
def add_rule_route():
    user_id = request.form.get('user_id')
    destination_ip = request.form.get('destination_ip')
    destination_port = request.form.get('destination_port')
    protocol = request.form.get('protocol')
    action = request.form.get('action')
    # forward_type removed
    
    if not destination_port:
        destination_port = None
    
    new_rule = Rule(
        user_id=user_id,
        destination_ip=destination_ip,
        destination_port=destination_port,
        protocol=protocol,
        action=action
    )
    
    db.session.add(new_rule)
    db.session.commit()
    flash('Rule added successfully!', 'success')
    
    # Redirect back to where we came from if possible, or default to rules list
    if request.referrer:
        return redirect(request.referrer)
    return redirect(url_for('manage_rules'))

# Keeping old add_rule for compatibility if needed, but add_rule_route covers it
@app.route('/user/<int:user_id>/rules/add', methods=['POST'])
def add_rule(user_id):
    # Redirect to new generic handler
    return add_rule_route()

@app.route('/rule/<int:rule_id>/delete', methods=['POST'])
def delete_rule(rule_id):
    rule = Rule.query.get_or_404(rule_id)
    db.session.delete(rule)
    db.session.commit()
    flash('Rule deleted!', 'success')
    
    if request.referrer:
        return redirect(request.referrer)
    return redirect(url_for('manage_rules'))

@app.route('/apply', methods=['POST'])
def apply_rules():
    users = User.query.all()
    commands = iptables.generate_rules(users)
    
    # In a real scenario, we might want to show the commands first or just run them.
    # The user asked for "rule reload, validate, add, modify, edit"
    # This is the "reload/apply" part.
    
    try:
        iptables.apply_rules(commands)
        flash('Rules applied successfully!', 'success')
    except Exception as e:
        flash(f'Error applying rules: {str(e)}', 'error')
        
    return redirect(url_for('index'))

@app.route('/validate', methods=['GET'])
def validate_rules():
    # Show what would be applied
    users = User.query.all()
    commands = iptables.generate_rules(users)
    return render_template('validate.html', commands=commands)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')
