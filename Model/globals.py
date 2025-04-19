from SQLService.Operation import create_database_and_table
from LoadEnviroment.LoadEnv import mysql_host, mysql_port, mysql_username, mysql_password
from sqlalchemy import create_engine, Column, Boolean, Index
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import declared_attr


class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False, nullable=False)

    @declared_attr
    def __table_args__(cls):
        # 为所有软删除模型添加索引
        return (Index(f'idx_{cls.__tablename__}_is_deleted', 'is_deleted'),)

    @classmethod
    def query_active(cls, session):
        # 基础查询方法
        return session.query(cls).filter(cls.is_deleted == False)


create_database_and_table()

engine = create_engine(f'mysql+pymysql://{mysql_username}:{mysql_password}@{mysql_host}:{mysql_port}/SITC')

# 创建 session factory
Session = sessionmaker(bind=engine)

Base = declarative_base()

def format_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None

__all__ = [
    "engine",
    "Session"
]
