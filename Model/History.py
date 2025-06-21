import enum
from datetime import datetime, timedelta

from sqlalchemy.orm import relationship, joinedload
from .globals import Base, Session
from sqlalchemy import Column, Integer, ForeignKey, Text, Enum, func, DateTime

class MethodEnum(enum.Enum):
    GET = 'GET'
    POST = 'POST'
    PATCH = 'PATCH'
    DELETE = 'DELETE'
    PUT = 'PUT'
    OPTION = 'OPTION'

class History(Base):
    __tablename__ = 'histories'
    user = relationship("User")

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))
    url = Column(Text)
    method = Column(Enum(MethodEnum))
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "user": {
                "studentId": self.user.studentId,
                "name": self.user.name,
                "department": self.user.department.value,
                "classname": self.user.classname,
            },
            "url": self.url,
            "method": self.method.value,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

    # 添加消息
    @classmethod
    def add_history(cls, user_id, method, url):
        session = Session()
        try:
            history = History(user_id=user_id, method=method, url=url)
            session.add(history)
            session.commit()
            return history.to_dict()
        except Exception as e:
            session.rollback()
            print(e)
        finally:
            session.close()

    @classmethod
    def get_all_histories(cls):
        session = Session()
        histories = session.query(cls).options(joinedload(cls.user)).all()
        session.close()
        histories_list = [history.to_dict() for history in histories]
        return histories_list

    @classmethod
    def cleanup_old_records(cls, save_histories_days=30, max_records=None):
        session = Session()
        try:
            # 条件1：基于时间清理
            time_cutoff = datetime.utcnow() - timedelta(days=save_histories_days)
            time_deleted = session.query(cls)\
                .filter(cls.created_at < time_cutoff)\
                .delete(synchronize_session=False)

            # 条件2：基于数量清理（如果设置了max_records）
            count_deleted = 0
            if max_records is not None:
                total = session.query(func.count(cls.id)).scalar()
                if total > max_records:
                    # 计算需要删除的超出数量
                    excess = total - max_records
                    # 找出最旧的excess条记录
                    oldest_ids = [
                        rec_id for (rec_id,) in session.query(cls.id)
                        .order_by(cls.created_at)
                        .limit(excess)
                        .all()
                    ]
                    count_deleted = session.query(cls)\
                        .filter(cls.id.in_(oldest_ids))\
                        .delete(synchronize_session=False)

            session.commit()
            return {
                "time_deleted": time_deleted,
                "count_deleted": count_deleted,
                "remaining": session.query(func.count(cls.id)).scalar()
            }
        except Exception as e:
            session.rollback()
            print(e)
        finally:
            session.close()
