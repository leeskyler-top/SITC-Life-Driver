from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from Handler.Handler import position_required
from Model.AskForLeaveApplication import AskForLeaveApplication, StatusEnum
from Model.User import User
from Model.User import PositionEnum
from .globals import json_response, Session, validate_schema
from sqlalchemy.exc import IntegrityError

ask_for_leave_controller = Blueprint('ask_for_leave_controller', __name__)


@ask_for_leave_controller.route('', methods=['POST'], endpoint='create_leave_application')
@jwt_required()
def create_leave_application():
    """
    创建请假申请
    """
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return json_response('fail', '未提供请求数据', code=422)

    schema = {
        'asl_type': {
            'type': 'string',
            'required': True
        },
        'asl_reason': {
            'type': 'string',
            'required': True
        }
    }

    result, reason = validate_schema(schema, data)
    if not result:
        return json_response('fail', f"请求数据格式错误: {reason}", code=422)

    try:
        leave_application = AskForLeaveApplication(
            check_in_user_id=user_id,
            asl_type=data['asl_type'],
            asl_reason=data['asl_reason'],
            status='PENDING'  # 初始状态为待审核
        )

        session = Session()
        session.add(leave_application)
        session.commit()
        return json_response('success', '请假申请创建成功', data={'id': leave_application.id})

    except IntegrityError:
        return json_response('fail', '请假申请已存在', code=400)
    except Exception as e:
        session.rollback()
        return json_response('fail', f'处理请求时出错：{str(e)}', code=500)
    finally:
        session.close()


@ask_for_leave_controller.route('', methods=['GET'], endpoint='get_leave_applications')
@jwt_required()
def get_leave_applications():
    """
    获取当前用户的所有请假申请
    """
    user_id = get_jwt_identity()
    session = Session()
    try:
        applications = session.query(AskForLeaveApplication).filter_by(check_in_user_id=user_id).all()

        result = [app.to_dict() for app in applications]
        return json_response('success', '获取成功', data=result)

    except Exception as e:
        return json_response('fail', f'查询失败：{str(e)}', code=500)
    finally:
        session.close()


@ask_for_leave_controller.route('/<int:application_id>', methods=['PUT'], endpoint='update_leave_application')
@jwt_required()
def update_leave_application(application_id):
    """
    更新请假申请
    """
    data = request.get_json()
    if not data:
        return json_response('fail', '未提供请求数据', code=422)

    schema = {
        'status': {
            'type': 'string',
            'allowed': ['PENDING', 'ACCEPTED', 'REJECTED'],
            'required': True
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

        # 仅允许管理员更新申请状态
        current_user = session.query(User).filter_by(id=get_jwt_identity()).first()
        if current_user.position not in [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER,
                                         PositionEnum.DEPARTMENT_LEADER]:
            return json_response('fail', '没有权限', code=403)

        application.status = data['status']
        if data['status'] == 'REJECTED':
            application.reject_reason = data.get('reject_reason', None)

        session.commit()
        return json_response('success', '请假申请状态已更新')

    except Exception as e:
        session.rollback()
        return json_response('fail', f'处理请求时出错：{str(e)}', code=500)
    finally:
        session.close()


@ask_for_leave_controller.route('/<int:application_id>', methods=['DELETE'], endpoint='delete_leave_application')
@jwt_required()
def delete_leave_application(application_id):
    """
    删除请假申请
    """
    session = Session()
    try:
        application = session.query(AskForLeaveApplication).filter_by(id=application_id).first()

        if not application:
            return json_response('fail', '请假申请不存在', code=404)

        session.delete(application)
        session.commit()
        return json_response('success', '请假申请已删除')

    except Exception as e:
        session.rollback()
        return json_response('fail', f'处理请求时出错：{str(e)}', code=500)
    finally:
        session.close()


@ask_for_leave_controller.route('/<int:application_id>', methods=['POST'],
                                endpoint='approve_or_reject_leave_application')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
def approve_or_reject_leave_application(application_id):
    """
    审批请假申请
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    if not data or 'status' not in data:
        return json_response('fail', '未提供状态', code=422)

    valid_statuses = [StatusEnum.ACCEPTED.value, StatusEnum.REJECTED.value]
    if data['status'] not in valid_statuses:
        return json_response('fail', '无效的状态', code=422)

    session = Session()
    try:
        application = session.query(AskForLeaveApplication).filter_by(id=application_id).first()
        if not application:
            return json_response('fail', '请假申请不存在', code=404)

        application.status = data['status']
        if data['status'] == StatusEnum.REJECTED.value:
            application.reject_reason = data.get('reject_reason', '无')

        session.commit()
        return json_response('success', '请假申请状态已更新')

    except IntegrityError:
        return json_response('fail', '审批提交失败', code=500)
    except Exception as e:
        session.rollback()
        return json_response('fail', f'处理请求时出错：{str(e)}', code=500)
    finally:
        session.close()
