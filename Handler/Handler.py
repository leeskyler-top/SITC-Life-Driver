import flask.wrappers
from flask_jwt_extended import get_jwt_identity, jwt_required, verify_jwt_in_request
from sqlalchemy.exc import IntegrityError
from functools import wraps
from flask import jsonify, request, Response

from Model.History import History, MethodEnum
from Model.User import User, PositionEnum
from Controller.globals import json_response  # 导入统一的 JSON 响应函数


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
