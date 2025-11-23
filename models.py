from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class SystemConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    host_ip = db.Column(db.String(45), nullable=False)
    user_network_cidr = db.Column(db.String(45), nullable=False)
    is_configured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    contact = db.Column(db.String(20), nullable=True)
    user_type = db.Column(db.String(20), default='employee') # employee, vendor, others
    forward_mode = db.Column(db.String(10), default='ROUTE') # ROUTE, NAT
    ip_address = db.Column(db.String(45), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rules = db.relationship('Rule', backref='user', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<User {self.username}>'

class Rule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    destination_ip = db.Column(db.String(45), nullable=False)
    destination_port = db.Column(db.Integer, nullable=True)
    protocol = db.Column(db.String(10), nullable=False, default='tcp') # tcp, udp, all
    action = db.Column(db.String(10), nullable=False, default='ACCEPT') # ACCEPT, DROP
    # forward_type removed as it is now per-user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Rule {self.id} for User {self.user_id}>'
