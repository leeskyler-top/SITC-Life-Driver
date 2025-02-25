from cerberus import Validator
from flask import jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from LoadEnviroment.LoadEnv import (mysql_host, mysql_port, mysql_username, mysql_password,
                                    refresh_token_exp_sec, access_token_exp_sec)


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


engine = create_engine(f'mysql+pymysql://{mysql_username}:{mysql_password}@{mysql_host}:{mysql_port}/SITC')

# 创建 session factory
Session = sessionmaker(bind=engine)

__all__ = [
    "engine",
    "Session",
    "refresh_token_exp_sec",
    "access_token_exp_sec",
    'json_response',
    'validate_schema'
]
