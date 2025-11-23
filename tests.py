import unittest
import os
import sys
from app import app, db, User, Rule, iptables

class FirewallManagerTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_index_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Firewall Manager', response.data)

    def test_add_user(self):
        response = self.app.post('/user/add', data=dict(
            username='testuser',
            ip_address='10.0.0.1'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'User added successfully!', response.data)
        self.assertIn(b'testuser', response.data)

    def test_add_rule(self):
        # Add user first
        with app.app_context():
            user = User(username='ruleuser', ip_address='10.0.0.2')
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        # Add rule
        response = self.app.post(f'/user/{user_id}/rules/add', data=dict(
            destination_ip='8.8.8.8',
            destination_port='53',
            protocol='udp',
            action='ACCEPT',
            forward_type='NAT'
        ), follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Rule added!', response.data)
        self.assertIn(b'8.8.8.8', response.data)

    def test_iptables_generation(self):
        with app.app_context():
            user = User(username='genuser', ip_address='10.0.0.3')
            db.session.add(user)
            db.session.commit()
            
            rule = Rule(
                user_id=user.id,
                destination_ip='1.1.1.1',
                destination_port=80,
                protocol='tcp',
                action='ACCEPT',
                forward_type='ROUTE'
            )
            db.session.add(rule)
            db.session.commit()
            
            users = User.query.all()
            commands = iptables.generate_rules(users)
            
            # Verify commands
            # Expected: iptables -A FORWARD -s 10.0.0.3 -d 1.1.1.1 -p tcp --dport 80 -j ACCEPT
            expected_part = "-A FORWARD -s 10.0.0.3 -d 1.1.1.1 -p tcp --dport 80 -j ACCEPT"
            found = any(expected_part in cmd for cmd in commands)
            self.assertTrue(found, f"Command not found in: {commands}")

if __name__ == '__main__':
    unittest.main()
