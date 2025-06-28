import os
import json
import ipaddress
from flask import Flask, jsonify, request, abort
import random
import string
from datetime import datetime, timedelta

app = Flask(__name__)

# Default configuration that matches your JSON structure
DEFAULT_CONFIG = {
    "length": 8,
    "include_letters": True,
    "include_digits": True,
    "include_special_chars": False,
    "refresh_sec": 60,
    "internal_networks": ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"],
    "internal_access_check": False
}


def load_config():
    """Load configuration from .env.json file"""
    config_path = os.path.join(os.path.dirname(__file__), '.env.json')

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        raise RuntimeError(f"Config file not found: {config_path}")
    except json.JSONDecodeError:
        raise RuntimeError(f"Invalid JSON in config file: {config_path}")

    # Validate all required fields exist
    for field in DEFAULT_CONFIG.keys():
        if field not in config:
            raise RuntimeError(f"Missing required config field: {field}")

    return config


def is_internal_ip(ip_str, networks):
    """Check if IP address is in any of the specified networks"""
    try:
        ip = ipaddress.ip_address(ip_str)
        for network in networks:
            if ip in ipaddress.ip_network(network):
                return True
        return False
    except ValueError:
        return False


# Load configuration
try:
    app.config['CAPTCHA_CONFIG'] = load_config()
except Exception as e:
    print(f"Failed to load configuration: {str(e)}")
    exit(1)

# Initialize captcha data with fixed config
captcha_data = {
    'code': None,
    'expire_time': None,
    'config': {
        'length': app.config['CAPTCHA_CONFIG']['length'],
        'include_letters': app.config['CAPTCHA_CONFIG']['include_letters'],
        'include_digits': app.config['CAPTCHA_CONFIG']['include_digits'],
        'include_special_chars': app.config['CAPTCHA_CONFIG']['include_special_chars'],
        'refresh_time': app.config['CAPTCHA_CONFIG']['refresh_sec']
    }
}


@app.before_request
def check_ip_whitelist():
    """Verify client IP is from internal network if enabled in config"""
    if not app.config['CAPTCHA_CONFIG'].get('internal_access_check', False):
        return

    client_ip = request.remote_addr
    print(client_ip)
    internal_networks = app.config['CAPTCHA_CONFIG'].get('internal_networks', [])

    if not is_internal_ip(client_ip, internal_networks):
        abort(403, description="Access denied: IP not in internal network")


def generate_captcha():
    """Generate random captcha based on fixed configuration"""
    characters = ''
    config = captcha_data['config']

    if config['include_letters']:
        characters += string.ascii_letters
    if config['include_digits']:
        characters += string.digits
    if config['include_special_chars']:
        characters += "!@#$%^&*()"

    if not characters:
        raise ValueError("At least one character type must be enabled")

    return ''.join(random.choice(characters) for _ in range(config['length']))


def refresh_captcha():
    """Refresh the current captcha"""
    captcha_data['code'] = generate_captcha()
    captcha_data['expire_time'] = datetime.now() + timedelta(
        seconds=captcha_data['config']['refresh_time']
    )


@app.route('/captcha', methods=['GET'])
def get_captcha():
    current_time = datetime.now()

    # Generate new captcha if needed
    if not captcha_data['code'] or current_time >= captcha_data['expire_time']:
        refresh_captcha()

    remaining_time = int((captcha_data['expire_time'] - current_time).total_seconds())

    return jsonify({
        'captcha': captcha_data['code'],
        'expire_time': captcha_data['expire_time'].strftime('%Y-%m-%d %H:%M:%S'),
        'remaining_seconds': remaining_time,
        'status': 'success'
    })


@app.route('/verify', methods=['POST'])
def verify_captcha():
    data = request.get_json()
    if not data or 'captcha' not in data:
        return jsonify({
            'valid': False,
            'code': 400,
            'message': 'Missing captcha in request body'
        }), 400

    current_time = datetime.now()

    if current_time >= captcha_data['expire_time']:
        return jsonify({
            'valid': False,
            'code': 401,
            'message': 'Captcha expired'
        }), 401

    if data['captcha'] == captcha_data['code']:
        return jsonify({
            'valid': True,
            'code': 200,
            'message': 'Captcha matched'
        })
    else:
        return jsonify({
            'valid': False,
            'code': 401,
            'message': 'Captcha not matched'
        }), 401


@app.route('/rotate', methods=['POST'])
def rotate_captcha():
    refresh_captcha()
    return jsonify({
        'status': 'success',
        'message': 'Captcha rotated successfully',
        'new_captcha': captcha_data['code'],
        'expire_time': captcha_data['expire_time'].strftime('%Y-%m-%d %H:%M:%S')
    })


if __name__ == '__main__':
    port = app.config['CAPTCHA_CONFIG'].get('port', 8081)
    app.run(host='0.0.0.0', port=port)