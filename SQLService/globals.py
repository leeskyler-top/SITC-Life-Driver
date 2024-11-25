from LoadEnviroment.LoadEnv import mysql_host, mysql_port, mysql_username, mysql_password
import pymysql
from pymysql.connections import Connection

# 数据库连接配置
config = {
    'host': mysql_host,
    'port': mysql_port,
    'user': mysql_username,
    'password': mysql_password,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,  # 返回字典形式，方便处理
}


def get_connection(database=None):
    """
    获取数据库连接，支持指定数据库。
    """

    if database:
        config['database'] = database

    return pymysql.connect(**config)
