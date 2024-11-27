from SQLService.Operation import create_database_and_table
from LoadEnviroment.LoadEnv import mysql_host, mysql_port, mysql_username, mysql_password
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

create_database_and_table()

engine = create_engine(f'mysql+pymysql://{mysql_username}:{mysql_password}@{mysql_host}:{mysql_port}/SITC')

# 创建 session factory
Session = sessionmaker(bind=engine)

__all__ = [
    "engine",
    "Session"
]