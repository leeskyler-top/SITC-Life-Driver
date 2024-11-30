from flask import Blueprint, request

from Handler.Handler import admin_required, position_required
from Model.User import PositionEnum
from .globals import json_response, validate_schema
from SQLService.Operation import read_template_from_sql, read_semester_config_from_sql
from AnyshareService.AnyShareOperation import findCYLCGroup, findLifeDepDir, findCurrentSemseter, genMonthDirBySemester, \
     genDayDir, findDir, genOtherDayDir, listLifeDepDir, listSemesterDir, listMonthDir, listOtherDir

driver_controller = Blueprint('driver_controller', __name__)

@driver_controller.route('/docid/groupid', methods=['GET'])
@admin_required
def get_group_id():
    """
    获取群组 ID
    """
    try:
        doc_id = findCYLCGroup()
        return json_response('success', '获取成功', data={'doc_id': doc_id})
    except Exception as e:
        return json_response('fail', f'获取群组 ID 失败：{str(e)}', code=500)


@driver_controller.route('/docid/lifedir', methods=['GET'])
@position_required([PositionEnum.MINISTER, PositionEnum.VICE_MINISTER])
def get_lifedir_id():
    """
    获取群组 ID
    """
    try:
        doc_id = findLifeDepDir(findCYLCGroup())
        return json_response('success', '获取成功', data={'doc_id': doc_id})
    except Exception as e:
        return json_response('fail', f'获取群组 ID 失败：{str(e)}', code=500)


@driver_controller.route('/docid/semesterdir', methods=['GET'])
def get_semesterdir_id():
    """
    获取群组 ID
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
def create_semester_all_dir():
    try:
        semester_name, start_month, end_month = read_semester_config_from_sql()
        if semester_name == "Not Set" or start_month is None or end_month is None:
            return json_response('fail', f'未设置学期配置，请先设置学期', code=500)
        print(semester_name)
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
def create_semester_month_dir():
    try:
        data = request.get_json()
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
        print(semester_name)
        doc_id = findCurrentSemseter(findLifeDepDir(findCYLCGroup()), semester_name)
        df = read_template_from_sql()
        status, reason = genDayDir(doc_id, df, month=data['month'])
        if status:
            return json_response('success', '月份与日期文件夹创建成功')
        else:
            return json_response('success', f'月份与日期文件夹创建失败：{reason}')
    except Exception as e:
        return json_response('fail', f'获取学期配置失败：{str(e)}', code=500)


@driver_controller.route('/dir/daily/create_by_semseter', methods=['POST'])
def create_semester_other_daily_dir():
    try:
        data = request.get_json()
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
        print(semester_name)
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
def list_month_dir():
    try:
        data = request.get_json()
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

@driver_controller.route('/dir/list/other', methods=['POST'])
def list_other_dir():
    try:
        data = request.get_json()
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
        req, code = listOtherDir(data['docid'])
        if code == 200:
            return json_response("success", "获取成功", data=req, code=code)
        else:
            return json_response("fail", "获取失败", code=code)
    except Exception as e:
        return json_response("fail", f"获取失败：{str(e)}", code=500)