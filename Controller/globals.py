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


def validate_schema(schema, data):
    v = Validator(schema)
    if not v.validate(data):
        return False, v.errors
    else:
        return True, ""

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
