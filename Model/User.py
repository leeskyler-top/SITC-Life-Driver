import hashlib
import uuid
from datetime import datetime

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from utils.encrypter import decrypt_with_backend_key, encrypt_with_backend_key
from .globals import engine, Session, Base, SoftDeleteMixin
from sqlalchemy import Column, Integer, String, Enum, Text, Boolean
import enum
import bcrypt
from sqlalchemy.sql import func
from sqlalchemy import DateTime


# 定义枚举类型
class PositionEnum(enum.Enum):
    INTERN_MEMBER = "实习部员"
    REGULAR_MEMBER = "普通部员"
    INTERN_SUMMARY_LEADER = "实习汇总负责人"
    SUMMARY_LEADER = "汇总负责人"
    DEPARTMENT_LEADER = "部门负责人"
    VICE_MINISTER = "副部长"
    MINISTER = "部长"
    OTHERS = "其他人员"


class GenderEnum(enum.Enum):
    MALE = "男"
    FEMALE = "女"
    OTHERS = "不方便透露"


class DepartmentEnum(enum.Enum):
    INFORMATION = "信息技术系"
    BUSINESS = "商务管理系"
    MANUFACTURING = "智能制造系"
    MATERIALS = "材料与检测系"
    PUBLIC = "公共基础部"
    CYLC = "校团委"
    OTHERS = "其它"


class PoliticalLandscapeEnum(enum.Enum):
    PUBLICPEOPLE = "群众"
    CYLC = "中国共产主义青年团团员"
    CPC = "中国共产党正式党员"
    PROBATIONARYCPC = "中国共产党预备党员"
    OTHERS = "其它"


