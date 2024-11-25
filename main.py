from flask import Flask, request, jsonify, Response
from cerberus import Validator
import io
import pandas as pd
from SQLService.Operation import create_database_and_table, truncate_template, insert_template, read_template_from_sql, \
    read_semester_config_from_sql, delete_template, update_current_semester_info
from AnyshareService.AnyShareOperation import findCYLCGroup, findLifeDepDir, findCurrentSemseter, genMonthDirBySemester, \
    genMonthDir
from CasService.CasLogin import *
import warnings
from urllib3.exceptions import InsecureRequestWarning

# 忽略 InsecureRequestWarning 警告
warnings.simplefilter('ignore', InsecureRequestWarning)

# 初始化数据库
create_database_and_table()

# 初始化 Flask 应用
app = Flask(__name__)

def json_response(status: str, message: str, data=None, code=200):
    """
    统一的 JSON 响应格式
    """
    response = {'status': status, 'message': message}
    if data is not None:
        response['data'] = data
    return jsonify(response), code


def validate_schema(schema, data):
    v = Validator(schema)
    if not v.validate(data):
        return False, v.errors
    else:
        return True, ""

@app.route('/api/v1/semester', methods=['POST'])
def update_semester():
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
        return json_response('fail', reason, code=422)

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
    try:
        pass
    except Exception as e:
        return json_response('fail', f"文件解析或处理错误：{str(e)}", code=500)
    status, reason = truncate_template()
    if status:
        return json_response('success', reason)
    else:
        return json_response('fail', reason, code=422)

@app.route('/api/v1/template', methods=['DELETE'])
def empty_template():
    """
    清空 template 表
    """
    status, reason = truncate_template()
    if status:
        return json_response('success', reason)
    else:
        return json_response('fail', reason, code=422)

@app.route('/api/v1/template/<int:id>', methods=['DELETE'])
def delete_template_by_id(id):
    """
    清空 template 表
    """

    status, reason = delete_template(id)
    if status:
        return json_response('success', reason)
    else:
        return json_response('fail', reason, code=404)

@app.route('/api/v1/template', methods=['POST'])
def add_template():
    try:
        data = request.get_json()
        if not data:
            return json_response('fail', "未传递任何参数", code=422)
        result, reason = validate_schema(
            {
                'building': {
                    'type': 'string',
                    'required': True
                },
                'room': {
                    'type': 'string',
                    'required': True
                },
                'classname': {
                    'type': 'string',
                    'required': True
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

@app.route('/api/v1/template/upload', methods=['POST'])
def upload_template():
    """
    上传并处理 CSV 文件，将数据插入 template 表
    """
    if 'file' not in request.files:
        return json_response('fail', '未提供文件', code=400)

    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return json_response('fail', '请上传 CSV 文件', code=400)

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


@app.route('/api/v1/template/download', methods=['GET'])
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


@app.route('/api/v1/template', methods=['GET'])
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


@app.route('/api/v1/docid/groupid', methods=['GET'])
def get_group_id():
    """
    获取群组 ID
    """
    try:
        doc_id = findCYLCGroup()
        return json_response('success', '获取成功', data={'doc_id': doc_id})
    except Exception as e:
        return json_response('fail', f'获取群组 ID 失败：{str(e)}', code=500)


@app.route('/api/v1/docid/lifedir', methods=['GET'])
def get_lifedir_id():
    """
    获取群组 ID
    """
    try:
        doc_id = findLifeDepDir(findCYLCGroup())
        return json_response('success', '获取成功', data={'doc_id': doc_id})
    except Exception as e:
        return json_response('fail', f'获取群组 ID 失败：{str(e)}', code=500)

@app.route('/api/v1/docid/semesterdir', methods=['GET'])
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

@app.route('/api/v1/dir/day/create_by_semseter', methods=['GET'])
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


if __name__ == '__main__':
    app.run(port=8080)
