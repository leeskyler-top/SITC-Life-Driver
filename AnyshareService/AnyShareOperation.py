import calendar
import random
import os
import re
from AnyshareService.AnyShareBaseService import entrydoc, listDir, createDir, getLinkDetail, openShareLink, \
    setShareLink, getBatchDownloadLink, delDir
from LoadEnviroment.LoadEnv import pan_host, wechat_send_group
from SQLService.Operation import *
from datetime import datetime

from WeChatBotService.WeChatBaseService import msgV1
from utils.utils import download_file, rm_results, rar_file_in_parts


def check_parent_docid(parent_docid):
    if not str(parent_docid).startswith(findLifeDepDir(findCYLCGroup())):
        print("请不要试图越界")
        return False
    return True


def findCYLCGroup(name="团委"):
    req, code = entrydoc()
    if code == 200:
        for group in req['docinfos']:
            if group['name'] == name:
                return group['docid']
        return None
    return None


def findDir(parent_docid, name):
    try:
        req, code = listDir(parent_docid)
        if code == 200 and req.get('dirs') is not None:
            for dir in req['dirs']:
                if dir['name'] == name:
                    return dir['docid']
            return None
        return None

    except Exception as e:
        return None


def tryCreateDir(parent_docid, name):
    try:
        req, code = createDir(parent_docid, name)
        if code == 200:
            return req['docid']
        return None
    except Exception as e:
        return None


def findLifeDepDir(group_docid, name="生活部相关"):
    return findDir(group_docid, name)


def findCurrentSemseter(life_dep_dir_docid, name):
    if not check_parent_docid(life_dep_dir_docid):
        return False, "文件夹越界"
    result = findDir(life_dep_dir_docid, name)
    if not result:
        return tryCreateDir(life_dep_dir_docid, name)
    return result


def genMonthDir(parent_docid, month):
    if not check_parent_docid(parent_docid):
        return False, "越界创建文件夹非法"
    result = findDir(parent_docid, month)
    if not result:
        return True, tryCreateDir(parent_docid, month)
    return False, "Already exists"


def genMonthDirBySemester(parent_docid, df_template):
    try:
        if not check_parent_docid(parent_docid):
            return False, "越界创建文件夹非法"
        # 获取学期信息（例如 '2024 Spring'）
        semseter_name, start_month, end_month = read_semester_config_from_sql()

        if semseter_name == "Not Set":
            print("未找到指定学期")
            return False, "未找到指定学期"

        # 提取学期的开始和结束日期
        start_date = pd.to_datetime(start_month)
        end_date = pd.to_datetime(end_month)

        # 获取起始和结束日期的年月范围
        # 使用 pd.date_range 生成从 start_date 到 end_date 的所有月份
        month_range = pd.date_range(start=start_date, end=end_date, freq='MS')  # 'MS' 表示每个月的开始
        print(month_range)
        # 遍历每个月份生成目录
        for month_start in month_range:
            # 获取当前月份的数字
            month = month_start.month
            print(month)
            # 调用 genDayDir 创建该月的目录
            genDayDir(parent_docid, df_template, month)  # 假设 df_template 是从数据库读取的模板数据
        return True, f"学期 {semseter_name} 的月份目录生成完成"

    except Exception as e:
        return False, f"生成学期目录失败：{e}"


def genBuildingDir(parent_docid, building):
    if not check_parent_docid(parent_docid):
        return False, None
    result = findDir(parent_docid, building)
    if not result:
        return True, tryCreateDir(parent_docid, building)
    return False, result


