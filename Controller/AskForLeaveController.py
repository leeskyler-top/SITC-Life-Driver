import os
import uuid
from datetime import datetime, timedelta
from PIL import Image
import json

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from Handler.Handler import position_required, record_history, admin_required
from LoadEnviroment.LoadEnv import upload_folder
from Model import CheckInUser
from Model.AskForLeaveApplication import AskForLeaveApplication, StatusEnum, AskForLeaveEnum
from Model.User import PositionEnum
from utils.utils import allowed_file, validate_image
from .globals import json_response, Session, validate_schema

ask_for_leave_controller = Blueprint('ask_for_leave_controller', __name__)

# 配置文件设置
MAX_IMAGE_SIZE = 35 * 1024 * 1024  # 35MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_IMAGES = 3


def cleanup_old_images():
    """
    自动清理一年前的图片（可在定时任务中调用）
    """
    one_year_ago = datetime.now() - timedelta(days=365)

    session = Session()
    try:
        records = session.query(AskForLeaveApplication).filter(
            AskForLeaveApplication.created_at < one_year_ago,
            AskForLeaveApplication.image_url.isnot(None)
        ).all()

        for record in records:
            try:
                image_urls = json.loads(record.image_url)
                for path in image_urls:
                    if os.path.exists(path):
                        os.remove(path)
                record.image_url = None
            except:
                continue

        session.commit()
    except:
        session.rollback()
    finally:
        session.close()


def save_uploaded_images(files, check_in_user_id):
    """保存上传的图片并返回路径列表"""
    saved_paths = []
    user_folder = os.path.join(upload_folder, f'user_{check_in_user_id}')

    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    for file in files:
        if file and allowed_file(file.filename) and validate_image(file.stream):
            # 生成安全的随机文件名
            ext = file.filename.rsplit('.', 1)[1].lower()
            new_filename = f"{uuid.uuid4()}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.{ext}"
            filepath = os.path.join(user_folder, new_filename)

            # 保存文件
            file.save(filepath)

            # 验证图片完整性
            try:
                img = Image.open(filepath)
                img.verify()
                saved_paths.append(filepath)
            except:
                os.remove(filepath)
                continue

    return saved_paths


@ask_for_leave_controller.route('/my/<int:check_in_user_id>', methods=['POST'], endpoint='create_leave_application')
@jwt_required()
@record_history
def create_my_leave_application(check_in_user_id):
    """
    为当前用户的某个签到创建请假申请（支持图片上传）
    """
    user_id = get_jwt_identity()

    # 检查表单数据
    if 'form' not in request.form:
        return json_response('fail', '未提供表单数据', code=422)

    try:
        data = json.loads(request.form['form'])
    except json.JSONDecodeError:
        return json_response('fail', '表单数据格式错误', code=422)

    # 验证请假类型
    asl_values = [item.value for item in AskForLeaveEnum]
    if 'asl_type' not in data or data['asl_type'] not in asl_values:
        return json_response('fail', '无效的请假类型', code=422)

    # 验证图片上传
    image_urls = []
    if data['asl_type'] != "事假":  # 事假不需要图片
        if 'image_url[]' not in request.files:
            return json_response('fail', '请上传证明图片', code=422)

        files = request.files.getlist('image_url[]')
        if len(files) > MAX_IMAGES:
            return json_response('fail', f'最多上传{MAX_IMAGES}张图片', code=422)

        # 检查总大小
        total_size = sum(len(file.read()) for file in files)
        for file in files:  # 重置文件指针
            file.seek(0)

        if total_size > MAX_IMAGE_SIZE:
            return json_response('fail', '图片总大小不能超过35MB', code=422)

        # 保存图片
        image_urls = save_uploaded_images(files, check_in_user_id)
        if not image_urls:
            return json_response('fail', '未上传有效的图片文件', code=422)

    # 验证其他字段
    if 'asl_reason' not in data or not data['asl_reason'].strip():
        return json_response('fail', '请填写请假原因', code=422)

    # 检查签到记录
    check_in_user = CheckInUser.get_by_id(check_in_user_id)
    if not check_in_user or check_in_user.user_id != int(user_id):
        return json_response('fail', "未找到签到记录", code=404)

    # 检查该签到记录是否已有待审核或已通过的请假
    session = Session()
    try:
        existing_asl = session.query(AskForLeaveApplication).filter(
            AskForLeaveApplication.check_in_user_id == check_in_user_id,
            AskForLeaveApplication.status.in_([StatusEnum.ACCEPTED, StatusEnum.PENDING])
        ).first()

        if existing_asl:
            return json_response('fail', '该签到已存在待审核或已批准的请假申请', code=400)
    finally:
        session.close()

    # 创建请假申请
    status, asl, code = AskForLeaveApplication.create_asl(
        check_in_user_id=check_in_user_id,
        asl_type=data['asl_type'],
        asl_reason=data['asl_reason'],
        status="待审核",
        image_url=json.dumps(image_urls) if image_urls else None
    )

    if not status:
        return json_response('fail', asl, code=code)

    return json_response('success', '请假申请创建成功', data={'id': asl['id']})


@ask_for_leave_controller.route('/my/<int:application_id>', methods=['GET'], endpoint='get_my_leave_application_info')
@jwt_required()
@record_history
def get_my_leave_application_info(application_id):
    """
    获取当前请假申请具体信息
    """
    user_id = get_jwt_identity()
    try:
        asl_application = AskForLeaveApplication.get_asl_by_id(application_id)
        if not asl_application or asl_application["check_in_user"]["user_id"] != int(user_id):
            return json_response('fail', "未找到请假", code=404)
        return json_response('success', '获取成功', data=asl_application)

    except Exception as e:
        return json_response('fail', f'查询失败：{str(e)}', code=500)


