import os
import uuid
from datetime import datetime, timedelta
from PIL import Image
import json

from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from Handler.Handler import position_required, record_history, admin_required
from LoadEnviroment.LoadEnv import upload_folder, storage, cloudflare_worker_baseurl
from MicrosoftGraphAPI.FileOperation import permanentDelete
from Model import CheckInUser, Message
from Model.AskForLeaveApplication import AskForLeaveApplication, StatusEnum, AskForLeaveEnum
from Model.CheckInUser import CheckInStatusEnum
from Model.User import PositionEnum
from utils.utils import allowed_file, detect_mime
from .globals import json_response, Session, validate_schema, auto_decrypt_if_present, get_data
from werkzeug.utils import secure_filename

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
                image_urls = json.loads(record.image_url) if record.image_url is not None else []
                if storage == 'local':
                    for path in image_urls:
                        if os.path.exists(os.path.join(upload_folder, path)):
                            os.remove(os.path.join(upload_folder, path))
                else:
                    for url in image_urls:
                        if url.startswith(cloudflare_worker_baseurl):
                            permanentDelete(url)
                        else:
                            continue
            except:
                continue

        session.commit()
    except:
        session.rollback()
    finally:
        session.close()


def validate_and_save_images(files, check_in_user_id):
    """
    遍历上传文件，验证格式、大小，并保存图片。返回保存路径列表或 None（失败）。
    """
    image_urls = []
    total_size = 0

    for file in files:
        if not file or file.filename == '':
            continue

        filename = secure_filename(file.filename)

        # 扩展名检查
        if not allowed_file(filename):
            continue

        # 检查文件大小（通过 seek/tell）
        file.seek(0, os.SEEK_END)
        size = file.tell()
        total_size += size
        if total_size > MAX_IMAGE_SIZE:
            return None  # 超出总大小限制
        file.seek(0)

        # 使用 PIL 验证图片有效性
        try:
            with Image.open(file) as img:
                img.verify()
                if img.format.lower() not in ALLOWED_EXTENSIONS:
                    continue
        except Exception:
            continue

        # 重置指针准备保存
        file.seek(0)

        # 构造安全文件名
        suffix = filename.rsplit('.', 1)[1].lower()
        unique_name = f"{check_in_user_id}_{uuid.uuid4().hex}.{suffix}"
        save_path = os.path.join(upload_folder, unique_name)

        try:
            file.save(save_path)
            image_urls.append(save_path)
        except Exception as e:
            print(f"[ERROR] 文件保存失败: {e}")
            continue

        if len(image_urls) >= MAX_IMAGES:
            break

    return image_urls


def size_check(files):
    # 只检查基本文件属性，不实际保存
    if len(files) > MAX_IMAGES:
        return False, f'最多上传{MAX_IMAGES}张图片'

    total_size = 0
    for file in files:
        chunk = file.stream.read(1024 * 1024)
        while chunk:
            total_size += len(chunk)
            if total_size > MAX_IMAGE_SIZE:
                return False, '图片总大小不能超过35MB'
            chunk = file.stream.read(1024 * 1024)
        file.seek(0)

    return True, None


@ask_for_leave_controller.route('/my', methods=['GET'], endpoint='get_my_leave_applications')
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


