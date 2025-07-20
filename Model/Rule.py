import enum
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import relationship, joinedload
from .globals import Session, Base, format_datetime, SoftDeleteMixin
from sqlalchemy import Column, Integer, ForeignKey, Boolean, func, String, Enum, Float
from sqlalchemy import DateTime


class ScoreModeEnum(enum.Enum):
    ADD = "加分项"
    REDUCE = "减分项"

class RuleTypeEnum(enum.Enum):
    SUBJECTIVE = "主观评分"
    OBJECTIVE = "客观评分"


class Rule(Base, SoftDeleteMixin):
    __tablename__ = 'rules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_group_id = Column(Integer, ForeignKey('rule_groups.id'), nullable=False)
    rule_name = Column(String(50), nullable=False)
    rule_type = Column(Enum(RuleTypeEnum), nullable=False)
    score_type = Column(Enum(ScoreModeEnum), nullable=False)
    score_step = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    min_score = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    rule_group = relationship("RuleGroup", back_populates="rules", cascade="all, delete-orphan")
    class_scores = relationship("classScore", back_populates="rule", cascade="all, delete-orphan")

    # 将 StudentClass 对象转换为 JSON 格式的字典
    def to_dict(self, include_rule_group=False, class_scores=False):
        rules = {
            "id": self.id,
            "rule_group_id": self.rule_group_id,
            "rule_name": self.rule_name,
            "rule_type": self.rule_type.value,
            "score_type": self.score_type.value,
            "score_step": self.score_step,
            "max_score": self.max_score,
            "min_score": self.min_score,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

        if include_rule_group:
            rules["rule_group"] = self.rule_group.to_dict()

        if class_scores:
            rules["class_scores"] = [score.to_dict() for score in self.class_scores]

        return rules

    @classmethod
    def get_rule_by_id(cls, rule_id: int):
        session = Session()
        rule = cls.query_active(session).filter_by(id=rule_id).first()
        session.close()
        if rule:
            return rule.to_dict()
        else:
            return None

    @classmethod
    def delete_rule_by_id(cls, rule_id: int):
        session = Session()
        try:
            # 只查询未删除的规则
            rule = cls.query_active(session).filter_by(id=rule_id).first()

            if not rule:
                return False, "规则不存在或已被删除", 404

            # 执行软删除
            rule.is_deleted = True
            rule.updated_at = func.now()  # 可选：更新修改时间

            session.commit()
            return True, "规则已标记为删除", 200

        except SQLAlchemyError as e:
            session.rollback()
            return False, f"删除失败: {str(e)}", 500
        finally:
            session.close()

    @classmethod
    def hard_delete_rule_by_id(cls, rule_id: int):
        session = Session()
        rule = session.query(cls).filter_by(id=rule_id).first()
        if not rule:
            return False, "规则不存在", 404
        rule.is_deleted = False
        try:
            # 提交更改到数据库
            session.delete(rule)
            session.close()
            return True, "规则已永久删除", 200
        except Exception as e:
            session.rollback()
            session.close()
            return False, f"规则永久删除失败: {str(e)}", 500

    @classmethod
    def patch_rule_by_id(
            cls,
            rule_id: int,
            rule_name: str = None,
            rule_type: str = None,
            score_type: str = None,
            score_step: int = None,
            max_score: int = None,
            min_score: int = None,
    ):
        # 创建一个新的Session
        session = Session()
        try:
            # 查询规则
            rule = cls.query_active(session).filter_by(id=rule_id).first()

            if rule:
                # 更新字段
                if rule_name is not None:
                    return rule.rule_name
                if rule_type is not None:
                    return rule.rule_type
                if score_type is not None:
                    return rule.score_type
                if score_step is not None:
                    return rule.score_step
                if max_score is not None:
                    return rule.max_score
                if min_score is not None:
                    return rule.min_score

                # 验证字段有效性
                if score_type not in ScoreModeEnum._value2member_map_:
                    return False, "评分类型无效", 422

                if rule_type not in RuleTypeEnum._value2member_map_:
                    return False, "评价类型无效", 422

                # 转换字段值
                rule.score_type = ScoreModeEnum(score_type)

                # 提交事务
                session.commit()
                return True, "更新成功", 200
            else:
                return False, "规则不存在", 404
        except SQLAlchemyError as e:
            session.rollback()  # 回滚事务
            return False, f"数据库操作失败: {str(e)}", 500
        finally:
            session.close()  # 确保会话被关闭

    @classmethod
    def create_rule_in_db(
            cls,
            rule_name: str,
            rule_type: str,
            score_type: str,
            score_step: int,
            max_score: int,
            min_score: int,
    ):
        session = Session()
        # 验证字段有效性
        if score_type not in ScoreModeEnum._value2member_map_:
            return False, "评分类型无效", 422

        if rule_type not in RuleTypeEnum._value2member_map_:
            return False, "规则类型无效", 422

        score_type = ScoreModeEnum(score_type)

        rule = cls(
            rule_name=rule_name,
            rule_type=rule_type,
            score_type=score_type,
            score_step=score_step,
            max_score=max_score,
            min_score=min_score
        )
        session.add(rule)  # 将规则对象添加到会话

        try:
            session.commit()  # 提交事务，保存数据到数据库
            session.refresh(rule)  # 刷新对象
        except IntegrityError as e:
            session.rollback()  # 回滚事务
            session.close()  # 关闭会话
            return False, f"创建规则失败: 违反唯一性", 500
        except Exception as e:
            session.rollback()  # 回滚事务
            session.close()  # 关闭会话
            return False, f"创建规则失败: {str(e)}", 500

        session.close()  # 关闭会话
        return True, rule.to_dict(), 201  # 返回创建的规则对象

    @classmethod
    def get_all_rules(cls):
        session = Session()
        rules = cls.query_active(session).all()  # 获取所有规则
        session.close()
        rules_list = [rule.to_dict() for rule in rules]
        return rules_list

    @classmethod
    def get_all_deleted_rules(cls):
        session = Session()
        rules = cls.query_inactive(session).all()  # 获取所有规则
        session.close()
        rules_list = [rule.to_dict() for rule in rules]
        return rules_list

    @classmethod
    def restore_deleted_rule(cls, rule_id):
        session = Session()
        rule = session.query(cls).filter_by(id=rule_id).first()
        if not rule:
            return False, "规则不存在", 404
        rule.is_deleted = False
        try:
            # 提交更改到数据库
            session.commit()
            session.close()
            return True, "规则已恢复", 200
        except Exception as e:
            session.rollback()
            session.close()
            return False, f"规则恢复失败: {str(e)}", 500
