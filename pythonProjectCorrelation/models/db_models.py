# coding=utf-8
import uuid
from sqlalchemy import Column, String, Integer, Float, Table, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref
from . import Base


class Candidate(Base):
    __tablename__ = 'candidates'

    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)

    def __init__(self, first_name, last_name, email):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email


class Question(Base):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    type = Column(String)
    text = Column(String)
    rate = Column(Float)

    def __init__(self, type, text, rate):
        self.type = type
        self.text = text
        self.rate = rate


class Answer(Base):
    __tablename__ = 'answers'

    id = Column(Integer, primary_key=True)
    text = Column(String)

    def __init__(self, text):
        self.text = text


pages_exercises_association = Table(
    'pages_exercises', Base.metadata,
    Column('page_id', Integer, ForeignKey('pages.id')),
    Column('exercise_id', Integer, ForeignKey('exercises.id'))
)

class Exercise(Base):
    __tablename__ = 'exercises'

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('questions.id'))
    question = relationship("Question", backref=backref("exercises"))
    answer_id = Column(Integer, ForeignKey('answers.id'))
    answer = relationship("Answer", backref=backref("exercises"))
    correct_answer = Column(Boolean)
    pages = relationship(
        "Page", secondary=pages_exercises_association, back_populates="exercises"
    )

    def __init__(self, question_id, answer_id, correct_answer = False):
        self.question_id = question_id
        self.answer_id = answer_id
        self.correct_answer = correct_answer



class Page(Base):
    __tablename__ = 'pages'

    id = Column(Integer, primary_key=True)
    topic = Column(String)
    assessment_id = Column(Integer, ForeignKey('assessments.id'))
    assessment = relationship("Assessment", backref=backref("pages"))
    exercises = relationship(
        "Exercise", secondary=pages_exercises_association, back_populates="pages"
    )

    def __init__(self, topic):
        self.topic = topic


class Assessment(Base):
    __tablename__ = 'assessments'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    minutes_duration = Column(Integer)

    def __init__(self, name, minutes_duration):
        self.name = name
        self.minutes_duration = minutes_duration


class AppSession(Base):
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True)
    unique_session_id = Column(String)
    candidate_id = Column(Integer, ForeignKey('candidates.id'))
    candidate = relationship("Candidate", backref=backref("session"))
    assessment_id = Column(Integer, ForeignKey('assessments.id'))
    assessment = relationship("Assessment", backref=backref("session"))
    time = Column(Float)
    score = Column(Float)
    state = Column(String)

    def __init__(self, candidate_id: int, assessment_id: int, unique_session_id: str = None, state: str = 'draft'):
        self.unique_session_id = unique_session_id and unique_session_id or uuid.uuid1().__str__()
        self.candidate_id = candidate_id
        self.assessment_id = assessment_id
        self.score = 0
        self.time = 0
        self.state = state



class CandidateResponses(Base):
    __tablename__ = 'candidate_responses'

    id = Column(Integer, primary_key=True)
    exercise_id = Column(Integer, ForeignKey('exercises.id'))
    exercise = relationship("Exercise", backref=backref("responses"))
    session_id = Column(Integer, ForeignKey('sessions.id'))
    session = relationship("AppSession", backref=backref("responses"))
    text_response = Column(String)





