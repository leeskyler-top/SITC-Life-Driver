from io import BytesIO

import pandas as pd
from dateutil.relativedelta import relativedelta
from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from Handler.Handler import position_required, record_history
from Model import CheckIn, CheckInUser, AskForLeaveApplication
from Model.AskForLeaveApplication import StatusEnum
from Model.CheckInUser import CheckInStatusEnum
from Model.Message import Message
from Model.Schedule import Schedule
from Model.User import PositionEnum, User
from .globals import json_response, Session, validate_schema, non_empty_string
from datetime import datetime

checkin_controller = Blueprint('checkin_controller', __name__)


@checkin_controller.route('/my', methods=['GET'], endpoint='list_my_checkins')
@jwt_required()
@record_history
def list_my_checkins():
    session = Session()
    try:
        user_id = get_jwt_identity()
        checkin_users = session.query(CheckInUser).filter_by(user_id=user_id).all()
        checkin_users = [ciu.to_dict(include_schedule=True, include_asl=True) for ciu in checkin_users]
        return json_response('success', '获取完成', checkin_users, code=200)
    except Exception as e:
        return json_response('fail', f'统计失败: {str(e)}', code=500)
    finally:
        session.close()


@checkin_controller.route('/create/<int:schedule_id>', methods=['POST'], endpoint='create_checkin')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
@record_history
def create_checkin(schedule_id):
    session = Session()
    try:
        schedule = session.query(Schedule).filter_by(id=schedule_id).first()
        if not schedule:
            return json_response('fail', '指定的排班不存在', code=404)

        data = request.get_json()
        if not data:
            return json_response('fail', '未提供请求数据', code=422)

        schema = {
            'check_in_start_time': {
                'type': 'string',
                'required': True,
                'regex': r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
            },
            'check_in_end_time': {
                'type': 'string',
                'required': True,
                'regex': r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
            },
            'need_check_schedule_time': {
                'type': 'boolean',
                'required': True,
            },
            'name': {
                'type': 'string',
                'required': True,
                'check_with': non_empty_string
            },
            'check_in_users': {
                'type': 'list',
                "schema": {
                    "type": "integer",
                },
                'required': True
            }
        }

        result, reason = validate_schema(schema, data)
        if not result:
            return json_response('fail', f"请求数据格式错误: {reason}", code=422)

        try:
            start_time = datetime.strptime(data['check_in_start_time'], "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(data['check_in_end_time'], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return json_response('fail', '时间格式应为 %Y-%m-%d %H:%M:%S', code=422)

        if start_time >= end_time:
            return json_response('fail', '开始时间必须早于结束时间', code=422)
        if start_time < datetime.now():
            return json_response('fail', '开始时间不能早于当前时间', code=422)

        status, result, code = CheckIn.create_check_in_in_db(
            schedule_id=schedule_id,
            name=data['name'].strip(),
            check_in_start_time=data['check_in_start_time'],
            check_in_end_time=data['check_in_end_time'],
            need_check_schedule_time=data['need_check_schedule_time'],
            check_in_users=data['check_in_users'],
            is_main_check_in=False
        )
        if status:
            return json_response('success', "签到创建成功", data=result, code=code)
        return json_response('fail', result, code=code)
    except Exception as e:
        session.rollback()
        return json_response('fail', f'处理请求时出错：{str(e)}', code=500)
    finally:
        session.close()


@checkin_controller.route('/assign', methods=['POST'], endpoint='assign_users_and_checkins')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
@record_history
def assign_users_and_checkins():
    session = Session()
    try:
        data = request.get_json()
        if not data:
            return json_response('fail', '未提供请求数据', code=422)

        schema = {
            'checkin_ids': {
                'type': 'list',
                'schema': {'type': 'integer'},
                'required': True
            },
            'user_ids': {
                'type': 'list',
                'schema': {'type': 'integer'},
                'required': True
            }
        }

        result, reason = validate_schema(schema, data)
        if not result:
            return json_response('fail', f"请求数据格式错误: {reason}", code=422)

        checkin_ids = data['checkin_ids']
        user_ids = data['user_ids']

        # 验证所有 checkin 是否存在且未开始
        checkins = session.query(CheckIn).filter(CheckIn.id.in_(checkin_ids)).all()
        if len(checkins) != len(checkin_ids):
            return json_response('fail', '部分签到记录不存在', code=422)

        now = datetime.now()
        for checkin in checkins:
            if now >= checkin.check_in_start_time:
                return json_response('fail', f'签到 {checkin.id} 已开始，无法分配用户', code=422)

        # 验证所有用户是否存在
        users = session.query(User).filter(User.id.in_(user_ids)).all()
        if len(users) != len(user_ids):
            return json_response('fail', '部分用户不存在', code=422)

        # 用于存储成功和失败的用户分配信息
        response_message = {
            'success': {},
            'failed': {}
        }

        # 分配用户
        for checkin in checkins:
            result, reason, code = checkin.sync_users(checkin.id, user_ids)
            if result:
                response_message['success'][checkin.id] = user_ids  # 映射成功的用户
            else:
                response_message['failed'][checkin.id] = reason  # 失败的用户及原因

        session.commit()
        for user in users:
            Message.add_message(
                user_id=user.id,
                msg_title="新排班(签到)通知",
                msg_text=f"<h3>请查看新的排班:</h3>"
                         f"<ul>{''.join(f'<li>{checkin.name}</li>' for checkin in checkins)}</ul>"
                         f"<p>如有异议联系管理员。</p>",
                msg_type='PRIVATE'
            )
        return json_response('success',
                             f"成功数据: {response_message['success']}, 出错数据: {response_message['failed']}",
                             code=200)

    except Exception as e:
        session.rollback()
        return json_response('fail', f'处理请求时出错：{str(e)}', code=500)
    finally:
        session.close()


@checkin_controller.route('/assign/<int:check_in_id>', methods=['POST'], endpoint='assign_users_by_check_in_id')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
@record_history
def assign_users_by_check_in_id(check_in_id):
    session = Session()
    try:
        data = request.get_json()
        if not data:
            return json_response('fail', '未提供请求数据', code=422)

        schema = {
            'user_ids': {
                'type': 'list',
                'schema': {'type': 'integer'},
                'required': True
            }
        }

        result, reason = validate_schema(schema, data)
        if not result:
            return json_response('fail', f"请求数据格式错误: {reason}", code=422)

        user_ids = data['user_ids']

        checkin = session.query(CheckIn).filter_by(id=check_in_id).first()
        if not checkin:
            return json_response('fail', '指定的签到记录不存在', code=404)

        now = datetime.now()
        if now >= checkin.check_in_start_time:
            return json_response('fail', '签到已开始，无法分配用户', code=422)

        users = session.query(User).filter(User.id.in_(user_ids)).all()
        existing_user_ids = {user.id for user in users}
        not_found_user_ids = set(user_ids) - existing_user_ids

        if not_found_user_ids:
            return json_response('fail', f'部分用户ID不存在: {list(not_found_user_ids)}', code=422)

        success_users = []
        failed_users = []
        result, reason, code = CheckIn.sync_users(check_in_id, user_ids)  # 假设 sync_users 也能处理列表

        if not result:
            return json_response("fail", reason, code=code)

        # 发送通知
        for user in users:
            Message.add_message(
                user_id=user.id,
                msg_title="新排班(签到)通知（单独排班）",
                msg_text=f"请查看新的排班，名称为{checkin.name}，如有异议联系管理员。",
                msg_type='PRIVATE'
            )

        # 构建返回的内容
        response_message = {
            'success': success_users,
            'failed': failed_users,
        }

        return json_response('success',
                             f"成功数据：{response_message['success']}, 出错数据: {response_message['failed']}")

    except Exception as e:
        session.rollback()
        return json_response('fail', f'处理请求时出错：{str(e)}', code=500)
    finally:
        session.close()


@checkin_controller.route('/checkin/<int:check_in_id>', methods=['GET'], endpoint='checkin')
@jwt_required()
@record_history
def checkin(check_in_id):
    session = Session()
    try:
        user_id = get_jwt_identity()
        checkin_user = session.query(CheckInUser).filter_by(check_in_id=check_in_id, user_id=user_id).first()
        if not checkin_user:
            return json_response('fail', '未找到对应的签到记录', code=404)

        if checkin_user.check_in_time:
            return json_response('fail', '已签到，无法重复签到', code=422)

        now = datetime.now()
        checkin = session.query(CheckIn).filter_by(id=check_in_id).first()
        if not checkin:
            return json_response('fail', '签到记录不存在', code=404)

        if now > checkin.check_in_end_time:
            return json_response('fail', '签到已结束，无法签到', code=422)

        checkin_user.check_in_time = now
        session.commit()
        return json_response('success', '签到成功')
    except Exception as e:
        session.rollback()
        return json_response('fail', f'处理请求时出错：{str(e)}', code=500)
    finally:
        session.close()


@checkin_controller.route('/cancel/<int:check_in_user_id>', methods=['GET'], endpoint='cancel')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
@record_history
def cancel(check_in_user_id):
    session = Session()
    try:
        checkin_user = session.query(CheckInUser).filter_by(id=check_in_user_id).first()
        if not checkin_user:
            return json_response('fail', '签到用户记录不存在', code=404)

        if not checkin_user.check_in_time:
            return json_response('fail', '该用户尚未签到，无法取消', code=422)

        checkin_user.check_in_time = None

        # 获取相关信息
        user = session.query(User).filter_by(id=checkin_user.user_id).first()
        checkin = session.query(CheckIn).filter_by(id=checkin_user.check_in_id).first()
        schedule = session.query(Schedule).filter_by(id=checkin.schedule_id).first()

        message = f"管理员对你在 {schedule.schedule_name}-{schedule.schedule_start_time.strftime('%Y-%m-%d %H:%M:%S')}-{schedule.schedule_type.value} 的 {checkin.name} 签到产生了质疑并取消了签到，如果对本次处理有异议，请联系管理员。"
        Message.add_message(
            user_id=user.id,
            msg_title="签到被驳回",
            msg_text=message,
            msg_type='PRIVATE'
        )
        session.commit()
        return json_response('success', '签到已取消', checkin_user.to_dict(), code=200)
    except Exception as e:
        session.rollback()
        return json_response('fail', f'处理请求时出错：{str(e)}', code=500)
    finally:
        session.close()


@checkin_controller.route('/change_record/<int:check_in_user_id>', methods=['POST'], endpoint='change_record')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
@record_history
def change_record(check_in_user_id):
    session = Session()
    try:
        data = request.get_json()
        if not data:
            return json_response('fail', '未提供请求数据', code=422)

        schema = {
            'check_in_time': {
                'type': 'string',
                'required': True,
                'regex': r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
            }
        }
        result, reason = validate_schema(schema, data)
        if not result:
            return json_response('fail', f'请求数据格式错误: {reason}', code=422)

        try:
            new_time = datetime.strptime(data['check_in_time'], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return json_response('fail', '时间格式应为 %Y-%m-%d %H:%M:%S', code=422)

        checkin_user = session.query(CheckInUser).filter_by(id=check_in_user_id).first()
        if not checkin_user:
            return json_response('fail', '签到用户记录不存在', code=404)

        checkin = session.query(CheckIn).filter_by(id=checkin_user.check_in_id).first()
        if not checkin:
            return json_response('fail', '签到记录不存在', code=404)

        if new_time < checkin.check_in_start_time or new_time > checkin.check_in_end_time:
            return json_response('fail', '签到时间必须在签到时段内', code=422)

        checkin_user.check_in_time = new_time
        session.commit()

        # 获取相关信息
        user = session.query(User).filter_by(id=checkin_user.user_id).first()
        schedule = session.query(Schedule).filter_by(id=checkin.schedule_id).first()
        message = f"管理员对你在 {schedule.schedule_name}-{schedule.schedule_start_time.strftime('%Y-%m-%d %H:%M:%S')}-{schedule.schedule_type.value} 的 {checkin.name} 签到时间进行了更改，如有疑问请联系管理员。"
        Message.add_message(
            user_id=user.id,
            msg_title="个人签到状态变更",
            msg_text=message,
            msg_type='PRIVATE'
        )
        return json_response('success', '签到时间修改成功', checkin_user.to_dict(), code=200)
    except Exception as e:
        session.rollback()
        return json_response('fail', f'处理请求时出错：{str(e)}', code=500)
    finally:
        session.close()


@checkin_controller.route('', methods=['GET'], endpoint='list_checkins')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
@record_history
def list_checkins():
    session = Session()
    try:
        checkins = CheckIn.get_all_check_ins()
        return json_response('success', '查询成功', data=checkins)
    except Exception as e:
        return json_response('fail', f'查询失败：{str(e)}', code=500)
    finally:
        session.close()


@checkin_controller.route('/checkinuser', methods=['POST'], endpoint='list_checkin_users')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
@record_history
def list_checkin_users():
    data = request.get_json()
    if not data:
        return json_response('fail', "未传递任何参数", code=422)
    schema = {
        'start_time': {'type': 'string', 'required': True,
                       'regex': r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'},
        'end_time': {'type': 'string', 'required': True,
                     'regex': r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'},
        'type': {'type': 'string', 'required': True, 'allowed': ['checkin_time', 'schedule_time']},
        'export': {'type': 'boolean', 'required': False, 'default': False}
    }
    result, reason = validate_schema(schema, data)
    if not result:
        return json_response('fail', f'请求参数错误: {reason}', code=422)

    checkinusers = CheckInUser.get_all_by_date_range(start=data['start_time'],
                                                     end=data['end_time'], type=data['type'])
    checkinusers = [ciu.to_dict(include_schedule=True, include_check_in=True, include_asl=True) for ciu in checkinusers]

    def get_nested_value(record, keys):
        """根据dataIndex路径获取嵌套值"""
        if isinstance(keys, str):
            return record.get(keys, '')
        value = record
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, '')
            else:
                return ''
        return value

    if data.get('export', False):
        # If export flag is True, return as Excel file
        # 定义与前端一致的列映射
        COLUMNS_MAPPING = [
            {'title': '签到流水ID', 'dataIndex': 'id'},
            {'title': '学籍号', 'dataIndex': ['user', 'studentId']},
            {'title': '姓名', 'dataIndex': ['user', 'name']},
            {'title': '计划ID', 'dataIndex': ['schedule', 'id']},
            {'title': '签到ID', 'dataIndex': ['check_in', 'id']},
            {'title': '计划名称', 'dataIndex': ['schedule', 'schedule_name']},
            {'title': '计划开始时间', 'dataIndex': ['schedule', 'schedule_start_time']},
            {'title': '计划类型', 'dataIndex': ['schedule', 'schedule_type']},
            {'title': '签到名称', 'dataIndex': ['check_in', 'name']},
            {'title': '签到开始时间', 'dataIndex': ['check_in', 'check_in_start_time']},
            {'title': '签到结束时间', 'dataIndex': ['check_in', 'check_in_end_time']},
            {'title': '主签到', 'dataIndex': ['check_in', 'is_main_check_in']},
            {'title': '检查迟到', 'dataIndex': ['check_in', 'need_check_schedule_time']},
            {'title': '状态', 'dataIndex': 'status'}
        ]

        # 准备导出数据
        export_data = []
        for ciu in checkinusers:
            row = {}
            for col in COLUMNS_MAPPING:
                value = get_nested_value(ciu, col['dataIndex'])
                row[col['title']] = value
            export_data.append(row)

        # 创建DataFrame（确保列顺序与前端一致）
        df = pd.DataFrame(export_data, columns=[col['title'] for col in COLUMNS_MAPPING])

        # 创建内存文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='签到记录')

        output.seek(0)

        # 创建文件名
        start = data['start_time'][:10].replace('-', '')
        end = data['end_time'][:10].replace('-', '')
        filename = f"签到记录_{start}_至_{end}.xlsx"

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    return json_response('success', '已列出指定日期内所有签到流水', data=checkinusers, code=200)


@checkin_controller.route('/<int:check_in_id>', methods=['PATCH'], endpoint='update_checkin')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
@record_history
def update_checkin(check_in_id):
    session = Session()
    try:
        data = request.get_json()
        if not data:
            return json_response('fail', "未传递任何参数", code=422)
        schema = {
            'name': {'type': 'string', 'required': False},
            'check_in_start_time': {'type': 'string', 'required': False,
                                    'regex': r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'},
            'check_in_end_time': {'type': 'string', 'required': False,
                                  'regex': r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'},
            'need_check_schedule_time': {'type': 'boolean', 'required': False, 'allowed': [True, False]},
            # 0 为普通用户，1 为管理员
        }
        result, reason = validate_schema(schema, data)
        if not result:
            return json_response('fail', f'请求参数错误: {reason}', code=422)

        checkin = session.query(CheckIn).filter_by(id=check_in_id).first()
        if not checkin:
            return json_response('fail', '签到记录不存在', code=404)

        schedule = session.query(Schedule).filter_by(id=checkin.schedule_id).first()
        if not schedule:
            return json_response('fail', '对应的值班计划不存在', code=404)

        if 'check_in_start_time' in data:
            try:
                new_start = datetime.strptime(data['check_in_start_time'], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return json_response('fail', '开始时间格式错误', code=422)
            checkin.check_in_start_time = new_start

        if 'check_in_end_time' in data:
            try:
                new_end = datetime.strptime(data['check_in_end_time'], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return json_response('fail', '结束时间格式错误', code=422)
            checkin.check_in_end_time = new_end

        if 'name' in data:
            checkin.name = data['name']

        if 'need_check_schedule_time' in data:
            checkin.need_check_schedule_time = data['need_check_schedule_time']

        session.commit()
        return json_response('success', '签到信息修改成功', checkin.to_dict(), code=200)
    except Exception as e:
        session.rollback()
        return json_response('fail', f'修改失败：{str(e)}', code=500)
    finally:
        session.close()


@checkin_controller.route('/<int:check_in_id>', methods=['DELETE'], endpoint='delete_checkin')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
@record_history
def delete_checkin(check_in_id):
    session = Session()
    try:
        checkin = session.query(CheckIn).filter_by(id=check_in_id).first()
        if not checkin:
            return json_response('fail', '签到记录不存在', code=404)

        if checkin.is_main_check_in:
            return json_response('fail', '主签到不可单独删除', code=403)

        # 同时删除关联的签到用户记录
        session.query(CheckInUser).filter_by(check_in_id=check_in_id).delete()
        session.delete(checkin)
        session.commit()
        return json_response('success', '签到删除成功')
    except Exception as e:
        session.rollback()
        return json_response('fail', f'删除失败：{str(e)}', code=500)
    finally:
        session.close()


@checkin_controller.route('/attendance/stats', methods=['POST'], endpoint='attendance_stats')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
@record_history
def attendance_stats():
    data = request.get_json()
    if not data:
        return json_response('fail', '未提供请求数据', code=422)

    schema = {
        'start_time': {
            'type': 'string',
            'required': True,
            'regex': r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
        },
        'end_time': {
            'type': 'string',
            'required': True,
            'regex': r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
        },
    }

    result, reason = validate_schema(schema, data)
    if not result:
        return json_response('fail', f"请求数据格式错误: {reason}", code=422)

    session = Session()
    try:
        # 解析请求参数
        start_time_str = data['start_time']
        end_time_str = data['end_time']

        if not start_time_str or not end_time_str:
            return json_response('fail', '缺少时间参数', code=422)

        try:
            start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
            end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return json_response('fail', '时间格式应为 %Y-%m-%d %H:%M:%S', code=422)

        if start_time >= end_time:
            return json_response('fail', '开始时间必须早于结束时间', code=422)

        # 获取活跃用户
        active_users = User.query_active(session)

        # 统计部门的数据（例如：所有用户的出勤率等）
        department_stats = {
            'total_sick_leaves': 0,
            'total_ordinary_leaves': 0,
            'total_attendance': 0,
            'total_absenteeism': 0,
            'total_late': 0,
            'total_schedule': 0,
        }

        attendance_stats_dict = {
            'user_data': [],
            'department_data': department_stats
        }

        # 统计每个用户的数据
        for user in active_users:
            user_data = {
                'studentId': user.studentId,
                'department': user.department.value,
                'classname': user.classname,
                'name': user.name,
                'approved_sick_leaves': 0,
                'approved_competition_leaves': 0,
                'approved_ordinary_leaves': 0,
                'attendance_count': 0,
                'absence_count': 0,
                'late_count': 0,
                'schedule_count': 0,
                'attendance_rate': 0,
                'absence_rate': 0,
            }

            # 获取该用户的所有 CheckInUser 记录
            check_in_users = session.query(CheckInUser).join(CheckIn).filter(
                CheckInUser.user_id == user.id,
                CheckIn.check_in_start_time >= start_time,
                CheckIn.check_in_end_time <= end_time,
                CheckIn.is_main_check_in == True,
            ).all()

            for ciu in check_in_users:
                # 只统计“未开始”状态的记录不算在出勤统计中
                if ciu.get_status() == CheckInStatusEnum.NOT_STARTED.value:
                    continue

                user_data['schedule_count'] += 1  # 应出勤次数

                if ciu.check_in_time:
                    user_data['attendance_count'] += 1  # 实际出勤次数
                    # 判断是否迟到
                    if ciu.check_in_time > ciu.check_in.check_in_start_time:
                        user_data['late_count'] += 1  # 迟到

            # 统计请假情况
            leave_applications = session.query(AskForLeaveApplication).filter(
                AskForLeaveApplication.check_in_user_id.in_([ciu.id for ciu in check_in_users]),  # 根据 CheckInUser 的 ID
                AskForLeaveApplication.status == StatusEnum.ACCEPTED,
                AskForLeaveApplication.created_at.between(start_time, end_time)
            ).all()
            for application in leave_applications:
                if application.asl_type.value == '病假':
                    user_data['approved_sick_leaves'] += 1
                elif application.asl_type.value == '事假':
                    user_data['approved_ordinary_leaves'] += 1
                else:  # 排除赛事、公务假
                    continue  # 不计入

            user_data['absence_count'] = user_data['schedule_count'] - user_data['attendance_count']  # 缺勤次数
            department_stats['total_absenteeism'] += user_data['absence_count']

            # 计算出勤率
            if user_data['schedule_count'] > 0:
                user_data['attendance_rate'] = round(user_data['attendance_count'] / user_data['schedule_count'], 2)
                user_data['absence_rate'] = round(user_data['absence_count'] / user_data['schedule_count'], 2)
            else:
                user_data['attendance_rate'] = user_data['absence_rate'] = 0

            attendance_stats_dict['user_data'].append(user_data)

        # 统计每个用户的数据
        for user in active_users:
            # 获取该用户的所有 CheckInUser 记录
            check_in_users = session.query(CheckInUser).join(CheckIn).filter(
                CheckInUser.user_id == user.id,
                CheckIn.check_in_start_time >= start_time,
                CheckIn.check_in_end_time <= end_time,
                CheckIn.is_main_check_in == True,
            ).all()

            for ciu in check_in_users:
                # 只统计“未开始”状态的记录不算在出勤统计中
                if ciu.get_status() == CheckInStatusEnum.NOT_STARTED.value:
                    continue

                department_stats['total_schedule'] += 1  # 应出勤次数

                if ciu.check_in_time:
                    department_stats['total_attendance'] += 1  # 实际出勤次数
                    # 判断是否迟到
                    if ciu.check_in_time > ciu.check_in.check_in_start_time:
                        department_stats['total_late'] += 1  # 迟到

            # 统计请假情况
            leave_applications = session.query(AskForLeaveApplication).filter(
                AskForLeaveApplication.check_in_user_id.in_([ciu.id for ciu in check_in_users]),
                AskForLeaveApplication.status == StatusEnum.ACCEPTED,
                AskForLeaveApplication.created_at.between(start_time, end_time)
            ).all()

            for application in leave_applications:
                if application.asl_type.value == '病假':
                    department_stats['total_sick_leaves'] += 1
                elif application.asl_type.value == '事假':
                    department_stats['total_ordinary_leaves'] += 1
                else:  # 排除赛事
                    continue  # 不计入

        # 计算出勤率、缺勤率和迟到率
        if department_stats['total_schedule'] > 0:
            department_stats['attendance_rate'] = round(
                department_stats['total_attendance'] / department_stats['total_schedule'], 2)
            department_stats['absenteeism_rate'] = (
                round(department_stats['total_absenteeism'] / department_stats['total_schedule'], 2)) if \
                department_stats[
                    'total_schedule'] > 0 else 0
            department_stats['late_rate'] = (
                round(department_stats['total_late'] / department_stats['total_schedule'], 2)) if \
                department_stats['total_schedule'] > 0 else 0
        else:
            department_stats['attendance_rate'] = 0
            department_stats['absenteeism_rate'] = 0
            department_stats['late_rate'] = 0
        attendance_stats_dict['department_data'] = department_stats

        monthly_leave_stats = []
        current_month = start_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        while current_month <= end_time:
            next_month = current_month + relativedelta(months=1)

            # Query leave applications for this month
            leave_applications = session.query(AskForLeaveApplication).filter(
                AskForLeaveApplication.status == StatusEnum.ACCEPTED,
                AskForLeaveApplication.created_at >= current_month,
                AskForLeaveApplication.created_at < next_month
            ).all()

            sick_leaves = 0
            ordinary_leaves = 0

            for application in leave_applications:
                if application.asl_type.value == '病假':
                    sick_leaves += 1
                elif application.asl_type.value == '事假':
                    ordinary_leaves += 1

            monthly_leave_stats.append({
                'month': current_month.strftime('%Y-%m'),
                'sick_leaves': sick_leaves,
                'ordinary_leaves': ordinary_leaves
            })

            current_month = next_month

        attendance_stats_dict['monthly_leave_stats'] = monthly_leave_stats

        return json_response('success', '统计数据获取成功', data=attendance_stats_dict)
    except Exception as e:
        return json_response('fail', f'处理请求时出错：{str(e)}', code=500)
    finally:
        session.close()


@checkin_controller.route('/export/<int:check_in_id>', methods=['POST'], endpoint='export_check_in_by_id')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
@record_history
def export_check_in_by_id(check_in_id):
    """根据签到ID导出签到信息（POST带export参数返回Excel）"""
    data = request.get_json() or {}
    export = data.get('export', False)

    check_in = CheckIn.get_check_in_by_id(check_in_id)
    if not check_in:
        return json_response('fail', '签到记录不存在', code=404)

    if not export:
        return json_response('success', '获取签到记录成功', data=check_in, code=200)

    # 使用您提供的列映射
    COLUMNS_MAPPING = [
        {'title': '签到流水ID', 'dataIndex': ['check_in_user', 'id']},
        {'title': '学籍号', 'dataIndex': ['check_in_user', 'user', 'studentId']},
        {'title': '姓名', 'dataIndex': ['check_in_user', 'user', 'name']},
        {'title': '计划ID', 'dataIndex': ['schedule', 'id']},
        {'title': '签到ID', 'dataIndex': 'id'},
        {'title': '计划名称', 'dataIndex': ['schedule', 'schedule_name']},
        {'title': '计划开始时间', 'dataIndex': ['schedule', 'schedule_start_time']},
        {'title': '计划类型', 'dataIndex': ['schedule', 'schedule_type']},
        {'title': '签到名称', 'dataIndex': 'name'},
        {'title': '签到开始时间', 'dataIndex': 'check_in_start_time'},
        {'title': '签到结束时间', 'dataIndex': 'check_in_end_time'},
        {'title': '主签到', 'dataIndex': 'is_main_check_in'},
        {'title': '检查迟到', 'dataIndex': 'need_check_schedule_time'},
        {'title': '状态', 'dataIndex': ['check_in_user', 'status']}
    ]

    def get_nested_value(record, keys):
        """处理多级嵌套字段"""
        if isinstance(keys, str):
            return record.get(keys, '')
        value = record
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, '')
            else:
                return ''
        return value

    # 准备导出数据（平铺签到用户和签到信息）
    export_data = []
    for check_in_user in check_in.get('check_in_users', []):
        row = {}
        # 合并签到基础信息和用户信息
        merged_data = {**check_in, 'check_in_user': check_in_user}

        for col in COLUMNS_MAPPING:
            value = get_nested_value(merged_data, col['dataIndex'])
            # 特殊类型转换
            if isinstance(value, bool):
                value = '是' if value else '否'
            row[col['title']] = value
        export_data.append(row)

    # 创建DataFrame
    df = pd.DataFrame(export_data, columns=[col['title'] for col in COLUMNS_MAPPING])

    # 生成Excel文件
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='签到详情')

        # 添加签到概要信息到第二个sheet
        summary_data = {
            '字段': ['签到ID', '签到名称', '签到开始时间', '签到结束时间',
                     '是否主签到', '需要检查迟到', '计划名称', '计划类型'],
            '值': [
                check_in.get('id', ''),
                check_in.get('name', ''),
                check_in.get('check_in_start_time', ''),
                check_in.get('check_in_end_time', ''),
                '是' if check_in.get('is_main_check_in', False) else '否',
                '是' if check_in.get('need_check_schedule_time', False) else '否',
                check_in.get('schedule', {}).get('schedule_name', ''),
                check_in.get('schedule', {}).get('schedule_type', '')
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, index=False, sheet_name='签到概要')

    output.seek(0)

    # 生成文件名
    filename = f"签到详情_{check_in_id}_{check_in.get('name', '')}.xlsx".replace(':', '-')

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


@checkin_controller.route('/checkinuser/user/<int:user_id>', methods=['POST'], endpoint='list_checkin_users_by_user_id')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
@record_history
def list_checkin_users_by_user_id(user_id):
    data = request.get_json()
    if not data:
        return json_response('fail', "未传递任何参数", code=422)
    schema = {
        'start_time': {'type': 'string', 'required': True,
                       'regex': r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'},
        'end_time': {'type': 'string', 'required': True,
                     'regex': r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'},
        'type': {'type': 'string', 'required': True, 'allowed': ['checkin_time', 'schedule_time']},
        'export': {'type': 'boolean', 'required': False, 'default': False}
    }
    result, reason = validate_schema(schema, data)
    if not result:
        return json_response('fail', f'请求参数错误: {reason}', code=422)

    checkinusers = CheckInUser.get_all_by_user_and_date_range(user_id=user_id, start=data['start_time'],
                                                              end=data['end_time'], type=data['type'])
    checkinusers = [ciu.to_dict(include_schedule=True, include_check_in=True, include_asl=True) for ciu in checkinusers]

    def get_nested_value(record, keys):
        """根据dataIndex路径获取嵌套值"""
        if isinstance(keys, str):
            return record.get(keys, '')
        value = record
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, '')
            else:
                return ''
        return value

    if data.get('export', False):
        # If export flag is True, return as Excel file
        # 定义与前端一致的列映射
        COLUMNS_MAPPING = [
            {'title': '签到流水ID', 'dataIndex': 'id'},
            {'title': '学籍号', 'dataIndex': ['user', 'studentId']},
            {'title': '姓名', 'dataIndex': ['user', 'name']},
            {'title': '计划ID', 'dataIndex': ['schedule', 'id']},
            {'title': '签到ID', 'dataIndex': ['check_in', 'id']},
            {'title': '计划名称', 'dataIndex': ['schedule', 'schedule_name']},
            {'title': '计划开始时间', 'dataIndex': ['schedule', 'schedule_start_time']},
            {'title': '计划类型', 'dataIndex': ['schedule', 'schedule_type']},
            {'title': '签到名称', 'dataIndex': ['check_in', 'name']},
            {'title': '签到开始时间', 'dataIndex': ['check_in', 'check_in_start_time']},
            {'title': '签到结束时间', 'dataIndex': ['check_in', 'check_in_end_time']},
            {'title': '主签到', 'dataIndex': ['check_in', 'is_main_check_in']},
            {'title': '检查迟到', 'dataIndex': ['check_in', 'need_check_schedule_time']},
            {'title': '状态', 'dataIndex': 'status'}
        ]

        # 准备导出数据
        export_data = []
        for ciu in checkinusers:
            row = {}
            for col in COLUMNS_MAPPING:
                value = get_nested_value(ciu, col['dataIndex'])
                row[col['title']] = value
            export_data.append(row)

        # 创建DataFrame（确保列顺序与前端一致）
        df = pd.DataFrame(export_data, columns=[col['title'] for col in COLUMNS_MAPPING])

        # 创建内存文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='签到记录')

        output.seek(0)

        # 创建文件名
        start = data['start_time'][:10].replace('-', '')
        end = data['end_time'][:10].replace('-', '')
        filename = f"签到记录_{start}_至_{end}.xlsx"

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    return json_response('success', '已列出指定日期内所有签到流水', data=checkinusers, code=200)


@checkin_controller.route('/checkinuser/schedule/<int:schedule_id>', methods=['POST'],
                          endpoint='list_checkin_users_by_schedule_id')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
@record_history
def list_checkin_users_by_schedule_id(schedule_id):
    data = request.get_json()
    if not data:
        return json_response('fail', "未传递任何参数", code=422)
    schema = {
        'export': {'type': 'boolean', 'required': False, 'default': False}
    }
    result, reason = validate_schema(schema, data)
    if not result:
        return json_response('fail', f'请求参数错误: {reason}', code=422)

    schedule = Schedule.get_schedule_by_id(schedule_id)
    if not schedule:
        return json_response('fail', f'未找到值班计划', code=404)
    schedule_dict = {
        'schedule_id': schedule['id'],
        'schedule_name': schedule['schedule_name'],
        'schedule_start_time': schedule['schedule_start_time'],
        'schedule_type': schedule['schedule_type'],
    }
    ciu = []
    checkinusers = [ciu.extend(ci['check_in_users']) for ci in schedule['check_ins']]
    for ciu_ele in ciu:
        ciu_ele['schedule'] = schedule_dict  # Or however you get the schedule data for each user    print(ciu)

    def get_nested_value(record, keys):
        """根据dataIndex路径获取嵌套值"""
        if isinstance(keys, str):
            return record.get(keys, '')
        value = record
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, '')
            else:
                return ''
        return value

    if data.get('export', False):
        # If export flag is True, return as Excel file
        # 定义与前端一致的列映射
        COLUMNS_MAPPING = [
            {'title': '签到流水ID', 'dataIndex': 'id'},
            {'title': '学籍号', 'dataIndex': ['user', 'studentId']},
            {'title': '姓名', 'dataIndex': ['user', 'name']},
            {'title': '计划ID', 'dataIndex': ['schedule', 'id']},
            {'title': '签到ID', 'dataIndex': ['check_in', 'id']},
            {'title': '计划名称', 'dataIndex': ['schedule', 'schedule_name']},
            {'title': '计划开始时间', 'dataIndex': ['schedule', 'schedule_start_time']},
            {'title': '计划类型', 'dataIndex': ['schedule', 'schedule_type']},
            {'title': '签到名称', 'dataIndex': ['check_in', 'name']},
            {'title': '签到开始时间', 'dataIndex': ['check_in', 'check_in_start_time']},
            {'title': '签到结束时间', 'dataIndex': ['check_in', 'check_in_end_time']},
            {'title': '主签到', 'dataIndex': ['check_in', 'is_main_check_in']},
            {'title': '检查迟到', 'dataIndex': ['check_in', 'need_check_schedule_time']},
            {'title': '状态', 'dataIndex': 'status'}
        ]

        # 准备导出数据
        export_data = []
        for ciu_ele in ciu:
            row = {}
            for col in COLUMNS_MAPPING:
                value = get_nested_value(ciu_ele, col['dataIndex'])
                row[col['title']] = value
            export_data.append(row)

        # 创建DataFrame（确保列顺序与前端一致）
        print(export_data)
        df = pd.DataFrame(export_data, columns=[col['title'] for col in COLUMNS_MAPPING])

        # 创建内存文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='签到记录')

        output.seek(0)

        # 创建文件名
        filename = f"签到记录_schedule_{schedule_id}.xlsx"

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    return json_response('success', '已列出指定日期内所有签到流水', data=checkinusers, code=200)
