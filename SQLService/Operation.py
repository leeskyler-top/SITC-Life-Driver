import pandas as pd
from datetime import datetime
from pymysql import IntegrityError, MySQLError
from .globals import get_connection


def create_database_and_table():
    """
    创建 SITC 数据库及其表（如果不存在）。
    """
    try:
        # 创建数据库
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    CREATE DATABASE IF NOT EXISTS SITC 
                    CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
                """)
                print("数据库 SITC 创建成功或已存在。")

        # 创建表
        with get_connection(database="SITC") as connection_with_db:
            with connection_with_db.cursor() as cursor:
                # 创建 template 表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS template (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        building VARCHAR(50) NOT NULL,
                        room VARCHAR(50) NOT NULL,
                        classname VARCHAR(100) NOT NULL,
                        UNIQUE (building, room),
                        UNIQUE (classname)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                print("表 template 创建成功或已存在。")

                # 创建 current_semester 表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS current_semester (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        semester_name VARCHAR(50) NOT NULL,
                        start_month DATE NOT NULL,
                        end_month DATE NOT NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                print("表 current_semester 创建成功或已存在。")

                connection_with_db.commit()

    except MySQLError as e:
        print(f"数据库操作失败：{e}")


def update_template(record_id: int, building=None, room=None, classname=None):
    """
    向 template 表中插入一条记录。
    """
    try:
        with get_connection(database="SITC") as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM template WHERE id = %s;", (record_id,))
                record = cursor.fetchone()

                if not record:
                    return False, f"ID {record_id} 的记录不存在"
                if not building:
                    building = record["building"]
                if not room:
                    room = record["room"]
                if not classname:
                    classname = record["classname"]

                cursor.execute("""
                UPDATE template SET building = %s, room = %s, classname = %s WHERE id = %s;
                """, (building, room, classname, record_id))
                connection.commit()
        return True, f"成功插入数据：building={building}, room={room}, classname={classname}"

    except IntegrityError as e:
        return False, f"插入失败：违反唯一性约束 - {e}"
    except MySQLError as e:
        return False, f"数据库错误：{e}"


def insert_template(building: str, room: str, classname: str):
    """
    向 template 表中插入一条记录。
    """
    try:
        with get_connection(database="SITC") as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO template (building, room, classname)
                    VALUES (%s, %s, %s);
                """, (building, room, classname))
                connection.commit()
        return True, f"成功插入数据"

    except IntegrityError as e:
        return False, f"插入失败：违反唯一性约束 - {e}"
    except MySQLError as e:
        return False, f"数据库错误：{e}"


def delete_template(record_id: int):
    """
    根据 ID 删除 template 表中的记录。
    """
    try:
        with get_connection(database="SITC") as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM template WHERE id = %s;", (record_id,))
                record = cursor.fetchone()

                if not record:
                    return False, f"ID {record_id} 的记录不存在"

                cursor.execute("DELETE FROM template WHERE id = %s;", (record_id,))
                connection.commit()
        return True, f"ID {record_id} 的记录已成功删除"

    except MySQLError as e:
        return False, f"删除记录时出错：{e}"


def truncate_template():
    """
    清空 template 表。
    """
    try:
        with get_connection(database="SITC") as connection:
            with connection.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE template;")
                connection.commit()
        return True, "模板已清空"
    except MySQLError as e:
        return False, f"数据库错误：{e}"


def update_current_semester_info(semester_name: str, start_month: str, end_month: str):
    """
    更新 current_semester 表中的学期信息。
    """
    try:
        # 将 start_month 和 end_month 格式化为有效的日期
        start_date = datetime.strptime(start_month, "%Y-%m")  # 将 'YYYY-mm' 转换为日期
        end_date = datetime.strptime(end_month, "%Y-%m")  # 同样处理 end_month

        # 确保日期格式是 'YYYY-mm-01' 格式，假设为每个月的第一天
        start_date = start_date.replace(day=1)
        end_date = end_date.replace(day=1)

        # 转换为字符串，确保格式为 'YYYY-mm-dd'
        start_month_str = start_date.strftime("%Y-%m-%d")
        end_month_str = end_date.strftime("%Y-%m-%d")

        # 连接数据库并执行更新操作
        with get_connection(database="SITC") as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM current_semester;")
                cursor.execute("""
                    INSERT INTO current_semester (semester_name, start_month, end_month)
                    VALUES (%s, %s, %s);
                """, (semester_name, start_month_str, end_month_str))
                connection.commit()

        return True, f"学期信息已更新为：{semester_name}, 开始月份：{start_month_str}, 结束月份：{end_month_str}"

    except MySQLError as e:
        return False, f"更新学期信息失败：{e}"
    except Exception as e:
        return False, f"日期格式化失败：{e}"


def read_from_mysql(query: str = "SELECT * FROM template;"):
    """
    使用 Pandas 从数据库中读取数据。
    """
    try:
        with get_connection(database="SITC") as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                return pd.DataFrame(result)

    except MySQLError as e:
        print(f"数据库读取失败: {e}")
        return None


def read_template_from_sql():
    """
    读取 template 表的所有记录。
    """
    return read_from_mysql("SELECT * FROM template;")


def read_semester_config_from_sql():
    """
    读取 current_semester 表中的学期配置信息。
    """
    try:
        with get_connection(database="SITC") as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT semester_name, start_month, end_month FROM current_semester LIMIT 1;")
                semester_info = cursor.fetchone()

                if not semester_info:
                    return "Not Set", None, None

                return (
                    semester_info["semester_name"],
                    semester_info["start_month"],
                    semester_info["end_month"],
                )

    except MySQLError as e:
        print(f"读取学期配置失败：{e}")
        return "Error", None, None
