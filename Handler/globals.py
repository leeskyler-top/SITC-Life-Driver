from LoadEnviroment.LoadEnv import mysql_host, mysql_port, mysql_username, mysql_password, mysql_use_ssl, mysql_ssl_ca, \
    mysql_ssl_cert, mysql_ssl_key, mysql_ssl_verify_cert
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

if mysql_use_ssl:
    ssl_config = {
        'ca': mysql_ssl_ca,
        'cert': mysql_ssl_cert,
        'key': mysql_ssl_key,
        'check_hostname': mysql_ssl_verify_cert,
        'verify_cert': mysql_ssl_verify_cert,
        'verify_identity': mysql_ssl_verify_cert
    }
    engine = create_engine(
        f'mysql+pymysql://{mysql_username}:{mysql_password}@{mysql_host}:{mysql_port}/SITC',
        connect_args={
            'ssl': ssl_config
        }
    )
else:
    engine = create_engine(f'mysql+pymysql://{mysql_username}:{mysql_password}@{mysql_host}:{mysql_port}/SITC')

# 创建 session factory
Session = sessionmaker(bind=engine)

__all__ = [
    "engine",
    "Session"
]
