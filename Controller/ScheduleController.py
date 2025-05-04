import io
import re
import pandas as pd
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from Handler.Handler import position_required
from Model.Schedule import TypeEnum, Schedule
from Model.User import PositionEnum
from .globals import json_response, Session, validate_schema
from sqlalchemy.exc import IntegrityError

schedule_controller = Blueprint('schedule_controller', __name__)


@schedule_controller.route('', methods=['POST'], endpoint='create_schedule')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
def create_schedule():
    """
    创建值班计划
    """
    schedule_type_enum_values = [item.value for item in TypeEnum]
    data = request.get_json()
    if not data:
        return json_response('fail', "未传递任何参数", code=422)
    schema = {
        'schedule_name': {'type': 'string', 'required': True},
        'schedule_type': {'type': 'string', 'required': True, 'allowed': schedule_type_enum_values},
        'schedule_start_time': {'type': 'string', 'regex': r'^\d{4}-\d{2}-\d{2}$ \d{2}:\d{2}:\d{2}'},  # YYYY-MM-DD 格式
    }
    # 验证请求数据
    is_valid, errors = validate_schema(schema, data)
    if not is_valid:
        return json_response('fail', f"请求数据格式错误: {errors}", code=422)

    try:
        # 查询已存在的 Schedule（避免重复插入）
        session = Session()
        existing_schedules = session.query(Schedule.schedule_name, Schedule.schedule_type,
                                           Schedule.schedule_start_time).all()
        session.close()
        existing_keys = {
            (s.schedule_name, s.schedule_type.value, s.schedule_start_time.strftime('%Y-%m-%d'))
            for s in existing_schedules
        }
        key = (data['schedule_name'], data['schedule_type'], data['schedule_start_time'])
        if key in existing_keys:
            return json_response('fail', f"值班安排 '{key}' 已存在", code=422)

        status, new_schedule, code = Schedule.create_schedule_in_db(
            schedule_name=data["schedule_name"],
            schedule_type=data["schedule_type"],
            schedule_start_time=data["schedule_start_time"]
        )

        # 返回成功响应
        if status:
            return json_response("success", "用户创建成功", data=new_schedule, code=code)
        else:
            return json_response("fail", "值班计划创建失败", code=code)
    except IntegrityError:
        return json_response('fail', '值班计划已存在', code=400)
    except Exception as e:
        return json_response('fail', f"值班计划创建失败：{str(e)}", code=500)


@schedule_controller.route('/upload', methods=['POST'], endpoint='batch_create_schedules')
@jwt_required()
def batch_create_schedules():
    """
    批量创建值班安排及对应主签到记录
    CSV格式，包含 schedule_name, schedule_type, schedule_start_time 列
    """
    if 'file' not in request.files:
        return json_response('fail', '未提供文件', code=422)

    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return json_response('fail', '请上传 CSV 文件', code=422)

    try:
        stream = io.StringIO(file.stream.read().decode("utf-8"))
        df = pd.read_csv(stream)

        required_columns = {"schedule_name", "schedule_type", "schedule_start_time"}
        if not required_columns.issubset(df.columns):
            return json_response('fail', f"CSV 文件缺少必要的列：{', '.join(required_columns)}", code=422)

        # 清洗数据
        df['schedule_name'] = df['schedule_name'].astype(str).str.strip()
        df['schedule_type'] = df['schedule_type'].astype(str).str.strip()
        df['schedule_start_time'] = df['schedule_start_time'].astype(str).str.strip()

        # 查询已存在的 Schedule（避免重复插入）
        session = Session()
        existing_schedules = session.query(Schedule.schedule_name, Schedule.schedule_type,
                                           Schedule.schedule_start_time).all()
        session.close()
        existing_keys = {
            (s.schedule_name, s.schedule_type.value, s.schedule_start_time.strftime('%Y-%m-%d'))
            for s in existing_schedules
        }

        # 校验数据格式
        errors = []
        for index, row in df.iterrows():
            if row['schedule_type'] not in [item.value for item in TypeEnum]:
                errors.append(f"第 {index + 1} 行: 无效的值班类型 '{row['schedule_type']}'")
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', row['schedule_start_time']):
                errors.append(f"第 {index + 1} 行: 无效的值班开始时间 '{row['schedule_start_time']}'")
        if errors:
            return json_response('fail', f"数据校验失败: {', '.join(errors)}", code=422)

        results = []
        created_schedules = []

        for index, row in df.iterrows():
            key = (row['schedule_name'], row['schedule_type'], row['schedule_start_time'])
            if key in existing_keys:
                results.append(f"第 {index + 1} 行: 值班安排 '{key}' 已存在，跳过处理")
                continue

            try:
                # 创建 Schedule
                status, new_schedule, code = Schedule.create_schedule_in_db(
                    schedule_name=row['schedule_name'],
                    schedule_type=row['schedule_type'],
                    schedule_start_time=row['schedule_start_time']
                )

                if status:
                    created_schedules.append(new_schedule)
                    results.append(
                        f"第 {index + 1} 行: 值班安排 '{row['schedule_name']}-{row['schedule_type']}-{row['schedule_start_time']}' 创建成功")

                    results.append(f"第 {index + 1} 行: 主签到创建成功")

                else:
                    results.append(f"第 {index + 1} 行: 创建失败，错误信息: {new_schedule}")

            except IntegrityError:
                results.append(
                    f"第 {index + 1} 行: 值班安排 '{row['schedule_name']}-{row['schedule_type']}-{row['schedule_start_time']}' 冲突")
            except Exception as e:
                results.append(f"第 {index + 1} 行: 创建失败，错误信息: {str(e)}")

        return json_response('success', '批量创建完成', data={
            'results': results,
            'schedules': created_schedules
        }, code=200)

    except Exception as e:
        return json_response('fail', f"文件解析或处理错误：{str(e)}", code=500)


@schedule_controller.route('/<int:schedule_id>', methods=['GET'], endpoint='get_schedule')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
def get_schedule(schedule_id):
    schedule = Schedule.get_schedule_by_id(schedule_id)
    if not schedule:
        return json_response("fail", "值班计划未找到", code=404)
    return json_response("success", "值班计划已列出", data=schedule, code=200)


@schedule_controller.route('/<int:schedule_id>', methods=['DELETE'], endpoint='delete_schedule')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
def delete_schedule(schedule_id):
    schedule = Schedule.get_schedule_by_id(schedule_id)
    if not schedule:
        return json_response("fail", "值班计划未找到", code=404)
    Schedule.delete_schedule_by_id(schedule_id)
    return json_response("success", "值班计划删除成功", code=200)


@schedule_controller.route('', methods=['GET'], endpoint='get_all_schedules')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
def get_all_schedules():
    schedules = Schedule.get_all_schedules()
    return json_response("success", "所有值班计划已列出", data=schedules, code=200)
