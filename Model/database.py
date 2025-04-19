# app/database.py
from Model.User import User
from Model.Schedule import Schedule  # 显式导入所有模型
from Model.CheckIn import CheckIn  # 显式导入所有模型
from Model.CheckInUser import CheckInUser  # 显式导入所有模型
from .globals import Base, engine

def init_db():
    Base.metadata.create_all(engine)  # 一次性创建所有表




