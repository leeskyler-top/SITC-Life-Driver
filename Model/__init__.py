from Model.User import User
from Model.Schedule import Schedule
from Model.CheckIn import CheckIn
from Model.CheckInUser import CheckInUser
from Model.AskForLeaveApplication import AskForLeaveApplication
from Model.Message import Message
from Model.History import History
from Model.StudentClass import StudentClass
from Model.RuleGroup import RuleGroup
from Model.Rule import Rule
from ClassScore import ClassScore
from SQLService.Operation import create_database_and_table
from .globals import Base, engine


def init_db():
    Base.metadata.create_all(engine)  # 一次性创建所有表
    User.create_default_user()


create_database_and_table()
init_db()