def genDayDir(parent_docid, df, month):
    """
    参数:
    - parent_docid: 父目录的 ID
    - df: 从 template 表读取的数据，包含 building 和 room 列
    - month: 当前生成日期目录的月份
    """
    try:
        if not check_parent_docid(parent_docid):
            print("请不要试图越界创建文件夹")
            return "ERROR"

        # 获取学期的开始和结束日期
        semester_name, start_month, end_month = read_semester_config_from_sql()

        if semester_name == "Not Set":
            return "学期信息未设置"

        # 将 start_month 和 end_month 转换为日期
        start_date = pd.to_datetime(start_month, format='%Y-%m')  # 假设 start_month 是 'YYYY-MM' 格式
        end_date = pd.to_datetime(end_month, format='%Y-%m')  # 同样假设 end_month 是 'YYYY-MM' 格式

        # 获取年份和月份
        start_year = start_date.year
        end_year = end_date.year
        start_month_num = start_date.month
        end_month_num = end_date.month

        # 检查 DataFrame 的必需列
        if 'building' not in df.columns or 'room' not in df.columns or 'classname' not in df.columns:
            raise ValueError("DataFrame 必须包含 'building' 和 'room' 和 'classname' 列")

        # 获取当前月份的天数

        if month < start_month_num:
            # 这是 start_year 中的月份
            month_dir_year = end_year
            days_in_month = calendar.monthrange(end_year, month)[1]
        else:
            # 这是 end_year 中的月份
            month_dir_year = start_year
            days_in_month = calendar.monthrange(start_year, month)[1]

        # 生成月份目录
        month_dir_name = f"{month_dir_year}-{month:02d}"  # 格式：YYYY-MM
        month_dir_docid = findDir(parent_docid, month_dir_name)
        if not month_dir_docid:
            month_dir_docid = tryCreateDir(parent_docid, month_dir_name)
            print(f"月份目录 '{month_dir_name}' 创建成功")

        # 生成该月的日期目录
        for day in range(1, days_in_month + 1):
            # 格式化日期为字符串：YYYY-MM-DD
            day_str = f"{month_dir_year}-{month:02d}-{day:02d}"
            print(day_str)

            # 检查日期目录是否存在
            day_dir_docid = findDir(month_dir_docid, day_str)
            if not day_dir_docid:
                day_dir_docid = tryCreateDir(month_dir_docid, day_str)
                print(f"日期目录 '{day_str}' 创建成功")

            # 遍历 DataFrame 中的每一行，生成楼栋和房间目录
            for _, row in df.iterrows():
                building = row['building']
                room = row['room']
                classname = row['classname']

                # 为每个楼栋生成目录，必须在日期目录下
                building_dir_docid = findDir(day_dir_docid, building)
                if not building_dir_docid:
                    building_dir_docid = tryCreateDir(day_dir_docid, building)
                    print(f"楼栋目录 '{building}' 创建成功")

                # 为每个房间生成目录，必须在楼栋目录下
                room_name = f"{room}-{classname}"
                room_dir_docid = findDir(building_dir_docid, room_name)
                if not room_dir_docid:
                    room_dir_docid = tryCreateDir(building_dir_docid, room_name)
                    print(f"房间目录 '{room_name}' 创建成功")

        print(f"月份 {month} 的日期/楼栋/房间目录生成完成")
        return "OK"

    except Exception as e:
        print(f"日期目录生成失败: {e}")
        return "ERROR"


def genOtherDayDir(parent_docid, df, other_name):
    """
    参数:
    - parent_docid: 父目录的 ID
    - df: 从 template 表读取的数据，包含 building 和 room 列
    - month: 当前生成日期目录的月份
    """
    try:
        if not str(parent_docid).startswith(findLifeDepDir(findCYLCGroup())):
            print("请不要试图越界创建文件夹")
            return "ERROR"

        # 获取学期的开始和结束日期
        semester_name, start_month, end_month = read_semester_config_from_sql()

        if semester_name == "Not Set":
            return "学期信息未设置"

        # 将 start_month 和 end_month 转换为日期
        start_date = pd.to_datetime(start_month, format='%Y-%m')  # 假设 start_month 是 'YYYY-MM' 格式
        end_date = pd.to_datetime(end_month, format='%Y-%m')  # 同样假设 end_month 是 'YYYY-MM' 格式

        # 获取年份和月份
        start_year = start_date.year
        end_year = end_date.year
        start_month_num = start_date.month
        end_month_num = end_date.month

        # 检查 DataFrame 的必需列
        if 'building' not in df.columns or 'room' not in df.columns or 'classname' not in df.columns:
            raise ValueError("DataFrame 必须包含 'building' 和 'room' 和 'classname' 列")

        # 检查日期目录是否存在
        day_dir_docid = findDir(parent_docid, other_name)
        if not day_dir_docid:
            day_dir_docid = tryCreateDir(parent_docid, other_name)
            print(f"月份下其它目录 '{other_name}' 创建成功")

        # 遍历 DataFrame 中的每一行，生成楼栋和房间目录
        for _, row in df.iterrows():
            building = row['building']
            room = row['room']
            classname = row['classname']

            # 为每个楼栋生成目录，必须在日期目录下
            building_dir_docid = findDir(day_dir_docid, building)
            if not building_dir_docid:
                building_dir_docid = tryCreateDir(day_dir_docid, building)
                print(f"楼栋目录 '{building}' 创建成功")

            # 为每个房间生成目录，必须在楼栋目录下
            room_name = f"{room}-{classname}"
            room_dir_docid = findDir(building_dir_docid, room_name)
            if not room_dir_docid:
                room_dir_docid = tryCreateDir(building_dir_docid, room_name)
                print(f"房间目录 '{room_name}' 创建成功")

        print(f"日期/楼栋/房间目录生成完成")
        return "OK"

    except Exception as e:
        print(f"日期目录生成失败: {e}")
        return "ERROR"


