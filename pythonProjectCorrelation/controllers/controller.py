import uuid, json
from models.pydantic_models import PyCandidate, PyStartAssessment, PySession
from models.db_models import Candidate, AppSession, CandidateResponses, Exercise
from utils.db.sqlalchemy import AlchemySession
from utils.amqp.manager import AMQPManager

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
    def get_session(cls, unique_session_id: str):
        return AlchemySession().session.query(AppSession). \
                filter(AppSession.unique_session_id == unique_session_id).first()

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
                filter(AppSession.state=='in_progress').\
                filter(AppSession.candidate_id==int(start_assessment.dict().get('candidate_id',0))).first()
            if not app_session:
                new_assessment = True
                assessment_data = start_assessment.dict()
                assessment_data.update({
                    "unique_session_id": uuid.uuid1().__str__(),
                    "assessment_id": 1, #TODO here we can add some random function to choose random assessment
                    "state": 'in_progress'
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
            app_session = cls.get_session(unique_session_id)
            if app_session:
                questions = list({exercise.question.text for page in app_session.assessment.pages
                             for exercise in page.exercises})
        except Exception as e:
            return cls.failure(e.__str__())
        return cls.success(f"These are the question for the session {unique_session_id}", questions)

    @classmethod
    def receive_answers(cls, pysession: PySession):
        message = "There is not in progress session"
        pysession_json = json.loads(pysession.json())
        try:
            app_session = cls.get_session(pysession_json['unique_session_id'])
            if app_session and app_session.state == 'in_progress':
                message = "Answers received successfully"
                received_exercise_ids = [e['exercise_id'] for e in pysession_json['answers']]

                received_exercises = AlchemySession().session.query(Exercise).\
                    filter(Exercise.id.in_(received_exercise_ids)).all()
                answered_questions = set([exercise.question_id for exercise in received_exercises])

                current_responses = AlchemySession().session.query(CandidateResponses).\
                    filter(CandidateResponses.session_id==app_session.id).all()

                to_delete_responses = [response.id for response in \
                                       current_responses if response.exercise.question.id in answered_questions]

                AlchemySession().session.query(CandidateResponses).\
                    filter(CandidateResponses.id.in_(to_delete_responses)).delete()
                AlchemySession().session.commit()

                AlchemySession().session.bulk_save_objects([
                    CandidateResponses(
                        exercise_id=exercise_id,
                        session_id=app_session.id,
                        text_response=pysession_json['text_response']
                    ) for exercise_id in received_exercise_ids
                ])
                AlchemySession().session.commit()
        except Exception as e:
            return cls.failure(e.__str__())
        return cls.success(message)

    @classmethod
    def close_session(cls, unique_session_id: str, time: int = None):
        message = f"There is no session for uuid: {unique_session_id}"
        try:
            app_session = cls.get_session(unique_session_id)
            if app_session and app_session.state == 'in_progress':
                message = AMQPManager().consume_message(queue=unique_session_id, consume_type='all')

                AlchemySession().session.query(AppSession). \
                    filter(AppSession.id==app_session.id).update({
                    AppSession.state:'done',
                    AppSession.time: time and (app_session.assessment.minutes_duration - time) or
                                     (message and (app_session.assessment.minutes_duration - message) or \
                             app_session.assessment.minutes_duration)
                })
                AlchemySession().session.commit()
                message = f"Session uuid {unique_session_id} has been close successfully"
        except Exception as e:
            return cls.failure(e.__str__())
        return cls.success(message, app_session)





