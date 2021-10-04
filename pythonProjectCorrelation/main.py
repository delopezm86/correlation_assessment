# import logging
# import os
# import time
# import uvicorn
# from rsmq import RedisSMQ
# from rsmq.consumer import RedisSMQConsumerThread
# from multiprocessing import Process, Queue
# from starlette.status import HTTP_200_OK
# from fastapi import FastAPI, Request, HTTPException, status
# from pydantic import BaseModel
# from app.pseudo_lib import ConOptReq
# import ray
#
# debug = True if os.environ.get("DEBUG") else False
#
#
# REDIS_QUEUE_NAME = "ray-test"
# REDIS_CONNECT_OPTION = False
#
# pqueue = Queue()
#
#
# class Person(BaseModel):
#     # job related inputs
#     name: str
#     age: int
#
# app = FastAPI(
#     debug=debug,
#     title="Blend Generation API",
#     description="Web service to generate blends.",
#     version="0.1.0",
#     openapi_url="/api/v1/openapi.json",
#     docs_url="/docs",
#     redoc_url="/redoc",
# )
#
# class Singleton(type):
#     _instances = {}
#     def __call__(cls, *args, **kwargs):
#         if cls not in cls._instances:
#             cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
#         return cls._instances[cls]
#
#
# class RedisQueuesContainer(metaclass=Singleton):
#     def __init__ (self, REDIS_CONNECT_OPTION = False):
#         blendgen_queue = RedisSMQ(
#             host='localhost', port=6379, qname=REDIS_QUEUE_NAME
#         )
#         blendgen_queue.createQueue(delay=0, vt=30).exceptions(False).execute()
#         self.blendgen_queue = blendgen_queue
#
#
# @app.post(
#     "/api/ray/test-multi-proc",
#     description="""Start ConOpt blend generation""",
#     responses={
#         HTTP_200_OK: {
#             "description": "This description is ignored by FastAPI",
#             "content": {
#                 "application/json": {
#                     "example": {"message": "starting conopt blend generation"}
#                 }
#             },
#         }
#     },
# )
# async def postConOptBlendGeneration(person: Person):
#     return ConOptReq.enqueue_blend_generation(person, RedisQueuesContainer(REDIS_CONNECT_OPTION).blendgen_queue)
#
#
#
#
#
# def get_from_shared_mp_queue(queue):
#     while True:
#         msg = queue.get()
#         if msg:
#             globals()[f"mp_process_{msg[3]}"](*msg[0:3])
#
#
#
# def blendgen_conopt_queue_processor(id, message, rc, ts):
#     pqueue.put((id,message,rc, 'blendgen_queue'))
#     return True
#
# def mp_process_blendgen_queue(id, message, rc):
#     print('***** Start processing Blend Gen *****')
#     time.sleep(3)
#     print('***** Finish processing Blend Gen *****')
#
#
# if __name__ == "__main__":
#     try:
#         ray.init(address='127.0.0.1:6379')
#     except Exception as e:
#         print(e)
#     num_cores = 4
#     consumers = []
#     for _ in range(num_cores):
#         p = Process(target=get_from_shared_mp_queue, args=(pqueue,))
#         # This is critical! The consumer function has an infinite loop
#         # Which means it will never exit unless we set daemon to true
#         p.daemon = True
#         consumers.append(p)
#
#     for process in consumers:
#         process.start()
#
#     redis_queue_consumer = RedisSMQConsumerThread(
#         REDIS_QUEUE_NAME,
#         blendgen_conopt_queue_processor,
#         host='localhost',
#         port=6379,
#         empty_queue_delay=1.0,
#     )
#     # Start the queue consumer threads
#     redis_queue_consumer.start()
#
#     uvicorn.run(
#         app,
#         host="0.0.0.0",
#         port=8888,
#     )

import os
import uvicorn
import threading
import time
from starlette.status import HTTP_200_OK
from collections import defaultdict
from fastapi import FastAPI, Request, HTTPException, status
from models import Base, engine
from models.pydantic_models import PyCandidate, PyStartAssessment, PyGetQuestion
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
            threading.Thread(target=session_timer_processing, args=(unique_session_id, timer)).start()
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


if __name__ == "__main__":

    uvicorn.run(
            app,
            host="0.0.0.0",
            port=8888,
        )


# candidate_one = Candidate('Daniel','Lopez','test@gmail.com')
# sqlsession.add(candidate_one)
# sqlsession.commit()
# sqlsession.close()


# if self.enableAMQPv1 == True:
#     scheme = configuration.getSecret("amqpv1.producer.scheme")
#     address = configuration.getSecret("amqpv1.producer.address")
#     port = configuration.getSecret("amqpv1.producer.port")
#     username = configuration.getSecret("amqpv1.producer.username")
#     password = configuration.getSecret("amqpv1.producer.password")
#     pathPrefix = configuration.getSecret("amqpv1.producer.pathPrefix")
#     path = f"{pathPrefix}{self.jobId}"
#     url = Url(
#         url=f"{address}:{port}",
#         defaults=True,
#         username=username,
#         password=password,
#         scheme=scheme,
#         path=path,
#     )
#     self.producer = AMQPv1MessageProducer(url, logger=fastapi_logger)

#
# if self.enableAMQPv1 == True:
#     msg = MessageProgress(
#         run_id=jobId,
#         status=StatusProgress.PROCESSING,
#         percent=percent,
#         message="Job {} in progress".format(self.jobId),
#     )
#     self.producer.send(msg)


