from .globals import Session, format_datetime, Base, SoftDeleteMixin
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import Column, Integer, String, Enum
import enum
from sqlalchemy.sql import func
from sqlalchemy import DateTime, exists
from sqlalchemy import UniqueConstraint


class DepartmentEnum(enum.Enum):
    INFORMATION = "信息技术系"
    BUSINESS = "商务管理系"
    MANUFACTURING = "智能制造系"
    MATERIALS = "材料与检测系"
    PUBLIC = "公共基础部"
    CYLC = "校团委"
    OTHERS = "其它"


class StudentClass(SoftDeleteMixin, Base):
    __tablename__ = 'student_classes'
    __table_args__ = (
        UniqueConstraint('class_name', name="uq_class_name"),
        UniqueConstraint('building', 'room', name='uq_building_room')  # 确保同一栋楼和教室的组合唯一
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    department = Column(Enum(DepartmentEnum), nullable=False)
    grade = Column(String(50), nullable=False)
    class_name = Column(String(50), nullable=False)
    building = Column(String(50), nullable=True)
    room = Column(String(50), nullable=True)
    class_adviser_id = Column(String(50), nullable=True)  # 班主任工号
    class_adviser_name = Column(String(50), nullable=True)  # 班主任姓名
    monitor_id = Column(String(50), nullable=True)  # 班长学籍号
    monitor_name = Column(String(50), nullable=True)  # 班长姓名
    labor_id = Column(String(50), nullable=True)  # 劳动委员学籍号
    labor_name = Column(String(50), nullable=True)  # 劳动委员姓名
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # 将 StudentClass 对象转换为 JSON 格式的字典
    def to_dict(self):
        return {
            "id": self.id,
            "department": self.department.value,
            "grade": self.grade,
            "class_name": self.class_name,
            "building": self.building,
            "room": self.room,
            "class_adviser_id": self.class_adviser_id,
            "class_adviser_name": self.class_adviser_name,
            "monitor_id": self.monitor_id,
            "monitor_name": self.monitor_name,
            "labor_id": self.labor_id,
            "labor_name": self.labor_name,
            "created_at": format_datetime(self.created_at),
            "updated_at": format_datetime(self.updated_at)
        }

    @classmethod
    def clear_room_and_building(cls):
        session = Session()
        try:
            # 只保持未被软删除的班级
            classes = cls.query_active(session).all()
            for student_class in classes:
                student_class.building = None
                student_class.room = None
            session.commit()
            return True, "已清空未被软删除班级的楼栋和教室室号信息", 200
        except SQLAlchemyError as e:
            session.rollback()
            return False, f"操作失败: {str(e)}", 500
        finally:
            session.close()

    @classmethod
    def get_student_class_by_id(cls, student_class_id: int):
        session = Session()
        student_class = cls.query_active(session).filter_by(id=student_class_id).first()
        session.close()
        if student_class:
            return student_class.to_dict()
        else:
            return None

    @classmethod
    def delete_student_class_by_id(cls, student_class_id: int):
        session = Session()
        try:
            # 只查询未删除的班级
            student_class = cls.query_active(session).filter_by(id=student_class_id).first()

            if not student_class:
                return False, "班级不存在或已被删除", 404

            # 执行软删除
            student_class.is_deleted = True
            student_class.updated_at = func.now()  # 可选：更新修改时间

            session.commit()
            return True, "班级已标记为删除", 200

        except SQLAlchemyError as e:
            session.rollback()
            return False, f"删除失败: {str(e)}", 500
        finally:
            session.close()

    @classmethod
    def hard_delete_student_class_by_id(cls, student_class_id: int):
        session = Session()
        student_class = session.query(cls).filter_by(id=student_class_id).first()
        if not student_class:
            return False, "班级不存在", 404
        student_class.is_deleted = False
        try:
            # 提交更改到数据库
            session.delete(student_class)
            session.close()
            return True, "班级已永久删除", 200
        except Exception as e:
            session.rollback()
            session.close()
            return False, f"班级永久删除失败: {str(e)}", 500

    @classmethod
    def patch_student_class_by_id(
            cls,
            student_class_id: int,
            department: str = None,
            grade: str = None,
            class_name: str = None,
            building: str = None,
            room: str = None,
            class_adviser_id: str = None,
            class_adviser_name: str = None,
            monitor_id: str = None,
            monitor_name: str = None,
            labor_id: str = None,
            labor_name: str = None
    ):
        # 创建一个新的Session
        session = Session()

        try:
            # 查询班级
            student_class = cls.query_active(session).filter_by(id=student_class_id).first()

            if student_class:
                # 更新字段
                if class_name is not None:
                    student_class.class_name = class_name
                if building is not None:
                    student_class.building = building
                if room is not None:
                    student_class.room = room
                if department is not None:
                    student_class.department = department
                if grade is not None:
                    student_class.grade = grade
                if class_adviser_id is not None:
                    student_class.class_adviser_id = class_adviser_id
                if class_adviser_name is not None:
                    student_class.class_adviser_name = class_adviser_name
                if monitor_id is not None:
                    student_class.monitor_id = monitor_id
                if monitor_name is not None:
                    student_class.monitor_name = monitor_name
                if labor_id is not None:
                    student_class.labor_id = labor_id
                if labor_name is not None:
                    student_class.labor_name = labor_name

                # 验证字段有效性
                if department not in DepartmentEnum._value2member_map_:
                    return False, "部门无效", 422

                # 转换字段值
                student_class.department = DepartmentEnum(department)

                # 提交事务
                session.commit()
                return True, "更新成功", 200
            else:
                return False, "班级不存在", 404
        except SQLAlchemyError as e:
            session.rollback()  # 回滚事务
            return False, f"数据库操作失败: {str(e)}", 500
        finally:
            session.close()  # 确保会话被关闭

    @classmethod
    def create_student_class_in_db(
            cls,
            department: str,
            grade: str,
            class_name: str,
            building: str = None,
            room: str = None,
            class_adviser_id: str = None,
            class_adviser_name: str = None,
            monitor_id: str = None,
            monitor_name: str = None,
            labor_id: str = None,
            labor_name: str = None,
    ):
        session = Session()

        # 验证唯一性
        existing_class = session.query(cls).filter_by(building=building, room=room).first()
        if existing_class:
            return False, "相同楼栋和教室号组合已存在", 400

        # 验证字段有效性
        if department not in DepartmentEnum._value2member_map_:
            return False, "部门无效", 422

        department_enum = DepartmentEnum(department)

        student_class = cls(
            department=department_enum,
            grade=grade,
            class_name=class_name,
            building=building,
            room=room,
            class_adviser_id=class_adviser_id,
            class_adviser_name=class_adviser_name,
            monitor_id=monitor_id,
            monitor_name=monitor_name,
            labor_id=labor_id,
            labor_name=labor_name
        )
        session.add(student_class)  # 将班级对象添加到会话

        try:
            session.commit()  # 提交事务，保存数据到数据库
            session.refresh(student_class)  # 刷新对象
        except IntegrityError as e:
            session.rollback()  # 回滚事务
            session.close()  # 关闭会话
            return False, f"创建班级失败: 违反唯一性", 500
        except Exception as e:
            session.rollback()  # 回滚事务
            session.close()  # 关闭会话
            return False, f"创建班级失败: {str(e)}", 500

        session.close()  # 关闭会话
        return True, student_class.to_dict(), 201  # 返回创建的班级对象

    @classmethod
    def get_all_student_classes(cls):
        session = Session()
        student_classes = cls.query_active(session).all()  # 获取所有班级
        session.close()
        student_classes_list = [student_class.to_dict() for student_class in student_classes]
        return student_classes_list

    @classmethod
    def get_all_deleted_student_classes(cls):
        session = Session()
        student_classes = cls.query_inactive(session).all()  # 获取所有班级
        session.close()
        student_classes_list = [student_class.to_dict() for student_class in student_classes]
        return student_classes_list

    @classmethod
    def restore_deleted_student_class(cls, student_class_id):
        session = Session()
        student_class = session.query(cls).filter_by(id=student_class_id).first()
        if not student_class:
            return False, "班级不存在", 404
        student_class.is_deleted = False
        try:
            # 提交更改到数据库
            session.commit()
            session.close()
            return True, "班级已恢复", 200
        except Exception as e:
            session.rollback()
            session.close()
            return False, f"班级恢复失败: {str(e)}", 500
