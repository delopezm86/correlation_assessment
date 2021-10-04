import os
import uvicorn
import threading
import time
from fastapi import FastAPI, Request
from models import Base, engine
from models.pydantic_models import PyCandidate, PyStartAssessment, PySession
from utils.amqp.manager import AMQPManager
from controllers.controller import AssessmentController

# - generate database schema
Base.metadata.create_all(engine)


debug = True if os.environ.get("DEBUG") else False

app = FastAPI(
    debug=debug,
    title="Correlation Assessment API",
    description="Web service to manage assessment.",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)


def session_timer_processing(unique_session_id: str = '', timer = 3600):
    while timer > 0:
        timer -= 1
        AMQPManager().send_message(message=timer, queue=unique_session_id)
        time.sleep(1)


@app.post(
    "/api/v1/create-candidate",
)
async def createCandidate(candidate: PyCandidate):
    res = AssessmentController.create_candidate(candidate)
    del res['response']
    del res['new']
    return res


@app.post(
    "/api/v1/start-assessment",
)
async def startAssessment(start_assessmet: PyStartAssessment):
    res = AssessmentController.start_new_assesment(start_assessmet)
    if res.get('code', False) == 200:
        try:
            AMQPManager().create_queue(res['response'].unique_session_id)
            unique_session_id = res.get('response', False) and res['response'].unique_session_id or ''
            timer = res.get('response', False) and res['response'].assessment.minutes_duration or 60
            if not res.get('new', False):
                message = AMQPManager().consume_message(queue=unique_session_id, consume_type='all')
                if message:
                    timer = message and message or 60
            threading.Thread(target=session_timer_processing, args=(unique_session_id, timer * 60)).start()
        except Exception as e:
            return {
                'status': 'failure',
                'code': 500,
                'msg': e.__str__()
            }
    del res['response']
    del res['new']
    return res


@app.get(
    "/api/v1/get-questions/{unique_session_id}"
)
async def getQuestions(unique_session_id: str, request: Request):
    res = AssessmentController.get_questions_per_session(unique_session_id)
    del res['new']
    return res

@app.post(
    "/api/v1/submit-answers",
)
async def submitAnswer(pysession: PySession):
    res = AssessmentController.receive_answers(pysession)
    del res['response']
    del res['new']
    return res


@app.post(
    "/api/v1/close-session",
)
async def closeSession(pysession: PySession):
    res = AssessmentController.close_session(pysession.dict().get('unique_session_id',''))
    del res['response']
    del res['new']
    return res


if __name__ == "__main__":

    uvicorn.run(
            app,
            host="0.0.0.0",
            port=8888,
        )