@ask_for_leave_controller.route('/my/<int:check_in_user_id>', methods=['POST'], endpoint='create_my_leave_application')
@jwt_required()
@record_history
def create_my_leave_application(check_in_user_id):
    """
    为当前用户的某个签到创建请假申请
    - 事假：可以不上传图片
    - 其他类型：必须上传图片
    """
    user_id = get_jwt_identity()

    if not request.form:
        return json_response('fail', '未提供表单数据', code=422)

    # 验证请假类型
    asl_values = [item.value for item in AskForLeaveEnum]
    if 'asl_type' not in request.form or request.form['asl_type'] not in asl_values:
        return json_response('fail', '无效的请假类型', code=422)

    is_valid, errors = validate_schema({'asl_reason': {'required': False}}, {'asl_reason': request.form['asl_reason']})
    if not is_valid:
        return json_response('fail', '请填写合法请假原因', code=422)

    # 获取上传的文件（但不立即处理）
    if storage == 'local':
        files = request.files.getlist('image_url')
        image_urls = files
    else:
        files = request.form.getlist('image_url')
        image_urls = files

    # 非事假类型必须上传图片
    if request.form['asl_type'] != AskForLeaveEnum.ASL.value and storage == 'local':
        if not files or not any(files):
            return json_response('fail', '请上传证明图片（该请假类型必须提供证明）', code=422)

        # 只检查基本文件属性，不实际保存
        result, reason = size_check(files)
        if not result:
            return json_response('fail', reason, code=422)
        # 实际保存图片
        image_urls = validate_and_save_images(files, check_in_user_id)

        # 非事假类型必须确保图片上传成功
        if not image_urls:
            return json_response('fail', '图片上传失败，请重新上传有效的证明图片-001', code=422)

    elif request.form['asl_type'] != AskForLeaveEnum.ASL.value and storage == 'microsoft':
        if not files or not any(files):
            return json_response('fail', '请上传证明图片（该请假类型必须提供证明）', code=422)
        if not isinstance(image_urls, list) or not all(
                isinstance(url, str) and url.startswith(cloudflare_worker_baseurl) for url in image_urls):
            return json_response('fail', '图片上传失败，请重新上传有效的证明图片-002', code=422)

    elif storage == 'local' and files and any(files):

        result, reason = size_check(files)

        if not result:
            return json_response('fail', reason, code=422)

        image_urls = validate_and_save_images(files, check_in_user_id)

        if not image_urls:
            return json_response('fail', '图片上传失败，请重新上传有效的证明图片', code=422)

    elif storage == 'microsoft' and files and any(files):

        if not isinstance(files, list) or not all(

                isinstance(url, str) and url.startswith(cloudflare_worker_baseurl) for url in files):
            return json_response("fail", "图片 URL 格式非法", code=422)

    # 验证其他字段
    if 'asl_reason' not in request.form or not request.form['asl_reason'].strip():
        return json_response('fail', '请填写请假原因', code=422)

    # 检查签到记录
    check_in_user = CheckInUser.get_by_id(check_in_user_id)
    if not check_in_user or check_in_user.user_id != int(user_id):
        return json_response('fail', "未找到签到记录", code=404)

    if check_in_user.to_dict()['status'] != CheckInStatusEnum.NOT_STARTED.value:
        return json_response('fail', '用户自己不可在签到开始后请假，如需操作联系管理员', code=403)

    # 检查是否已有待审核或已通过的请假
    session = Session()
    existing_asl = session.query(AskForLeaveApplication).filter(
        AskForLeaveApplication.check_in_user_id == check_in_user_id,
        AskForLeaveApplication.status.in_([StatusEnum.ACCEPTED, StatusEnum.PENDING])
    ).first()
    if existing_asl:
        return json_response('fail', '该签到已存在待审核或已批准的请假申请', code=400)
    session.close()

    # 创建请假申请
    status, asl, code = AskForLeaveApplication.create_asl(
        check_in_user_id=check_in_user_id,
        asl_type=request.form['asl_type'],
        asl_reason=request.form['asl_reason'],
        status="待审核",
        image_url=json.dumps(image_urls) if image_urls else None
    )

    if not status:
        # 如果创建失败，删除已上传的图片
        if image_urls:
            for path in image_urls:
                try:
                    os.remove(path)
                except:
                    pass
        return json_response('fail', asl, code=code)

    Message.add_message(
        user_id=None,
        msg_title=f"有一条请假申请待审批-{asl['created_at']}",
        msg_text=f""
                 f"<h3>请假ID:{asl['id']}</h3>"
                 f"<p>请假者:{asl['check_in_user']['user']['studentId']}-{asl['check_in_user']['user']['name']}</p>"
                 f"<p>值班：{asl['check_in_user']['schedule']['schedule_name']}-{asl['check_in_user']['schedule']['schedule_type']}-{asl['check_in_user']['schedule']['schedule_start_time']}</p>"
                 f"<p>签到：{asl['check_in_user']['check_in']['name']}</p>"
                 f"<p>申请时间：{asl['created_at']}</p>"
                 f"<p>详情请前往审批页面。</p>",
        msg_type="ADMIN"
    )
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


@ask_for_leave_controller.route('/my/cancel/<int:application_id>', methods=['GET'],
                                endpoint='cancel_my_leave_application')
@jwt_required()
@record_history
def cancel_my_leave_application(application_id):
    """
    取消请假申请
    """
    user_id = get_jwt_identity()
    session = Session()
    try:
        application = session.query(AskForLeaveApplication).filter_by(id=application_id).first()

        if not application or application.check_in_user.user_id != int(user_id):
            return json_response('fail', '请假申请不存在', code=404)

        if application.status != StatusEnum.PENDING:
            return json_response('fail', '请假状态错误', code=400)
        application.status = StatusEnum("已取消")
        session.commit()
        return json_response('success', '请假申请已删除')

    except Exception as e:
        session.rollback()
        return json_response('fail', f'处理请求时出错：{str(e)}', code=500)
    finally:
        session.close()


