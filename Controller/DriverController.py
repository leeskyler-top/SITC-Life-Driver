from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from datetime import date

from AnyshareService.AnyShareBaseService import listDir
from Handler.Handler import admin_required, position_required, record_history
from Model.User import PositionEnum, User
from .globals import json_response, validate_schema, get_data, auto_decrypt_if_present
from SQLService.Operation import read_template_from_sql, read_semester_config_from_sql
from AnyshareService.AnyShareOperation import \
    findCYLCGroup, findLifeDepDir, findCurrentSemseter, genMonthDirBySemester, \
    genDayDir, findDir, genOtherDayDir, listLifeDepDir, listSemesterDir, listMonthDir, listOtherDir, getLink, \
    downloadZip, safeDelDir

driver_controller = Blueprint('driver_controller', __name__)


@driver_controller.route('/docid/groupid', methods=['GET'])
@admin_required
@record_history
def get_group_id():
    """
    获取群组文件夹 ID
    """
    try:
        doc_id = findCYLCGroup()
        return json_response('success', '获取成功', data={'doc_id': doc_id})
    except Exception as e:
        return json_response('fail', f'获取群组 ID 失败：{str(e)}', code=500)


@driver_controller.route('/docid/lifedir', methods=['GET'])
@position_required([PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER])
@record_history
def get_lifedir_id():
    """
    获取生活部文件夹 ID
    """
    try:
        doc_id = findLifeDepDir(findCYLCGroup())
        return json_response('success', '获取成功', data={'doc_id': doc_id})
    except Exception as e:
        return json_response('fail', f'获取群组 ID 失败：{str(e)}', code=500)


@driver_controller.route('/docid/semesterdir', methods=['GET'])
@position_required([PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER])
@record_history
def get_semesterdir_id():
    """
    获取学期文件夹 ID
    """
    try:
        semester_name, start_month, end_month = read_semester_config_from_sql()
        if semester_name == "Not Set" or start_month is None or end_month is None:
            return json_response('fail', f'未设置学期配置，请先设置学期', code=500)
        doc_id = findCurrentSemseter(findLifeDepDir(findCYLCGroup()), semester_name)
        return json_response('success', '获取成功', data={'doc_id': doc_id})
    except Exception as e:
        return json_response('fail', f'获取部门文件夹 ID 失败：{str(e)}', code=500)


@driver_controller.route('/dir/all/create_by_semseter', methods=['GET'])
@position_required([PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER])
@record_history
def create_semester_all_dir():
    try:
        semester_name, start_month, end_month = read_semester_config_from_sql()
        if semester_name == "Not Set" or start_month is None or end_month is None:
            return json_response('fail', f'未设置学期配置，请先设置学期', code=500)
        doc_id = findCurrentSemseter(findLifeDepDir(findCYLCGroup()), semester_name)
        df = read_template_from_sql()
        status, reason = genMonthDirBySemester(doc_id, df)
        if status:
            return json_response('success', '月份与日期文件夹创建成功')
        else:
            return json_response('success', f'月份与日期文件夹创建失败：{reason}')
    except Exception as e:
        return json_response('fail', f'获取学期配置失败：{str(e)}', code=500)


@driver_controller.route('/dir/month/create_by_semseter', methods=['POST'])
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER, PositionEnum.SUMMARY_LEADER,
     PositionEnum.INTERN_SUMMARY_LEADER])
@record_history
@auto_decrypt_if_present
def create_semester_month_dir():
    try:
        data = get_data()
        if not data:
            return json_response('fail', "未传递任何参数", code=422)
        result, reason = validate_schema(
            {
                "month": {
                    'type': 'integer',
                    'required': True,
                    'min': 1,
                    'max': 12
                }
            }
            , data
        )
        if not result:
            return json_response('fail', reason, code=422)

        semester_name, start_month, end_month = read_semester_config_from_sql()
        if semester_name == "Not Set" or start_month is None or end_month is None:
            return json_response('fail', f'未设置学期配置，请先设置学期', code=500)
        doc_id = findCurrentSemseter(findLifeDepDir(findCYLCGroup()), semester_name)
        df = read_template_from_sql()
        status, reason = genDayDir(doc_id, df, month=data['month'])
        if status:
            return json_response('success', '月份与日期文件夹创建成功')
        else:
            return json_response('success', f'月份与日期文件夹创建失败：{reason}')
    except Exception as e:
        return json_response('fail', f'获取学期配置失败：{str(e)}', code=500)


