import enum
from datetime import datetime
from sqlalchemy.orm import relationship, joinedload
from .globals import Session, Base, format_datetime
from sqlalchemy import Column, Integer, ForeignKey, Boolean, func
from sqlalchemy import DateTime


class CheckInStatusEnum(enum.Enum):
    NOT_STARTED = "未开始"
    NOT_SIGNED = "未签到"
    NORMAL = "正常"
    LATE = "迟到"
    ABSENTEEISM = "缺勤"
    ASK_FOR_LEAVE = "请假"


class StatusEnum(enum.Enum):
    PENDING = "待审核"
    ACCEPTED = "已批准"
    REJECTED = "已拒绝"
    CANCELLED = "已取消"


class CheckInUser(Base):
    __tablename__ = 'check_in_users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    check_in_id = Column(Integer, ForeignKey('check_ins.id', ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    is_necessary = Column(Boolean, nullable=False, default=True)
    check_in_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # 添加关系
    ask_for_leaves = relationship(
        "AskForLeaveApplication",
        back_populates="check_in_user",
        cascade="all, delete-orphan"
    )
    check_in = relationship("CheckIn", back_populates="check_in_users")
    user = relationship("User")

    def get_status(self, schedule_start_time=None):
        # 通过 ORM 关系直接访问请假申请
        approved_asl = next((
            asl for asl in self.ask_for_leaves
            if asl.status.value == StatusEnum.ACCEPTED.value
        ), None)
        if approved_asl:
            return approved_asl.asl_type.value

        if not self.check_in_time:
            if datetime.now() > self.check_in.check_in_end_time:
                return CheckInStatusEnum.ABSENTEEISM.value
            elif datetime.now() > self.check_in.check_in_start_time:
                return CheckInStatusEnum.NOT_SIGNED.value
            else:
                return CheckInStatusEnum.NOT_STARTED.value

        if self.check_in.need_check_schedule_time and schedule_start_time:
            if self.check_in_time > schedule_start_time:
                return CheckInStatusEnum.LATE.value
        return CheckInStatusEnum.NORMAL.value

    def to_dict(self, include_user=True, include_check_in=True, include_schedule=False, include_asl=False):
        checkInUsers = {
            "id": self.id,
            "check_in_id": self.check_in_id,
            "user_id": self.user_id,
            "is_necessary": self.is_necessary,
            "check_in_time": format_datetime(self.check_in_time),
            "status": self.get_status(self.check_in.schedule.schedule_start_time),
            "created_at": format_datetime(self.created_at),
            "updated_at": format_datetime(self.updated_at)
        }
        if include_user:
            checkInUsers["user"] = {
                "id": self.user.id,
                "studentId": self.user.studentId,
                "name": self.user.name
            }
        if include_check_in:
            checkInUsers["check_in"] = {
                "id": self.check_in.id,
                "name": self.check_in.name,
                "need_check_schedule_time": self.check_in.need_check_schedule_time,
                "is_main_check_in": self.check_in.is_main_check_in,
                "check_internal": self.check_in.check_internal,
                "check_in_start_time": format_datetime(self.check_in.check_in_start_time),
                "check_in_end_time": format_datetime(self.check_in.check_in_end_time)
            }
        if include_schedule:
            checkInUsers["schedule"] = {
                "id": self.check_in.schedule_id,
                "schedule_name": self.check_in.schedule.schedule_name,
                "schedule_start_time": format_datetime(self.check_in.schedule.schedule_start_time),
                "schedule_type": self.check_in.schedule.schedule_type.value
            }
        if include_asl:
            checkInUsers["asl"] = [
                {
                    "id": asl.id,
                    "asl_type": asl.asl_type.value,
                    "asl_reason": asl.asl_reason,
                    "image_url": asl.image_url,
                    "reject_reason": asl.reject_reason,
                    "status": asl.status.value,
                    "created_at": format_datetime(asl.created_at)
                } for asl in self.ask_for_leaves
            ]
        return checkInUsers

    @classmethod
    def get_by_id(cls, check_in_user_id: int):
        session = Session()
        try:
            from Model.CheckIn import CheckIn
            return session.query(cls).options(
                joinedload(cls.user),
                joinedload(cls.check_in).joinedload(CheckIn.schedule),  # 假设 CheckIn 有 schedule 属性
                joinedload(cls.ask_for_leaves)
            ).filter(cls.id == check_in_user_id).first()
        finally:
            session.close()

    @classmethod
    def get_all_by_user_and_date_range(cls, user_id: int, start: datetime, end: datetime, type: str):
        session = Session()
        try:
            if type == 'checkin_time':
                from Model.CheckIn import CheckIn
                return session.query(cls).join(CheckIn).filter(
                    cls.user_id == user_id,
                    CheckIn.check_in_start_time >= start,
                    CheckIn.check_in_end_time <= end
                ).options(
                    joinedload(cls.user),
                    joinedload(cls.check_in).joinedload(CheckIn.schedule),
                    joinedload(cls.ask_for_leaves)
                ).all()
            else:
                from Model.CheckIn import CheckIn
                from Model.Schedule import Schedule
                return session.query(cls).join(CheckIn, cls.check_in).join(Schedule, CheckIn.schedule).filter(
                    cls.user_id == user_id,
                    Schedule.schedule_start_time >= start,
                    Schedule.schedule_start_time <= end
                ).options(
                    joinedload(cls.user),
                    joinedload(cls.check_in).joinedload(CheckIn.schedule),
                    joinedload(cls.ask_for_leaves)
                ).all()
        finally:
            session.close()

    @classmethod
    def get_all_by_date_range(cls, start: datetime, end: datetime, type: str):
        session = Session()
        try:
            if type == 'checkin_time':
                from Model.CheckIn import CheckIn
                return session.query(cls).join(CheckIn).filter(
                    CheckIn.check_in_start_time >= start,
                    CheckIn.check_in_end_time <= end
                ).options(
                    joinedload(cls.user),
                    joinedload(cls.check_in).joinedload(CheckIn.schedule),
                    joinedload(cls.ask_for_leaves)
                ).all()
            else:
                from Model.CheckIn import CheckIn
                from Model.Schedule import Schedule
                return session.query(cls).join(CheckIn, cls.check_in).join(Schedule, CheckIn.schedule).filter(
                    Schedule.schedule_start_time >= start,
                    Schedule.schedule_start_time <= end
                ).options(
                    joinedload(cls.user),
                    joinedload(cls.check_in).joinedload(CheckIn.schedule),
                    joinedload(cls.ask_for_leaves)
                ).all()
        finally:
            session.close()

    @classmethod
    def update(cls, check_in_user_id: int, **kwargs):
        session = Session()
        try:
            target = session.query(cls).filter_by(id=check_in_user_id).first()
            if not target:
                return None
            for key, value in kwargs.items():
                if hasattr(target, key):
                    setattr(target, key, value)
            session.commit()
            return target
        finally:
            session.close()
