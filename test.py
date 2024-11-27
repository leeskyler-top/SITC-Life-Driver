# from datetime import datetime
#
# now = int((datetime.now().timestamp() + 60 * 60 * 24) * 1000000)
# print(now)
# print(1732543200000000)
from Model import User
from Model.User import PositionEnum

import importlib
import Model.User
importlib.reload(Model.User)

new_user = User.User.create_user_in_db(
    studentId="20240001",
    password="securepassword123",
    name="张三",
    classname="计算机科学与技术",
    phone="12345678901",
    qq="123456789",
    position=PositionEnum.REGULAR_MEMBER.value,
    note="备注信息"
)