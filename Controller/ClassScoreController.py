from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from Handler.Handler import record_history, position_required
from Model import Schedule, User
from Model.User import PositionEnum
from .globals import json_response, validate_schema, get_data, auto_decrypt_if_present
from Model.ClassScore import ClassScore

class_score_controller = Blueprint('class_score_controller', __name__)


def check_user_permission(schedule_id, user_id):
    """检查用户是否有权限删除或更新评分"""
    user = User.get_user_by_id(user_id)
    # 获取对应的 Schedule
    schedule = Schedule.get_schedule_by_id(schedule_id)
    if not schedule:
        return False, '相关 Schedule 不存在'

    # 查找主签到（假定每个 Schedule 只有一个主签到）
    main_check_in = next((check_in for check_in in schedule['check_ins'] if check_in['is_main_check_in'] is True), None)

    user_has_access = False

    # 检查是否有主签到，并且当前用户是否在其中
    if main_check_in:
        for check_in_user in main_check_in.check_in_users:
            if check_in_user.user_id == user_id:
                user_has_access = True
                break

    # 如果用户没有访问权限，检查用户职位是否允许删除
    if not user_has_access:
        if user['is_admin'] is True:
            return True, ''
        if user['position'] not in ['部长', '副部长', '部门负责人', '汇总负责人']:
            return False, '您没有权限进行此操作'

    return True, ''


@class_score_controller.route('', methods=['POST'], endpoint='create_or_update_class_score')
@jwt_required()
@record_history
@auto_decrypt_if_present
def create_or_update_class_score():
    data = get_data()
    schema = {
        'schedule_id': {'type': 'integer', 'required': True},
        'student_class_id': {'type': 'integer', 'required': True},
        'rule_id': {'type': 'integer', 'required': True},
        'score_value': {'type': 'float', 'required': True},
    }

    is_valid, errors = validate_schema(schema, data)
    if not is_valid:
        return json_response('fail', f"请求数据格式错误: {errors}", code=422)

    schedule_id = data['schedule_id']
    user_id = get_jwt_identity()  # 获取当前用户的 ID

    # 权限检查
    has_permission, message = check_user_permission(schedule_id, user_id)
    if not has_permission:
        return json_response('fail', message, code=403)

    # 创建或更新评分记录
    status, result, code = ClassScore.create_or_update_score(
        schedule_id=schedule_id,
        student_class_id=data['student_class_id'],
        rule_id=data['rule_id'],
        score_value=data['score_value']
    )
    return json_response(status, result, code=code)


@class_score_controller.route('/schedule/<int:schedule_id>', methods=['GET'], endpoint='get_scores_by_schedule_id')
@jwt_required()
@record_history
@auto_decrypt_if_present
def get_scores_by_schedule(schedule_id):
    schedule = Schedule.get_schedule_by_id(schedule_id)
    if not schedule:
        return json_response("fail", "值班计划未找到", code=404)
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    scores = ClassScore.get_scores_by_schedule_id(schedule_id, include_deleted)
    return json_response('success', 'Scores fetched successfully', data=scores, code=200)


@class_score_controller.route('/schedule-range', methods=['POST'], endpoint='get_scores_by_time_range')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
@record_history
@auto_decrypt_if_present
def get_scores_by_time_range():
    data = get_data()
    schema = {
        'start_time': {'type': 'string', 'required': True, 'regex': r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'},
        'end_time': {'type': 'string', 'required': True, 'regex': r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'},
        'include_deleted': {'type': 'boolean', 'default': False},
    }

    is_valid, errors = validate_schema(schema, data)
    if not is_valid:
        return json_response('fail', f"请求数据格式错误: {errors}", code=422)

    scores = ClassScore.get_scores_by_time_range(data['start_time'], data['end_time'], data['include_deleted'])
    return json_response('success', 'Scores fetched successfully', data=scores, code=200)


@class_score_controller.route('/<int:score_id>', methods=['DELETE'], endpoint='delete_class_score')
@jwt_required()
@record_history
@auto_decrypt_if_present
def delete_class_score(score_id):
    user_id = get_jwt_identity()  # 获取当前用户的 ID

    # 检查评分记录是否存在
    score = ClassScore.get_score_by_id(score_id)
    if not score:
        return json_response('fail', '评分记录不存在', code=404)

    # 权限检查
    has_permission, message = check_user_permission(score.schedule_id, user_id)
    if not has_permission:
        return json_response('fail', message, code=403)

    # 进行删除评分记录
    status, message, code = ClassScore.delete_score_by_id(score_id)
    return json_response(status, message, code=code)
