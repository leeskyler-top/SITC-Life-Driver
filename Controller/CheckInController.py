import pandas as pd
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from Handler.Handler import position_required
from Model import CheckIn, CheckInUser, AskForLeaveApplication
from Model.Message import Message
from Model.Schedule import Schedule
from Model.User import PositionEnum, User
from .globals import json_response, Session, validate_schema, non_empty_string
from datetime import datetime

checkin_controller = Blueprint('checkin_controller', __name__)


@checkin_controller.route('/my', methods=['GET'], endpoint='list_my_checkins')
@jwt_required()
def list_my_checkins():
    session = Session()
    try:
        user_id = get_jwt_identity()
        checkin_users = session.query(CheckInUser).filter_by(user_id=user_id).all()
        checkin_users = [ciu.to_dict() for ciu in checkin_users]
        return json_response('success', '获取完成', checkin_users, code=200)
    except Exception as e:
        return json_response('fail', f'统计失败: {str(e)}', code=500)
    finally:
        session.close()


@checkin_controller.route('/create/<int:schedule_id>', methods=['POST'], endpoint='create_checkin')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
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
            'name': {
                'type': 'string',
                'required': True,
                'check_with': non_empty_string
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

        new_checkin = CheckIn(
            schedule_id=schedule_id,
            name=data['name'].strip(),
            check_in_start_time=start_time,
            check_in_end_time=end_time,
            is_main_check_in=False
        )
        session.add(new_checkin)
        session.commit()
        return json_response('success', '签到创建成功', data={'check_in_id': new_checkin.id})
    except Exception as e:
        session.rollback()
        return json_response('fail', f'处理请求时出错：{str(e)}', code=500)
    finally:
        session.close()


@checkin_controller.route('/assign', methods=['POST'], endpoint='assign_users_and_checkins')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
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

        sep = "\n"
        # 发送通知
        for user in users:
            Message.add_message(
                user_id=user.id,
                msg_title="新排班通知",
                msg_text=f"请查看新的排班:\n {sep.join([checkin.name for checkin in checkins])} \n，如有异议联系管理员。",
                msg_type='PRIVATE'
            )

        session.commit()

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
                msg_title="新排班通知（单独排班）",
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
        message = f"管理员对你在 {schedule.schedule_name}-{schedule.schedule_start_time.strftime('%Y-%m-%d %H:%M:%S')}-{schedule.schedule_type.value  } 的 {checkin.name} 签到时间进行了更改，如有疑问请联系管理员。"
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


@checkin_controller.route('/', methods=['GET'], endpoint='list_checkins')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
def list_checkins():
    session = Session()
    try:
        schedule_id = request.args.get('schedule_id', type=int)
        query = session.query(CheckIn)
        if schedule_id:
            query = query.filter(CheckIn.schedule_id == schedule_id)

        checkins = query.all()
        result = []
        for checkin in checkins:
            result.append({
                'id': checkin.id,
                'name': checkin.name,
                'check_in_start_time': checkin.check_in_start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'check_in_end_time': checkin.check_in_end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'schedule_id': checkin.schedule_id,
                'is_main_check_in': checkin.is_main_check_in
            })
        return json_response('success', '查询成功', data=result)
    except Exception as e:
        return json_response('fail', f'查询失败：{str(e)}', code=500)
    finally:
        session.close()


@checkin_controller.route('/<int:check_in_id>', methods=['PATCH'], endpoint='update_checkin')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
def update_checkin(check_in_id):
    session = Session()
    try:
        data = request.get_json()
        schema = {
            'name': {'type': 'string', 'required': False},
            'check_in_start_time': {'type': 'string', 'required': False, 'regex': r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'},
            'check_in_end_time': {'type': 'string', 'required': False, 'regex': r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'},
            'need_check_schedule_time': {'type': 'boolean', 'required': False, 'allowed': [True, False]},  # 0 为普通用户，1 为管理员
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
        return json_response('success', '签到信息修改成功', checkin.to_dict(),code=200)
    except Exception as e:
        session.rollback()
        return json_response('fail', f'修改失败：{str(e)}', code=500)
    finally:
        session.close()


@checkin_controller.route('/<int:check_in_id>', methods=['DELETE'], endpoint='delete_checkin')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
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


@checkin_controller.route('/attendance/statistics', methods=['GET'], endpoint='attendance_statistics')
@jwt_required()
def attendance_statistics():
    user_id = get_jwt_identity()
    session = Session()

    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    if not start_time or not end_time:
        return json_response('fail', '请提供起止时间', code=400)

    try:
        # 转换时间格式
        start_date = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end_date = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')

        if start_date >= end_date:
            return json_response('fail', '结束时间必须晚于开始时间', code=400)

        # 查询签到记录
        check_in_users = session.query(CheckInUser).join(CheckIn).filter(
            CheckIn.schedule_id == Schedule.id,
            CheckIn.check_in_start_time >= start_date,
            CheckIn.check_in_end_time <= end_date,
            CheckInUser.user_id == user_id
        ).all()

        # 统计个人出勤率和旷班次数
        attendance_count = len(check_in_users)
        absentee_count = sum(1 for user in check_in_users if not user.check_in_time)

        # 计算每月平均出勤次数
        monthly_attendance = pd.Series()
        for user in check_in_users:
            month = user.check_in.check_in_start_time.strftime('%Y-%m')  # 提取年月
            monthly_attendance[month] = monthly_attendance.get(month, 0) + 1

        average_monthly_attendance = monthly_attendance.mean() if not monthly_attendance.empty else 0

        # 获取部门的平均出勤率
        department_id = session.query(User).filter_by(id=user_id).first().department
        department_checkins = session.query(CheckInUser).join(CheckIn).join(User).filter(
            CheckIn.schedule_id == Schedule.id,
            CheckIn.check_in_start_time >= start_date,
            CheckIn.check_in_end_time <= end_date,
            User.department == department_id
        ).all()

        department_attendance_count = len(department_checkins)
        department_absentee_count = sum(1 for user in department_checkins if not user.check_in_time)
        department_average_attendance_rate = (department_attendance_count / (
                department_attendance_count + department_absentee_count)) * 100 if department_attendance_count + department_absentee_count > 0 else 0

        # 查询请假记录
        leave_applications = session.query(AskForLeaveApplication).filter(
            AskForLeaveApplication.check_in_user_id == user_id,
            AskForLeaveApplication.created_at >= start_date,
            AskForLeaveApplication.created_at <= end_date
        ).all()

        leave_count = len(leave_applications)
        leave_counts_by_type = {}

        for application in leave_applications:
            leave_type = application.asl_type
            leave_counts_by_type[leave_type] = leave_counts_by_type.get(leave_type, 0) + 1

        # 统计部门请假数据
        department_leave_applications = session.query(AskForLeaveApplication).join(User).filter(
            AskForLeaveApplication.created_at >= start_date,
            AskForLeaveApplication.created_at <= end_date,
            User.department == department_id
        ).all()

        department_leave_count = len(department_leave_applications)
        department_leave_count_by_type = {}

        for application in department_leave_applications:
            leave_type = application.asl_type
            department_leave_count_by_type[leave_type] = department_leave_count_by_type.get(leave_type, 0) + 1

        return json_response('success', '统计数据获取成功', data={
            'individual_attendance_count': attendance_count,
            'individual_absentee_count': absentee_count,
            'average_monthly_attendance': average_monthly_attendance,
            'department_average_attendance_rate': department_average_attendance_rate,
            'individual_leave_count': leave_count,
            'individual_leave_count_by_type': leave_counts_by_type,
            'department_leave_count': department_leave_count,
            'department_leave_count_by_type': department_leave_count_by_type
        })

    except Exception as e:
        return json_response('fail', f'统计失败: {str(e)}', code=500)
    finally:
        session.close()
