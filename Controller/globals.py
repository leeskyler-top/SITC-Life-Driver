import re
from cerberus import Validator
from flask import jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from LoadEnviroment.LoadEnv import (mysql_host, mysql_port, mysql_username, mysql_password,
                                    refresh_token_exp_sec, access_token_exp_sec, mysql_use_ssl, mysql_ssl_ca,
                                    mysql_ssl_cert, mysql_ssl_key, mysql_ssl_verify_cert)


def json_response(status: str, message: str, data=None, code=200):
    """
    统一的 JSON 响应格式
    """
    response = {'status': status, 'msg': message}
    if data is not None:
        response['data'] = data
    return jsonify(response), code


# Define the custom validator for non-empty strings
def non_empty_string(field, value, error):
    try:
        if str(value).strip() == "" or not value:  # Check for empty or whitespace-only strings
            error(field, f"{field} must not be empty!")
        return True
    except Exception:
        return False


def validate_schema(schema, data, check_xml_tag: bool = True, strict: bool = True) -> tuple:
    html_tag_pattern = re.compile(r'<[^>]+>')

    def contains_html(value) -> bool:
        if value is None or isinstance(value, (int, float)):
            return False
        if isinstance(value, str):
            return bool(html_tag_pattern.search(value))
        return False

    def strip_html(value):
        if value is None or isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            return re.sub(html_tag_pattern, '', value)
        return value

    def check_for_html(data) -> bool:
        if data is None or isinstance(data, (int, float)):
            return False
        if isinstance(data, str):
            return contains_html(data)
        if isinstance(data, dict):
            return any(check_for_html(v) for v in data.values())
        if isinstance(data, list):
            return any(check_for_html(item) for item in data)
        return False

    def process_data(data):
        if data is None or isinstance(data, (int, float)):
            return data
        if isinstance(data, str):
            return strip_html(data)
        if isinstance(data, dict):
            return {k: process_data(v) for k, v in data.items()}
        if isinstance(data, list):
            return [process_data(item) for item in data]
        return data

    # First check for HTML tags
    if check_xml_tag and check_for_html(data):
        if strict:
            return False, '非法传入HTML、XML标签'
        processed_data = process_data(data)
        v = Validator(schema)
        if not v.validate(processed_data):
            return False, v.errors
        return True, processed_data  # Return processed data in non-strict mode

    v = Validator(schema)
    if not v.validate(data):
        return False, v.errors
    return True, data if not strict else ""


if mysql_use_ssl:
    ssl_config = {
        'ca': mysql_ssl_ca,
        'cert': mysql_ssl_cert,
        'key': mysql_ssl_key,
        'check_hostname': mysql_ssl_verify_cert,
        'verify_cert': mysql_ssl_verify_cert,
        'verify_identity': mysql_ssl_verify_cert
    }
    engine = create_engine(
        f'mysql+pymysql://{mysql_username}:{mysql_password}@{mysql_host}:{mysql_port}/SITC',
        connect_args={
            'ssl': ssl_config
        }
    )
else:
    engine = create_engine(f'mysql+pymysql://{mysql_username}:{mysql_password}@{mysql_host}:{mysql_port}/SITC')

# 创建 session factory
Session = sessionmaker(bind=engine)

__all__ = [
    "engine",
    "Session",
    "refresh_token_exp_sec",
    "access_token_exp_sec",
    'json_response',
    'validate_schema',
    'non_empty_string'
]
