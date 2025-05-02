import enum
from datetime import datetime
from sqlalchemy.orm import relationship, joinedload
from .globals import Session, Base, format_datetime
from sqlalchemy import Column, Integer, ForeignKey, Boolean, func
from sqlalchemy import DateTime


class CheckInStatusEnum(enum.Enum):
    NOT_STARTED = "未开始"
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
            if asl.status == StatusEnum.ACCEPTED
        ), None)

        if approved_asl:
            return approved_asl.asl_type.value

        if not self.check_in_time:
            if datetime.now() > self.check_in.check_in_end_time:
                return CheckInStatusEnum.ABSENTEEISM.value
            return CheckInStatusEnum.NOT_STARTED.value

        if self.check_in.need_check_schedule_time and schedule_start_time:
            if self.check_in_time > schedule_start_time:
                return CheckInStatusEnum.LATE.value

        return CheckInStatusEnum.NORMAL.value

    def to_dict(self, schedule_start_time=None):
        return {
            "id": self.id,
            "check_in_id": self.check_in_id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "is_necessary": self.is_necessary,
            "check_in_time": format_datetime(self.check_in_time),
            "status": self.get_status(schedule_start_time),
            "created_at": format_datetime(self.created_at),
            "updated_at": format_datetime(self.updated_at)
        }

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
    def get_all_by_user_and_date_range(cls, user_id: int, start: datetime, end: datetime):
        session = Session()
        try:
            from Model.CheckIn import CheckIn
            return session.query(cls).join(CheckIn).filter(
                cls.user_id == user_id,
                CheckIn.check_in_start_time >= start,
                CheckIn.check_in_end_time <= end
            ).options(
                joinedload(cls.check_in).joinedload(CheckIn.schedule),
                joinedload(cls.user),
                joinedload(cls.ask_for_leaves)
            ).all()
        finally:
            session.close()

    @classmethod
    def get_all_by_date_range(cls, start: datetime, end: datetime):
        session = Session()
        try:
            from Model.CheckIn import CheckIn
            return session.query(cls).join(CheckIn).filter(
                CheckIn.check_in_start_time >= start,
                CheckIn.check_in_end_time <= end
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
