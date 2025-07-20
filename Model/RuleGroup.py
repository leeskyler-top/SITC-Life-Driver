from sqlalchemy.orm import relationship

from .globals import Session, format_datetime, Base, SoftDeleteMixin
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
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


class RuleGroup(SoftDeleteMixin, Base):
    __tablename__ = 'rule_groups'
    __table_args__ = (
        UniqueConstraint('group_name', name='group_name_unique')
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_name = Column(String(50), nullable=False)
    group_type = Column(Enum(TypeEnum), nullable=False)
    maximum_score = Column(Integer, nullable=False, default=20)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    rules = relationship("Rule", back_populates="rule_groups", cascade="all, delete-orphan")

    # 将 StudentClass 对象转换为 JSON 格式的字典
    def to_dict(self, include_rules=False):
        rules = {
            "id": self.id,
            "group_name": self.group_name,
            "group_type": self.group_type.value,
            "maximum_score": self.maximum_score,
            "created_at": format_datetime(self.created_at),
            "updated_at": format_datetime(self.updated_at)
        }

        if include_rules:
            rules["rules"] = [rule.to_dict() for rule in self.rules]

        return rules

    @classmethod
    def get_rule_group_by_id(cls, rule_group_id: int):
        session = Session()
        rule_group = cls.query_active(session).filter_by(id=rule_group_id).first()
        session.close()
        if rule_group:
            return rule_group.to_dict()
        else:
            return None

    @classmethod
    def delete_rule_group_by_id(cls, rule_group_id: int):
        session = Session()
        try:
            # 只查询未删除的规则组
            rule_group = cls.query_active(session).filter_by(id=rule_group_id).first()

            if not rule_group:
                return False, "规则组不存在或已被删除", 404

            # 执行软删除
            rule_group.is_deleted = True
            rule_group.updated_at = func.now()  # 可选：更新修改时间

            session.commit()
            return True, "规则组已标记为删除", 200

        except SQLAlchemyError as e:
            session.rollback()
            return False, f"删除失败: {str(e)}", 500
        finally:
            session.close()

    @classmethod
    def hard_delete_rule_group_by_id(cls, rule_group_id: int):
        session = Session()
        rule_group = session.query(cls).filter_by(id=rule_group_id).first()
        if not rule_group:
            return False, "规则组不存在", 404
        rule_group.is_deleted = False
        try:
            # 提交更改到数据库
            session.delete(rule_group)
            session.close()
            return True, "规则组已永久删除", 200
        except Exception as e:
            session.rollback()
            session.close()
            return False, f"规则组永久删除失败: {str(e)}", 500

    @classmethod
    def patch_rule_group_by_id(
            cls,
            rule_group_id: int,
            group_name: str = None,
            group_type: str = None,
            maximum_score: int = None,
    ):
        # 创建一个新的Session
        session = Session()
        try:
            # 查询规则组
            rule_group = cls.query_active(session).filter_by(id=rule_group_id).first()

            if rule_group:
                # 更新字段
                if group_name is not None:
                    rule_group.group_name = group_name
                if group_type is not None:
                    rule_group.group_type = group_type
                if maximum_score is not None:
                    rule_group.maximum_score = maximum_score

                # 验证字段有效性
                if group_type not in TypeEnum._value2member_map_:
                    return False, "类型无效", 422

                # 转换字段值
                rule_group.group_type = TypeEnum(group_type)

                # 提交事务
                session.commit()
                return True, "更新成功", 200
            else:
                return False, "规则组不存在", 404
        except SQLAlchemyError as e:
            session.rollback()  # 回滚事务
            return False, f"数据库操作失败: {str(e)}", 500
        finally:
            session.close()  # 确保会话被关闭

    @classmethod
    def create_rule_group_in_db(
            cls,
            group_name: str,
            group_type: str,
            maximum_score: int,
    ):
        session = Session()
        # 验证字段有效性
        if group_type not in TypeEnum._value2member_map_:
            return False, "类型无效", 422

        group_type = TypeEnum(group_type)

        rule_group = cls(
            group_name=group_name,
            group_type=group_type,
            maximum_score=maximum_score
        )
        session.add(rule_group)  # 将规则组对象添加到会话

        try:
            session.commit()  # 提交事务，保存数据到数据库
            session.refresh(rule_group)  # 刷新对象
        except IntegrityError as e:
            session.rollback()  # 回滚事务
            session.close()  # 关闭会话
            return False, f"创建规则组失败: 违反唯一性", 500
        except Exception as e:
            session.rollback()  # 回滚事务
            session.close()  # 关闭会话
            return False, f"创建规则组失败: {str(e)}", 500

        session.close()  # 关闭会话
        return True, rule_group.to_dict(), 201  # 返回创建的规则组对象

    @classmethod
    def get_all_rule_groups(cls):
        session = Session()
        rule_groups = cls.query_active(session).all()  # 获取所有规则组
        session.close()
        rule_groups_list = [rule_group.to_dict() for rule_group in rule_groups]
        return rule_groups_list

    @classmethod
    def get_all_deleted_rule_groups(cls):
        session = Session()
        rule_groups = cls.query_inactive(session).all()  # 获取所有规则组
        session.close()
        rule_groups_list = [rule_group.to_dict() for rule_group in rule_groups]
        return rule_groups_list

    @classmethod
    def restore_deleted_rule_group(cls, rule_group_id):
        session = Session()
        rule_group = session.query(cls).filter_by(id=rule_group_id).first()
        if not rule_group:
            return False, "规则组不存在", 404
        rule_group.is_deleted = False
        try:
            # 提交更改到数据库
            session.commit()
            session.close()
            return True, "规则组已恢复", 200
        except Exception as e:
            session.rollback()
            session.close()
            return False, f"规则组恢复失败: {str(e)}", 500
