from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import relationship

from .globals import Session, Base, format_datetime
import enum
from sqlalchemy import Column, Integer, Enum, ForeignKey, Boolean, func
from sqlalchemy import DateTime


class CheckInStatusEnum(enum.Enum):
    NORMAL = "正常"
    LATE = "迟到"
    ABSENTEEISM = "缺勤"
    ASK_FOR_LEAVE = "请假"


class AskForLeaveEnum(enum.Enum):
    SICK = "病假"
    COMPETITION = "符合要求的赛事或集训"
    ASL = "事假"
    OFFICIAL = "公务假"


class CheckInUser(Base):
    __tablename__ = 'check_in_users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    check_in_id = Column(Integer, ForeignKey('check_ins.id', ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    ask_for_leave = Column(Enum(AskForLeaveEnum), nullable=True)
    need_check_schedule_time = Column(Boolean, nullable=False, default=False)
    is_necessary = Column(Boolean, nullable=False, default=True)
    check_in_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # 添加关系
    check_in = relationship("CheckIn", back_populates="check_in_users")
    user = relationship("User")

    def get_status(self, schedule_start_time=None):
        if self.ask_for_leave:
            return CheckInStatusEnum.ASK_FOR_LEAVE.value

        if not self.check_in_time:
            if datetime.now() > self.check_in.check_in_end_time:
                return CheckInStatusEnum.ABSENTEEISM.value
            return None

        if self.need_check_schedule_time and schedule_start_time:
            if self.check_in_time > schedule_start_time:
                return CheckInStatusEnum.LATE.value

        return CheckInStatusEnum.NORMAL.value

    def to_dict(self, schedule_start_time=None):
        return {
            "id": self.id,
            "check_in_id": self.check_in_id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "ask_for_leave": self.ask_for_leave.value if self.ask_for_leave else None,
            "need_check_schedule_time": self.need_check_schedule_time,
            "is_necessary": self.is_necessary,
            "check_in_time": format_datetime(self.check_in_time),
            "status": self.get_status(schedule_start_time),
            "created_at": format_datetime(self.created_at),
            "updated_at": format_datetime(self.updated_at)
        }

    @classmethod
    def get_check_in_by_id(cls, check_in_id: int):
        session = Session()
        try:
            # 使用 joinedload 优化查询
            from sqlalchemy.orm import joinedload
            check_in = session.query(cls) \
                .options(
                joinedload(cls.check_in_users)
                .joinedload(CheckInUser.user)  # 加载关联的用户信息
            ) \
                .filter_by(id=check_in_id) \
                .first()

            if not check_in:
                return None

            result = check_in.to_dict()
            # 使用 CheckInUser 的 to_dict 方法
            result['check_in_users'] = [
                ciu.to_dict(schedule_start_time=check_in.check_in_start_time)
                for ciu in check_in.check_in_users
            ]
            return result
        finally:
            session.close()

    @classmethod
    def delete_check_in_by_id(cls, check_in_user_id: int):
        session = Session()
        check_in = session.query(cls).filter_by(id=check_in_user_id).first()
        if check_in:
            session.delete(check_in)  # 删除用户
            session.commit()  # 提交事务
        session.close()

    @classmethod
    def get_all_check_ins(cls):
        session = Session()
        try:
            from sqlalchemy.orm import joinedload
            check_ins = session.query(cls) \
                .options(
                joinedload(cls.check_in_users)
                .joinedload(CheckInUser.user)
            ) \
                .all()

            return [
                {
                    **check_in.to_dict(),
                    # 使用 CheckInUser.to_dict() 并传入需要的时间参数
                    'check_in_users': [
                        ciu.to_dict(check_in.check_in_start_time)
                        for ciu in check_in.check_in_users
                    ]
                }
                for check_in in check_ins
            ]
        finally:
            session.close()

