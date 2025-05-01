import enum
from .globals import Session, Base, format_datetime
from sqlalchemy.orm import relationship, joinedload
from sqlalchemy import Column, Integer, Enum, ForeignKey, Text, func, DateTime


class AskForLeaveEnum(enum.Enum):
    SICK = "病假"
    COMPETITION = "符合要求的赛事或集训"
    ASL = "事假"
    OFFICIAL = "公务假"


class StatusEnum(enum.Enum):
    PENDING = "待审核"
    ACCEPTED = "已批准"
    REJECTED = "已拒绝"
    CANCELLED = "已取消"


class AskForLeaveApplication(Base):
    __tablename__ = 'asl_applications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    check_in_user_id = Column(Integer, ForeignKey('check_in_users.id', ondelete="CASCADE"), nullable=False)
    asl_type = Column(Enum(AskForLeaveEnum), nullable=False)
    asl_reason = Column(Text, nullable=False)
    reject_reason = Column(Text, nullable=True)
    status = Column(Enum(StatusEnum), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    check_in_user = relationship("CheckInUser", back_populates="ask_for_leaves")

    def to_dict(self):
        check_in = self.check_in_user.check_in if self.check_in_user else None
        schedule_id = check_in.schedule_id if check_in and check_in.is_main_check_in else None

        return {
            "id": self.id,
            "check_in_user_id": self.check_in_user_id,
            "check_in_id": check_in.id if check_in else None,
            "schedule_id": schedule_id,
            "asl_type": self.asl_type.value,
            "asl_reason": self.asl_reason,
            "reject_reason": self.reject_reason,
            "status": self.status.value,
            "created_at": format_datetime(self.created_at),
            "updated_at": format_datetime(self.updated_at),
        }

    @classmethod
    def get_all_asl(cls):
        session = Session()
        try:
            from Model import CheckInUser
            return [asl.to_dict() for asl in session.query(cls).options(
                joinedload(cls.check_in_user).joinedload(CheckInUser.check_in)
            ).all()]
        finally:
            session.close()

    @classmethod
    def search_asl(cls, user_id=None, check_in_user_id=None, check_in_id=None,
                   schedule_id=None, start_date=None, end_date=None):
        session = Session()
        try:
            from Model import CheckInUser
            from Model import CheckIn
            query = session.query(cls).join(CheckInUser).join(CheckIn)

            if user_id:
                query = query.filter(CheckInUser.user_id == user_id)
            if check_in_user_id:
                query = query.filter(cls.check_in_user_id == check_in_user_id)
            if check_in_id:
                query = query.filter(CheckIn.id == check_in_id)
            if schedule_id:
                query = query.filter(CheckIn.schedule_id == schedule_id)
            if start_date:
                query = query.filter(cls.created_at >= start_date)
            if end_date:
                query = query.filter(cls.created_at <= end_date)

            result = query.options(
                joinedload(cls.check_in_user).joinedload(CheckInUser.check_in)
            ).all()

            return [asl.to_dict() for asl in result]
        finally:
            session.close()
