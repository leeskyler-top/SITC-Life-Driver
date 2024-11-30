from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from Handler.Handler import admin_required, position_required
from Model.User import PositionEnum
from SQLService.Operation import read_semester_config_from_sql, update_current_semester_info
from .globals import json_response, validate_schema

semester_controller = Blueprint('semester_controller', __name__)
@semester_controller.route('', methods=['GET'])
@jwt_required()
def get_semester():
    try:
        result = read_semester_config_from_sql()
        try:
            result = {
                "semester_name": result[0],
                "start_month": result[1].strftime("%Y-%m"),
                "end_month": result[2].strftime("%Y-%m"),
            }
        except:
            result = {
                "semester_name": "Not Set",
                "start_month": "1970-01",
                "end_month": "1970-01",
            }
        return json_response('success', '获取成功', data=result, code=200)
    except Exception as e:
        return json_response('fail', f"文件解析或处理错误：{str(e)}", code=500)

@semester_controller.route('', methods=['POST'])
@position_required([PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER])
def update_semester():
    try:
        data = request.get_json()
        if not data:
            return json_response('fail', "未传递任何参数", code=422)
        result, reason = validate_schema(
            {
                'start_month': {
                    'type': 'string',
                    'regex': r'^\d{4}-\d{2}$',  # 正则表达式匹配 YYYY-mm 格式
                    'required': True
                },
                'end_month': {
                    'type': 'string',
                    'regex': r'^\d{4}-\d{2}$',  # 正则表达式匹配 YYYY-mm 格式
                    'required': True
                },
                'semester_name': {
                    'type': 'string',
                    'required': True
                },
            }
            , data
        )
        if not result:
            return json_response('fail', message=f"请求数据格式错误: {reason}", code=422)

        status, result = update_current_semester_info(
            data['semester_name'].strip(),
            data['start_month'].strip(),
            data['end_month'].strip()
        )

        if status:
            return json_response('success', '模板已添加', data={
                'semester_name': data['semester_name'].strip(),
                'start_month': data['start_month'].strip(),
                'end_month': data['end_month'].strip()
            })
        else:
            return json_response('fail', result, code=404)
    except Exception as e:
        return json_response('fail', f"文件解析或处理错误：{str(e)}", code=500)