def listLifeDepDir():
    req, code = listDir(findLifeDepDir(findCYLCGroup()))
    return req, code


def listSemesterDir():
    semseter_name, start_month, end_month = read_semester_config_from_sql()
    req, code = listDir(findCurrentSemseter(findLifeDepDir(findCYLCGroup()), semseter_name))
    return req, code


def listMonthDir(month: str):
    semseter_name, start_month, end_month = read_semester_config_from_sql()
    req, code = listDir(findDir(findCurrentSemseter(findLifeDepDir(findCYLCGroup()), semseter_name), month))
    return req, code


def listOtherDir(parent_docid):
    if not check_parent_docid(parent_docid):
        return None, 403
    req, code = listDir(parent_docid)
    return req, code


def safeDelDir(docid):
    if not check_parent_docid(docid):
        return None, 403
    req, code = delDir(docid)
    return req, code


def getLink(docid, end_time, perm, use_password):
    try:
        if not str(docid).startswith(findLifeDepDir(findCYLCGroup())):
            return None, 403
        req, code = getLinkDetail(docid)
        if code == 200 and req['link'] == '':
            req, code = openShareLink(docid)
            if code == 200:
                req, code = setShareLink(docid, end_time, -1, perm, use_password)
                return req, code
            return req, code
        elif code == 200:
            req, code = setShareLink(docid, end_time, -1, perm, use_password)
            return req, code
        else:
            return req, code
    except Exception as e:
        return None, 500


def downloadZip(name, docid):
    if str(docid).startswith(findLifeDepDir(findCYLCGroup())):
        docid_lst = [docid]
        name = name + ".zip"
        url, code = getBatchDownloadLink(name, dirs=docid_lst)

        # 如果下载成功
        if code == 200 and url:
            try:
                print(f"下载链接: {url}")
                # 假设 url 返回的是压缩包文件路径
                zip_data = download_file(url)  # 从 URL 下载压缩包内容

                # 如果文件大小小于分卷大小（15 MB），直接发送
                if len(zip_data) <= 15 * 1024 * 1024:
                    print("文件小于分卷大小限制，直接发送")
                    status, response, code = msgV1(wechat_send_group, 1, zip_data, name)
                    if not status or code != 200:
                        print(f"直接发送失败，状态码: {code}")
                        return False, f"直接发送失败，状态码: {code}", 500
                    else:
                        print(f"文件直接发送成功")
                        return True, f"发送成功,\n\n {str(response)}", 200

                # 如果文件大小超出分卷大小，进行分卷处理
                print("文件超出分卷大小限制，开始分卷")
                rm_results()  # 清理结果

                # 设置输出目录
                output_dir = os.path.join(os.getcwd(), 'results', 'zip_file')

                # 使用 WinRAR 对压缩包进行分卷
                result = rar_file_in_parts(zip_data, 15, output_dir, name)

                # 如果分卷处理失败，返回 500 错误
                if not result:
                    return False, "分卷处理失败", 500

                # 获取所有分卷文件
                part_files = [
                    f for f in os.listdir(output_dir)
                    if re.match(rf"{re.escape(name)}\.part\d+\.rar$", f)
                ]

                # 如果没有找到任何分卷文件，返回失败
                if not part_files:
                    print("未找到任何分卷文件")
                    return False, "未找到任何分卷文件", 500

                # 按文件名排序以保证顺序发送
                part_files.sort()

                # 逐一发送分卷文件
                for part_file in part_files:
                    part_path = os.path.join(output_dir, part_file)

                    # 提取分卷编号
                    match = re.search(r"\.part(\d+)\.rar$", part_file)
                    if match:
                        part_num = match.group(1)  # 获取分卷编号（带前导零）
                        # 发送分卷文件，并将编号填入文件名
                        status, response, code = msgV1(wechat_send_group, 1, part_path, f"{name}.part{part_num}.rar")
                        if not status or code != 200:
                            print(f"上传分卷 {part_num} 失败，状态码: {code}")
                            return False, f"上传分卷 {part_num} 失败，状态码: {code}", 500
                        else:
                            print(f"上传分卷 {part_num} 成功")
                    else:
                        print(f"无法解析分卷编号: {part_file}")
                        return False, f"无法解析分卷编号: {part_file}", 500

                print(f"所有分卷文件上传完成,\n {response}")
                return True, f"上传成功,\n\n {str(response)}", 200

            except Exception as e:
                print(f"下载或嵌入过程中发生错误: {e}")
                return False, f"下载或嵌入过程中发生错误: {e}", 500
        else:
            print(f"获取下载链接失败，状态码: {code}")
            return False, f"获取下载链接失败，状态码: {code}", 500

    print("条件不满足，无法继续操作")
    return False, "条件不满足，无法继续操作", 500