@driver_controller.route('/dir/month/create_current_month', methods=['GET'])
@jwt_required()
@record_history
def create_current_month_dir():
    try:
        semester_name, start_month, end_month = read_semester_config_from_sql()
        if semester_name == "Not Set" or start_month is None or end_month is None:
            return json_response('fail', f'未设置学期配置，请先设置学期', code=500)
        doc_id = findCurrentSemseter(findLifeDepDir(findCYLCGroup()), semester_name)
        df = read_template_from_sql()
        current_month = date.today().month
        status, reason = genDayDir(doc_id, df, month=current_month)
        if status:
            return json_response('success', '月份与日期文件夹创建成功')
        else:
            return json_response('success', f'月份与日期文件夹创建失败：{reason}')
    except Exception as e:
        return json_response('fail', f'获取学期配置失败：{str(e)}', code=500)


@driver_controller.route('/dir/daily/create_by_semseter', methods=['POST'])
@position_required([PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER])
@record_history
@auto_decrypt_if_present
def create_semester_other_daily_dir():
    try:
        data = get_data()
        if not data:
            return json_response('fail', "未传递任何参数", code=422)
        result, reason = validate_schema(
            {
                "month": {
                    'type': 'string',
                    'regex': r'^\d{4}-\d{2}$',  # 正则表达式匹配 YYYY-mm 格式
                    'required': True
                },
                "name": {
                    'type': 'string',
                    'required': True,
                }
            }
            , data
        )

        if not result:
            return json_response('fail', reason, code=422)

        semester_name, start_month, end_month = read_semester_config_from_sql()
        if semester_name == "Not Set" or start_month is None or end_month is None:
            return json_response('fail', f'未设置学期配置，请先设置学期', code=500)
        doc_id = findDir(findCurrentSemseter(findLifeDepDir(findCYLCGroup()), semester_name), data['month'])
        if doc_id is None:
            return json_response("failed", "未找到月份文件夹")
        df = read_template_from_sql()
        status, reason = genOtherDayDir(doc_id, df, data['name'])
        if status:
            return json_response('success', '特殊日期文件夹创建成功')
        else:
            return json_response('success', f'特殊日期文件夹创建失败：{reason}')
    except Exception as e:
        return json_response('fail', f'获取学期配置失败：{str(e)}', code=500)


@driver_controller.route('/dir/list/life_dep', methods=['GET'])
@position_required([PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER])
@record_history
def list_life_dep_dir():
    req, code = listLifeDepDir()
    try:
        if code == 200:
            return json_response("success", "获取成功", data=req, code=code)
        else:
            return json_response("fail", "获取失败", code=code)
    except Exception as e:
        return json_response("fail", f"获取失败：{str(e)}", code=500)


@driver_controller.route('/dir/list/semester', methods=['GET'])
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER, PositionEnum.SUMMARY_LEADER,
     PositionEnum.INTERN_SUMMARY_LEADER])
@record_history
def list_semester_dir():
    req, code = listSemesterDir()
    try:
        if code == 200:
            return json_response("success", "获取成功", data=req, code=code)
        else:
            return json_response("fail", "获取失败", code=code)
    except Exception as e:
        return json_response("fail", f"获取失败：{str(e)}", code=500)


@driver_controller.route('/dir/list/month', methods=['POST'])
@jwt_required()
@record_history
@auto_decrypt_if_present
def list_month_dir():
    try:
        data = get_data()
        if not data:
            return json_response('fail', "未传递任何参数", code=422)
        result, reason = validate_schema(
            {
                "month": {
                    'type': 'string',
                    'regex': r'^\d{4}-\d{2}$',  # 正则表达式匹配 YYYY-mm 格式
                    'required': True
                }
            }
            , data
        )

        if not result:
            return json_response('fail', reason, code=422)
        req, code = listMonthDir(data['month'])
        if code == 200:
            return json_response("success", "获取成功", data=req, code=code)
        else:
            return json_response("fail", "获取失败", code=code)
    except Exception as e:
        return json_response("fail", f"获取失败：{str(e)}", code=500)


def check_valid_access(user, docid):
    minister_positions = [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER]
    minister_positions = [position.value for position in minister_positions]
    if (user["position"] not in minister_positions) or (user["is_admin"]):
        if docid.startswith(str(findLifeDepDir(findCYLCGroup()))):
            return True
    else:
        semester_name, start_month, end_month = read_semester_config_from_sql()
        if semester_name == "Not Set" or start_month is None or end_month is None:
            return False
        if docid.startswith(str(findCurrentSemseter(findLifeDepDir(findCYLCGroup()), semester_name))):
            return True
    return False


@driver_controller.route('/dir/list/other', methods=['POST'])
@jwt_required()
@record_history
@auto_decrypt_if_present
def list_other_dir():
    try:
        data = get_data()
        if not data:
            return json_response('fail', "未传递任何参数", code=422)
        result, reason = validate_schema(
            {
                "docid": {
                    'type': 'string',
                    'required': True
                }
            }
            , data
        )

        if not result:
            return json_response('fail', reason, code=422)
        current_user_id = get_jwt_identity()
        user = User.get_user_by_id(current_user_id)
        if not check_valid_access(user, data['docid']):
            return json_response("fail", "获取失败,试图越界", code=403)
        req, code = listOtherDir(data['docid'])
        if code == 200:
            return json_response("success", "获取成功", data=req, code=code)
        else:
            return json_response("fail", "获取失败", code=code)
    except Exception as e:
        return json_response("fail", f"获取失败：{str(e)}", code=500)