@ask_for_leave_controller.route('/my/photo/<int:application_id>/<string:photo_name>', methods=['GET'],
                                endpoint='get_my_photo')
@jwt_required()
@record_history
def get_my_photo(application_id, photo_name):
    """
    获取请假申请中的特定图片（自动检测MIME类型）
    """
    user_id = get_jwt_identity()
    try:
        # 获取请假申请
        asl_application = AskForLeaveApplication.get_asl_by_id(application_id)

        # 验证权限和图片存在性
        if (not asl_application or
                asl_application["check_in_user"]["user_id"] != int(user_id) or
                asl_application['image_url'] is None or
                photo_name not in asl_application['image_url']):
            return json_response('fail', "未授权访问或图片不存在", code=404)

        # 构建完整文件路径
        file_path = os.path.join(upload_folder, photo_name)

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return json_response('fail', "图片文件不存在", code=404)

        # 使用send_file并自动设置MIME
        return send_file(
            file_path,
            mimetype=detect_mime(file_path),
            as_attachment=False,  # 直接显示而非下载
            conditional=True  # 支持条件请求（缓存相关）
        )

    except Exception as e:
        return json_response('fail', f'获取图片失败: {str(e)}', code=500)


@ask_for_leave_controller.route('/<int:application_id>', methods=['PATCH'], endpoint='update_leave_application')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
@record_history
def update_leave_application(application_id):
    """
    更新请假申请（含审批、撤回批准）
    """
    data = get_data()
    if not data:
        return json_response('fail', '未提供请求数据', code=422)

    asl_values = [item.value for item in AskForLeaveEnum]
    status_values = ["已批准", "已拒绝"]

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

        if not application or application.status == StatusEnum.CANCELLED:
            return json_response('fail', '请假申请不存在', code=404)

        if data['status'] == '已拒绝' and data.get('reject_reason', '').strip() == '':
            return json_response('fail', '拒绝批准请填写理由', code=422)
        application.status = StatusEnum(data['status'])

        if data.get('reject_reason', None) is not None:
            application.reject_reason = data['reject_reason']

        if data.get('asl_type', None) is not None:
            application.asl_type = AskForLeaveEnum(data['asl_type'])
        session.commit()
        application = application.to_dict()
        Message.add_message(
            user_id=application['check_in_user']['user']['id'],
            msg_title=f"请假审批通知（{application['status']}）",
            msg_text=f""
                     f"<h3>请假ID: {application['id']}</h3>"
                     f"<p>值班: {application['check_in_user']['schedule']['schedule_name']}-{application['check_in_user']['schedule']['schedule_type']}-{application['check_in_user']['schedule']['schedule_start_time']} </p> "
                     f"<p>签到: {application['check_in_user']['check_in']['name']} </p>"
                     f'<p>请假申请<span style="color: red;">{application["status"]}</span></p>'
                     f"<p>审批意见：{application['reject_reason']}</p>"
                     f"<p>如果存在疑问，请联系管理员。</p>"
            ,
            msg_type='PRIVATE'
        )

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


@ask_for_leave_controller.route('/<int:application_id>', methods=['GET'], endpoint='get_leave_application_info')
@position_required([PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER])
@record_history
def get_leave_application_info(application_id):
    """
    获取当前请假申请具体信息
    """
    try:
        asl_application = AskForLeaveApplication.get_asl_by_id(application_id)
        if not asl_application:
            return json_response('fail', "未找到请假", code=404)
        return json_response('success', '获取成功', data=asl_application)

    except Exception as e:
        return json_response('fail', f'查询失败：{str(e)}', code=500)


