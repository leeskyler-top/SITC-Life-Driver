import enum
from .globals import Base, format_datetime, Session
from sqlalchemy import Column, Integer, Boolean, ForeignKey, Text, Enum, func, DateTime
from sqlalchemy import or_, and_


class MsgTypeEnum(enum.Enum):
    PRIVATE = 'PRIVATE'
    PUBLIC = 'PUBLIC'
    ADMIN = 'ADMIN'


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=True)
    msg_text = Column(Text, nullable=False)
    msg_type = Column(Enum(MsgTypeEnum), nullable=False)
    status = Column(Boolean, nullable=True, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "msg_text": self.msg_text,
            "msg_type": self.msg_type,
            "status": self.status,
            "created_at": format_datetime(self.created_at),
            "updated_at": format_datetime(self.updated_at)
        }

    @classmethod
    def get_message_by_id(cls, message_id):
        session = Session()
        try:
            message = session.query(Message).filter_by(id=message_id).first()
            if message:
                return message.to_dict()
            return None
        finally:
            session.close()

    # 添加消息
    @classmethod
    def add_message(cls, user_id, msg_text, msg_type):
        session = Session()
        try:
            message = Message(user_id=user_id, msg_text=msg_text, msg_type=MsgTypeEnum(msg_type))
            session.add(message)
            session.commit()
            return message.to_dict()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # 获取某用户的消息（私有 + 公共），按时间倒序
    @classmethod
    def list_user_messages(cls, user_id: int, is_admin: bool = False):
        session = Session()
        try:
            filters = [
                Message.msg_type == MsgTypeEnum.PUBLIC,
                and_(Message.msg_type == MsgTypeEnum.PRIVATE, Message.user_id == user_id)
            ]

            if is_admin:
                filters.append(Message.msg_type == MsgTypeEnum.ADMIN)

            messages = session.query(Message).filter(
                or_(*filters)
            ).order_by(Message.created_at.desc()).all()

            return [m.to_dict() for m in messages]
        finally:
            session.close()

    # 设置某条消息为已读
    @classmethod
    def mark_message_read_by_id(cls, message_id: int):
        session = Session()
        try:
            message = session.query(Message).filter_by(id=message_id).first()
            if message:
                message.status = True
                session.commit()
                return message.to_dict()
            return None
        finally:
            session.close()

    # 将某用户所有私人消息设为已读
    @classmethod
    def mark_all_private_messages_read(cls, user_id: int):
        session = Session()
        try:
            updated_count = session.query(Message).filter_by(user_id=user_id, msg_type=MsgTypeEnum.PRIVATE,
                                                             status=False) \
                .update({Message.status: True})
            session.commit()
            return updated_count
        finally:
            session.close()
