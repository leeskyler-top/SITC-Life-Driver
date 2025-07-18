from Handler.Handler import record_history
from SQLService.RedisUtils import get_redis
from utils.captchaUtils import generate_captcha
from utils.encrypter import PUBLIC_KEY_PEM, encrypt_with_backend_key, decrypt_with_backend_key
from utils.limiter import limiter
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

redis_client = get_redis()

@auth_controller.route('/captcha', methods=['GET'])
@limiter.limit("30 per minute", key_func=lambda: request.headers.get('Cf-Connecting-Ip') or request.remote_addr)
def get_captcha():
    captcha_type = request.args.to_dict().get('type', 'image')
    uuid, data, answer = generate_captcha(True, True, 5, type=captcha_type)
    answer = encrypt_with_backend_key(answer.strip().lower())
    redis_client.setex(f'captcha:{uuid}', 180, answer)
    return json_response('success', '获取成功', data={
        'uuid': uuid,
        'image_data': f'data:image/png;base64,{data}' if captcha_type == 'image' else f'data:audio/mpeg;base64,{data}'
    })


# 登录逻辑
@auth_controller.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return json_response('fail', '请提供账号和密码', code=400)



    student_id = data.get('studentId')
    password = data.get('password')
    captcha_uuid = data.get('captcha_uuid')
    captcha_answer = data.get('captcha_answer')

    if not captcha_uuid or not captcha_answer:
        return json_response('fail', '验证码缺失', code=400)

    ip = request.headers.get('Cf-Connecting-Ip')
    # 若Cf-Connecting-Ip存在，按IP限制频率
    if ip:
        key = f'login:ip:{ip}'
        fail_key = f'login:ban:{ip}'
    else:
        # 否则按 studentId 限制（锁定学号）
        key = f'login:id:{student_id}'
        fail_key = f'login:ban:{student_id}'

    if redis_client.exists(fail_key):
        return json_response('fail', '登录频率过高，请稍后再试', code=429)

        # 超过 20 次则封禁
    if int(redis_client.get(key) or 0) > 20:
        redis_client.setex(fail_key, 900, 1)  # 封禁15分钟
        return json_response('fail', '登录频率过高，请15分钟后再试', code=429)

    redis_key = f'captcha:{captcha_uuid}'
    correct_answer = redis_client.get(redis_key)
    redis_client.delete(redis_key)  # 阅后即焚

    if not correct_answer or captcha_answer.strip().lower() != decrypt_with_backend_key(correct_answer):
        return json_response('fail', '验证码错误', code=400)

    # 验证用户身份
    session = Session()
    user = session.query(User).filter_by(studentId=student_id).first()

    if not user or not user.verify_password(password, user.password):  # 假设 User 模型有 verify_password 方法

        redis_client.incr(key)
        redis_client.expire(key, 600)  # 10分钟内计数

        return json_response('fail', '用户名或密码错误', code=401)
    if user.is_deleted == True:
        return json_response('fail', '账户已封禁，联系管理员', code=403)

    # 创建访问和刷新 Token
    access_token = create_access_token(identity=str(user.id), expires_delta=ACCESS_EXPIRES)
    refresh_token = create_refresh_token(identity=str(user.id), expires_delta=REFRESH_EXPIRES)

    return json_response('success', '登录成功', data={
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict(),
        'public_key': PUBLIC_KEY_PEM
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
