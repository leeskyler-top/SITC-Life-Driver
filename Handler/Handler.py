from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError
from functools import wraps
from flask import jsonify
from Model.User import User, PositionEnum
from Controller.globals import json_response  # 导入统一的 JSON 响应函数
from .globals import Session

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
            return jsonify({"status": "fail", "message": "权限不足"}), 403  # 403 禁止访问

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
            session = Session()
            user = session.query(User).filter_by(id=current_user_id).first()
            session.close()

            if not user:
                return jsonify({"status": "fail", "message": "用户不存在"}), 404

            # 检查是否满足角色或管理员的要求
            if is_admin_required and user["is_admin"]:
                return f(*args, **kwargs)

            if (user["position"] in positions) or (user["is_admin"]):
                return f(*args, **kwargs)

            return jsonify({"status": "fail", "message": "权限不足"}), 403  # 权限不足的错误

        return wrapper

    return decorator