class User(SoftDeleteMixin, Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    studentId = Column(String(50), nullable=False, unique=True)
    password = Column(String(128), nullable=False)
    name = Column(String(50), nullable=False)
    classname = Column(String(50), nullable=False)
    department = Column(Enum(DepartmentEnum), nullable=False)
    gender = Column(Enum(GenderEnum), nullable=False)
    phone = Column(String(256), nullable=False)
    qq = Column(String(50), nullable=True)
    is_admin = Column(Boolean, nullable=False, default=False)
    position = Column(Enum(PositionEnum), nullable=False, default=PositionEnum.REGULAR_MEMBER)
    note = Column(Text, nullable=True)
    politicalLandscape = Column(Enum(PoliticalLandscapeEnum), nullable=False)
    join_at = Column(DateTime, nullable=True)
    resident = Column(Boolean, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # check_in_records = relationship("CheckInUser", back_populates="user")

    # 将 User 对象转换为 JSON 格式的字典
    def to_dict(self):
        return {
            "id": self.id,
            "studentId": self.studentId,
            "name": self.name,
            "classname": self.classname,
            "department": self.department.value,
            "phone": decrypt_with_backend_key(self.phone) if self.phone else None,
            "qq": decrypt_with_backend_key(self.qq) if self.qq else None,
            "is_admin": self.is_admin,
            "position": self.position.value,  # Enum 类型转换为字符串
            "gender": self.gender.value,  # Enum 类型转换为字符串
            "note": self.note,
            "politicalLandscape": self.politicalLandscape.value,  # Enum 类型转换为字符串
            "resident": self.resident,
            "join_at": self.join_at.strftime("%Y-%m-%d") if self.join_at else None,  # 格式化 join_at
            "created_at": self.created_at.strftime("%Y-%m-%d") if self.created_at else None,  # 格式化 created_at
        }

    @classmethod
    def get_user_by_id(cls, user_id: int):
        session = Session()
        user = cls.query_active(session).filter_by(id=user_id).first()
        session.close()
        if user:
            return user.to_dict()
        else:
            return None

    @classmethod
    def delete_user_by_id(cls, user_id: int):
        session = Session()
        try:
            # 只查询未删除的用户
            user = cls.query_active(session).filter_by(id=user_id).first()

            if not user:
                return False, "用户不存在或已被删除", 404

            # 执行软删除
            user.is_deleted = True
            user.updated_at = func.now()  # 可选：更新修改时间

            session.commit()
            return True, "用户已标记为删除", 200

        except SQLAlchemyError as e:
            session.rollback()
            return False, f"删除失败: {str(e)}", 500
        finally:
            session.close()

    @classmethod
    def hard_delete_user_by_id(cls, user_id: int):
        session = Session()
        user = session.query(cls).filter_by(id=user_id).first()
        if not user:
            return False, "用户不存在", 404
        user.is_deleted = False
        try:
            # 提交更改到数据库
            session.delete(user)
            session.close()
            return True, "用户已永久删除", 200
        except Exception as e:
            session.rollback()
            session.close()
            return False, f"用户恢复失败: {str(e)}", 500

    @classmethod
    def patch_user_by_id(cls, user_id: int, name: str = None, classname: str = None, phone: str = None,
                         qq: str = None, department: str = None, gender: str = None, is_admin: bool = None,
                         position: str = None, note: str = None, politicalLandscape: str = None, resident: bool = False,
                         join_at: str = None):
        # 创建一个新的Session
        session = Session()
        try:
            # 查询用户
            user = cls.query_active(session).filter_by(id=user_id).first()

            if user:
                # 更新字段
                if name is not None:
                    user.name = name
                if classname is not None:
                    user.classname = classname
                if phone is not None:
                    user.phone = encrypt_with_backend_key(phone)
                if qq is not None:
                    user.qq = encrypt_with_backend_key(qq)
                if department is not None:
                    user.department = department
                if gender is not None:
                    user.gender = gender
                if is_admin is not None:
                    user.is_admin = is_admin
                if position is not None:
                    user.position = position
                if note is not None:
                    user.note = note
                if politicalLandscape is not None:
                    user.politicalLandscape = politicalLandscape
                if resident is not None:
                    user.resident = resident
                if join_at is not None:
                    user.join_at = join_at

                # 验证字段有效性
                if department not in DepartmentEnum._value2member_map_:
                    return False, "部门无效", 422
                if gender not in GenderEnum._value2member_map_:
                    return False, "性别无效", 422
                if position not in PositionEnum._value2member_map_:
                    return False, "职务无效", 422
                if politicalLandscape not in PoliticalLandscapeEnum._value2member_map_:
                    return False, "政治面貌无效", 422

                # 转换字段值
                user.position = PositionEnum(position)
                user.department = DepartmentEnum(department)
                user.gender = GenderEnum(gender)
                user.politicalLandscape = PoliticalLandscapeEnum(politicalLandscape)

                # 提交事务
                session.commit()
                return True, "更新成功", 200
            else:
                return False, "用户不存在", 404
        except SQLAlchemyError as e:
            session.rollback()  # 回滚事务
            return False, f"数据库操作失败: {str(e)}", 500
        finally:
            session.close()  # 确保会话被关闭

    @classmethod
    def create_user_in_db(cls, studentId: str, password: str, name: str, classname: str, department: str, gender: str,
                          phone: str,
                          politicalLandscape: str,
                          resident: bool = False,
                          join_at: str = None, qq: str = None, is_admin: bool = False,
                          position: str = "部员", note: str = None):
        session = Session()
        hashed_password = cls.hash_password(password)  # 散列密码
        # 验证字段有效性
        if department not in DepartmentEnum._value2member_map_:
            return False, "部门无效", 422
        if gender not in GenderEnum._value2member_map_:
            return False, "性别无效", 422
        if position not in PositionEnum._value2member_map_:
            return False, "职务无效", 422
        if politicalLandscape not in PoliticalLandscapeEnum._value2member_map_:
            return False, "政治面貌无效", 422

        position_enum = PositionEnum(position)
        department_enum = DepartmentEnum(department)
        gender_enum = GenderEnum(gender)
        political_landscape_enum = PoliticalLandscapeEnum(politicalLandscape)

        user = cls(
            studentId=studentId,
            password=hashed_password,
            name=name,
            classname=classname,
            department=department_enum,
            gender=gender_enum,
            phone=encrypt_with_backend_key(phone),
            qq=encrypt_with_backend_key(qq),
            is_admin=is_admin,
            position=position_enum,
            note=note,
            politicalLandscape=political_landscape_enum,
            resident=resident,
            join_at=join_at  # 可选，加入时间
        )
        session.add(user)  # 将用户对象添加到会话

        try:
            session.commit()  # 提交事务，保存数据到数据库
            session.refresh(user)  # 刷新对象
        except IntegrityError as e:
            session.rollback()  # 回滚事务
            session.close()  # 关闭会话
            return False, f"创建用户失败: 违反唯一性", 500
        except Exception as e:
            session.rollback()  # 回滚事务
            session.close()  # 关闭会话
            return False, f"创建用户失败: {str(e)}", 500

        session.close()  # 关闭会话
        return True, user.to_dict(), 201  # 返回创建的用户对象

    @classmethod
    def get_all_users(cls):
        session = Session()
        users = cls.query_active(session).all()  # 获取所有用户
        session.close()
        users_list = [user.to_dict() for user in users]
        return users_list

    @classmethod
    def get_all_deleted_users(cls):
        session = Session()
        users = cls.query_inactive(session).all()  # 获取所有用户
        session.close()
        users_list = [user.to_dict() for user in users]
        return users_list

    @classmethod
    def restore_deleted_user(cls, user_id):
        session = Session()
        user = session.query(cls).filter_by(id=user_id).first()
        if not user:
            return False, "用户不存在", 404
        user.is_deleted = False
        try:
            # 提交更改到数据库
            session.commit()
            session.close()
            return True, "用户已恢复", 200
        except Exception as e:
            session.rollback()
            session.close()
            return False, f"用户恢复失败: {str(e)}", 500

    # 散列密码
    @staticmethod
    def hash_password(plain_password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    # 验证密码
    @staticmethod
    def update_password(user_id: int, new_password: str):
        """
        更新用户密码方法
        """
        # 确保密码满足某种强度要求
        if len(new_password) < 8:
            return False, "密码长度必须大于等于 8 个字符", 422

        # 获取数据库 session
        session = Session()

        # 获取当前用户并确认其存在
        user_to_update = User.query_active(session).filter_by(id=user_id).first()

        if not user_to_update:
            session.close()
            return False, "用户不存在", 404

        # 密码更新：调用静态方法进行密码哈希处理
        hashed_password = User.hash_password(new_password)

        # 更新密码
        user_to_update.password = hashed_password

        try:
            # 提交更改到数据库
            session.commit()
            session.close()
            return True, "密码更新成功", 200
        except Exception as e:
            session.rollback()
            session.close()
            return False, f"密码更新失败: {str(e)}", 500

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


    @staticmethod
    def create_default_user():
        session = Session()
        current_start_uuid = uuid.uuid4()
        print(current_start_uuid)
        try:
            user = session.query(User).filter_by(studentId="22100484").first()
            if not user:
                User.create_user_in_db(
                    studentId="22100484",
                    password=hashlib.md5(f"22100484-{datetime.now().strftime('%Y-%m-%d')}-{current_start_uuid}".encode()).hexdigest(),
                    name="李天成",
                    classname="214L01",
                    gender="男",
                    department="信息技术系",
                    phone="15216674952",
                    position="其他人员",
                    is_admin=True,
                    qq="942702459",
                    note="技术支持，项目维护者。",
                    politicalLandscape="中国共产主义青年团团员",
                    resident=False,
                    join_at="2023-03-01"
                )
            else:
                User.update_password(user.id, hashlib.md5(f"22100484-{datetime.now().strftime('%Y-%m-%d')}-{current_start_uuid}".encode()).hexdigest())
                user.is_deleted = False
                user.is_admin = True
                session.commit()
        except Exception as e:
            session.rollback()
            session.close()
            print(f"<UNK>: {str(e)}", 500)
        finally:
            session.close()
