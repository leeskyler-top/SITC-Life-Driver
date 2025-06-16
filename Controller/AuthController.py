from Handler.Handler import record_history
from .globals import access_token_exp_sec, refresh_token_exp_sec
from flask import Blueprint, request
from flask_jwt_extended import (
    jwt_required,
    create_access_token,
    create_refresh_token,
    get_jwt_identity
)
from datetime import timedelta
from Model.User import User
from Controller.globals import json_response, Session

# 初始化 Blueprint
auth_controller = Blueprint('auth_controller', __name__)

# 配置 Token 的过期时间
ACCESS_EXPIRES = timedelta(seconds=access_token_exp_sec)  # 设置为 3 分钟的有效期
REFRESH_EXPIRES = timedelta(seconds=refresh_token_exp_sec)  # 设置为 30 分钟的有效期


# 登录逻辑
@auth_controller.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return json_response('fail', '请提供账号和密码', code=400)

    student_id = data.get('studentId')
    password = data.get('password')

    # 验证用户身份
    session = Session()
    user = session.query(User).filter_by(studentId=student_id).first()

    if not user or not user.verify_password(password, user.password):  # 假设 User 模型有 verify_password 方法
        return json_response('fail', '用户名或密码错误', code=401)
    if user.is_deleted == True:
        return json_response('fail', '账户已封禁，联系管理员', code=403)

    # 创建访问和刷新 Token
    access_token = create_access_token(identity=str(user.id), expires_delta=ACCESS_EXPIRES)
    refresh_token = create_refresh_token(identity=str(user.id), expires_delta=REFRESH_EXPIRES)

    return json_response('success', '登录成功', data={
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    })


# 登出逻辑
@auth_controller.route('/logout', methods=['DELETE'])
@jwt_required()
@record_history
def logout():
    # 实际登出逻辑是在客户端删除 Token
    return json_response('success', '已成功登出')


# 刷新 Token
@auth_controller.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    print(current_user_id)
    # 创建新的 Access Token
    access_token = create_access_token(identity=current_user_id, expires_delta=ACCESS_EXPIRES)

    return json_response('success', 'Token 刷新成功', data={
        'access_token': access_token
    }, code=200)
