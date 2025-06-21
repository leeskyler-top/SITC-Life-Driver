import string
import random
import re

from flask import Blueprint, request, Response
from flask_jwt_extended import get_jwt_identity, jwt_required
from .globals import json_response, validate_schema, Session
from Model.User import User, PositionEnum, GenderEnum, DepartmentEnum, PoliticalLandscapeEnum
from Handler.Handler import admin_required, position_required, record_history
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
import io
import pandas as pd

user_controller = Blueprint('user_controller', __name__)


@user_controller.route('', methods=['POST'], endpoint='create_user')
@admin_required
@record_history
def create_user():
    """
    创建用户，默认密码为账户名
    """
    position_enum_values = [item.value for item in PositionEnum]
    gender_enum_values = [item.value for item in GenderEnum]
    department_enum_values = [item.value for item in DepartmentEnum]
    political_landscape_enum_values = [item.value for item in PoliticalLandscapeEnum]
    data = request.get_json()
    if not data:
        return json_response('fail', "未传递任何参数", code=422)
    schema = {
        'studentId': {'type': 'string', 'required': True, 'minlength': 5, 'maxlength': 50},
        'name': {'type': 'string', 'required': True, 'minlength': 2, 'maxlength': 50},
        'classname': {'type': 'string', 'required': True, 'minlength': 2, 'maxlength': 50},
        'phone': {'type': 'string', 'required': True, 'minlength': 10, 'maxlength': 15},
        'position': {'type': 'string', 'required': True,
                     'allowed': position_enum_values},
        'gender': {'type': 'string', 'required': True, 'allowed': gender_enum_values},
        'department': {'type': 'string', 'required': True, 'allowed': department_enum_values},
        'is_admin': {'type': 'boolean', 'required': True, 'allowed': [True, False]},  # 0 为普通用户，1 为管理员
        'qq': {'type': 'string', 'maxlength': 50},
        'note': {'type': 'string', 'maxlength': 255},
        'politicalLandscape': {'type': 'string', 'allowed': political_landscape_enum_values},
        'resident': {'type': 'boolean', 'required': True, 'allowed': [True, False]},
        'join_at': {'type': 'string', 'regex': r'^\d{4}-\d{2}-\d{2}$'},  # YYYY-MM-DD 格式
    }
    # 验证请求数据
    is_valid, errors = validate_schema(schema, data)
    if not is_valid:
        return json_response('fail', f"请求数据格式错误: {errors}", code=422)

    # 获取请求参数
    studentId = data['studentId']
    password = data['studentId']
    name = data['name']
    classname = data['classname']
    phone = data['phone']
    position = data['position']
    is_admin = data['is_admin']
    gender = data['gender']
    department = data['department']
    qq = data.get('qq', None)
    note = data.get('note', None)
    politicalLandscape = data['politicalLandscape']
    resident = data['resident']
    join_at = data.get('join_at', None)

    try:
        # 使用 User 类创建新用户
        status, new_user, code = User.create_user_in_db(
            studentId=studentId,
            password=password,
            name=name,
            classname=classname,
            gender=gender,
            department=department,
            phone=phone,
            position=position,
            is_admin=is_admin,
            qq=qq,
            note=note,
            politicalLandscape=politicalLandscape,
            resident=resident,
            join_at=join_at
        )
        # 返回成功响应
        if status:
            return json_response("success", "用户创建成功", data={
                'id': new_user["id"],
                'studentId': new_user["studentId"],
                'name': new_user["name"],
                'classname': new_user["classname"],
                'phone': new_user["phone"],
                'department': new_user["department"],
                'gender': new_user["gender"],
                'position': new_user["position"],
                'is_admin': new_user["is_admin"],
                'qq': new_user["qq"],
                'note': new_user["note"],
                'politicalLandscape': new_user["politicalLandscape"],
                'resident': new_user["resident"],
                'join_at': new_user["join_at"]
            }, code=code)
        else:
            return json_response("fail", new_user, code=code)
    except IntegrityError:
        return json_response('fail', '学生ID已存在，请选择其他学号', code=400)
    except Exception as e:
        return json_response('fail', f"用户创建失败：{str(e)}", code=500)


