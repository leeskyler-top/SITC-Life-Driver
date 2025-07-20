from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import relationship, validates, joinedload

from . import Schedule
from .StudentClass import StudentClass
from .globals import Session, Base, format_datetime
from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, func, exists
from Model.Rule import Rule, ScoreModeEnum


class ClassScore(Base):
    __tablename__ = 'class_scores'

    id = Column(Integer, primary_key=True, autoincrement=True)
    schedule_id = Column(Integer, ForeignKey('schedules.id'), nullable=False)
    student_class_id = Column(Integer, ForeignKey('student_classes.id'), nullable=False)
    rule_id = Column(Integer, ForeignKey('rules.id'), nullable=False)
    score_value = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    schedule = relationship("Schedule")
    student_class = relationship("StudentClass")
    rule = relationship("Rule")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "schedule_id": self.schedule_id,
            "student_class_id": self.student_class_id,
            "rule_id": self.rule_id,
            "rule": self.rule.to_dict(),
            "score_value": self.score_value,
            "created_at": format_datetime(self.created_at),
            "updated_at": format_datetime(self.updated_at)
        }

    @validates('score_value')
    def validate_score_value(self, key, value):
        # 获取规则信息
        session = Session()
        if self.rule_id:
            rule = session.query(Rule).filter_by(id=self.rule_id).first()
            if not rule:
                session.close()
                raise ValueError(f"Rule with ID {self.rule_id} not found.")

            # 根据评分类型处理评分值
            if rule.score_type == ScoreModeEnum.REDUCE:  # 扣分
                if value < rule.min_score:
                    value = rule.min_score  # Set to minimum score if below
                elif value > rule.max_score:
                    value = rule.max_score  # Set to maximum score if above
            elif rule.score_type == ScoreModeEnum.ADD:  # 加分
                if value < 0:  # 不允许负分
                    value = 0
                elif value > rule.max_score:
                    value = rule.max_score  # Set to maximum score if above
        session.close()
        return value  # 返回经过验证的分数值

    @classmethod
    def get_score_by_id(cls, score_id: int):
        session = Session()
        try:
            # 使用 joinedload 来避免 N+1 问题，如果需要的话可以加载相关的 Schedule 和 Rule
            score = session.query(cls).options(joinedload(cls.schedule), joinedload(cls.rule)).filter_by(
                id=score_id).first()
            return score  # 这将返回 score 对象，包含所有字段和关联关系
        finally:
            session.close()

    @classmethod
    def prevent_score_spike(cls, session, schedule_id: int, student_class_id: int, rule_id: int):
        """ 检查当前班级在当前的Schedule下是否已经存在该评分要求。 """
        exists_query = session.query(cls).filter(
            cls.schedule_id == schedule_id,
            cls.student_class_id == student_class_id,
            cls.rule_id == rule_id
        ).first()
        if exists_query:
            raise IntegrityError(f"Class already has a score record for this Rule in the Schedule.")

    @classmethod
    def get_scores_by_schedule_id(cls, schedule_id: int, include_deleted: bool = False):
        session = Session()
        try:
            query = session.query(cls).filter(cls.schedule_id == schedule_id)
            if not include_deleted:
                query = query.join(StudentClass).filter(StudentClass.is_deleted == False)

            return [score.to_dict() for score in query.all()]
        finally:
            session.close()

    @classmethod
    def get_scores_by_time_range(cls, start_time: DateTime, end_time: DateTime, include_deleted: bool = False):
        session = Session()
        try:
            # Assuming Schedule is properly defined with time range
            query = session.query(cls).join(Schedule).filter(Schedule.schedule_start_time >= start_time,
                                                             Schedule.schedule_start_time <= end_time)
            if not include_deleted:
                query = query.join(StudentClass).filter(StudentClass.is_deleted == False)

            return [score.to_dict() for score in query.all()]
        finally:
            session.close()

    @classmethod
    def create_or_update_score(cls, schedule_id: int, student_class_id: int, rule_id: int, score_value: float):
        session = Session()

        try:
            # 检查评分记录是否已存在
            score = session.query(cls).filter_by(schedule_id=schedule_id, student_class_id=student_class_id,
                                                 rule_id=rule_id).first()

            if score:
                # 如果评分记录存在，更新评分
                score.score_value = score_value
                session.commit()
                return True, score.to_dict(), 200
            else:
                # 如果评分记录不存在，创建新的评分
                new_score = cls(schedule_id=schedule_id, student_class_id=student_class_id, rule_id=rule_id,
                                score_value=score_value)
                session.add(new_score)
                session.commit()
                return True, new_score.to_dict(), 201
        except IntegrityError:
            session.rollback()
            return False, "评分记录已存在", 400
        except Exception as e:
            session.rollback()
            return False, str(e), 500
        finally:
            session.close()

    @classmethod
    def delete_score_by_id(cls, score_id: int):
        session = Session()
        try:
            score = session.query(cls).filter_by(id=score_id).first()
            if not score:
                return False, "Score record does not exist", 404

            session.delete(score)
            session.commit()
            return True, "Score deleted successfully", 200
        except Exception as e:
            session.rollback()
            return False, str(e), 500
        finally:
            session.close()
