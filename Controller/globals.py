from cerberus import Validator
from flask import jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from LoadEnviroment.LoadEnv import mysql_host, mysql_port, mysql_username, mysql_password
def json_response(status: str, message: str, data=None, code=200):
    """
    统一的 JSON 响应格式
    """
    response = {'status': status, 'message': message}
    if data is not None:
        response['data'] = data
    return jsonify(response), code


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
    'json_response',
    'validate_schema',
]