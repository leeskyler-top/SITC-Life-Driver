from LoadEnviroment.LoadEnv import mysql_host, mysql_port, mysql_username, mysql_password, mysql_ssl_ca, mysql_ssl_cert, \
    mysql_ssl_key, mysql_ssl_verify_cert
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
    'ssl': {
        'ca': mysql_ssl_ca,
        'cert': mysql_ssl_cert,
        'key': mysql_ssl_key,
        'verify_cert': mysql_ssl_verify_cert,
        'verify_identity': mysql_ssl_verify_cert
    }
}


def get_connection(database=None):
    """
    获取数据库连接，支持指定数据库。
    """

    if database:
        config['database'] = database

    return pymysql.connect(**config)
