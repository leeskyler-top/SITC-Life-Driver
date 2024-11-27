from flask import Blueprint, request, Response

from Handler.Handler import position_required
from .globals import json_response, validate_schema
from AnyshareService.AnyShareOperation import delete_template, update_current_semester_info, update_template
from SQLService.Operation import truncate_template, insert_template, delete_template, update_current_semester_info, \
    update_template, read_template_from_sql

template_controller = Blueprint('template_controller', __name__)
import io
import pandas as pd

@template_controller.route('/<int:id>', methods=['PATCH'])
@position_required
def update_template_by_id(id):
    try:
        data = request.get_json()
        if not data:
            return json_response('fail', "未传递任何参数", code=422)
        result, reason = validate_schema(
            {
                'building': {
                    'nullable': True,
                    'required': False,
                    'default': None
                },
                'room': {
                    'nullable': True,
                    'required': False,
                    'default': None
                },
                'classname': {
                    'nullable': True,
                    'required': False,
                    'default': None
                },
            }
            , data
        )
        if not result:
            return json_response('fail', reason, code=422)

        status, result = update_template(
            id,
            data['building'],
            data['room'],
            data['classname']
        )

        if status:
            return json_response('success', '模板已变更', data={
                'building': data['building'],
                'room': data['room'],
                'classname': data['classname']
            })
        else:
            return json_response('fail', result, code=404)
    except Exception as e:
        return json_response('fail', f"文件解析或处理错误：{str(e)}", code=500)


@template_controller.route('/', methods=['DELETE'])
@position_required
def empty_template():
    """
    清空 template 表
    """
    status, reason = truncate_template()
    if status:
        return json_response('success', reason)
    else:
        return json_response('fail', reason, code=422)


@template_controller.route('/<int:id>', methods=['DELETE'])
@position_required
def delete_template_by_id(id):
    """
    清空 template 表
    """

    status, reason = delete_template(id)
    if status:
        return json_response('success', reason)
    else:
        return json_response('fail', reason, code=404)


@template_controller.route('/', methods=['POST'])
@position_required
def add_template():
    try:
        data = request.get_json()
        if not data:
            return json_response('fail', "未传递任何参数", code=422)
        result, reason = validate_schema(
            {
                'building': {
                    'type': 'string',
                    'required': True,
                },
                'room': {
                    'type': 'string',
                    'required': True,
                },
                'classname': {
                    'type': 'string',
                    'required': True,
                },
            }
            , data
        )
        if not result:
            return json_response('fail', reason, code=422)

        status, result = insert_template(
            data['building'].strip(),
            data['room'].strip(),
            data['classname'].strip()
        )

        if status:
            return json_response('success', '模板已添加', data={
                'building': data['building'].strip(),
                'room': data['room'].strip(),
                'classname': data['classname'].strip()
            })
        else:
            return json_response('fail', result, code=404)

    except Exception as e:
        return json_response('fail', f"文件解析或处理错误：{str(e)}", code=500)


@template_controller.route('/upload', methods=['POST'])
@position_required
def upload_template():
    """
    上传并处理 CSV 文件，将数据插入 template 表
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
        required_columns = {'building', 'room', 'classname'}
        if not required_columns.issubset(df.columns):
            return json_response('fail', 'CSV 文件缺少必要的列：building, room, classname', code=422)
        df['building'] = df['building'].astype('str')
        df['room'] = df['room'].astype('str')
        df['classname'] = df['classname'].astype('str')
        # 清理数据
        df = df.dropna(subset=['building', 'room', 'classname']).reset_index(drop=True)
        # 检查唯一性
        if df.duplicated(subset=['building', 'room']).any():
            return json_response('fail', 'CSV 文件中 building 和 room 的组合存在重复', code=422)
        if df['classname'].duplicated().any():
            return json_response('fail', 'CSV 文件中 classname 存在重复', code=422)

        # 插入数据
        results = []
        for index, row in df.iterrows():
            status, result = insert_template(
                row['building'].strip(),
                row['room'].strip(),
                row['classname'].strip()
            )
            results.append(f"第 {index + 1} 行: {result}")

        return json_response('success', '文件处理完成', data=results)

    except Exception as e:
        return json_response('fail', f"文件解析或处理错误：{str(e)}", code=500)


@template_controller.route('/download', methods=['GET'])
@position_required
def download_templates():
    """
    下载 template 表中的所有数据为 CSV 文件
    """
    try:
        df = read_template_from_sql()

        if df.empty:
            return json_response('fail', '表 template 中没有数据', code=404)

        # 转换为 CSV 文件
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=template_data.csv"}
        )

    except Exception as e:
        return json_response('fail', f'处理请求时出错：{str(e)}', code=500)


@template_controller.route('/', methods=['GET'])
@position_required
def get_templates():
    """
    查询 template 表的所有记录
    """
    try:
        df = read_template_from_sql()
        if df.empty:
            return json_response('success', '表 template 没有数据', data=[], code=200)
        return json_response('success', '查询成功', data=df.to_dict(orient='records'))

    except Exception as e:
        return json_response('fail', f'处理请求时出错：{str(e)}', code=500)

