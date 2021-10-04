import uuid, json
from models.pydantic_models import PyCandidate, PyStartAssessment
from models.db_models import Candidate, AppSession
from utils.db.sqlalchemy import AlchemySession

class AssessmentController:

    @classmethod
    def failure(cls, message, obj=None, new: bool = False):
        return {
                'status': 'failure',
                'code': 500,
                'msg': message,
                'new': new,
                'response': obj
            }
    @classmethod
    def success(cls, message, obj=None, new: bool = False):
        return {
            'status': 'success',
            'code': 200,
            'msg': message,
            'new': new,
            'response': obj
        }

    @classmethod
    def create_candidate(cls, pycandidate: PyCandidate):
        new_candidate = False
        try:
            candidate = AlchemySession().session.query(Candidate).filter(Candidate.email==pycandidate.dict().\
                                                                         get('email')).first()
            if not candidate:
                new_candidate = True
                candidate = Candidate(**pycandidate.dict())
                AlchemySession().session.add(candidate)
                AlchemySession().session.commit()
        except Exception as e:
            return cls.failure(e.__str__())
        return cls.success(f"Candidate {new_candidate and 'has been created' or 'already exists '}", candidate, new_candidate)

    @classmethod
    def start_new_assesment(cls, start_assessment: PyStartAssessment):
        new_assessment = False
        try:
            app_session = AlchemySession().session.query(AppSession).\
                filter(AppSession.candidate_id==int(start_assessment.dict().get('candidate_id',0))).first()
            if not app_session:
                new_assessment = True
                assessment_data = start_assessment.dict()
                assessment_data.update({
                    "unique_session_id": uuid.uuid1().__str__(),
                    "assessment_id": 1 #TODO here we can add some random function to choose random assessment
                })
                app_session = AppSession(**assessment_data)
                AlchemySession().session.add(app_session)
                AlchemySession().session.commit()
        except Exception as e:
            return cls.failure(e.__str__())
        return cls.success(f"Assessment {app_session.unique_session_id} "
                           f"{new_assessment and 'has been started' or 'already exists'}",
                           app_session, new_assessment)

    @classmethod
    def get_questions_per_session(cls, unique_session_id: str):
        questions = []
        try:
            app_session = AlchemySession().session.query(AppSession). \
                filter(AppSession.unique_session_id == unique_session_id).first()
            if app_session:
                questions = list({exercise.question.text for page in app_session.assessment.pages
                             for exercise in page.exercises})
        except Exception as e:
            return cls.failure(e.__str__())
        return cls.success(f"These are the question for the session {unique_session_id}", questions)



