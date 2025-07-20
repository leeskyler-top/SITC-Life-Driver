import io
import re
import pandas as pd
from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError

from Handler.Handler import admin_required, record_history, position_required
from Model.User import PositionEnum
from .globals import json_response, validate_schema, get_data, auto_decrypt_if_present, Session
from Model.StudentClass import StudentClass, DepartmentEnum

student_class_controller = Blueprint('student_class_controller', __name__)


# Create student class
@student_class_controller.route('', methods=['POST'], endpoint='create_student_class')
@position_required([PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER])
@record_history
@auto_decrypt_if_present
def create_student_class():
    data = get_data()
    department_enum_values = [item.value for item in DepartmentEnum]
    schema = {
        'department': {'type': 'string', 'required': True, 'allowed': department_enum_values},
        'grade': {'type': 'string', 'required': True, 'regex': r'^\d{4}-\d{2}$'},
        'class_name': {'type': 'string', 'required': True},
        'class_adviser_id': {'type': 'string', 'nullable': True},
        'class_adviser_name': {'type': 'string', 'nullable': True},
        'monitor_id': {'type': 'string', 'nullable': True},
        'monitor_name': {'type': 'string', 'nullable': True},
        'labor_id': {'type': 'string', 'nullable': True},
        'labor_name': {'type': 'string', 'nullable': True},
    }

    is_valid, errors = validate_schema(schema, data)
    if not is_valid:
        return json_response('fail', f"请求数据格式错误: {errors}", code=422)

    try:
        class_id = StudentClass.create_student_class_in_db(**data)
        return json_response('success', '班级创建成功', data={'id': class_id}, code=201)
    except IntegrityError:
        return json_response('fail', '班级已存在', code=400)
    except Exception as e:
        return json_response('fail', f'创建班级失败: {str(e)}', code=500)



@student_class_controller.route('/<int:student_class_id>', methods=['GET'], endpoint='get_student_class')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
@record_history
@auto_decrypt_if_present
def get_student_class(student_class_id):
    student_class = StudentClass.get_student_class_by_id(student_class_id)
    if student_class:
        return json_response('success', '班级信息获取成功', data=student_class, code=200)
    return json_response('fail', '班级不存在', code=404)


@student_class_controller.route('/<int:student_class_id>', methods=['PATCH'], endpoint='update_student_class')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
@record_history
def update_student_class(student_class_id):
    data = get_data()
    department_enum_values = [item.value for item in DepartmentEnum]
    schema = {
        'department': {'type': 'string', 'required': True, 'allowed': department_enum_values},
        'grade': {'type': 'string', 'required': True, 'regex': r'^\d{4}-\d{2}$'},
        'class_name': {'type': 'string', 'required': True},
        'class_adviser_id': {'type': 'string', 'nullable': True},
        'class_adviser_name': {'type': 'string', 'nullable': True},
        'monitor_id': {'type': 'string', 'nullable': True},
        'monitor_name': {'type': 'string', 'nullable': True},
        'labor_id': {'type': 'string', 'nullable': True},
        'labor_name': {'type': 'string', 'nullable': True},
    }

    is_valid, errors = validate_schema(schema, data)
    if not is_valid:
        return json_response('fail', f"请求数据格式错误: {errors}", code=422)

    # 唯一性检查
    existing_class = StudentClass.query_active(Session()).filter(
        (StudentClass.class_name == data['class_name']) & (StudentClass.id != student_class_id)
    ).first()

    if existing_class:
        return json_response('fail', '班级名称已存在', code=400)


    update_result = StudentClass.patch_student_class_by_id(student_class_id, **data)
    if update_result:
        return json_response('success', '班级更新成功', code=200)
    return json_response('fail', '班级不存在', code=404)


@student_class_controller.route('/<int:student_class_id>', methods=['DELETE'], endpoint='delete_student_class')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
@record_history
def delete_student_class(student_class_id):
    status, message, code = StudentClass.delete_student_class_by_id(student_class_id)
    return json_response(status, message, code=code)


@student_class_controller.route('/delete/<int:student_class_id>', methods=['DELETE'],
                                endpoint='hard_delete_student_class')
@admin_required
@record_history
@auto_decrypt_if_present
def hard_delete_student_class(student_class_id):
    status, reason, code = StudentClass.hard_delete_student_class_by_id(student_class_id)
    return json_response(status, reason, code=code)


@student_class_controller.route('/clear_room_and_building', methods=['POST'], endpoint='clear_room_and_building')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
@record_history
def clear_student_class_room_and_building():
    status, message, code = StudentClass.clear_room_and_building()
    return json_response(status, message, code=code)


@student_class_controller.route('/upload', methods=['POST'], endpoint='upload_student_classes')
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
)
@record_history
def upload_student_classes():
    if 'file' not in request.files:
        return json_response('fail', '未提供文件', code=422)

    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return json_response('fail', '请上传 CSV 文件', code=422)

    try:
        # 解析 CSV 文件
        stream = io.StringIO(file.stream.read().decode("utf-8"))
        df = pd.read_csv(stream)

        # 检查列名是否正确
        required_columns = {'department', 'grade', 'class_name', 'class_adviser_id',
                            'class_adviser_name', 'monitor_id', 'monitor_name',
                            'labor_id', 'labor_name'}
        if not required_columns.issubset(df.columns):
            return json_response('fail', f"CSV 文件缺少必要的列：{', '.join(required_columns)}", code=422)

        # 清理数据
        df = df.replace(r'^\s*$', None, regex=True)

        # 检查非法字符和过滤
        # 定义非法字符的正则表达式
        illegal_pattern = re.compile(r'[<>\/:\\|?*"]')

        def clean_and_validate(value):
            """清理和验证每个值"""
            if pd.isna(value):
                return None
            clean_value = str(value).strip()
            if illegal_pattern.search(clean_value):  # 检查是否存在非法字符
                raise ValueError(f"发现非法字符: {clean_value}")
            return clean_value

        # 对每个列进行清理
        for col in required_columns:
            df[col] = df[col].apply(clean_and_validate)

        # 检查楼栋和教室的唯一性
        if df.duplicated(subset=['building', 'room']).any():
            return json_response('fail', 'CSV 文件中同一楼栋和室号的组合存在重复', code=422)

        # 插入数据
        results = []
        for index, row in df.iterrows():
            try:
                status, new_class, code = StudentClass.create_student_class_in_db(
                    department=row['department'],
                    grade=row['grade'],
                    class_name=row['class_name'],
                    class_adviser_id=row.get('class_adviser_id', None),
                    class_adviser_name=row.get('class_adviser_name', None),
                    monitor_id=row.get('monitor_id', None),
                    monitor_name=row.get('monitor_name', None),
                    labor_id=row.get('labor_id', None),
                    labor_name=row.get('labor_name', None)
                )
                results.append(f"第 {index + 1} 行: 班级 '{new_class['class_name']}' 创建成功")
            except IntegrityError:
                results.append(f"第 {index + 1} 行: 班级已存在，班级名称: {row['class_name']}")
            except Exception as e:
                results.append(f"第 {index + 1} 行: 创建班级失败，错误信息: {str(e)}")

        return json_response('success', '班级导入完成', data=results, code=200)

    except Exception as e:
        return json_response('fail', f"文件解析或处理错误：{str(e)}", code=500)
