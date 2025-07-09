import flask.wrappers
from flask_jwt_extended import get_jwt_identity, jwt_required, verify_jwt_in_request
from flask_limiter import RateLimitExceeded
from sqlalchemy.exc import IntegrityError
from functools import wraps
from flask import jsonify, request

from LoadEnviroment.LoadEnv import hmac_secret_key, cloudflare_worker_secret
from Model.History import History, MethodEnum
from Model.User import User, PositionEnum
from Controller.globals import json_response  # 导入统一的 JSON 响应函数
import hmac
import hashlib


def handle_global_exceptions(app):
    """
    全局异常捕获
    """

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        # 解析错误信息，提取字段信息（如果需要）
        error_message = str(error.orig)  # 提取底层数据库的错误信息
        # 返回统一的 JSON 响应格式，状态码 422
        return json_response(
            status="fail",
            message="数据库约束错误：可能存在唯一性冲突",
            data={"details": error_message},
            code=422
        )

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit_exceeded(e):
        return jsonify({
            "status": "error",
            "msg": "请求过快",
            "data": {
                "details": str(e)  # 可选替换为自定义提示
            }
        }), 429

    @app.errorhandler(Exception)
    def handle_general_exception(error):
        # 捕获其他未明确处理的异常
        return json_response(
            status="error",
            message="服务器内部错误",
            data={"details": str(error)},
            code=500
        )


def admin_required(f):
    """
    装饰器：限制仅管理员可以访问的路由
    """

    @wraps(f)
    @jwt_required()  # 确保是已认证的用户
    def decorated_function(*args, **kwargs):
        # 获取当前用户的ID
        current_user_id = get_jwt_identity()

        # 查询当前用户信息，假设有一个方法 get_user_by_id()
        user = User.get_user_by_id(current_user_id)  # 替换为你的查询方法

        if not user or not user["is_admin"]:
            return jsonify({"status": "fail", "msg": "权限不足"}), 403  # 403 禁止访问

        return f(*args, **kwargs)

    return decorated_function


def position_required(positions=None, is_admin_required=False):
    if positions is None:
        positions = [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER,
                     PositionEnum.SUMMARY_LEADER, PositionEnum.INTERN_SUMMARY_LEADER]
    positions = [position.value for position in positions]

    def decorator(f):
        @wraps(f)
        @jwt_required()  # 确保是已认证的用户
        def wrapper(*args, **kwargs):
            current_user_id = get_jwt_identity()  # 获取当前用户的 ID
            user = User.get_user_by_id(current_user_id)

            if not user:
                return jsonify({"status": "fail", "msg": "用户不存在"}), 404

            # 检查是否满足角色或管理员的要求
            if is_admin_required and user["is_admin"]:
                return f(*args, **kwargs)

            if (user["position"] in positions) or (user["is_admin"]):
                return f(*args, **kwargs)

            return jsonify({"status": "fail", "msg": "权限不足"}), 403  # 权限不足的错误

        return wrapper

    return decorator


def record_history(f):
    """
    智能历史记录装饰器：
    - 只记录成功通过JWT认证的请求
    - 自动排除OPTIONS预检请求
    - 错误处理不会影响主流程
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 先执行视图函数获取响应
        response = f(*args, **kwargs)
        # 只在响应成功时记录历史(2xx/3xx状态码)
        if (
                (isinstance(response, tuple) and 200 <= response[1] < 400)
                or
                (isinstance(response, flask.wrappers.Response) and response.status == "200 OK")
        ):
            try:
                # 检查请求是否携带有效JWT(不抛出异常)
                verify_jwt_in_request(optional=True)
                user_id = get_jwt_identity()

                if user_id and request.method != 'OPTIONS':
                    method_enum = MethodEnum[request.method]
                    History.add_history(
                        user_id=user_id,
                        method=method_enum,
                        url=request.url
                    )
            except Exception as e:
                print(f"历史记录失败: {str(e)}")

        return response

    return decorated_function


def is_cloudflare_worker_request():
    """验证请求是否来自 Cloudflare Worker（HMAC + IP）"""
    signature = request.headers.get("X-Cloudflare-Signature")
    if not signature:
        return False

    client_ip = (
        request.headers.get("X-Original-IP") or
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
        request.remote_addr
    )
    expected_signature = hmac.new(
        cloudflare_worker_secret.encode('utf-8'),
        client_ip.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)

def cloudflare_worker_required(func):
    """装饰器：限制仅 Cloudflare Worker 访问"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_cloudflare_worker_request():
            return {"status": "fail", "msg": "Unauthorized Worker Request"}, 403
        return func(*args, **kwargs)
    return wrapper


def is_internal_request():
    """验证请求是否来自内网（基于HMAC签名）"""
    received_signature = request.headers.get("X-Network-Signature")
    if not received_signature:
        return False

    client_ip = request.headers.get('X-Real-IP') or request.remote_addr
    expected_signature = hmac.new(
        hmac_secret_key.encode(),
        client_ip.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(received_signature, expected_signature)


def internal_required(func):
    """装饰器：将内网验证结果作为参数传递给路由函数"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        is_internal = is_internal_request()
        return func(is_internal=is_internal, *args, **kwargs)

    return wrapper


# 可选：严格模式装饰器（非内网直接返回403）
def internal_strict(func):
    """装饰器：非内网请求直接返回403"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_internal_request():
            return jsonify({"status": "fail", "message": "内网访问要求"}), 403
        return func(*args, **kwargs)

    return wrapper
