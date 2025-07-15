from functools import wraps
import os
import re
from cerberus import Validator
from flask import jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from LoadEnviroment.LoadEnv import (mysql_host, mysql_port, mysql_username, mysql_password,
                                    refresh_token_exp_sec, access_token_exp_sec, mysql_use_ssl, mysql_ssl_ca,
                                    mysql_ssl_cert, mysql_ssl_key, mysql_ssl_verify_cert)
from Crypto.Cipher import AES
import base64
import json

from utils.encrypter import rsa_decrypt, private_key, decrypt_aes_gcm


def get_data():
    data = getattr(request, 'decrypted_json', None)
    if data is None:
        # 没加密，正常用 request.json
        data = request.get_json()
    return data


def encrypt_response(original_function=None):
    """
    路由是否启用强制加密的标志。
    - 如果装饰在路由上 → 强制加密（无 X-AES-Key 返回 400）
    - 如果不装饰 → 由 json_response 判断是否加密（X-AES-Key 有就加密，没有就正常返回）
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            response = fn(*args, **kwargs)

            # 获取 header 中加密的 AES 密钥（base64）
            encrypted_aes_key = request.headers.get('X-AES-Key')

            # 强制加密路由但未提供加密密钥
            if not encrypted_aes_key:
                return jsonify({
                    'status': 'fail',
                    'msg': '缺少加密密钥：X-AES-Key 不能为空（当前接口强制加密）'
                }), 400

            try:
                # 解密 AES 密钥
                aes_key = rsa_decrypt(encrypted_aes_key, private_key)

                # 获取原始数据内容
                obj = response[0].get_json()

                if obj.get('data') is not None:
                    iv = os.urandom(12)
                    cipher = AES.new(aes_key, AES.MODE_GCM, nonce=iv)
                    ciphertext, tag = cipher.encrypt_and_digest(
                        json.dumps(obj['data']).encode()
                    )

                    encrypted_data = {
                        'iv': base64.b64encode(iv).decode(),
                        'ciphertext': base64.b64encode(ciphertext).decode(),
                        'tag': base64.b64encode(tag).decode()
                    }

                    return jsonify({
                        'status': obj['status'],
                        'msg': obj['msg'],
                        'data': encrypted_data
                    }), obj['code']
                return response
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'msg': f'加密失败: {str(e)}'
                }), 500

        return wrapper

    # 支持无参数使用 @encrypt_response
    if callable(original_function):
        return decorator(original_function)
    return decorator


# 修改json_response为自动应用装饰器
def json_response(status: str, message: str, data=None, code=200):
    def _build_response():
        response = {'status': status, 'msg': message, 'code': code}
        if data is not None:
            response['data'] = data

        encrypted_aes_key = request.headers.get('X-AES-Key')
        if encrypted_aes_key:
            try:
                aes_key = rsa_decrypt(encrypted_aes_key, private_key)

                iv = os.urandom(12)
                cipher = AES.new(aes_key, AES.MODE_GCM, nonce=iv)
                ciphertext, tag = cipher.encrypt_and_digest(json.dumps(data).encode())

                encrypted = {
                    'iv': base64.b64encode(iv).decode(),
                    'ciphertext': base64.b64encode(ciphertext).decode(),
                    'tag': base64.b64encode(tag).decode()
                }

                return jsonify({'status': status, 'msg': message, 'data': encrypted}), code
            except Exception as e:
                return jsonify({'status': 'error', 'msg': f'加密失败: {str(e)}'}), 500

        return jsonify(response), code

    return _build_response()


def require_encrypted_json(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if 'X-AES-Key' not in request.headers:
            return jsonify({'status': 'fail', 'msg': '缺少 X-AES-Key 请求头，强制要求加密'}), 400
        if not request.is_json:
            return jsonify({'status': 'fail', 'msg': '请求体必须是 application/json'}), 400

        encrypted_data = request.get_json()
        if not all(k in encrypted_data for k in ('ciphertext', 'iv', 'tag')):
            return jsonify({'status': 'fail', 'msg': '请求体缺少加密字段'}), 400

        try:
            aes_key = rsa_decrypt(request.headers['X-AES-Key'], private_key)
            decrypted_json = decrypt_aes_gcm(encrypted_data, aes_key)
            # 传入解密数据给路由，覆盖request.json
            request.decrypted_json = decrypted_json
        except Exception as e:
            return jsonify({'status': 'fail', 'msg': f'请求解密失败: {str(e)}'}), 400

        return view_func(*args, **kwargs)

    return wrapper


def auto_decrypt_if_present(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if 'X-AES-Key' in request.headers and request.is_json:
            encrypted_data = request.get_json()
            if all(k in encrypted_data for k in ('ciphertext', 'iv', 'tag')):
                try:
                    aes_key = rsa_decrypt(request.headers['X-AES-Key'], private_key)
                    decrypted_json = decrypt_aes_gcm(encrypted_data, aes_key)
                    # 动态替换 request.json，供后续使用
                    # Flask request.json 是只读的，我们用 request.decrypted_json 自定义属性，
                    # 需要在路由中自己用这个属性替代 request.json
                    request.decrypted_json = decrypted_json
                except Exception as e:
                    return jsonify({'status': 'fail', 'msg': f'请求解密失败: {str(e)}'}), 400
        return view_func(*args, **kwargs)

    return wrapper


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
