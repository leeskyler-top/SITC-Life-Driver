from .globals import Session, format_datetime, Base
from datetime import timedelta, datetime
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import relationship, joinedload
from sqlalchemy import Column, Integer, String, Enum
import enum
from sqlalchemy.sql import func
from sqlalchemy import DateTime, exists
from sqlalchemy import UniqueConstraint


class TypeEnum(enum.Enum):
    AFTERSCHOOL = "放学"
    NOON = "午间"
    NIGHT = "晚间"
    MORNING = "早间"
    OTHERS = "其它"


class Schedule(Base):
    __tablename__ = 'schedules'
    __table_args__ = (
        UniqueConstraint('schedule_name', 'schedule_start_time', 'schedule_type',
                         name='_schedule_name_start_time_type_uc'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    schedule_name = Column(String(50), nullable=False)
    schedule_start_time = Column(DateTime, nullable=False)
    schedule_type = Column(Enum(TypeEnum), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # 添加关系
    check_ins = relationship("CheckIn", back_populates="schedule", cascade="all, delete-orphan")

    # 将 User 对象转换为 JSON 格式的字典
    def to_dict(self):
        return {
            "id": self.id,
            "schedule_name": self.schedule_name,
            "schedule_start_time": format_datetime(self.schedule_start_time),
            "schedule_type": self.schedule_type.value,
            "created_at": format_datetime(self.created_at),
            "updated_at": format_datetime(self.updated_at)
        }

    @classmethod
    def get_schedule_by_id(cls, schedule_id: int):
        session = Session()
        try:
            schedule = session.query(cls).filter_by(id=schedule_id).first()
            if not schedule:
                return None

            result = schedule.to_dict()
            # 包含所有的 CheckIn 的用户数据
            result['check_ins'] = []
            for check_in in schedule.check_ins:
                check_in_data = check_in.to_dict()
                check_in_data['check_in_users'] = [
                    ciu.to_dict() for ciu in check_in.check_in_users
                ]
                result['check_ins'].append(check_in_data)

            return result
        finally:
            session.close()

    @classmethod
    def delete_schedule_by_id(cls, schedule_id: int):
        session = Session()
        try:
            schedule = session.query(cls) \
                .options(joinedload(cls.check_ins)) \
                .filter_by(id=schedule_id) \
                .first()

            if not schedule:
                return False, "值班计划不存在", 404

            # 这将自动级联删除所有关联的check_ins和check_in_users
            session.delete(schedule)
            session.commit()
            return True, "删除成功", 200

        except SQLAlchemyError as e:
            session.rollback()
            return False, f"数据库错误: {str(e)}", 500
        finally:
            session.close()

    @classmethod
    def patch_schedule_by_id(
            cls,
            schedule_id: int,
            schedule_name: str = None,
            schedule_start_time: str = None,
            schedule_type: str = None
    ):
        # 创建一个新的Session
        session = Session()
        try:
            # 查询用户
            schedule = session.query(cls).filter_by(id=schedule_id).first()

            if schedule:
                # 更新字段
                if schedule_name is not None:
                    schedule.schedule_name = schedule_name
                if schedule_start_time is not None:
                    schedule.schedule_start_time = schedule_start_time
                if schedule_type is not None:
                    schedule.schedule_type = schedule_type

                # 验证字段有效性
                if schedule_type not in TypeEnum._value2member_map_:
                    return False, "值班类型无效", 422

                type_enum = TypeEnum(schedule_type)
                schedule.schedule_type = type_enum

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
    def create_schedule_in_db(cls, schedule_start_time, schedule_name="日常值班", schedule_type="放学"):
        session = Session()
        try:
            # 验证参数
            if schedule_type not in TypeEnum._value2member_map_:
                return False, "值班类型无效", 422

            # 转换时间格式（如果输入是字符串）
            if isinstance(schedule_start_time, str):
                try:
                    schedule_start_time = datetime.strptime(schedule_start_time, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    return False, "时间格式错误，应为 YYYY-MM-DD HH:MM:SS", 400

            # 验证开始时间不能是过去时间
            if schedule_start_time < datetime.now():
                return False, "值班开始时间不能是过去时间", 400

            # 检查是否已存在
            if session.query(exists().where(
                    (cls.schedule_name == schedule_name) &
                    (cls.schedule_start_time == schedule_start_time) &
                    (cls.schedule_type == TypeEnum(schedule_type))
            )).scalar():
                return False, "相同的值班计划已存在", 400

            # 1. 创建Schedule
            schedule = cls(
                schedule_name=schedule_name,
                schedule_start_time=schedule_start_time,
                schedule_type=TypeEnum(schedule_type)
            )
            session.add(schedule)
            session.flush()

            # 2. 创建主CheckIn
            from Model import CheckIn
            main_check_in = CheckIn(
                schedule_id=schedule.id,
                name=f"{schedule_name}-{schedule_start_time.strftime('%Y-%m-%d %H:%M:%S')}-{schedule_type}-主签到",
                need_check_schedule_time=True,
                check_internal=True,
                check_in_start_time=schedule_start_time - timedelta(minutes=25),
                check_in_end_time=schedule_start_time + timedelta(minutes=10),
                is_main_check_in=True
            )
            session.add(main_check_in)

            session.commit()
            session.refresh(schedule)

            # 获取并格式化check_ins
            check_ins_data = []
            for check_in in schedule.check_ins:
                check_in_data = check_in.to_dict()
                # 假设check_in有check_in_users字段需要展开
                check_in_data['check_in_users'] = [
                    ciu.to_dict() for ciu in check_in.check_in_users
                ]
                check_ins_data.append(check_in_data)

            schedule = schedule.to_dict()
            schedule['check_ins'] = check_ins_data
            return True, schedule, 201

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
    def get_all_schedules(cls):
        session = Session()
        try:
            schedules = session.query(cls).all()
            result = []
            for schedule in schedules:
                schedule_data = schedule.to_dict()
                # 包含所有的 CheckIn 和 CheckInUser 数据
                schedule_data['check_ins'] = []
                for check_in in schedule.check_ins:
                    check_in_data = check_in.to_dict()
                    schedule_data['check_ins'].append(check_in_data)

                result.append(schedule_data)
            return result
        finally:
            session.close()
