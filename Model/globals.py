from LoadEnviroment.LoadEnv import mysql_host, mysql_port, mysql_username, mysql_password, mysql_use_ssl, mysql_ssl_ca, \
    mysql_ssl_cert, mysql_ssl_key, mysql_ssl_verify_cert
from sqlalchemy import create_engine, Column, Boolean, Index
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import declared_attr


class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False, nullable=False)

    @declared_attr
    def __table_args__(self):
        # 为所有软删除模型添加索引
        return (Index(f'idx_{self.__tablename__}_is_deleted', 'is_deleted'),)

    @classmethod
    def query_active(cls, session):
        # 基础查询方法
        return session.query(cls).filter(cls.is_deleted == False)

    @classmethod
    def query_inactive(cls, session):
        # 基础查询方法
        return session.query(cls).filter(cls.is_deleted == True)


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

Base = declarative_base()


def format_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None


__all__ = [
    "engine",
    "Session",
    "Base",
    "format_datetime"
]