@ask_for_leave_controller.route('/my/checkinuser/<int:check_in_user_id>', methods=['GET'],
                                endpoint='get_my_check_in_leave_applications')
@jwt_required()
@record_history
def get_my_check_in_leave_application(check_in_user_id):
    """
    获取当前用户自己的某个签到中所有请假申请
    """
    user_id = get_jwt_identity()
    try:
        result = AskForLeaveApplication.search_asl(check_in_user_id=check_in_user_id, user_id=int(user_id))
        if not result:
            return json_response('fail', "未找到请假", code=404)
        return json_response('success', '获取成功', data=result)

    except Exception as e:
        return json_response('fail', f'查询失败：{str(e)}', code=500)


@ask_for_leave_controller.route('', methods=['GET'], endpoint='get_my_leave_applications')
@jwt_required()
@record_history
def get_my_leave_applications():
    """
    获取当前用户的所有请假申请
    """
    user_id = get_jwt_identity()
    try:
        result = AskForLeaveApplication.search_asl(user_id=user_id)
        return json_response('success', '获取成功', data=result)

    except Exception as e:
        return json_response('fail', f'查询失败：{str(e)}', code=500)


@ask_for_leave_controller.route('/my/cancel/<int:application_id>', methods=['POST'],
                                endpoint='cancel_my_leave_application')
@jwt_required()
@record_history
def cancel_my_leave_application(application_id):
    """
    取消请假申请
    """
    session = Session()
    try:
        application = session.query(AskForLeaveApplication).filter_by(id=application_id).first()

        if not application:
            return json_response('fail', '请假申请不存在', code=404)

        if application.status != "待审核":
            return json_response('fail', '请假状态错误', code=400)
        application.status = StatusEnum("已取消")
        session.commit()
        return json_response('success', '请假申请已删除')

    except Exception as e:
        session.rollback()
        return json_response('fail', f'处理请求时出错：{str(e)}', code=500)
    finally:
        session.close()


@ask_for_leave_controller.route('/<int:application_id>', methods=['PATCH'], endpoint='update_leave_application')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
@record_history
def update_leave_application(application_id):
    """
    更新请假申请（含审批、撤回批准）
    """
    data = request.get_json()
    if not data:
        return json_response('fail', '未提供请求数据', code=422)

    asl_values = [item.value for item in AskForLeaveEnum]
    status_values = [item.value for item in StatusEnum]

    schema = {
        'status': {
            'type': 'string',
            'allowed': status_values,
            'required': True
        },
        'asl_type': {
            'type': 'string',
            'required': False,
            'allowed': asl_values
        },
        'reject_reason': {
            'type': 'string',
            'required': False
        }
    }

    result, reason = validate_schema(schema, data)
    if not result:
        return json_response('fail', f"请求数据格式错误: {reason}", code=422)

    session = Session()
    try:
        application = session.query(AskForLeaveApplication).filter_by(id=application_id).first()

        if not application:
            return json_response('fail', '请假申请不存在', code=404)

        if data['status'] == '已拒绝' and data.get('reject_reason', '').strip() == '':
            return json_response('fail', '拒绝批准请填写理由', code=422)
        application.status = StatusEnum(data['status'])

        if data.get('asl_type', None) is not None:
            application.asl_type = AskForLeaveEnum(data['asl_type'])

        session.commit()
        return json_response('success', '请假申请状态已更新')

    except Exception as e:
        session.rollback()
        return json_response('fail', f'处理请求时出错：{str(e)}', code=500)
    finally:
        session.close()


@ask_for_leave_controller.route('', methods=['GET'], endpoint='get_all_leave_applications')
@position_required([PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER])
@record_history
def get_all_leave_applications():
    """
    获取所有请假记录（管理员权限）
    """
    try:
        # 自动清理一年前的图片
        cleanup_old_images()

        # 获取所有记录
        result = AskForLeaveApplication.search_asl()
        return json_response('success', '获取成功', data=result)

    except Exception as e:
        return json_response('fail', f'查询失败: {str(e)}', code=500)


@ask_for_leave_controller.route('/cleanup-images', methods=['POST'], endpoint='cleanup_images')
@admin_required
def cleanup_images():
    """
    清理指定日期的图片并更新数据库记录
    """
    data = request.get_json()
    if not data or 'target_date' not in data:
        return json_response('fail', '请提供目标日期', code=422)

    try:
        target_date = datetime.strptime(data['target_date'], '%Y-%m-%d').date()
    except ValueError:
        return json_response('fail', '日期格式错误，应为YYYY-MM-DD', code=422)

    session = Session()
    try:
        # 查找目标日期的记录
        records = session.query(AskForLeaveApplication).filter(
            func.date(AskForLeaveApplication.created_at) == target_date,
            AskForLeaveApplication.image_url.isnot(None)
        ).all()

        deleted_count = 0
        for record in records:
            try:
                image_urls = json.loads(record.image_url)
                for path in image_urls:
                    if os.path.exists(path):
                        os.remove(path)
                record.image_url = None
                deleted_count += 1
            except:
                continue

        session.commit()
        return json_response('success', f'成功清理{deleted_count}条记录的图片')

    except Exception as e:
        session.rollback()
        return json_response('fail', f'清理失败: {str(e)}', code=500)
    finally:
        session.close()