@user_controller.route('/upload', methods=['POST'], endpoint='batch_create_users')
@admin_required  # 需要管理员权限
@record_history
def batch_create_users():
    """
    批量创建用户，默认密码为学号
    """
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
        required_columns = {'studentId', 'name', 'classname', 'phone', 'position', 'gender', 'department', 'is_admin',
                            'qq', 'note', 'politicalLandscape', 'join_at'}
        if not required_columns.issubset(df.columns):
            return json_response('fail', f"CSV 文件缺少必要的列：{', '.join(required_columns)}", code=422)

        # 转换数据类型
        df['studentId'] = df['studentId'].astype('str').str.strip()
        df['name'] = df['name'].astype('str').str.strip()
        df['classname'] = df['classname'].astype('str').str.strip()
        df['phone'] = df['phone'].astype('str').str.strip()
        df['position'] = df['position'].astype('str').str.strip()
        df['gender'] = df['gender'].astype('str').str.strip()
        df['department'] = df['department'].astype('str').str.strip()
        df['is_admin'] = df['is_admin'].fillna(0).astype(bool)  # 默认值为 0
        df['qq'] = df['qq'].astype('str').str.strip().fillna(' ')
        df['note'] = df['note'].astype('str').str.strip().fillna(' ')
        df['politicalLandscape'] = df['politicalLandscape'].astype('str').str.strip().fillna('群众')
        df['resident'] = df['resident'].fillna(0).astype(bool)  # 默认值为 0
        df['join_at'] = df['join_at'].astype('str').apply(lambda x: x.strip() if x else None)

        # 检查 CSV 内部是否有重复的 studentId
        if df['studentId'].duplicated().any():
            duplicates = df[df['studentId'].duplicated()]['studentId'].tolist()
            return json_response('fail', f"CSV 文件中存在重复的 studentId: {', '.join(duplicates)}", code=422)

        # 检查数据库中是否已存在相同的 studentId
        session = Session()
        existing_ids = session.query(User.studentId).filter(User.studentId.in_(df['studentId'].tolist())).all()
        session.close()
        existing_ids = {user_id[0] for user_id in existing_ids}  # 转为集合以便快速检查

        # 校验数据的有效性
        errors = []
        for index, row in df.iterrows():
            if row['join_at'] == "INVALID":
                errors.append(f"第 {index + 1} 行: 无效的加入时间 '{row['join_at']}'")
            if row['position'] not in [item.value for item in PositionEnum]:
                errors.append(f"第 {index + 1} 行: 无效的职位字段 '{row['position']}'")
            if row['gender'] not in [item.value for item in GenderEnum]:
                errors.append(f"第 {index + 1} 行: 无效的性别字段 '{row['gender']}'")
            if row['department'] not in [item.value for item in DepartmentEnum]:
                errors.append(f"第 {index + 1} 行: 无效的部门字段 '{row['department']}'")
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', row['join_at']) and row['join_at']:
                errors.append(f"第 {index + 1} 行: 无效的加入时间 '{row['join_at']}'")
        if errors:
            return json_response('fail', f"数据校验失败: {', '.join(errors)}", code=422)

        # 插入数据
        results = []
        created_users = []  # This will store successfully created users
        for index, row in df.iterrows():
            if row['studentId'] in existing_ids:
                results.append(f"第 {index + 1} 行: studentId {row['studentId']} 已存在于数据库中，跳过处理")
                continue
            if row['join_at']:
                try:
                    row['join_at'] = pd.to_datetime(row['join_at'], format='%Y-%m-%d').strftime('%Y-%m-%d')
                except ValueError:
                    results.append(f"第 {index + 1} 行: 加入时间格式无效，应为 YYYY-MM-DD")
                    continue
            try:
                status, new_user, code = User.create_user_in_db(
                    studentId=row['studentId'],
                    password=row['studentId'],  # 默认密码为学号
                    name=row['name'],
                    classname=row['classname'],
                    phone=row['phone'],
                    position=row['position'],
                    is_admin=row['is_admin'],
                    gender=row['gender'],
                    department=row['department'],
                    qq=row['qq'] or None,
                    note=row['note'] or None,
                    politicalLandscape=row['politicalLandscape'],
                    resident=row['resident'],
                    join_at=row['join_at'] or None
                )
                if status:
                    results.append(f"第 {index + 1} 行: 用户 '{new_user['studentId']}' 创建成功")
                    created_users.append(new_user)  # Add to created users list
                else:
                    results.append(f"第 {index + 1} 行: 用户创建失败，错误信息: {new_user}")
            except IntegrityError:
                results.append(f"第 {index + 1} 行: 学生ID '{row['studentId']}' 已存在")
            except Exception as e:
                results.append(f"第 {index + 1} 行: 用户创建失败，错误信息: {str(e)}")

        data = {
            'results': results,
            'users': created_users
        }
        return json_response('success', '批量创建完成', data=data, code=200)

    except Exception as e:
        return json_response('fail', f"文件解析或处理错误：{str(e)}", code=500)