@driver_controller.route('/dir/del', methods=['POST'])
@position_required([PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER])
@record_history
@auto_decrypt_if_present
def delete_dir():
    try:
        data = get_data()
        if not data:
            return json_response('fail', "未传递任何参数", code=422)
        result, reason = validate_schema(
            {
                "docid": {
                    'type': 'string',
                    'required': True
                }
            }
            , data
        )
        if not result:
            return json_response('fail', reason, code=422)
        current_user_id = get_jwt_identity()
        user = User.get_user_by_id(current_user_id)
        if not check_valid_access(user, data['docid']):
            return json_response("fail", "获取失败,试图越界", code=403)
        req, code = safeDelDir(data['docid'])
        if code == 200:
            return json_response("success", "删除成功", data=req, code=code)
        else:
            return json_response("fail", "删除失败", code=code)
    except Exception as e:
        return json_response("fail", f"删除失败：{str(e)}", code=500)


@driver_controller.route('/file/del', methods=['POST'])
@jwt_required()
@record_history
@auto_decrypt_if_present
def delete_file():
    try:
        data = get_data()
        if not data:
            return json_response('fail', "未传递任何参数", code=422)
        result, reason = validate_schema(
            {
                "docid": {
                    'type': 'string',
                    'required': True
                }
            }
            , data
        )
        if not result:
            return json_response('fail', reason, code=422)
        current_user_id = get_jwt_identity()
        user = User.get_user_by_id(current_user_id)
        if not check_valid_access(user, data['docid']):
            return json_response("fail", "越界访问不被允许", code=403)

        def is_docid_in_files(docid, result):
            return any(file["docid"] == docid for file in result.get("files", []))

        last_slash_index = data['docid'].rfind('/')
        result = data['docid'][:last_slash_index]
        req, code = listDir(result)
        if not is_docid_in_files(data['docid'], req):
            return json_response("fail", f"普通用户只允许删除单个文件", code=403)
        req, code = safeDelDir(data['docid'])
        if code == 200:
            return json_response("success", "删除成功", data=req, code=code)
        else:
            return json_response("fail", "删除失败", code=code)
    except Exception as e:
        return json_response("fail", f"删除失败：{str(e)}", code=500)


@driver_controller.route('/dir/link', methods=['POST'])
@jwt_required()
@record_history
@auto_decrypt_if_present
def get_link():
    try:
        data = get_data()
        if not data:
            return json_response('fail', "未传递任何参数", code=422)
        result, reason = validate_schema(
            {
                "usePassword": {
                    'type': 'boolean',
                    'required': True,
                    'default': False
                },
                "perm": {
                    'type': 'integer',
                    'required': True,
                    "allowed": [1, 3, 4, 5, 7]
                },
                "docid": {
                    'type': 'string',
                    "required": True
                },
                "endtime": {
                    'type': 'integer',
                    "required": True,
                }
            }
            , data
        )
        if not result:
            return json_response('fail', reason, code=422)
        current_user_id = get_jwt_identity()
        user = User.get_user_by_id(current_user_id)
        if not check_valid_access(user, data['docid']):
            return json_response("fail", "获取失败,试图越界", code=403)

        req, code = getLink(docid=data['docid'], end_time=data['endtime'], perm=data['perm'],
                            use_password=data['usePassword'])
        if code == 200:
            return json_response("success", "链接获取成功", data=req, code=200)
        else:
            return json_response("fail", "获取失败", code=code)
    except Exception as e:
        return json_response("fail", f"获取失败：{str(e)}", code=500)


@driver_controller.route('/dir/download', methods=['POST'])
@position_required(
    [PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER, PositionEnum.SUMMARY_LEADER,
     PositionEnum.INTERN_SUMMARY_LEADER])
@record_history
@auto_decrypt_if_present
def download_a_zip():
    try:
        data = get_data()
        if not data:
            return json_response('fail', "未传递任何参数", code=422)
        result, reason = validate_schema(
            {
                "session_id": {
                    'type': 'string',
                    'required': True
                },
                "docid": {
                    'type': 'string',
                    'required': True
                },
                "name": {
                    'type': 'string',
                    'required': True
                },
            }
            , data
        )
        if not result:
            return json_response('fail', reason, code=422)
        req, result, code = downloadZip(data['session_id'], data["name"], data["docid"])
        if code == 200:
            return json_response("success", f"已尝试发送:{result}", data=req, code=200)
        else:
            return json_response("fail", f"发送失败:{result}", code=code)
    except Exception as e:
        print(e)
        return json_response("fail", f"发送失败：{e}", code=500)
