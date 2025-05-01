from datetime import datetime
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import relationship, validates
from .globals import Session, Base, format_datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, func, UniqueConstraint
from sqlalchemy import DateTime, exists


class CheckIn(Base):
    __tablename__ = 'check_ins'
    __table_args__ = (
        UniqueConstraint('schedule_id', 'is_main_check_in', name='_schedule_main_check_in_uc'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    schedule_id = Column(Integer, ForeignKey('schedules.id'), nullable=False)
    name = Column(String(50), nullable=False)
    check_in_start_time = Column(DateTime, nullable=False)
    check_in_end_time = Column(DateTime, nullable=False)
    is_main_check_in = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    @validates('is_main_check_in')
    def validate_main_check_in(self, key, value):
        if value is True:
            # 应用层验证确保每个 schedule 只有一个主签到
            existing = Session().query(CheckIn).filter(
                CheckIn.schedule_id == self.schedule_id,
                CheckIn.is_main_check_in == True
            ).first()
            if existing and existing.id != self.id:
                raise ValueError("每个值班计划只能有一个主签到记录")
        return value

    # 添加关系
    schedule = relationship("Schedule", back_populates="check_ins")
    check_in_users = relationship("CheckInUser", back_populates="check_in", cascade="all, delete-orphan")

    def to_dict(self):

        return {
            "id": self.id,
            "schedule_id": self.schedule_id,
            "name": self.name,
            "check_in_start_time": format_datetime(self.check_in_start_time),
            "check_in_end_time": format_datetime(self.check_in_end_time),
            "is_main_check_in": self.is_main_check_in,
            "created_at": format_datetime(self.created_at),
            "updated_at": format_datetime(self.updated_at)
        }

    @classmethod
    def get_check_in_by_id(cls, check_in_id: int):
        session = Session()
        try:
            # 使用 joinedload 一次性加载关联的 check_in_users
            from sqlalchemy.orm import joinedload
            check_in = session.query(cls) \
                .options(joinedload(cls.check_in_users)) \
                .filter_by(id=check_in_id) \
                .first()

            if not check_in:
                return None

            result = check_in.to_dict()
            # 添加关联的 check_in_users 数据
            result['check_in_users'] = [
                ciu.to_dict()  # 使用 CheckInUser 的 to_dict 方法
                for ciu in check_in.check_in_users
            ]
            return result
        finally:
            session.close()

    @classmethod
    def create_check_in_in_db(cls, check_in_id: int, name: str, check_in_start_time: str, check_in_end_time: str,
                              is_main_check_in: bool, need_check_schedule_time: bool = True, check_in_users: list = []):
        session = Session()

        try:
            # 1. 验证所有用户存在
            nonexistent_users = []
            for user_id in check_in_users:
                from Model.User import User
                if not session.query(
                        exists().where(User.id == user_id)
                ).scalar():
                    nonexistent_users.append(str(user_id))

            if len(nonexistent_users) > 0:
                raise ValueError(
                    f"以下用户ID不存在: {', '.join(nonexistent_users)}"
                )

            # 转换时间格式（如果输入是字符串）
            @validates('check_in_start_time', 'check_in_end_time')
            def validate_check_in_times(self, key, value):
                if key == 'check_in_end_time' and hasattr(self, 'check_in_start_time'):
                    if value <= self.check_in_start_time:
                        raise ValueError("签到结束时间必须晚于开始时间")
                return value

            check_in = cls(
                id=check_in_id,
                name=name,
                check_in_start_time=check_in_start_time,
                check_in_end_time=check_in_end_time,
                need_check_schedule_time=need_check_schedule_time,
                is_main_check_in=is_main_check_in
            )
            session.add(check_in)
            session.flush()

            if len(check_in_users) > 0:  # 只有在有用户时才创建关联
                from Model.CheckInUser import CheckInUser
                session.bulk_insert_mappings(
                    CheckInUser,
                    [{
                        'check_in_id': check_in.id,
                        'user_id': uid,
                        'is_necessary': True,
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    } for uid in check_in_users]
                )

            session.flush()

            result = check_in.to_dict()
            result['check_in_users'] = [
                ciu.to_dict()  # 使用 CheckInUser 的 to_dict 方法
                for ciu in check_in.check_in_users
            ]
            return True, check_in.to_dict(), 201

        except IntegrityError as e:
            session.rollback()
            return False, "值班计划已存在（名称/时间/类型组合需唯一）", 400
        except ValueError as e:
            session.rollback()
            return False, str(e), 400
        except Exception as e:
            session.rollback()
            return False, f"创建失败: {str(e)}", 500
        finally:
            session.close()

    @classmethod
    def patch_check_in_by_id(
            cls,
            check_in_id,
            name,
            check_in_start_time,
            check_in_end_time,
            need_check_schedule_time
    ):
        # 创建一个新的Session
        session = Session()
        try:
            check_in = session.query(cls).filter_by(id=check_in_id).first()

            if check_in:
                # 更新字段
                if name is not None:
                    check_in.name = name
                if check_in_start_time is not None:
                    check_in.schedule_start_time = check_in_start_time
                if check_in_end_time is not None:
                    check_in.schedule_start_time = check_in_end_time
                if need_check_schedule_time is not None:
                    check_in.schedule_start_time = need_check_schedule_time

                # 提交事务
                session.commit()
                return True, "更新成功", 200
            else:
                return False, "用户不存在", 404
        except IntegrityError as e:
            session.rollback()  # 回滚事务
            return False, "不能有重复的值班计划（名称、开始时间和类型组合必须唯一）", 400
        except SQLAlchemyError as e:
            session.rollback()  # 回滚事务
            return False, f"数据库操作失败: {str(e)}", 500
        finally:
            session.close()  # 确保会话被关闭

    @classmethod
    def delete_check_in_by_id(cls, check_in_id: int):
        session = Session()
        try:
            check_in = session.query(cls).filter_by(id=check_in_id).first()
            if not check_in:
                session.close()
                return False, "签到记录不存在", 404

            # 检查是否是主签到
            if check_in.is_main_check_in:
                session.close()
                return False, "不能直接删除主签到，请通过删除值班计划来移除", 403

            # 执行删除（会自动级联删除关联的check_in_users）
            session.delete(check_in)
            session.commit()
            return True, "删除成功", 200

        except SQLAlchemyError as e:
            session.rollback()
            return False, f"数据库错误: {str(e)}", 500
        finally:
            session.close()

    @classmethod
    def get_all_check_ins(cls):
        session = Session()
        try:
            # 使用 joinedload 优化查询，避免 N+1 问题
            from sqlalchemy.orm import joinedload
            check_ins = session.query(cls) \
                .options(joinedload(cls.check_in_users)) \
                .all()

            return [
                {
                    **check_in.to_dict(),
                    'check_in_users': [
                        ciu.to_dict()  # 使用 CheckInUser 的 to_dict 方法
                        for ciu in check_in.check_in_users
                    ]
                }
                for check_in in check_ins
            ]
        finally:
            session.close()

    # 添加批量创建方法
    @classmethod
    def bulk_create_check_in_users(cls, check_in_id, user_ids):
        session = Session()
        try:
            session.bulk_insert_mappings(
                cls,
                [{
                    'check_in_id': check_in_id,
                    'user_id': user_id,
                    'created_at': datetime.now()
                } for user_id in user_ids]
            )
            session.commit()
            return True, f"成功创建 {len(user_ids)} 条记录", 201
        except Exception as e:
            session.rollback()
            return False, f"批量创建失败: {str(e)}", 500
        finally:
            session.close()

    @classmethod
    def sync_users(cls, check_in_id: int, user_id_list: list):
        """
        同步签到用户（类似 Laravel 的 sync 方法）
        不传入的用户将被删除，新用户将添加，已有用户保持不变
        """
        session = Session()
        try:
            # 验证 check_in 存在
            check_in = session.query(cls).get(check_in_id)
            if not check_in:
                return False, "签到记录不存在", 404

            # 获取现有关联
            from Model.CheckInUser import CheckInUser
            existing_records = session.query(CheckInUser).filter_by(check_in_id=check_in_id).all()
            existing_user_ids = {r.user_id for r in existing_records}

            # 计算需要添加和删除的用户
            new_user_ids = set(user_id_list)
            to_add = new_user_ids - existing_user_ids
            to_remove = existing_user_ids - new_user_ids

            # 执行删除
            if to_remove:
                session.query(CheckInUser).filter(
                    CheckInUser.check_in_id == check_in_id,
                    CheckInUser.user_id.in_(to_remove)
                ).delete(synchronize_session=False)

            # 执行添加
            if to_add:
                session.bulk_insert_mappings(
                    CheckInUser,
                    [{
                        'check_in_id': check_in_id,
                        'user_id': user_id,
                        'created_at': datetime.now()
                    } for user_id in to_add]
                )

            session.commit()
            result = {
                "added": len(to_add),
                "removed": len(to_remove),
                "total": len(user_id_list)
            }
            return True, f"{result}", 200

        except SQLAlchemyError as e:
            session.rollback()
            return False, f"同步失败: {str(e)}", 500
        finally:
            session.close()