# 管理员重置用户密码接口
@user_controller.route('/pwd/reset/<int:user_id>', methods=['GET'], endpoint='reset_user_password')
@admin_required  # 确保用户已登录
@record_history
def reset_user_password(user_id):
    current_user_id = get_jwt_identity()  # 获取当前用户的 ID

    # 确保管理员不能重置自己的密码
    if int(current_user_id) == user_id:
        return json_response("fail", "不能重置自己的密码", code=403)

    # 生成一个随机密码
    new_password = generate_random_password()

    # 获取数据库 session
    session = Session()
    user = User.get_user_by_id(user_id)

    if not user:
        session.close()
        return json_response("fail", "用户不存在", code=404)

    try:
        # 更新密码
        status, reason, code = User.update_password(user_id, new_password)
        if status:
            return json_response("success", "密码重置成功", data={
                "new_password": new_password  # 明文密码返回给前端
            }, code=200)
        else:
            return json_response("fail", reason, code=code)
    except Exception as e:
        session.rollback()
        session.close()
        return json_response("fail", f"密码重置失败：{str(e)}", code=500)


# 随机生成密码函数
def generate_random_password(length=8):
    """生成一个包含字母和数字的随机密码"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


# 其他用户管理功能类似
# 用户更新密码接口
@user_controller.route('/pwd/update', methods=['PATCH'], endpoint='update_own_password')
@jwt_required()  # 确保用户已登录
@record_history
def update_own_password():
    current_user_id = get_jwt_identity()  # 获取当前用户的 ID

    # 定义验证规则
    schema = {
        'old_password': {'type': 'string', 'required': True},
        'new_password': {'type': 'string', 'required': True},
        'confirm_password': {'type': 'string', 'required': True}
    }

    data = request.get_json()

    # 验证请求数据
    is_valid, errors = validate_schema(schema, data)
    if not is_valid:
        return json_response('fail', f"请求数据格式错误: {errors}", code=422)

    old_password = data['old_password']
    new_password = data['new_password']
    confirm_password = data['confirm_password']

    # 检查新密码和确认密码是否一致
    if new_password != confirm_password:
        return json_response('fail', "新密码和确认密码不一致", code=400)

    # 获取数据库 session
    session = Session()
    user = session.query(User).filter_by(id=current_user_id).first()

    if not user:
        session.close()
        return json_response('fail', "用户不存在", code=404)

    # 验证旧密码是否正确
    if not User.verify_password(old_password, user.password):
        session.close()
        return json_response('fail', "旧密码错误", code=401)

    try:
        status, reason, code = User.update_password(current_user_id, new_password)
        if status:
            return json_response('success', reason, code=code)
        else:
            return json_response("fail", reason, code=code)
    except Exception as e:
        session.rollback()
        session.close()
        return json_response('fail', f"密码更新失败：{str(e)}", code=500)


@user_controller.route('/<int:user_id>', methods=['PATCH'], endpoint='patch_user')
@admin_required
@record_history
def patch_user(user_id):
    """
    更新用户信息，除了密码和学生ID字段
    """
    data = request.get_json()
    if not data:
        return json_response('fail', "未传递任何参数", code=422)

    position_enum_values = [item.value for item in PositionEnum]
    gender_enum_values = [item.value for item in GenderEnum]
    department_enum_values = [item.value for item in DepartmentEnum]
    political_landscape_enum_values = [item.value for item in PoliticalLandscapeEnum]

    schema = {
        'name': {'type': 'string', 'required': True, 'minlength': 2, 'maxlength': 50},
        'classname': {'type': 'string', 'required': True, 'minlength': 2, 'maxlength': 50},
        'phone': {'type': 'string', 'required': True, 'minlength': 10, 'maxlength': 15},
        'position': {'type': 'string', 'required': True,
                     'allowed': position_enum_values},
        'gender': {'type': 'string', 'required': True, 'allowed': gender_enum_values},
        'department': {'type': 'string', 'required': True, 'allowed': department_enum_values},
        'politicalLandscape': {'type': 'string', 'required': True, 'allowed': political_landscape_enum_values},
        'is_admin': {'type': 'integer', 'required': True, 'allowed': [0, 1]},  # 0 为普通用户，1 为管理员
        'resident': {'type': 'integer', 'required': True, 'allowed': [0, 1]},
        'qq': {'type': 'string', 'maxlength': 50},
        'note': {'type': 'string', 'maxlength': 255},
        'join_at': {'type': 'string', 'regex': r'^\d{4}-\d{2}-\d{2}$'}  # YYYY-MM-DD 格式
    }

    is_valid, errors = validate_schema(schema, data)
    if not is_valid:
        return json_response('fail', f"请求数据格式错误: {errors}", code=422)

    current_user_id = get_jwt_identity()
    current_user = User.get_user_by_id(current_user_id)

    if not current_user:
        return json_response("fail", "用户不存在", code=404)
    # 防止用户修改自己的 is_admin 字段，确保只有管理员能够更改
    if int(current_user_id) == user_id:
        # 如果修改的是当前用户的权限，禁止更改 is_admin
        data = request.get_json()
        if 'is_admin' in data and data['is_admin'] != current_user['is_admin']:
            return json_response("fail", "不可修改自己的管理员字段", code=403)

    status, updated_user, code = User.patch_user_by_id(
        user_id=user_id,
        name=data.get('name'),
        classname=data.get('classname'),
        phone=data.get('phone'),
        qq=data.get('qq'),
        department=data.get('department'),
        gender=data.get('gender'),
        is_admin=data.get('is_admin'),
        position=data.get('position'),
        politicalLandscape=data.get('politicalLandscape'),
        note=data.get('note'),
        join_at=data.get('join_at')
    )

    if status:
        return json_response("success", "用户信息已更新", updated_user, code=code)
    else:
        return json_response("fail", updated_user, code)


@user_controller.route('/<int:user_id>', methods=['GET'], endpoint='get_user')
@admin_required
@record_history
def get_user(user_id):
    """
    获取某一用户信息
    """
    user = User.get_user_by_id(user_id)
    if user:
        return json_response("success", "用户信息获取成功", data=user, code=200)
    else:
        return json_response("fail", "用户不存在", code=404)


@user_controller.route('/<int:user_id>', methods=['DELETE'], endpoint='delete_user')
@admin_required
@record_history
def delete_user(user_id):
    """
    删除某一用户，但不能删除自己
    """
    current_user_id = get_jwt_identity()
    if user_id == int(current_user_id):
        return json_response("fail", "不能删除自己", code=403)

    user = User.get_user_by_id(user_id)
    if not user:
        return json_response("fail", "值班计划未找到", code=404)

    # 删除用户
    User.delete_user_by_id(user_id)
    return json_response("success", "用户删除成功", code=200)


@user_controller.route('', methods=['GET'], endpoint='get_all_users')
@admin_required
@record_history
def get_all_users():
    """
    获取所有用户信息
    """
    users = User.get_all_users()
    return json_response("success", "用户列表获取成功", data=users, code=200)


@user_controller.route('/my', methods=['GET'], endpoint='get_my_info')
@jwt_required()
@record_history
def get_my_info():
    """
    获取某一用户信息
    """
    current_user_id = get_jwt_identity()
    user = User.get_user_by_id(current_user_id)
    if user:
        return json_response("success", "用户信息获取成功", data=user, code=200)
    else:
        return json_response("fail", "用户不存在", code=404)


@user_controller.route('/count', methods=['GET'], endpoint='calculate_statistics')
@position_required([PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER])
@record_history
def calculate_statistics():
    session = Session()
    try:
        # 过滤掉 "其他人员"
        query = User.query_active(session).filter(User.position != PositionEnum.OTHERS)

        def data_count(data_query, cond, enum):
            return data_query.filter(cond == enum).count()

        # 统计数据
        CYLC_Count = data_count(query, User.politicalLandscape, PoliticalLandscapeEnum.CYLC)
        PublicPeople_Count = data_count(query, User.politicalLandscape, PoliticalLandscapeEnum.PUBLICPEOPLE)
        Male_Count = data_count(query, User.gender, GenderEnum.MALE)
        Female_Count = data_count(query, User.gender, GenderEnum.FEMALE)
        # 部门人数统计
        Information_Count = data_count(query, User.department, DepartmentEnum.INFORMATION)
        Manufacturing_Count = data_count(query, User.department, DepartmentEnum.MANUFACTURING)
        Business_Count = data_count(query, User.department, DepartmentEnum.BUSINESS)
        Material_Count = data_count(query, User.department, DepartmentEnum.MATERIALS)
        Public_Count = data_count(query, User.department, DepartmentEnum.PUBLIC)

        # 部门总人数
        Department_Count = query.count()

        # 计算团青比
        Youth_Ratio = CYLC_Count / Department_Count if Department_Count > 0 else 0

        # 查询班级名称的前两位，并分组统计年级人数
        grade_counts = session.query(
            func.substring(User.classname, 1, 2).label('grade'),
            func.count(User.id).label('count')
        ).filter(
            User.is_deleted == False,  # 确保只统计未删除用户
            User.position != PositionEnum.OTHERS
        )  # 过滤掉非团员

        # 进行分组统计
        grade_counts = grade_counts.group_by(func.substring(User.classname, 1, 2))

        # 获取结果
        grade_counts_result = grade_counts.all()

        # 将统计结果组织成字典形式
        Grade_Count = [{"name": f"{grade}级", "value": count} for grade, count in grade_counts_result]

        # 构造返回数据
        result = {
            "CYLC_Count": CYLC_Count,
            "PublicPeople_Count": PublicPeople_Count,
            "Department_Count": Department_Count,
            "Male_Count": Male_Count,
            "Female_Count": Female_Count,
            "Youth_Ratio": Youth_Ratio,
            "Information_Count": Information_Count,
            "Manufacturing_Count": Manufacturing_Count,
            "Business_Count": Business_Count,
            "Material_Count": Material_Count,
            "Public_Count": Public_Count,
            "Grade_Count": Grade_Count
        }

        # 使用统一 JSON 格式返回
        return json_response("success", "统计数据获取成功", data=result)
    except Exception as e:
        return json_response("error", f"统计数据获取失败: {str(e)}", code=500)
    finally:
        session.close()


@user_controller.route('/export', methods=['GET'], endpoint='export_current_user')
@admin_required  # 确保用户已登录
@record_history
def export_all_users():
    """
    导出所有用户信息为 CSV 格式
    """
    users = User.get_all_users()  # 获取所有用户信息
    if not users:
        return json_response("fail", "没有用户信息", code=404)

    # 将用户信息放入字典列表
    user_data_list = []
    for user in users:
        user_data = {
            "studentId": user["studentId"],
            "name": user["name"],
            "classname": user["classname"],
            "phone": user["phone"],
            "position": user["position"],
            "gender": user["gender"],
            "department": user["department"],
            "is_admin": user["is_admin"],
            "qq": user["qq"],
            "note": user["note"],
            "politicalLandscape": user["politicalLandscape"],
            "resident": user["resident"],
            "join_at": user["join_at"]
        }
        user_data_list.append(user_data)

    # 创建 DataFrame
    df = pd.DataFrame(user_data_list)

    # 转换为 CSV 格式
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    # 返回 CSV 文件
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=all_users_info.csv"}
    )


@user_controller.route('/deleted', methods=['GET'], endpoint='show_deleted_user')
@admin_required  # 确保用户已登录
@record_history
def show_deleted_users():
    deleted_users = User.get_all_deleted_users()
    return json_response("success", "用户列表获取成功", data=deleted_users, code=200)


@user_controller.route('/restore/<int:user_id>', methods=['PATCH'], endpoint='restore_deleted_user')
@admin_required  # 确保用户已登录
@record_history
def restore_deleted_user(user_id):
    status, reason, code = User.restore_deleted_user(user_id)
    if status:
        return json_response("success", reason, code=code)
    return json_response("fail", reason, code=code)