@ask_for_leave_controller.route('/<int:check_in_user_id>', methods=['POST'], endpoint='create_leave_application')
@position_required([PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER])
@record_history
def create_leave_application(check_in_user_id):
    """
    为当前用户的某个签到创建请假申请
    - 事假：可以不上传图片
    - 其他类型：必须上传图片
    """

    if not request.form:
        return json_response('fail', '未提供表单数据', code=422)

    # 验证请假类型
    asl_values = [item.value for item in AskForLeaveEnum]
    if 'asl_type' not in request.form or request.form['asl_type'] not in asl_values:
        return json_response('fail', '无效的请假类型', code=422)

    is_valid, errors = validate_schema({'asl_reason': {'required': False}}, {'asl_reason': request.form['asl_reason']})
    if not is_valid:
        return json_response('fail', '请填写合法请假原因', code=422)

    # 获取上传的文件（但不立即处理）
    if storage == 'local':
        files = request.files.getlist('image_url')
        image_urls = files
    else:
        files = request.form.getlist('image_url')
        image_urls = files

    if storage == 'local' and files and any(files):
        result, reason = size_check(files)
        if not result:
            return json_response('fail', reason, code=422)
        # 实际保存图片
        image_urls = validate_and_save_images(files, check_in_user_id)
        if not image_urls:
            return json_response('fail', '图片上传失败，请重新上传有效的证明图片', code=422)
    elif storage == 'microsoft' and files and any(files):
        if not isinstance(files, list) or not all(
                isinstance(url, str) and url.startswith(cloudflare_worker_baseurl) for url in files):
            return json_response("fail", "图片 URL 格式非法", code=422)

    # 检查签到记录
    check_in_user = CheckInUser.get_by_id(check_in_user_id)
    if not check_in_user:
        return json_response('fail', "未找到签到记录", code=404)

    # 检查是否已有待审核或已通过的请假
    session = Session()
    existing_asl = session.query(AskForLeaveApplication).filter(
        AskForLeaveApplication.check_in_user_id == check_in_user_id,
        AskForLeaveApplication.status.in_([StatusEnum.ACCEPTED, StatusEnum.PENDING])
    ).first()
    if existing_asl:
        return json_response('fail', '该签到已存在待审核或已批准的请假申请', code=400)
    session.close()

    # 创建请假申请
    status, asl, code = AskForLeaveApplication.create_asl(
        check_in_user_id=check_in_user_id,
        asl_type=request.form['asl_type'],
        asl_reason=request.form['asl_reason'],
        status="已批准",
        image_url=json.dumps(image_urls) if image_urls else None
    )

    if not status:
        # 如果创建失败，删除已上传的图片
        if image_urls:
            for path in image_urls:
                try:
                    os.remove(path)
                except:
                    pass
        return json_response('fail', asl, code=code)

    Message.add_message(
        user_id=asl['check_in_user']['user']['id'],
        msg_title="管理员帮助你补充请假",
        msg_text=f""
                 f"<h3>请假ID: {asl['id']}</h3>"
                 f"<p>值班: {asl['check_in_user']['schedule']['schedule_name']}-{asl['check_in_user']['schedule']['schedule_type']}-{asl['check_in_user']['schedule']['schedule_start_time']} </p> "
                 f"<p>签到: {asl['check_in_user']['check_in']['name']} </p>"
                 f"<p>如果存在疑问，请联系管理员。</p>",
        msg_type='PRIVATE'
    )

    return json_response('success', '请假申请创建成功', data={'id': asl['id']})


@ask_for_leave_controller.route('/photo/<int:application_id>/<string:photo_name>', methods=['GET'],
                                endpoint='get_photo')
@position_required([PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER])
@record_history
def get_photo(application_id, photo_name):
    """
    获取请假申请中的特定图片（自动检测MIME类型）
    """
    try:
        # 获取请假申请
        asl_application = AskForLeaveApplication.get_asl_by_id(application_id)

        # 验证权限和图片存在性
        if (not asl_application or
                asl_application['image_url'] is None or
                photo_name not in asl_application['image_url']):
            return json_response('fail', "图片不存在", code=404)

        # 构建完整文件路径
        file_path = os.path.join(upload_folder, photo_name)

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return json_response('fail', "图片文件不存在", code=404)

        # 使用send_file并自动设置MIME
        return send_file(
            file_path,
            mimetype=detect_mime(file_path),
            as_attachment=False,  # 直接显示而非下载
            conditional=True  # 支持条件请求（缓存相关）
        )

    except Exception as e:
        return json_response('fail', f'获取图片失败: {str(e)}', code=500)


@ask_for_leave_controller.route('/cleanup-images', methods=['POST'], endpoint='cleanup_images')
@admin_required
@record_history
@auto_decrypt_if_present
def cleanup_images():
    """
    清理指定日期的图片并更新数据库记录
    """
    data = get_data()
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
            func.date(AskForLeaveApplication.created_at) <= target_date,
            AskForLeaveApplication.image_url.isnot(None)
        ).all()

        deleted_count = 0
        for record in records:
            try:
                image_urls = json.loads(record.image_url) if record.image_url else []
                if storage == 'local':
                    for path in image_urls:
                        if os.path.exists(os.path.join(upload_folder, path)):
                            os.remove(os.path.join(upload_folder, path))
                else:
                    for url in image_urls:
                        if url.startswith("https://"):
                            permanentDelete(url.split("/")[-1])
                        else:
                            continue
                record.image_url = None
                deleted_count += 1
            except Exception as e:
                print(e)
                continue
        session.commit()
        return json_response('success', f'成功清理{deleted_count}条记录的图片')

    except Exception as e:
        session.rollback()
        return json_response('fail', f'清理失败: {str(e)}', code=500)
    finally:
        session.close()
